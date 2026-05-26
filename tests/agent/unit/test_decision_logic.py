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


# ─────────────────────────────────────────────────────────────────────────────
# L6 — PRICE_TOO_LOW filter tests (2026-05-25 layers paradigm)
# ─────────────────────────────────────────────────────────────────────────────

def _good_signal_at_price(price):
    """Helper: a signal that passes all filters except price."""
    return {
        "ticker": "TEST", "price": price, "volume": 5_000_000,
        "market_cap": 50_000_000, "open": (price * 0.9) if price else 0,
        "high": (price * 1.05) if price else 0, "low": (price * 0.85) if price else 0,
        "mxv": -500.0, "run_up": 35.0, "atrx": 2.5, "rsi": 75.0,
        "rel_vol": 8.0, "change": 25.0, "typical_price_dist": 0.05,
    }


def test_l6_price_too_low_blocks_under_3():
    """Sub-$3 stocks must be blocked with PRICE_TOO_LOW."""
    from agent.trader.decision_logic import evaluate_signal as evaluate
    decision = evaluate(_good_signal_at_price(2.50))
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("PRICE_TOO_LOW"), \
        f"Expected PRICE_TOO_LOW, got: {decision.skip_reason}"


def test_l6_price_too_low_blocks_at_zero():
    """price=0 (missing/bad data) must be blocked safely."""
    from agent.trader.decision_logic import evaluate_signal as evaluate
    decision = evaluate(_good_signal_at_price(0.0))
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("PRICE_TOO_LOW"), \
        f"Expected PRICE_TOO_LOW, got: {decision.skip_reason}"


def test_l6_price_too_low_blocks_at_none():
    """price=None must be blocked without raising."""
    from agent.trader.decision_logic import evaluate_signal as evaluate
    sig = _good_signal_at_price(5.0)
    sig["price"] = None
    decision = evaluate(sig)
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("PRICE_TOO_LOW"), \
        f"Expected PRICE_TOO_LOW, got: {decision.skip_reason}"


def test_l6_price_at_exactly_3_passes_filter():
    """Boundary: price == 3.0 must NOT trigger PRICE_TOO_LOW."""
    from agent.trader.decision_logic import evaluate_signal as evaluate
    decision = evaluate(_good_signal_at_price(3.0))
    if decision.action == "SKIP":
        assert not decision.skip_reason.startswith("PRICE_TOO_LOW"), \
            f"price=3.0 should pass L6, got: {decision.skip_reason}"


def test_l6_price_above_3_passes_filter():
    """Normal pump stock at $7.26 (winners median) must pass L6."""
    from agent.trader.decision_logic import evaluate_signal as evaluate
    decision = evaluate(_good_signal_at_price(7.26))
    if decision.action == "SKIP":
        assert not decision.skip_reason.startswith("PRICE_TOO_LOW"), \
            f"price=7.26 should pass L6, got: {decision.skip_reason}"


# ─────────────────────────────────────────────────────────────────────────────
# Filter 4c — BLACKLISTED_TICKER (Stage 2, 2026-05-26 Toxic Blacklist)
# ─────────────────────────────────────────────────────────────────────────────

def _good_signal_with_ticker(ticker, price=7.0):
    return {
        "ticker": ticker, "price": price, "volume": 5_000_000,
        "market_cap": 50_000_000, "open": price * 0.9,
        "high": price * 1.05, "low": price * 0.85,
        "mxv": -500.0, "run_up": 35.0, "atrx": 2.5, "rsi": 75.0,
        "rel_vol": 8.0, "change": 25.0, "typical_price_dist": 0.05,
    }


def test_l3_blacklist_blocks_aehl():
    from agent.trader.decision_logic import evaluate_signal
    decision = evaluate_signal(_good_signal_with_ticker("AEHL"))
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("BLACKLISTED_TICKER"), \
        f"Expected BLACKLISTED_TICKER, got: {decision.skip_reason}"


def test_l3_blacklist_blocks_tdic():
    from agent.trader.decision_logic import evaluate_signal
    decision = evaluate_signal(_good_signal_with_ticker("TDIC"))
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("BLACKLISTED_TICKER"), \
        f"Expected BLACKLISTED_TICKER, got: {decision.skip_reason}"


def test_l3_blacklist_passes_non_blacklisted():
    """Non-blacklisted ticker (e.g., ATRA winner) must not trigger blacklist filter."""
    from agent.trader.decision_logic import evaluate_signal
    decision = evaluate_signal(_good_signal_with_ticker("ATRA"))
    if decision.action == "SKIP":
        assert not decision.skip_reason.startswith("BLACKLISTED_TICKER"), \
            f"ATRA should pass blacklist, got: {decision.skip_reason}"


def test_l3_blacklist_priority_after_price():
    """If ticker is blacklisted AND price < $3, PRICE_TOO_LOW fires first (4b before 4c)."""
    from agent.trader.decision_logic import evaluate_signal
    decision = evaluate_signal(_good_signal_with_ticker("AEHL", price=2.0))
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("PRICE_TOO_LOW"), \
        f"Expected PRICE_TOO_LOW (Filter 4b runs before 4c), got: {decision.skip_reason}"
