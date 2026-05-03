"""Unit tests for agent/perception/tradability.py"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.perception.tradability import check_tradability, MOCK_DEFAULTS, clear_cache


def test_returns_dict_with_required_keys():
    """check_tradability returns a dict with all expected keys."""
    result = check_tradability("AAPL")
    required_keys = {"is_shortable", "borrow_fee_pct", "borrow_available", "locate_status"}
    assert isinstance(result, dict)
    assert set(result.keys()) == required_keys


def test_mock_returns_consistent_values():
    """Mock always returns the same hardcoded values."""
    r1 = check_tradability("AAPL")
    r2 = check_tradability("TSLA")
    r3 = check_tradability("AKAN")

    assert r1["is_shortable"] is True
    assert r1["borrow_fee_pct"] == 12.5
    assert r1["borrow_available"] is True
    assert r1["locate_status"] == "MOCK"

    # All tickers return same mock values
    assert r1 == r2 == r3


def test_invalid_ticker_raises_value_error():
    """Empty or non-string ticker raises ValueError."""
    with pytest.raises(ValueError):
        check_tradability("")

    with pytest.raises(ValueError):
        check_tradability(None)

    with pytest.raises(ValueError):
        check_tradability(123)


def test_returned_dict_is_independent_copy():
    """Mutating returned dict does not affect MOCK_DEFAULTS."""
    result = check_tradability("TEST")
    result["is_shortable"] = False
    result["borrow_fee_pct"] = 999.0

    # MOCK_DEFAULTS unchanged
    assert MOCK_DEFAULTS["is_shortable"] is True
    assert MOCK_DEFAULTS["borrow_fee_pct"] == 12.5

    # Next call still returns clean defaults
    fresh = check_tradability("TEST2")
    assert fresh["is_shortable"] is True
    assert fresh["borrow_fee_pct"] == 12.5


# ════════════════════════════════════════════════════════════════════════
# M5 broker-aware tests
# ════════════════════════════════════════════════════════════════════════

class TestBrokerIntegration:
    def test_no_broker_uses_mock(self):
        """No broker passed → mock fallback."""
        result = check_tradability("AAPL")
        assert result["locate_status"] == "MOCK"

    def test_broker_with_dry_run_uses_mock(self):
        """Broker passed but AGENT_DRY_RUN=True → mock fallback."""
        broker = MagicMock()
        result = check_tradability("AAPL", broker=broker)
        assert result["locate_status"] == "MOCK"
        broker.is_shortable.assert_not_called()
