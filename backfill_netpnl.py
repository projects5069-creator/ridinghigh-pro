#!/usr/bin/env python3
"""
backfill_netpnl.py — TASK-140: FILL-ONLY backfill of the 4 NetPnL columns into
post_analysis (historical rows that already have complete OHLC).

  - Computes NetPnL via calculate_stats(scan_price, ohlc) — the SAME SSoT path the
    collector uses, so backfilled values are identical to forward-collected ones.
  - Touches ONLY NetPnL_SlipOnly / Borrow50 / Borrow200 / Borrow500. NEVER OHLC,
    Score, or any existing stat.
  - FILL-ONLY: writes a computable value only into an EMPTY cell. None
    (PENDING/WHIPSAW/NO_TOUCH) -> left NULL; already-filled cell -> skipped.
    => idempotent, zero churn on re-run.
  - cell-level batch_update (mirrors backfill_ohlc_v2). Dry-run by default.

Usage:
    python3 backfill_netpnl.py --months 2026-04,2026-05            # dry-run (zero writes)
    python3 backfill_netpnl.py --months 2026-04,2026-05 --apply    # write
"""
import argparse
import sys
import os
import json

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(REPO_DIR, "sheets_config.json")
sys.path.insert(0, REPO_DIR)

import pandas as pd
from datetime import datetime
from gspread.utils import rowcol_to_a1

import sheets_manager
from backfill_ohlc_v2 import _load_month   # SSoT loader (same row->sheet mapping)
from utils import calculate_stats, _is_missing, PERU_TZ

NETPNL_COLS = ["NetPnL_SlipOnly", "NetPnL_Borrow50", "NetPnL_Borrow200", "NetPnL_Borrow500"]


def _num(v):
    """Coerce a sheet cell to float, or None if missing/non-numeric (NOT NaN)."""
    try:
        f = float(str(v).replace('%', '').replace(',', '').replace('$', '').strip())
    except (ValueError, TypeError):
        return None
    return None if pd.isna(f) else f


def build_updates(df, header):
    """Pure (no I/O): cell-level updates for EMPTY NetPnL cells with a computable value.

    Mirrors backfill_ohlc_v2 cell format. FILL-ONLY + None-skip => idempotent.
    df position i maps to sheet row i+2 (header is row 1).
    """
    col_idx = {name: j + 1 for j, name in enumerate(header)}
    cols = [c for c in NETPNL_COLS if c in col_idx]
    updates = []
    for pos, row in df.iterrows():
        scan_price = _num(row.get("ScanPrice"))
        if scan_price is None or scan_price <= 0:
            continue
        ohlc = {f"D{i}_{k}": _num(row.get(f"D{i}_{k}"))
                for i in range(1, 6) for k in ("Open", "High", "Low", "Close")}
        stats = calculate_stats(scan_price, ohlc)   # same SSoT as the collector
        for col in cols:
            val = stats.get(col)
            if val is None:
                continue                            # PENDING/WHIPSAW/NO_TOUCH -> leave NULL
            if not _is_missing(row.get(col)):
                continue                            # FILL-ONLY: never overwrite an existing value
            updates.append({"range": rowcol_to_a1(pos + 2, col_idx[col]),
                            "values": [[str(round(val, 4))]]})
    return updates


def run(months, apply):
    mode = "APPLY" if apply else "DRY-RUN"
    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    print(f"🔧 backfill_netpnl — {today} — mode: {mode} — months: {months}")
    total = 0
    for month in months:
        ws, header, df = _load_month(month)
        if df.empty:
            print(f"  {month}: empty/unreachable — skipped")
            continue
        missing_cols = [c for c in NETPNL_COLS if c not in (header or [])]
        if missing_cols:
            print(f"  ⚠️ {month}: header missing {missing_cols} — collector/save must add them first; skipped")
            continue
        updates = build_updates(df, header)
        if updates and apply:
            sheets_manager._with_retry(ws.batch_update, updates, value_input_option="USER_ENTERED")
            print(f"  ✅ {month}: WROTE {len(updates)} NetPnL cells")
        else:
            prefix = "DRY-RUN — " if not apply else ""
            print(f"  🔍 {month}: {prefix}would write {len(updates)} NetPnL cells")
        total += len(updates)
    print(f"\n══════ SUMMARY ══════  NetPnL cells {'written' if apply else 'to write (dry-run)'}: {total} | mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FILL-ONLY NetPnL backfill for post_analysis (TASK-140)")
    parser.add_argument("--months", type=str, default=None,
                        help="comma-separated YYYY-MM list (default: all in sheets_config)")
    parser.add_argument("--apply", action="store_true",
                        help="actually write to Sheets (default: dry-run, zero writes)")
    args = parser.parse_args()
    if args.months:
        _months = [m.strip() for m in args.months.split(",") if m.strip()]
    else:
        with open(CONFIG_PATH) as fh:
            _months = sorted(json.load(fh).keys())
    run(_months, apply=args.apply)
