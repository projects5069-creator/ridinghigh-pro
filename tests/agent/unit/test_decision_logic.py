"""Unit tests for decision_logic.py"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.trader.decision_logic import evaluate_signal, Decision


@pytest.fixture
def good_signal():
    """A signal that should ENTER."""
    return {
        "ticker": "TEST",
        "price": 5.0,
        "volume": 5_000_000,
        "market_cap": 50_000_000,
        "open": 4.0, "high": 5.5, "low": 3.9,
        "mxv": -300,
        "run_up": 45.0,
        "atrx": 2.5,
        "rsi": 78,
        "rel_vol": 8.0,
        "change": 25.0,
        "typical_price_dist": 0.05,
        "float_shares": 10_000_000,
    }


def test_good_signal_returns_enter(good_signal):
    d = evaluate_signal(good_signal)
    assert d.action == "ENTER", f"Expected ENTER, got {d.action} with reason: {d.reason}"
    assert d.skip_reason is None
    assert d.quantity is not None
    assert d.tp_price is not None and d.tp_price < d.price
    assert d.sl_price is not None and d.sl_price > d.price


def test_low_score_skips(good_signal):
    good_signal["mxv"] = 50   # weak — score will drop below 60
    good_signal["run_up"] = 5
    good_signal["atrx"] = 0.5
    good_signal["rsi"] = 40
    good_signal["rel_vol"] = 1.0
    good_signal["change"] = 2.0
    good_signal["typical_price_dist"] = 0.01
    d = evaluate_signal(good_signal)
    assert d.action == "SKIP"
    assert "SCORE" in d.skip_reason or "RUNUP" in d.skip_reason or "MXV" in d.skip_reason


def test_low_volume_skips(good_signal):
    good_signal["volume"] = 50  # below 100K threshold
    d = evaluate_signal(good_signal)
    assert d.action == "SKIP"
    assert "VOLUME" in d.skip_reason


def test_existing_position_skips(good_signal):
    state = {
        "existing_positions": ["TEST"],
        "buying_power": 100_000,
        "cold_start_concurrent_used": 0,
        "cold_start_daily_used": 0,
    }
    d = evaluate_signal(good_signal, state)
    assert d.action == "SKIP"
    assert "EXISTING_POSITION" in d.skip_reason


def test_cold_start_concurrent_limit(good_signal):
    state = {
        "existing_positions": [],
        "buying_power": 100_000,
        "cold_start_concurrent_used": 5,  # at limit
        "cold_start_daily_used": 0,
    }
    d = evaluate_signal(good_signal, state)
    assert d.action == "SKIP"
    assert "COLD_START_CONCURRENT" in d.skip_reason


def test_decision_has_41_fields():
    """Verify the dataclass schema matches the Sheet."""
    from dataclasses import fields
    field_names = [f.name for f in fields(Decision)]
    assert len(field_names) == 41, f"Expected 41 fields, got {len(field_names)}: {field_names}"
