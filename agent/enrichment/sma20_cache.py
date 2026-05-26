"""
SMA20 cache for Toxic Profile filter (L3).

Computes Simple Moving Average over 20 trading days, and the percent
distance from current price. Cached per-ticker per-day in
data/sma20_cache.json (pattern reused from market_cap_cache.json).

Used by Filter 4d (TOXIC_PROFILE) in decision_logic.
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import pytz

PERU_TZ = pytz.timezone("America/Lima")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sma20_cache.json")


def _load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(c: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(c, f, indent=2)
    except OSError as e:
        print(f"[sma20_cache] WARN: failed to save cache: {e}")


def get_price_vs_sma20(ticker: str, current_price: float, provider=None) -> Optional[float]:
    """
    Return percent distance of current_price from SMA20.
    Positive value = price ABOVE SMA20.
    Returns None if data unavailable.
    Cached per (ticker, date_today) — one provider call per ticker per day.
    """
    if current_price is None or current_price <= 0:
        return None
    
    today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    cache = _load_cache()
    cache_key = f"{ticker}:{today_str}"
    
    cached = cache.get(cache_key)
    if cached is not None:
        sma20 = cached.get("sma20")
        if sma20 is not None and sma20 > 0:
            return round((current_price - sma20) / sma20 * 100, 2)
        return None
    
    if provider is None:
        from data_provider import get_daily_bars
        try:
            bars = get_daily_bars(ticker, days=25)
        except Exception as e:
            print(f"[sma20_cache] WARN: {ticker}: {type(e).__name__}: {e}")
            return None
    else:
        try:
            bars = provider.get_daily_bars(ticker, days=25)
        except Exception as e:
            print(f"[sma20_cache] WARN: {ticker}: {type(e).__name__}: {e}")
            return None

    if bars is None or len(bars) < 15:
        return None
    
    closes = bars["close"].dropna().tolist()
    if len(closes) < 15:
        return None
    
    sma20 = sum(closes[-20:]) / min(len(closes), 20)
    
    # Cache it
    cache[cache_key] = {"sma20": round(sma20, 4), "computed_at": today_str}
    # Prune entries older than 7 days
    cutoff = datetime.now(PERU_TZ).strftime("%Y-%m")
    cache = {k: v for k, v in cache.items() if k.split(":")[1][:7] >= cutoff[:7]}
    _save_cache(cache)
    
    if sma20 <= 0:
        return None
    
    return round((current_price - sma20) / sma20 * 100, 2)
