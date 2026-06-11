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

import sheets_manager
import utils

SOURCE = "ALPACA"


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
