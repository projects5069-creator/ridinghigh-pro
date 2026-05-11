"""
agent/sentinel/checks/price_sanity.py
──────────────────────────────────────
Check 3: price bounds and OHLC consistency.

Validates:
1. price within [SENTINEL_PRICE_MIN_USD, SENTINEL_PRICE_MAX_USD]
2. If high/low present: low <= price <= high

Out of bounds → BLOCK (PRICE_ANOMALY).
"""
from typing import Dict, Any
from agent.sentinel.data_sentinel import SentinelResult


def _safe_float(val):
    """Convert to float or return None if invalid."""
    if val is None or val == "":
        return None
    try:
        f = float(val)
        if f != f:  # NaN check
            return None
        return f
    except (ValueError, TypeError):
        return None


def check_price_sanity(signal: Dict[str, Any],
                       market_state: Dict[str, Any]) -> SentinelResult:
    """Verify price is within sane bounds and consistent with high/low."""
    from config import SENTINEL_PRICE_MIN_USD, SENTINEL_PRICE_MAX_USD

    ticker = signal.get("ticker", "?")
    price = _safe_float(signal.get("price"))

    if price is None:
        return SentinelResult(
            decision="BLOCK",
            reason="PRICE_MISSING",
            details={"ticker": ticker},
        )

    # Bounds check
    if price < SENTINEL_PRICE_MIN_USD or price > SENTINEL_PRICE_MAX_USD:
        return SentinelResult(
            decision="BLOCK",
            reason="PRICE_OUT_OF_BOUNDS",
            details={
                "ticker": ticker,
                "price": price,
                "min": SENTINEL_PRICE_MIN_USD,
                "max": SENTINEL_PRICE_MAX_USD,
            },
        )

    # OHLC consistency (only if high/low present)
    high = _safe_float(signal.get("high") or signal.get("High"))
    low = _safe_float(signal.get("low") or signal.get("Low"))

    if high is not None and low is not None:
        if low > high:
            return SentinelResult(
                decision="BLOCK",
                reason="OHLC_INVERTED",
                details={"ticker": ticker, "high": high, "low": low},
            )
        if not (low <= price <= high):
            return SentinelResult(
                decision="WARN",
                reason="PRICE_OUTSIDE_OHLC",
                details={"ticker": ticker, "price": price, "high": high, "low": low},
            )

    return SentinelResult(
        decision="ALLOW",
        reason="OK",
        details={"ticker": ticker, "price": price},
    )
