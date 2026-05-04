"""Unit tests for agent/orchestrator.py — all mocked, no API/Sheets calls."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.orchestrator import (
    _signal_from_timeline_row,
    is_market_hours,
    is_eod_window,
    check_emergency_stop,
    build_account_state,
    read_latest_signals,
    run,
    PERU_TZ,
)


# ════════════════════════════════════════════════════════════════════
# Signal conversion
# ════════════════════════════════════════════════════════════════════

class TestSignalConversion:
    def test_maps_all_required_fields(self):
        row = {
            "Ticker": "AAPL", "Price": "150.5", "Volume": "1000000",
            "MarketCap": "2.5e12", "Score": "75.5", "MxV": "-300",
            "RunUp": "45.0", "ATRX": "2.5", "RSI": "78", "REL_VOL": "8.0",
            "Change": "25.0", "TypicalPriceDist": "5.0", "Gap": "10.0",
            "Open_price": "120", "High_today": "155", "Low_today": "118",
            "Float%": "60", "FloatShares": "1000000",
            "ScanTime": "10:30:00", "Date": "2026-05-04",
        }
        signal = _signal_from_timeline_row(row)
        assert signal["ticker"] == "AAPL"
        assert signal["price"] == 150.5
        assert signal["volume"] == 1000000
        assert signal["score"] == 75.5
        assert signal["mxv"] == -300.0

    def test_handles_missing_fields_gracefully(self):
        row = {"Ticker": "TEST"}
        signal = _signal_from_timeline_row(row)
        assert signal["ticker"] == "TEST"
        assert signal["price"] == 0.0
        assert signal["volume"] == 0

    def test_lowercase_ticker_uppercased(self):
        row = {"Ticker": "  aapl  "}
        signal = _signal_from_timeline_row(row)
        assert signal["ticker"] == "AAPL"

    def test_empty_string_values_use_defaults(self):
        row = {"Ticker": "X", "Price": "", "Volume": "", "Score": None}
        signal = _signal_from_timeline_row(row)
        assert signal["price"] == 0.0
        assert signal["volume"] == 0
        assert signal["score"] == 0.0


# ════════════════════════════════════════════════════════════════════
# Time helpers
# ════════════════════════════════════════════════════════════════════

class TestMarketHours:
    def test_weekday_in_hours(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 10, 30))  # Mon 10:30
        assert is_market_hours(now) is True

    def test_weekend_returns_false(self):
        now = PERU_TZ.localize(datetime(2026, 5, 3, 10, 30))  # Sun 10:30
        assert is_market_hours(now) is False

    def test_before_open(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 7, 0))  # Mon 7:00
        assert is_market_hours(now) is False

    def test_after_close(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 15, 30))  # Mon 15:30
        assert is_market_hours(now) is False

    def test_exactly_at_open(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 8, 30))  # Mon 8:30
        assert is_market_hours(now) is True

    def test_exactly_at_close(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 15, 0))  # Mon 15:00
        assert is_market_hours(now) is False


class TestEODWindow:
    def test_eod_window_active_at_1455(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 14, 55))
        assert is_eod_window(now) is True

    def test_eod_window_active_at_1459(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 14, 59))
        assert is_eod_window(now) is True

    def test_eod_window_not_active_at_1454(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 14, 54))
        assert is_eod_window(now) is False

    def test_eod_window_not_active_at_1500(self):
        now = PERU_TZ.localize(datetime(2026, 5, 4, 15, 0))
        assert is_eod_window(now) is False


# ════════════════════════════════════════════════════════════════════
# Emergency stop
# ════════════════════════════════════════════════════════════════════

class TestEmergencyStop:
    @patch("agent.orchestrator.sheets_manager", create=True)
    def test_no_stop_when_no_events(self, mock_sm):
        with patch.dict("sys.modules", {"sheets_manager": mock_sm}):
            mock_ws = MagicMock()
            mock_ws.get_all_records.return_value = []
            mock_sm.get_worksheet.return_value = mock_ws
            result = check_emergency_stop()
            assert result is False

    def test_returns_false_on_import_failure(self):
        """Graceful fallback when sheets_manager unavailable."""
        with patch.dict("sys.modules", {"sheets_manager": None}):
            result = check_emergency_stop()
            # Should not crash — returns False on any exception
            assert result is False


# ════════════════════════════════════════════════════════════════════
# Run flow (end-to-end, heavily mocked)
# ════════════════════════════════════════════════════════════════════

class TestRunFlow:
    @patch("agent.orchestrator.is_market_hours")
    def test_run_returns_halted_outside_market_hours(self, mock_is_market):
        mock_is_market.return_value = False
        result = run()
        assert result["halted"] is True
        assert result["halt_reason"] == "OUTSIDE_MARKET_HOURS"

    @patch("agent.orchestrator.check_emergency_stop")
    @patch("agent.orchestrator.is_market_hours")
    def test_run_halts_on_emergency_stop(self, mock_is_market, mock_es):
        mock_is_market.return_value = True
        mock_es.return_value = True
        result = run()
        assert result["halted"] is True
        assert result["halt_reason"] == "EMERGENCY_STOP"

    @patch("agent.orchestrator.check_emergency_stop")
    @patch("agent.orchestrator.is_market_hours")
    def test_run_returns_summary_keys(self, mock_is_market, mock_es):
        mock_is_market.return_value = False
        result = run()
        expected_keys = {"timestamp", "halted", "halt_reason", "signals",
                         "decisions", "enters", "skips", "errors",
                         "monitored", "eod_closed"}
        assert expected_keys == set(result.keys())
