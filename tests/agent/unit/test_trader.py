"""Unit tests for trader.py"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.trader.trader import Trader
from agent.trader.decision_logic import Decision


@pytest.fixture
def good_signal():
    return {
        "ticker": "TEST", "price": 5.0, "volume": 5_000_000,
        "market_cap": 50_000_000, "open": 4.0, "high": 5.5, "low": 3.9,
        "mxv": -300, "run_up": 45.0, "atrx": 2.5, "rsi": 78,
        "rel_vol": 8.0, "change": 25.0, "typical_price_dist": 0.05,
        "float_shares": 10_000_000,
    }


def test_default_mode_is_dry_run():
    """Per config, AGENT_DRY_RUN=True, AGENT_LIVE_PAPER=False -> mode=DRY_RUN."""
    t = Trader()
    assert t.mode == "DRY_RUN"


def test_explicit_mode_override():
    t = Trader(mode="LIVE_PAPER")
    assert t.mode == "LIVE_PAPER"


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        Trader(mode="INVALID")


def test_evaluate_sets_agent_mode_in_decision(good_signal):
    t = Trader(mode="DRY_RUN")
    d = t.evaluate(good_signal)
    assert d.agent_mode == "DRY_RUN"
    assert isinstance(d, Decision)


def test_evaluate_batch_returns_list(good_signal):
    t = Trader()
    signals = [good_signal, good_signal, good_signal]
    decisions = t.evaluate_batch(signals)
    assert len(decisions) == 3
    assert all(isinstance(d, Decision) for d in decisions)
    assert all(d.agent_mode == "DRY_RUN" for d in decisions)
