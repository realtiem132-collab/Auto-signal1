# ============================================================
# f3_data_fetcher.py  —  Twelve Data API থেকে candle data আনে
# ============================================================

import requests
import pandas as pd
from datetime import datetime
import pytz
import logging
from f2_config import TWELVEDATA_API_KEY, CANDLE_MINS, SIGNAL_TZ

logger = logging.getLogger(__name__)

BASE_URL = "https://api.twelvedata.com"


def fetch_candles(pair: str, outputsize: int = 50) -> pd.DataFrame | None:
    """
    পেয়ারের শেষ N টি 1m candle আনে।
    Returns DataFrame with columns: open, high, low, close, volume
    Error হলে None return করে।
    """
    symbol = pair.replace("/", "")   # EUR/USD → EURUSD
    interval = f"{CANDLE_MINS}min"

    params = {
        "symbol":     symbol,
        "interval":   interval,
        "outputsize": outputsize,
        "apikey":     TWELVEDATA_API_KEY,
        "format":     "JSON",
        "timezone":   SIGNAL_TZ,
    }

    try:
        resp = requests.get(
            f"{BASE_URL}/time_series",
            params=params,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "error":
            logger.warning(f"API error for {pair}: {data.get('message')}")
            return None

        values = data.get("values", [])
        if len(values) < 30:
            logger.warning(f"Not enough candles for {pair}: {len(values)}")
            return None

        df = pd.DataFrame(values)
        df["open"]   = df["open"].astype(float)
        df["high"]   = df["high"].astype(float)
        df["low"]    = df["low"].astype(float)
        df["close"]  = df["close"].astype(float)
        df["volume"] = df.get("volume", pd.Series([0]*len(df))).astype(float)

        # সবচেয়ে পুরনো → সবচেয়ে নতুন order
        df = df.iloc[::-1].reset_index(drop=True)
        return df

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {pair}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {pair}: {e}")
        return None


def get_current_price(pair: str) -> float | None:
    """
    পেয়ারের latest price আনে।
    """
    symbol = pair.replace("/", "")
    params = {
        "symbol": symbol,
        "apikey": TWELVEDATA_API_KEY,
    }
    try:
        resp = requests.get(f"{BASE_URL}/price", params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        price = data.get("price")
        return float(price) if price else None
    except Exception as e:
        logger.error(f"Price fetch error {pair}: {e}")
        return None
