"""TASK-192 (C4) — buffer per-position portfolio writes, flush ONE batch_update.

Today the orchestrator's portfolio writer issues one safe_batch_update PER monitored
position (orchestrator.py:622) → N open positions = N API writes/run (cap = 5 concurrent).
C4 buffers each position's row-specific cells and flushes a single batch_update.

The ONE thing that must never break: every buffered cell stays targeted at its OWN
position's `_row_number` (Bug #2 fix). A merge that mis-targets a row would corrupt the
portfolio. These tests lock per-row targeting + the single flush. Pure: FakeWs, no live Sheets.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.orchestrator import make_portfolio_batch_writer


class FakeWs:
    def __init__(self, col_values_map=None):
        self.batch_update_calls = 0
        self.last_cells = None
        self.last_opt = None
        self._cv = col_values_map or {}

    def batch_update(self, cells, value_input_option=None):
        self.batch_update_calls += 1
        self.last_cells = list(cells)   # snapshot — real batch_update consumes synchronously before buffer.clear()
        self.last_opt = value_input_option
        return {"ok": True}

    def col_values(self, col):
        return self._cv.get(col, [])


HDR = ["PositionID", "Ticker", "CurrentPrice", "UnrealizedPnL"]  # cols 1..4 -> A..D


def _row_of(a1):
    return int(re.sub(r"[A-Z]+", "", a1))


def test_n3_one_batch_targets_each_row_no_cross():
    ws = FakeWs()
    writer, flush = make_portfolio_batch_writer(ws, HDR, 0)
    writer({"_row_number": 2, "PositionID": "P2"}, {"CurrentPrice": 1.11})
    writer({"_row_number": 5, "PositionID": "P5"}, {"CurrentPrice": 2.22, "UnrealizedPnL": 50})
    writer({"_row_number": 9, "PositionID": "P9"}, {"CurrentPrice": 3.33})
    n = flush()
    assert ws.batch_update_calls == 1                       # ONE API write for all 3 positions
    cells = ws.last_cells
    assert {"range": "C2", "values": [[1.11]]} in cells     # P2 -> row 2
    assert {"range": "C5", "values": [[2.22]]} in cells     # P5 -> row 5
    assert {"range": "D5", "values": [[50]]} in cells       # P5 second col -> row 5
    assert {"range": "C9", "values": [[3.33]]} in cells     # P9 -> row 9
    assert all(_row_of(c["range"]) in (2, 5, 9) for c in cells)   # NO cell mis-targets a row
    assert ws.last_opt == "USER_ENTERED"
    assert n == 4


def test_n1_single_write_no_regression():
    ws = FakeWs()
    writer, flush = make_portfolio_batch_writer(ws, HDR, 0)
    writer({"_row_number": 7, "PositionID": "P7"}, {"CurrentPrice": 9.9})
    n = flush()
    assert ws.batch_update_calls == 1
    assert ws.last_cells == [{"range": "C7", "values": [[9.9]]}]
    assert n == 1


def test_n0_no_api_write():
    ws = FakeWs()
    writer, flush = make_portfolio_batch_writer(ws, HDR, 0)
    n = flush()
    assert ws.batch_update_calls == 0     # nothing buffered -> no batch_update at all
    assert n == 0


def test_buffer_clears_after_flush():
    ws = FakeWs()
    writer, flush = make_portfolio_batch_writer(ws, HDR, 0)
    writer({"_row_number": 2, "PositionID": "P2"}, {"CurrentPrice": 1.0})
    flush()
    n2 = flush()                          # second flush, buffer already drained
    assert ws.batch_update_calls == 1     # not 2
    assert n2 == 0


def test_unknown_column_dropped():
    ws = FakeWs()
    writer, flush = make_portfolio_batch_writer(ws, HDR, 0)
    writer({"_row_number": 2, "PositionID": "P2"}, {"CurrentPrice": 1.0, "NotAColumn": "x"})
    flush()
    assert ws.last_cells == [{"range": "C2", "values": [[1.0]]}]   # NotAColumn not in HDR -> skipped
