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


def _sma20_from_bars(ticker: str, bars) -> Optional[float]:
    """Shared bars→SMA20 step. Prints the SAME per-ticker diagnostics the serial
    path prints, so batching does not lose them. Returns None when unusable."""
    if bars is None or len(bars) < 15:
        print(f"[sma20_cache] BARS_INSUFFICIENT: {ticker} bars={None if bars is None else len(bars)}", flush=True)
        return None
    closes = bars["close"].dropna().tolist()
    if len(closes) < 15:
        print(f"[sma20_cache] CLOSES_INSUFFICIENT: {ticker} closes={len(closes)}", flush=True)
        return None
    sma20 = sum(closes[-20:]) / min(len(closes), 20)
    return sma20 if sma20 > 0 else None


def prime_sma20_cache(tickers, provider=None) -> int:
    """TASK-259: fill the cache for many tickers with ONE provider request.

    The agent asked for daily bars once per ticker, 60 times a run, against a
    cache that is always cold on a GitHub runner (data/ is gitignored, so every
    checkout starts empty). Measured 2026-08-05 on the 60 real tickers of run
    31030383592: 9.05s serial vs 0.67s batched.

    Semantics are deliberately unchanged for callers: this only PRE-FILLS the
    same cache get_price_vs_sma20 already reads, so that function keeps its
    signature, its return values and its None-handling. Priming is optional —
    skip it and everything still works, one call per ticker.

    A ticker with no data (absent from the batch) or with too few bars is cached
    as a null marker, which get_price_vs_sma20 already reads as None. That stops
    a second lookup from re-firing a request for a ticker known to be empty.

    If the batch request fails ENTIRELY, this falls back to the serial path and
    says so on stdout (SMA20_BATCH_FAILED) — never a silent degradation.

    Returns the number of tickers newly cached.
    """
    if not tickers:
        return 0

    today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    cache = _load_cache()
    todo = [t for t in dict.fromkeys(tickers)
            if t and f"{t}:{today_str}" not in cache]
    if not todo:
        return 0

    frames = None
    try:
        if provider is None:
            from data_provider import get_daily_bars_batch
            frames = get_daily_bars_batch(todo, days=25)
        else:
            frames = provider.get_daily_bars_batch(todo, days=25)
    except Exception as e:
        print(f"[sma20_cache] SMA20_BATCH_FAILED: {type(e).__name__}: {e} — "
              f"falling back to serial for {len(todo)} tickers", flush=True)
        frames = None

    if frames is None:
        # Serial fallback: exactly the pre-TASK-259 path, one call per ticker.
        for t in todo:
            try:
                if provider is None:
                    from data_provider import get_daily_bars
                    bars = get_daily_bars(t, days=25)
                else:
                    bars = provider.get_daily_bars(t, days=25)
            except Exception as e:
                print(f"[sma20_cache] WARN: {t}: {type(e).__name__}: {e}", flush=True)
                bars = None
            sma20 = _sma20_from_bars(t, bars)
            cache[f"{t}:{today_str}"] = {"sma20": sma20, "computed_at": today_str}
    else:
        for t in todo:
            sma20 = _sma20_from_bars(t, frames.get(t))
            cache[f"{t}:{today_str}"] = {"sma20": sma20, "computed_at": today_str}

    cutoff = datetime.now(PERU_TZ).strftime("%Y-%m")
    cache = {k: v for k, v in cache.items() if k.split(":")[1][:7] >= cutoff[:7]}
    _save_cache(cache)
    return len(todo)


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
        print(f"[sma20_cache] BARS_INSUFFICIENT: {ticker} bars={None if bars is None else len(bars)}", flush=True)
        return None
    
    closes = bars["close"].dropna().tolist()
    if len(closes) < 15:
        print(f"[sma20_cache] CLOSES_INSUFFICIENT: {ticker} closes={len(closes)}", flush=True)
        return None
    
    sma20 = sum(closes[-20:]) / min(len(closes), 20)
    
    # Cache it. TASK-259: store the FULL-PRECISION mean. It used to be
    # round(sma20, 4), which made the first call of the day (computed from the
    # unrounded value below) disagree with every later call (read back rounded)
    # by up to 0.03 percentage points — measured on 8 of 60 real tickers,
    # 2026-08-05. On a runner the cache is always cold, so production always
    # took the unrounded branch; keeping full precision is what preserves it.
    cache[cache_key] = {"sma20": sma20, "computed_at": today_str}
    # Prune entries older than 7 days
    cutoff = datetime.now(PERU_TZ).strftime("%Y-%m")
    cache = {k: v for k, v in cache.items() if k.split(":")[1][:7] >= cutoff[:7]}
    _save_cache(cache)
    
    if sma20 <= 0:
        return None
    
    return round((current_price - sma20) / sma20 * 100, 2)
