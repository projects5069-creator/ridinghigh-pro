"""
Tradability checker — determines if a stock is shortable and at what borrow fee.

M3 IMPLEMENTATION IS A MOCK.
This module currently returns hardcoded "always shortable" values.
The Alpaca paper environment generally allows shorting most US stocks,
so the mock is reasonable for DRY_RUN testing.

# TODO M5: Replace _mock_check() with real Alpaca API call:
#   - alpaca.get_asset(ticker).shortable
#   - alpaca.get_asset(ticker).easy_to_borrow
#   - Cache results to borrow_data sheet to reduce API calls

Used by: decision_logic.py (M3), alpaca_broker.py (M5)
"""

from typing import Any


# Mock defaults — replaced in M5
MOCK_DEFAULTS = {
    "is_shortable": True,
    "borrow_fee_pct": 12.5,
    "borrow_available": True,
    "locate_status": "MOCK",  # M5 will use: AVAILABLE / UNAVAILABLE / NEEDED
}


def check_tradability(ticker: str) -> dict[str, Any]:
    """
    Check if a ticker is shortable and at what borrow fee.

    Args:
        ticker: stock symbol (uppercase, e.g. "AAPL")

    Returns:
        dict with:
            - is_shortable: bool
            - borrow_fee_pct: float (annualized %)
            - borrow_available: bool (HTB locate available)
            - locate_status: str ("MOCK" in M3; "AVAILABLE"/"UNAVAILABLE"/"NEEDED" in M5)

    Raises:
        ValueError: If ticker is empty or not a string.

    NOTE (M3): This is a MOCK. Always returns shortable=True with
    fee 12.5%. For real shortability check, see TODO M5 in module docstring.
    """
    # TODO M5: Replace this mock with real Alpaca API call
    return _mock_check(ticker)


def _mock_check(ticker: str) -> dict[str, Any]:
    """Mock implementation — returns hardcoded MOCK_DEFAULTS."""
    if not ticker or not isinstance(ticker, str):
        raise ValueError(f"Invalid ticker: {ticker!r}")

    return dict(MOCK_DEFAULTS)  # copy, not reference
