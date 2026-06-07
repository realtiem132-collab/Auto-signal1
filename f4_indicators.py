# ============================================================
# f4_indicators.py  —  RSI, MACD, Bollinger, MTF calculation
# ============================================================

import pandas as pd
import numpy as np
from f2_config import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD
)


# ── RSI ──────────────────────────────────────────────────────
def calc_rsi(close: pd.Series, period: int = RSI_PERIOD) -> float:
    if len(close) < period + 1:
        return 50.0
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2)


# ── EMA helper ───────────────────────────────────────────────
def calc_ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


# ── MACD ─────────────────────────────────────────────────────
def calc_macd(close: pd.Series):
    """
    Returns dict: {macd, signal, histogram}
    """
    ema_fast   = calc_ema(close, MACD_FAST)
    ema_slow   = calc_ema(close, MACD_SLOW)
    macd_line  = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, MACD_SIGNAL)
    histogram   = macd_line - signal_line
    return {
        "macd":      round(float(macd_line.iloc[-1]), 6),
        "signal":    round(float(signal_line.iloc[-1]), 6),
        "histogram": round(float(histogram.iloc[-1]), 6),
    }


# ── Bollinger Bands ──────────────────────────────────────────
def calc_bollinger(close: pd.Series):
    """
    Returns dict: {upper, mid, lower, bandwidth, %b}
    """
    if len(close) < BB_PERIOD:
        mid = float(close.iloc[-1])
        return {"upper": mid, "mid": mid, "lower": mid, "bandwidth": 0, "pct_b": 0.5}

    mid   = close.rolling(BB_PERIOD).mean()
    std   = close.rolling(BB_PERIOD).std()
    upper = mid + BB_STD * std
    lower = mid - BB_STD * std
    price = float(close.iloc[-1])
    m     = float(mid.iloc[-1])
    u     = float(upper.iloc[-1])
    l     = float(lower.iloc[-1])
    bw    = (u - l) / m * 100 if m != 0 else 0
    pct_b = (price - l) / (u - l) if (u - l) != 0 else 0.5

    return {
        "upper":     round(u, 6),
        "mid":       round(m, 6),
        "lower":     round(l, 6),
        "bandwidth": round(bw, 4),
        "pct_b":     round(pct_b, 4),
    }


# ── Volatility (Coefficient of Variation) ────────────────────
def calc_volatility(close: pd.Series) -> float:
    if len(close) < 5:
        return 0.0
    mean = close.mean()
    std  = close.std()
    return round(float(std / mean * 100), 6) if mean != 0 else 0.0


# ── MTF Bias — 1m trend vs 5m trend ─────────────────────────
def calc_mtf_bias(close: pd.Series):
    """
    close = 1m candles
    1m  → last 4 candles
    5m  → last 20 candles (20×1m ≈ 4×5m)
    Returns: {m1: 1/-1, m5: 1/-1, agree: bool}
    """
    if len(close) < 20:
        return {"m1": 1, "m5": 1, "agree": True}

    # 1m trend
    m1_slice = close.iloc[-4:]
    m1 = 1 if float(m1_slice.iloc[-1]) > float(m1_slice.iloc[0]) else -1

    # 5m trend (compare first 5 avg vs last 5 avg of 20 candles)
    m5_early = float(close.iloc[-20:-15].mean())
    m5_late  = float(close.iloc[-5:].mean())
    m5 = 1 if m5_late > m5_early else -1

    return {"m1": m1, "m5": m5, "agree": m1 == m5}


# ── MAIN: সব indicator একসাথে ────────────────────────────────
def analyze(df: pd.DataFrame) -> dict:
    """
    DataFrame (open/high/low/close) নিয়ে সব indicator calculate করে।
    Returns full analysis dict।
    """
    close = df["close"]
    rsi   = calc_rsi(close)
    macd  = calc_macd(close)
    bb    = calc_bollinger(close)
    mtf   = calc_mtf_bias(close)
    vol   = calc_volatility(close)
    price = float(close.iloc[-1])

    # ── Voting: প্রতিটি indicator CALL(+1) বা PUT(-1) vote দেয় ──
    score = 0
    votes = {}

    # RSI vote
    if rsi > 55:
        votes["RSI"] = "CALL"
        score += 1
    elif rsi < 45:
        votes["RSI"] = "PUT"
        score -= 1
    else:
        votes["RSI"] = "NEUTRAL"

    # MACD vote
    if macd["histogram"] > 0:
        votes["MACD"] = "CALL"
        score += 1
    elif macd["histogram"] < 0:
        votes["MACD"] = "PUT"
        score -= 1
    else:
        votes["MACD"] = "NEUTRAL"

    # Bollinger vote
    if price > bb["mid"]:
        votes["BB"] = "CALL"
        score += 1
    elif price < bb["mid"]:
        votes["BB"] = "PUT"
        score -= 1
    else:
        votes["BB"] = "NEUTRAL"

    # MTF vote (5m — double weight)
    if mtf["m5"] > 0:
        votes["MTF"] = "CALL"
        score += 2
    else:
        votes["MTF"] = "PUT"
        score -= 2

    # MTF alignment bonus
    if mtf["agree"]:
        score += mtf["m1"]

    max_score = 6
    confidence = round(50 + (abs(score) / max_score) * 44)
    confidence = max(52, min(94, confidence))

    direction = "CALL" if score > 0 else ("PUT" if score < 0 else None)

    return {
        "direction":  direction,
        "score":      score,
        "confidence": confidence,
        "price":      price,
        "rsi":        rsi,
        "macd":       macd,
        "bb":         bb,
        "mtf":        mtf,
        "volatility": vol,
        "votes":      votes,
    }
