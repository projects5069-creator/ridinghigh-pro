"""T-401 (Sprint 0) — every rejected candidate must persist its six entry
metrics.

E-05: skip_summary carries Timestamp/RunID/SkipReason/Count/Tickers/ScoreMin/
ScoreMax — none of MxV/RunUp/ATRX/RSI/REL_VOL/ScanChange — so the gate has no
counterfactual and 1,414 rejection rows are unusable for edge evaluation.
The fix adds a parallel skip_metrics buffer (skip_summary itself is untouched —
it has consumers). RED before fix.
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from agent.logging.decision_logger import DecisionLogger


def _skip_decision():
    return SimpleNamespace(
        ticker="AATPC",
        skip_reason="MXV_TOO_HIGH: -50 > -100",
        reason="",
        score=41.2,
        timestamp="2026-08-07T10:00:00-05:00",
        mxv=-50.0,
        run_up=12.0,
        atrx=1.1,
        rsi=55.0,
        rel_vol=2.2,
        scan_change=8.8,
    )


def test_flush_skip_metrics_persists_the_six_entry_metrics():
    lg = DecisionLogger(sheet_id="test-sheet")
    lg._accumulate_skip(_skip_decision())

    written = []

    def fake_writer(rows):
        written.extend(rows)
        return True

    n = lg.flush_skip_metrics(writer=fake_writer)
    assert n == 1, f"expected 1 metrics row flushed, got {n}"
    row = written[0]
    # Schema: Timestamp, RunID, Ticker, SkipReason, MxV, RunUp, ATRX, RSI, REL_VOL, ScanChange
    assert row[2] == "AATPC", row
    assert "MXV_TOO_HIGH" in str(row[3]), row
    assert row[4:10] == [-50.0, 12.0, 1.1, 55.0, 2.2, 8.8], (
        f"the six entry metrics must be persisted in schema order, got {row[4:10]!r}"
    )


def test_flush_skip_metrics_clears_buffer_and_is_idempotent():
    lg = DecisionLogger(sheet_id="test-sheet")
    lg._accumulate_skip(_skip_decision())
    first = lg.flush_skip_metrics(writer=lambda rows: True)
    second = lg.flush_skip_metrics(writer=lambda rows: True)
    assert first == 1 and second == 0, (first, second)
