"""TASK-128 C2-A — shadow_gate_events per-run summary also counts the MxV+price
would-enter (mirror of the existing Score-divergence count). Isolated from the fragile
FIELD_MAPPING<->decision_log coupling: touches ONLY the shadow-gate accumulator/builder.

The observer (C1, commit 52dafbb) sets decision.shadow_mxv_price_enter. C2-A accumulates
it per run and adds MxVPriceWouldEnter (+ tickers) to the one summary row.

RED (before): the summary ignores shadow_mxv_price_enter — when there are no Score skips
the row is None, and the MxV+price count is absent.
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from agent.logging.decision_logger import DecisionLogger


def _fresh_logger():
    lg = DecisionLogger.__new__(DecisionLogger)  # bypass __init__ (no network/sheet)
    lg._shadow_acc = {"score_skips": 0, "would_allow": [], "mxv_price_enter": []}
    lg.run_start = "2026-06-29 00:00:00"
    lg.run_id = "TEST-RUN"
    return lg


def _decision(ticker, mxv_price=False, score_skip=False, explicit_div=False):
    return SimpleNamespace(
        ticker=ticker,
        skip_reason="SCORE_TOO_LOW: 10 < 50" if score_skip else "",
        shadow_explicit_divergence=explicit_div,
        shadow_mxv_price_enter=mxv_price,
    )


def test_only_mxv_price_still_writes_a_row():
    # No Score skips, but 2 MxV+price would-enters -> a summary row MUST be written.
    lg = _fresh_logger()
    lg._accumulate_shadow_gate(_decision("AAA", mxv_price=True))
    lg._accumulate_shadow_gate(_decision("BBB", mxv_price=True))
    lg._accumulate_shadow_gate(_decision("CCC", mxv_price=False))
    row = lg._build_shadow_gate_row()
    assert row is not None, "row must be written when MxV+price would-enters exist"


def test_mxv_price_count_present():
    lg = _fresh_logger()
    lg._accumulate_shadow_gate(_decision("AAA", mxv_price=True))
    lg._accumulate_shadow_gate(_decision("BBB", mxv_price=True))
    lg._accumulate_shadow_gate(_decision("CCC", mxv_price=False))
    row = lg._build_shadow_gate_row()
    assert 2 in row, f"MxV+price would-enter count (2) must be in the row: {row}"


def test_score_divergence_still_counted():
    # Mirror: the existing Score-divergence count must not break.
    lg = _fresh_logger()
    lg._accumulate_shadow_gate(_decision("XXX", score_skip=True, explicit_div=True))
    row = lg._build_shadow_gate_row()
    assert row is not None
    assert row[3] == 1, f"ScoreSkips should be 1: {row}"
