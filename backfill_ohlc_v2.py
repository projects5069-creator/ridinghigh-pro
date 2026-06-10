#!/usr/bin/env python3
"""
backfill_ohlc_v2.py — TASK-123
Closes stale-PENDING post_analysis rows across MONTHS (not just active) with a
WIDER trigger (ANY missing D1..D5 cell whose trading day is complete), filling
ONLY empty cells. v1 (backfill_ohlc.py) is left untouched per Iron Rule §12.

Differences vs v1 (kept side by side on purpose):
  1. Trigger: any D{i} OHLC cell empty for a settled day — not just D1_Open.
  2. Scope:   iterates months explicitly (default: all in sheets_config).
  3. Safety:  FILL-ONLY — an existing cell value is never overwritten; writes
              go through ws.batch_update of the filled cells ONLY (no full-sheet
              rewrite, no clobber/race risk with the collector).
  4. Stats:   recomputed (calculate_stats) only for rows that received at least
              one new cell, from the MERGED existing+new OHLC picture.
  5. Default is --dry-run style: nothing is written without --apply.

Usage (run off-market-hours):
    python3 backfill_ohlc_v2.py --months 2026-04,2026-05            # dry-run
    python3 backfill_ohlc_v2.py --months 2026-04,2026-05 --apply    # write
"""

import argparse
import sys, os, time, json
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
from datetime import datetime
from gspread.utils import rowcol_to_a1

import sheets_manager
from backfill_ohlc import fetch_ohlc  # reuse v1 fetcher (4 attempts, 15-day window)
from utils import (
    is_day_complete,
    get_trading_days_after,
    calculate_stats,
    _is_missing,
    PERU_TZ,
)

OHLC_FIELDS = ("Open", "High", "Low", "Close")
STATS_KEYS = ("MaxDrop%", "BestDay", "TP10_Hit", "TP15_Hit", "TP20_Hit",
              "D1_Gap%", "SL_Hit_D5", "IntraDay_SL")


def _load_month(month: str):
    """Load one month's post_analysis as (worksheet, header, DataFrame).
    Row order is preserved — df position i == sheet row i+2."""
    ws = sheets_manager.get_worksheet("post_analysis", month=month)
    if ws is None:
        return None, None, pd.DataFrame()
    raw = sheets_manager._with_retry(ws.get_all_values)
    if len(raw) <= 1:
        return ws, raw[0] if raw else [], pd.DataFrame()
    return ws, raw[0], pd.DataFrame(raw[1:], columns=raw[0])


def _missing_days(row, trading_days):
    """Day indices (1..5) that are settled (is_day_complete) but have at least
    one empty OHLC cell. This is the v2 trigger."""
    need = []
    for i, day in enumerate(trading_days, 1):
        if not is_day_complete(day):
            continue
        if any(_is_missing(row.get(f"D{i}_{f}")) for f in OHLC_FIELDS):
            need.append(i)
    return need


def _merged_ohlc(row, fetched):
    """Existing cells win; fetched values fill only the holes."""
    merged = {}
    for i in range(1, 6):
        for f in OHLC_FIELDS:
            key = f"D{i}_{f}"
            cur = row.get(key)
            if not _is_missing(cur):
                try:
                    merged[key] = float(str(cur).replace(",", ""))
                except (TypeError, ValueError):
                    merged[key] = None
            else:
                merged[key] = fetched.get(key)
    return merged


def process_month(month: str, today_str: str, apply: bool):
    print(f"\n══════ {month} ══════")
    ws, header, df = _load_month(month)
    if df.empty:
        print("  (empty or unreachable — skipped)")
        return {"rows": 0, "candidates": 0, "cells": 0, "unfillable": []}

    col_idx = {name: j + 1 for j, name in enumerate(header)}
    print(f"  rows: {len(df)}")

    candidates = []
    for pos, row in df.iterrows():
        ticker = str(row.get("Ticker", "")).strip()
        scan_date = str(row.get("ScanDate", "")).strip()
        scan_price = pd.to_numeric(row.get("ScanPrice", 0), errors="coerce") or 0
        if not ticker or not scan_date or scan_price <= 0 or scan_date == today_str:
            continue
        trading_days = get_trading_days_after(scan_date, 5)
        need = _missing_days(row, trading_days)
        if need:
            candidates.append((pos, ticker, scan_date, scan_price, trading_days, need))

    print(f"  candidates (any settled-but-empty D-day): {len(candidates)}")
    cell_updates, filled_cells, unfillable = [], 0, []

    for pos, ticker, scan_date, scan_price, trading_days, need in candidates:
        fetched = fetch_ohlc(ticker, trading_days)
        new_cells = []
        for i in need:
            for f in OHLC_FIELDS:
                key = f"D{i}_{f}"
                val = fetched.get(key)
                if val is None or key not in col_idx:
                    continue
                if not _is_missing(df.at[pos, key]):
                    continue  # FILL-ONLY: never touch an existing value
                new_cells.append((key, val))
        if not new_cells:
            unfillable.append(f"{ticker} {scan_date} (missing D{need})")
            print(f"  ⏭ {ticker} {scan_date}: fetch returned nothing fillable — left untouched")
            time.sleep(0.4)
            continue

        # queue OHLC cells + update in-memory copy
        for key, val in new_cells:
            df.at[pos, key] = str(val)
            cell_updates.append({"range": rowcol_to_a1(pos + 2, col_idx[key]),
                                 "values": [[str(val)]]})
        filled_cells += len(new_cells)

        # recompute stats from the MERGED picture (derived values — overwrite ok)
        stats = calculate_stats(scan_price, _merged_ohlc(df.loc[pos], fetched))
        for key in STATS_KEYS:
            val = stats.get(key)
            if val is None or key not in col_idx:
                continue
            cell_updates.append({"range": rowcol_to_a1(pos + 2, col_idx[key]),
                                 "values": [[str(val)]]})

        print(f"  📥 {ticker} {scan_date}: filled D{need} -> {len(new_cells)} cells (+stats)")
        time.sleep(0.4)  # rate limit (same as v1)

    if cell_updates:
        if apply:
            sheets_manager._with_retry(
                ws.batch_update, cell_updates, value_input_option="USER_ENTERED"
            )
            print(f"  ✅ WROTE {len(cell_updates)} cells ({filled_cells} OHLC + stats)")
        else:
            print(f"  🔍 DRY-RUN: would write {len(cell_updates)} cells "
                  f"({filled_cells} OHLC + stats) — re-run with --apply")
    else:
        print("  ✅ nothing to write")

    # after-count from the in-memory (post-fill) state
    still = 0
    for pos, row in df.iterrows():
        scan_date = str(row.get("ScanDate", "")).strip()
        if not scan_date or scan_date == today_str:
            continue
        if _missing_days(row, get_trading_days_after(scan_date, 5)):
            still += 1
    print(f"  still-missing rows after this run: {still}")
    return {"rows": len(df), "candidates": len(candidates),
            "cells": filled_cells, "unfillable": unfillable}


def run(months, apply: bool):
    today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"🔧 backfill_ohlc_v2 — {today_str} — mode: {mode} — months: {months}")
    totals = {"candidates": 0, "cells": 0}
    unfillable = []
    for month in months:
        r = process_month(month, today_str, apply)
        totals["candidates"] += r["candidates"]
        totals["cells"] += r["cells"]
        unfillable += r["unfillable"]
    print("\n══════ SUMMARY ══════")
    print(f"candidate rows: {totals['candidates']} | OHLC cells filled: {totals['cells']} | mode: {mode}")
    if unfillable:
        print(f"unfillable rows ({len(unfillable)} — delisted/no data, left untouched):")
        for u in unfillable:
            print(f"  - {u}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-month post_analysis OHLC backfill (TASK-123)")
    with open(os.path.expanduser("~/RidingHighPro/sheets_config.json")) as fh:
        _default_months = ",".join(sorted(json.load(fh).keys()))
    parser.add_argument("--months", type=str, default=_default_months,
                        help="comma-separated YYYY-MM list (default: all in sheets_config)")
    parser.add_argument("--apply", action="store_true",
                        help="actually write to Sheets (default: dry-run, zero writes)")
    args = parser.parse_args()
    run([m.strip() for m in args.months.split(",") if m.strip()], apply=args.apply)
