"""
agent/perception/borrow_collector.py
─────────────────────────────────────
TASK-139 [BORROW] layer 1 — daily borrow / shortability snapshot collector.

Reads real Alpaca shortability per active ticker (read-only get_asset_info,
even under AGENT_DRY_RUN) and writes ONE batched row per ticker per day to the
borrow_data tab. Borrow fee is recorded as an explicit NULL (empty cell) —
Alpaca exposes no real borrow fee.

Mirrors decision_logger.flush_skip_summary: lazy worksheet resolve, a single
safe_append_rows per run, wrapped so it NEVER raises — borrow visibility must
not fail a trading run.

Schema (9): Ticker, CheckDate, CheckTime, IsShortable, IsETB, IsHTB,
            BorrowFeePct, SharesAvailable, Source
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

import sheets_manager
import utils
from config import AGENT_MXV_MAX

SOURCE = "ALPACA"


def get_scanned_universe(snapshots_df, mxv_max=AGENT_MXV_MAX):
    """Set of tickers in snapshots_df with MxV <= mxv_max (the scanned universe).
    TASK-208-B: switched from Score>=min_score — in the scoreless era (SCORE_WRITE_FROZEN)
    daily_snapshots.Score is blank "" -> NaN -> selects nothing; MxV is kept and is the
    live entry driver. Pure, no I/O. Empty set on empty df or missing Ticker/MxV cols."""
    if snapshots_df is None or snapshots_df.empty:
        return set()
    if "Ticker" not in snapshots_df.columns or "MxV" not in snapshots_df.columns:
        return set()
    mxv = pd.to_numeric(snapshots_df["MxV"], errors="coerce")
    sel = snapshots_df["Ticker"][mxv <= mxv_max]
    return {str(t).strip() for t in sel if str(t).strip()}


def _is_true(v):
    """Coerce a borrow_data IsShortable cell (bool or \"True\"/\"False\" string) to bool."""
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() == "true"


def compute_coverage(universe, borrow_rows):
    """Coverage of the scanned universe by borrow data. Pure (no I/O).

    universe: set of scanned tickers (the denominator for BOTH pcts).
    borrow_rows: borrow_data sheet rows (idx0=Ticker, idx3=IsShortable).
    Only rows whose ticker is in `universe` are counted. Returns a dict of
    5 fields; both pcts are over the universe size (pct=0.0 when universe empty).
    """
    n = len(universe)
    seen = set()
    shortable = 0
    for row in borrow_rows:
        if not row:
            continue
        t = str(row[0]).strip()
        if t not in universe or t in seen:
            continue
        seen.add(t)
        if len(row) > 3 and _is_true(row[3]):
            shortable += 1
    with_borrow = len(seen)
    pct_borrow = round(100.0 * with_borrow / n, 2) if n else 0.0
    pct_short = round(100.0 * shortable / n, 2) if n else 0.0
    return {
        "ScannedUniverse": n,
        "WithBorrowData": with_borrow,
        "ShortableCount": shortable,
        "PctWithBorrowData": pct_borrow,
        "PctShortable": pct_short,
    }


def build_coverage_row(cov, check_dt):
    """Build one borrow_coverage row: 8 values in schema order. Pure (no I/O).

    Schema: CheckDate, CheckTime, ScannedUniverse, WithBorrowData,
    PctWithBorrowData, ShortableCount, PctShortable, Source.
    """
    return [
        check_dt.strftime("%Y-%m-%d"),   # CheckDate (Peru)
        check_dt.strftime("%H:%M:%S"),   # CheckTime (Peru)
        cov["ScannedUniverse"],
        cov["WithBorrowData"],
        cov["PctWithBorrowData"],
        cov["ShortableCount"],
        cov["PctShortable"],
        SOURCE,
    ]


def build_borrow_row(ticker, asset_info, check_dt):
    """Build one borrow_data row: 9 values in schema order. Pure (no I/O).

    BorrowFeePct is "" (explicit NULL — Alpaca exposes no fee).
    IsHTB = IsShortable AND NOT IsETB. SharesAvailable is "" unless exposed.
    """
    shortable = asset_info["shortable"]
    etb = asset_info["easy_to_borrow"]
    return [
        ticker,
        check_dt.strftime("%Y-%m-%d"),            # CheckDate (Peru)
        check_dt.strftime("%H:%M:%S"),            # CheckTime (Peru)
        shortable,                                # IsShortable
        etb,                                      # IsETB
        shortable and not etb,                    # IsHTB
        "",                                       # BorrowFeePct — NULL
        asset_info.get("shares_available", ""),   # SharesAvailable — NULL unless exposed
        SOURCE,
    ]


def collect_borrow_coverage(universe, check_dt=None):
    """TASK-172: compute + write ONE borrow_coverage row for `universe`.

    Reads today's borrow_data rows, computes coverage (two separate pcts over
    the universe denominator), appends one row to borrow_coverage (dedup on
    CheckDate -> one row/day). Non-fatal: logs to stderr and returns None on
    any failure; never raises. Returns the coverage dict on success.
    """
    if check_dt is None:
        check_dt = utils.get_peru_time()
    today = check_dt.strftime("%Y-%m-%d")
    try:
        data_ws = sheets_manager.get_worksheet("borrow_data")
        cov_ws = sheets_manager.get_worksheet("borrow_coverage")
        if data_ws is None or cov_ws is None:
            print("[borrow_collector] coverage: worksheet unavailable", file=sys.stderr)
            return None
        all_rows = data_ws.get_all_values()[1:]
        today_rows = [r for r in all_rows if len(r) >= 2 and r[1] == today]
        cov = compute_coverage(universe, today_rows)
        row = build_coverage_row(cov, check_dt)
        sheets_manager.safe_append_rows(cov_ws, [row], dedup_col=0, dedup_vals={today})
        return cov
    except Exception as e:
        print(f"[borrow_collector] coverage failed (non-fatal): {e}", file=sys.stderr)
        return None


def collect_borrow_data(tickers, broker, check_dt=None):
    """Collect borrow data for `tickers` and write ONE batched append.

    Reads broker.get_asset_info() directly (real read, even under DRY_RUN).
    Pre-filters tickers already collected today (dedup on Ticker+CheckDate).
    A per-ticker broker error skips that ticker only. Any Sheets/worksheet
    error is non-fatal: the function never raises and returns the number of
    rows written (0 on no-op/error).
    """
    if check_dt is None:
        check_dt = utils.get_peru_time()
    try:
        ws = sheets_manager.get_worksheet("borrow_data")
        if ws is None:
            print("[borrow_collector] borrow_data worksheet unavailable", file=sys.stderr)
            return 0

        today = check_dt.strftime("%Y-%m-%d")
        existing = {(r[0], r[1]) for r in ws.get_all_values()[1:] if len(r) >= 2}

        rows = []
        for ticker in tickers:
            if (ticker, today) in existing:
                continue                          # already collected today (dedup / guard)
            try:
                info = broker.get_asset_info(ticker)
            except Exception as e:                # per-ticker failure is non-fatal
                print(f"[borrow_collector] {ticker} asset_info failed (skip): {e}", file=sys.stderr)
                continue
            rows.append(build_borrow_row(ticker, info, check_dt))

        if rows:
            sheets_manager.safe_append_rows(
                ws, rows, dedup_col=0, dedup_vals={r[0] for r in rows}
            )
        return len(rows)
    except Exception as e:
        print(f"[borrow_collector] collect failed (non-fatal): {e}", file=sys.stderr)
        return 0
