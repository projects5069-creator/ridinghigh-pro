"""
agent/sentinel/checks/price_freshness.py
─────────────────────────────────────────
Check 5: FINVIZ scanner price vs Alpaca live price.

The most critical check — caught the ELPW bug where scanner said $8.07
but market was actually $7.24 (10% stale → instant false TP).

Uses in-memory cache (TTL=60s) to avoid hammering Alpaca with duplicate
calls for the same ticker within a minute.

Returns:
  - BLOCK if delta > SENTINEL_PRICE_DELTA_MAX_PCT (default 2%)
  - WARN if Alpaca call fails (don't block — fallback to FINVIZ)
  - ALLOW otherwise
"""
from typing import Dict, Any, Optional
import time
import logging
from agent.sentinel.data_sentinel import SentinelResult

logger = logging.getLogger("agent.sentinel.price_freshness")

# In-memory cache: {ticker: (fetch_timestamp, live_price)}
_price_cache: Dict[str, tuple] = {}
_CACHE_TTL_SEC = 60


def _get_cached_live_price(ticker: str, market_state: Dict[str, Any]) -> Optional[float]:
    """Get live price from cache or fetch from Alpaca. Returns None on failure."""
    # Check cache
    cached = _price_cache.get(ticker)
    if cached:
        ts, price = cached
        if time.time() - ts < _CACHE_TTL_SEC:
            return price

    # Cache miss — fetch from Alpaca via market_state
    data_provider = market_state.get("data_provider")
    if data_provider is None:
        # Lazy import on first use (avoid circular)
        try:
            from providers.data_provider_factory import get_data_provider
            data_provider = get_data_provider()
        except Exception as e:
            logger.warning("Could not get data_provider for %s: %s", ticker, e)
            return None

    try:
        bar = data_provider.get_latest_bar(ticker)
        if bar and isinstance(bar, dict) and "close" in bar:
            price = float(bar["close"])
            _price_cache[ticker] = (time.time(), price)
            return price
    except Exception as e:
        logger.warning("Alpaca get_latest_bar failed for %s: %s", ticker, e)
        return None

    return None


def check_price_freshness(signal: Dict[str, Any],
                          market_state: Dict[str, Any]) -> SentinelResult:
    """Compare FINVIZ scanner price vs Alpaca live price."""
    from config import SENTINEL_PRICE_DELTA_MAX_PCT

    ticker = signal.get("ticker", "?")
    finviz_price = signal.get("price")

    if finviz_price is None:
        return SentinelResult(
            decision="WARN", reason="NO_FINVIZ_PRICE",
            details={"ticker": ticker},
        )

    try:
        finviz_price = float(finviz_price)
    except (ValueError, TypeError):
        return SentinelResult(
            decision="WARN", reason="UNPARSEABLE_FINVIZ_PRICE",
            details={"ticker": ticker, "price": finviz_price},
        )

    live_price = _get_cached_live_price(ticker, market_state)
    if live_price is None:
        return SentinelResult(
            decision="WARN", reason="LIVE_PRICE_UNAVAILABLE",
            details={"ticker": ticker, "finviz_price": finviz_price},
        )

    if live_price <= 0:
        return SentinelResult(
            decision="WARN", reason="INVALID_LIVE_PRICE",
            details={"ticker": ticker, "live_price": live_price},
        )

    delta_pct = abs(finviz_price - live_price) / live_price * 100

    if delta_pct > SENTINEL_PRICE_DELTA_MAX_PCT:
        return SentinelResult(
            decision="BLOCK", reason="STALE_FINVIZ_PRICE",
            details={
                "ticker": ticker,
                "finviz_price": finviz_price,
                "live_price": live_price,
                "delta_pct": round(delta_pct, 2),
                "max_allowed": SENTINEL_PRICE_DELTA_MAX_PCT,
            },
        )

    return SentinelResult(
        decision="ALLOW", reason="OK",
        details={"ticker": ticker, "delta_pct": round(delta_pct, 2)},
    )


def clear_cache():
    """For testing — reset the price cache."""
    _price_cache.clear()
