"""TASK-140 backfill — dedicated FILL-ONLY NetPnL backfill for post_analysis.

Tests the pure builder (build_updates) + the dry-run/apply write gate.
NetPnL is computed via calculate_stats (same SSoT as the collector), written
cell-level (mirrors backfill_ohlc_v2). FILL-ONLY: only empty cells get a
computable value; None (PENDING/WHIPSAW/NO_TOUCH) and already-filled cells are
skipped → idempotent, zero churn.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backfill_netpnl import build_updates, run, NETPNL_COLS

HEADER = (["Ticker", "ScanDate", "ScanPrice"]
          + [f"D{i}_{k}" for i in range(1, 6) for k in ("Open", "High", "Low", "Close")]
          + NETPNL_COLS)


def _row(scan, days, net_vals=("", "", "", "")):
    """days = list of (Open,High,Low,Close) per D1.. ; net_vals = 4 existing NetPnL cells."""
    r = {"Ticker": "AAA", "ScanDate": "2026-05-01", "ScanPrice": str(scan)}
    for i in range(1, 6):
        for k in ("Open", "High", "Low", "Close"):
            r[f"D{i}_{k}"] = ""
    for i, (o, h, lo, c) in enumerate(days, start=1):
        r[f"D{i}_Open"], r[f"D{i}_High"], r[f"D{i}_Low"], r[f"D{i}_Close"] = str(o), str(h), str(lo), str(c)
    for col, v in zip(NETPNL_COLS, net_vals):
        r[col] = v
    return r


# 5 days that resolve WIN on D1 (scan=100, tp=90): D1 Low=89, rest neutral
WIN_DAYS = [(100, 105, 89, 95), (100, 105, 95, 100), (100, 105, 95, 100),
            (100, 105, 95, 100), (100, 105, 95, 100)]
# Only D1-D2 present -> PENDING
PENDING_DAYS = [(100, 105, 95, 100), (100, 105, 95, 100)]


def _df(rows):
    return pd.DataFrame(rows, columns=HEADER)


def test_win_row_yields_4_netpnl_updates():
    df = _df([_row(100, WIN_DAYS)])
    updates = build_updates(df, HEADER)
    assert len(updates) == 4
    by_a1 = {u["range"]: float(u["values"][0][0]) for u in updates}
    # SlipOnly column value ≈ 0.0818 (WIN gross, no borrow)
    col_idx = {n: j + 1 for j, n in enumerate(HEADER)}
    from gspread.utils import rowcol_to_a1
    slip_a1 = rowcol_to_a1(0 + 2, col_idx["NetPnL_SlipOnly"])
    assert by_a1[slip_a1] == pytest.approx(0.0818, abs=1e-3)


def test_pending_row_yields_no_updates():
    df = _df([_row(100, PENDING_DAYS)])
    assert build_updates(df, HEADER) == []


def test_fill_only_skips_already_filled_cells():
    """A WIN row whose 4 NetPnL cells already hold values -> 0 updates (FILL-ONLY)."""
    df = _df([_row(100, WIN_DAYS, net_vals=("0.08", "0.07", "0.06", "0.05"))])
    assert build_updates(df, HEADER) == []


def test_bad_scan_price_skipped():
    df = _df([_row(0, WIN_DAYS)])
    assert build_updates(df, HEADER) == []


# ─────────────── write gate: dry-run vs apply ───────────────

def test_dry_run_does_not_write():
    df = _df([_row(100, WIN_DAYS)])
    ws = MagicMock()
    with patch("backfill_netpnl._load_month", return_value=(ws, HEADER, df)), \
         patch("backfill_netpnl.sheets_manager._with_retry") as retry:
        run(["2026-05"], apply=False)
    retry.assert_not_called()


def test_apply_writes_via_batch_update():
    df = _df([_row(100, WIN_DAYS)])
    ws = MagicMock()
    with patch("backfill_netpnl._load_month", return_value=(ws, HEADER, df)), \
         patch("backfill_netpnl.sheets_manager._with_retry") as retry:
        run(["2026-05"], apply=True)
    retry.assert_called_once()
    # called as _with_retry(ws.batch_update, updates, value_input_option=...)
    assert retry.call_args.args[0] == ws.batch_update
