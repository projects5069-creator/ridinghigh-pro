"""
agent/perception/tradability.py
─────────────────────────────────
Tradability checker — determines if a stock is shortable.

M5 update: now broker-aware. Falls back to mock if no broker provided
or if AGENT_DRY_RUN is True.

Usage (M3-compatible):
    is_tradable = check_tradability("AAPL")  # mock-only

Usage (M5+):
    is_tradable = check_tradability("AAPL", broker=alpaca_broker)

Used by: decision_logic.py (M3), alpaca_broker.py (M5)
"""

import sys
import os
import time
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AGENT_DRY_RUN

# Mock defaults (M3, kept for fallback)
MOCK_DEFAULTS = {
    "is_shortable": True,
    "borrow_fee_pct": 12.5,
    "borrow_available": True,
    "locate_status": "MOCK",
}

# Session cache for real broker calls (TTL = 1 hour)
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 3600


def check_tradability(ticker: str, broker=None) -> Dict[str, Any]:
    """
    Check if a ticker is shortable.

    Args:
        ticker: stock symbol (uppercase, e.g. "AAPL")
        broker: optional AlpacaBroker instance. If None or AGENT_DRY_RUN → mock.

    Returns:
        dict with:
            - is_shortable: bool
            - borrow_fee_pct: float (annualized %)
            - borrow_available: bool
            - locate_status: str ("MOCK" / "AVAILABLE" / "UNAVAILABLE")

    Raises:
        ValueError: If ticker is empty or not a string.
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError(f"Invalid ticker: {ticker!r}")

    # Mock fallback
    if broker is None or AGENT_DRY_RUN:
        return _mock_check(ticker)

    # Real check via broker (with cache)
    return _real_check_cached(ticker, broker)


def _mock_check(ticker: str) -> Dict[str, Any]:
    """Mock implementation — returns hardcoded MOCK_DEFAULTS."""
    return dict(MOCK_DEFAULTS)


def _real_check_cached(ticker: str, broker) -> Dict[str, Any]:
    """Real check via broker, with 1-hour cache."""
    now = time.time()

    if ticker in _CACHE:
        cached = _CACHE[ticker]
        if now - cached["_cached_at"] < _CACHE_TTL_SECONDS:
            return {k: v for k, v in cached.items() if k != "_cached_at"}

    # Cache miss or expired — fetch fresh
    try:
        is_shortable = broker.is_shortable(ticker)
        asset_info = broker.get_asset_info(ticker) if hasattr(broker, "get_asset_info") else {}
        result = {
            "is_shortable": is_shortable,
            "borrow_fee_pct": 0.0,  # Alpaca paper doesn't expose real fees
            "borrow_available": asset_info.get("easy_to_borrow", is_shortable),
            "locate_status": "AVAILABLE" if is_shortable else "UNAVAILABLE",
        }
        _CACHE[ticker] = {**result, "_cached_at": now}
        return result
    except Exception:
        # On failure, fall back to mock
        return _mock_check(ticker)


def clear_cache():
    """Clear the tradability cache (for tests and session reset)."""
    _CACHE.clear()
