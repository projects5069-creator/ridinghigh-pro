"""TASK-128 T-B — pure would-enter predicate for the MxV+price shadow gate.

would_enter = (MxV <= AGENT_MXV_MAX) AND (price >= AGENT_MIN_SCANPRICE_USD).
This is the ONLY entry-to-tracking condition עמיחי approved: MxV<=-100 AND price>=$3.
It is a SEPARATE observer (decision_logic._observe_mxv_price_gate) that sets a runtime
field — it never touches _check_filters or d.action, so it cannot affect the live gate.

RED (before): mxv_price_would_enter does not exist (ImportError).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from config import AGENT_MXV_MAX, AGENT_MIN_SCANPRICE_USD
from agent.trader.decision_logic import mxv_price_would_enter


def test_deep_mxv_and_price_ok_enters():
    assert mxv_price_would_enter(-150.0, 5.0) is True


def test_price_below_floor_rejected():
    # MxV deep but price < $3 -> not a tracking entry.
    assert mxv_price_would_enter(-150.0, 2.0) is False


def test_shallow_mxv_rejected():
    assert mxv_price_would_enter(-50.0, 5.0) is False


def test_boundaries_inclusive():
    # MxV == AGENT_MXV_MAX (-100) and price == floor ($3) are both inclusive.
    assert mxv_price_would_enter(float(AGENT_MXV_MAX), float(AGENT_MIN_SCANPRICE_USD)) is True


def test_missing_inputs_rejected():
    assert mxv_price_would_enter(None, 5.0) is False
    assert mxv_price_would_enter(-150.0, None) is False
