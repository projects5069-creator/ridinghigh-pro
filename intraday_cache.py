"""TASK-155 — cached intraday (minute) bars fetcher.

Wraps `data_provider.get_intraday_bars` with a disk cache so each
(ticker, settled-day, timeframe) is fetched from Alpaca at most once. Mirrors the
`agent/enrichment/sma20_cache.py` precedent: JSON files under `data/` (gitignored).

Rules:
- A still-moving day (date == today, Peru tz) is NEVER cached (bars keep changing).
- An empty fetch is NEVER written (so a later run can retry).
- Bars are stored with their UTC timestamp and restored as a tz-aware
  DatetimeIndex on read, so cached output matches the provider's native shape.

This is fetch+cache only — no trading logic, no resolution. The WHIPSAW resolver
(utils.resolve_whipsaw) and the offline study consume this.
"""
import os
import json

import pandas as pd

from utils import get_peru_time
import data_provider

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "intraday_cache")
_COLS = ["open", "high", "low", "close", "volume"]


def _cache_path(cache_dir, ticker, date_str, timeframe):
    return os.path.join(cache_dir, f"{ticker}_{date_str}_{timeframe}.json")


def _df_to_records(df):
    tmp = df.copy()
    tmp.index = tmp.index.map(lambda t: t.isoformat() if hasattr(t, "isoformat") else str(t))
    tmp.index.name = "timestamp"
    return tmp.reset_index().to_dict("records")


def _records_to_df(records):
    if not records:
        return pd.DataFrame(columns=_COLS)
    df = pd.DataFrame(records)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp")
    return df[[c for c in _COLS if c in df.columns]]


def get_intraday_bars_cached(ticker, date, timeframe="1Min", cache_dir=None, today=None):
    """Return 1-min (or other tf) bars for (ticker, date), cached on disk.

    cache_dir / today are injectable for tests; in production they default to
    CACHE_DIR and the current Peru date.
    """
    cache_dir = cache_dir or CACHE_DIR
    date_str = str(date)[:10]
    today_str = today or get_peru_time().date().isoformat()
    settled = date_str < today_str          # YYYY-MM-DD compares chronologically
    path = _cache_path(cache_dir, ticker, date_str, timeframe)

    if settled and os.path.exists(path):
        try:
            with open(path) as f:
                payload = json.load(f)
            return _records_to_df(payload.get("bars", []))
        except Exception:
            pass  # corrupt/partial cache -> fall through and re-fetch

    df = data_provider.get_intraday_bars(ticker, date, timeframe=timeframe)
    if df is None:
        return pd.DataFrame(columns=_COLS)

    if settled and not df.empty:
        os.makedirs(cache_dir, exist_ok=True)
        payload = {"bars": _df_to_records(df),
                   "cached_at": get_peru_time().isoformat(),
                   "count": int(len(df))}
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(payload, f)
        os.replace(tmp, path)               # atomic publish
    return df
