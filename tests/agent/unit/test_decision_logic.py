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


def test_low_volume_skips(good_signal, monkeypatch):
    monkeypatch.setattr("config.ENTRY_GATE_MINIMAL", False)  # this tests the full-gate (Volume now opt-in)
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


def test_field_mapping_backed_by_decision_fields():
    """Every decision_log column (FIELD_MAPPING) is backed by a real Decision field.

    Drift-proof invariant — replaces the hardcoded `== 43`. The logger maps Decision
    attributes to Sheet columns, so each mapped name must exist on Decision (a missing
    one would AttributeError at log time). The dataclass legitimately has MORE fields
    than columns (runtime-only: reentries_used_today, portfolio_written), so a raw
    field-count was the wrong guard and broke on benign additions."""
    from dataclasses import fields
    from agent.logging.decision_logger import FIELD_MAPPING
    decision_field_names = {f.name for f in fields(Decision)}
    unmapped = [src for src, _col in FIELD_MAPPING if src not in decision_field_names]
    assert not unmapped, f"FIELD_MAPPING references non-existent Decision fields: {unmapped}"
    assert len(FIELD_MAPPING) <= len(decision_field_names)


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


def test_l3_blacklist_blocks_aehl(monkeypatch):
    monkeypatch.setattr("config.ENTRY_GATE_MINIMAL", False)  # blacklist (F4c) is opt-in under minimal
    from agent.trader.decision_logic import evaluate_signal
    decision = evaluate_signal(_good_signal_with_ticker("AEHL"))
    assert decision.action == "SKIP"
    assert decision.skip_reason.startswith("BLACKLISTED_TICKER"), \
        f"Expected BLACKLISTED_TICKER, got: {decision.skip_reason}"


def test_l3_blacklist_blocks_tdic(monkeypatch):
    monkeypatch.setattr("config.ENTRY_GATE_MINIMAL", False)  # blacklist (F4c) is opt-in under minimal
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


# ─────────────────────────────────────────────────────────────────────────────
# Filter 4d — TOXIC_PROFILE (L3 Layers, 2026-05-26)
# Blocks: RSI > 88 AND Price/SMA20 > 250 (BOTH conditions)
# ─────────────────────────────────────────────────────────────────────────────

def _signal_with_l3(rsi, price_vs_sma20, ticker="TEST", price=7.0):
    return {
        "ticker": ticker, "price": price, "volume": 5_000_000,
        "market_cap": 50_000_000, "open": price * 0.9,
        "high": price * 1.05, "low": price * 0.85,
        "mxv": -500.0, "run_up": 35.0, "atrx": 2.5, "rsi": rsi,
        "rel_vol": 8.0, "change": 25.0, "typical_price_dist": 0.05,
        "price_vs_sma20": price_vs_sma20,
    }


def test_l3_toxic_profile_blocks_extreme(monkeypatch):
    """Toxic median: RSI=92.61, Price/SMA20=305 — MUST be blocked."""
    monkeypatch.setattr("config.ENTRY_GATE_MINIMAL", False)  # Toxic (F4d) is opt-in under minimal
    from agent.trader.decision_logic import evaluate_signal
    d = evaluate_signal(_signal_with_l3(rsi=92.61, price_vs_sma20=305))
    assert d.action == "SKIP"
    assert d.skip_reason.startswith("TOXIC_PROFILE"), f"got: {d.skip_reason}"


def test_l3_winner_passes():
    """Winner median: RSI=83.62, Price/SMA20=194 — MUST pass L3."""
    from agent.trader.decision_logic import evaluate_signal
    d = evaluate_signal(_signal_with_l3(rsi=83.62, price_vs_sma20=194))
    if d.action == "SKIP":
        assert not d.skip_reason.startswith("TOXIC_PROFILE"), \
            f"Winner blocked by L3: {d.skip_reason}"


def test_l3_rsi_high_but_sma_low_passes():
    """Only RSI > 88 should NOT trigger — needs BOTH conditions."""
    from agent.trader.decision_logic import evaluate_signal
    d = evaluate_signal(_signal_with_l3(rsi=92.0, price_vs_sma20=180))
    if d.action == "SKIP":
        assert not d.skip_reason.startswith("TOXIC_PROFILE"), \
            f"L3 fired on RSI alone (sma not extreme): {d.skip_reason}"


def test_l3_sma_high_but_rsi_low_passes():
    """Only Price/SMA20 > 250 should NOT trigger — needs BOTH conditions."""
    from agent.trader.decision_logic import evaluate_signal
    d = evaluate_signal(_signal_with_l3(rsi=85.0, price_vs_sma20=300))
    if d.action == "SKIP":
        assert not d.skip_reason.startswith("TOXIC_PROFILE"), \
            f"L3 fired on SMA alone (rsi not extreme): {d.skip_reason}"


def test_l3_missing_sma_data_does_not_block():
    """If price_vs_sma20 is None (data unavailable), L3 must NOT block."""
    from agent.trader.decision_logic import evaluate_signal
    d = evaluate_signal(_signal_with_l3(rsi=92.0, price_vs_sma20=None))
    if d.action == "SKIP":
        assert not d.skip_reason.startswith("TOXIC_PROFILE"), \
            f"L3 fired on missing data: {d.skip_reason}"
