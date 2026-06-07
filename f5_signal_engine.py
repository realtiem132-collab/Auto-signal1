# ============================================================
# f5_signal_engine.py  —  Signal generate + filter করে
# ============================================================

import random
import logging
from datetime import datetime, timedelta
import pytz

from f2_config import (
    PAIRS, MIN_CONFLUENCE, ENTRY_OFFSET_MIN,
    DISPLAY_TZ, SIGNAL_TZ, FIBONACCI_STEPS, MAX_LOSS_STREAK
)
from f3_data_fetcher import fetch_candles, get_current_price
from f4_indicators import analyze

logger = logging.getLogger(__name__)

# ── Session state ──
_state = {
    "loss_streak": 0,
    "mm_step":     0,
    "wins":        0,
    "losses":      0,
    "total":       0,
}


def get_state() -> dict:
    return _state.copy()


def update_result(won: bool):
    """Trade result আসলে state update করে।"""
    _state["total"] += 1
    if won:
        _state["wins"]       += 1
        _state["loss_streak"] = 0
        _state["mm_step"]     = 0
    else:
        _state["losses"]     += 1
        _state["loss_streak"] += 1
        _state["mm_step"]     = min(_state["mm_step"] + 1, len(FIBONACCI_STEPS) - 1)


def current_amount() -> int:
    return FIBONACCI_STEPS[_state["mm_step"]]


def is_trading_allowed() -> bool:
    return _state["loss_streak"] < MAX_LOSS_STREAK


def _price_precision(pair: str) -> int:
    if "JPY" in pair:
        return 3
    return 5


def fmt_price(pair: str, price: float) -> str:
    return f"{price:.{_price_precision(pair)}f}"


def _entry_time_str(offset_min: int = ENTRY_OFFSET_MIN) -> tuple[str, int, int]:
    """
    এখনকার Bangladesh সময় + offset_min = entry time
    :00 বা :30 এ পড়লে +1 করে safe করে
    Returns: (time_str "HH:MM:00", hour, minute)
    """
    tz_bd = pytz.timezone(DISPLAY_TZ)
    now   = datetime.now(tz_bd)
    entry = now + timedelta(minutes=offset_min)

    h = entry.hour
    m = entry.minute

    # :00 বা :30 risky — candle open
    if m % 30 == 0:
        m += 1
    if m >= 60:
        m -= 60
        h  = (h + 1) % 24

    return f"{h:02d}:{m:02d}:00", h, m


def generate_signal(pair: str | None = None) -> dict | None:
    """
    একটি pair-এর জন্য signal generate করে।
    pair=None হলে PAIRS থেকে random বাছে।
    Returns signal dict বা None (skip)।
    """
    if not is_trading_allowed():
        logger.info("Max loss streak reached — trading stopped")
        return None

    if pair is None:
        pair = random.choice(PAIRS)

    # ── Data fetch ──
    df = fetch_candles(pair, outputsize=50)
    if df is None or len(df) < 30:
        logger.warning(f"Skipping {pair} — insufficient data")
        return None

    # ── Analyze ──
    result = analyze(df)
    direction = result["direction"]

    if direction is None:
        logger.info(f"Skipping {pair} — score tie")
        return None

    # ── Confluence filter ──
    # votes-এ কতটি indicator direction-এর সাথে agree করে
    agree_count = sum(1 for v in result["votes"].values() if v == direction)
    if agree_count < MIN_CONFLUENCE:
        logger.info(
            f"Skipping {pair} — confluence {agree_count}/{MIN_CONFLUENCE} "
            f"(dir={direction})"
        )
        return None

    # ── Volatility filter ──
    if result["volatility"] < 0.0015:
        logger.info(f"Skipping {pair} — low volatility {result['volatility']}")
        return None

    # ── Entry time ──
    time_str, entry_h, entry_m = _entry_time_str()

    # ── Current price ──
    live_price = get_current_price(pair) or result["price"]

    return {
        "pair":        pair,
        "direction":   direction,
        "entry_time":  time_str,
        "entry_h":     entry_h,
        "entry_m":     entry_m,
        "price":       live_price,
        "price_str":   fmt_price(pair, live_price),
        "confidence":  result["confidence"],
        "rsi":         result["rsi"],
        "macd_hist":   result["macd"]["histogram"],
        "bb_mid":      result["bb"]["mid"],
        "bb_pct_b":    result["bb"]["pct_b"],
        "mtf_agree":   result["mtf"]["agree"],
        "mtf_m1":      result["mtf"]["m1"],
        "mtf_m5":      result["mtf"]["m5"],
        "volatility":  result["volatility"],
        "votes":       result["votes"],
        "score":       result["score"],
        "amount":      current_amount(),
        "mm_step":     _state["mm_step"] + 1,
        "wins":        _state["wins"],
        "losses":      _state["losses"],
    }


def scan_all_pairs() -> dict | None:
    """
    সব pair scan করে সবচেয়ে ভালো signal return করে।
    """
    best = None
    for pair in PAIRS:
        sig = generate_signal(pair)
        if sig is None:
            continue
        # সবচেয়ে বেশি confidence যেটার সেটা নেয়
        if best is None or sig["confidence"] > best["confidence"]:
            best = sig
    return best
