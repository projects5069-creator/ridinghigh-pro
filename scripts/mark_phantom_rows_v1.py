#!/usr/bin/env python3
"""
mark_phantom_rows_v1.py — TASK-246
──────────────────────────────────
Marks the rows that the finviz doubled-first-letter corruption produced, so
research can exclude them by rule instead of by memory. MARKS ONLY. Never
deletes a row, never rewrites a metric, never fabricates an exit.

The phantom test itself is NOT implemented here. It lives in
formulas.classify_phantom_tier, which delegates the proven case to
formulas.is_confirmed_phantom (rule 10, single source of truth), mirroring the
is_interday_artifact precedent. This script only decides which cell to write.

Two tiers are marked, never one (wired 2026-08-03). CONFIRMED means the stripped
form appears in the data, SUSPECT means the first letter is doubled but nothing
corroborates it. On the July measurement that is 67 and 16 of the 83 stuck open
positions; filtering on CONFIRMED alone left those 16 with no mark at all, which
is precisely the group a researcher cannot otherwise explain. CLEAN is never
written: a row with an undoubled first letter is not touched.

Where the mark goes, and why each choice:
  post_analysis    new column PhantomTicker. SCHEMA.json declares this tab
                   mode=required_subset with 5 required columns, so an added
                   column is not drift and health_audit check_08 stays green.
  daily_snapshots  new column PhantomTicker. Not present in SCHEMA.json at all,
                   so no contract to violate.
  paper_portfolio  the EXISTING DataQuality column. This tab is mode=exact with
                   25 columns, so adding a 26th WOULD make check_08 report drift.
                   Status is left untouched on purpose: cross_month_loaders:383,
                   deep_scan:182, auto_scanner:696 and dashboard:2180 all branch
                   on Status values, and inventing a fifth value risks breaking
                   them silently.

Universe: the CONFIRMED test needs a set of real symbols drawn from the same
data. It is built from every ticker seen across the tabs read, exactly as the
measurement script does.

Usage:
    python3 scripts/mark_phantom_rows_v1.py --dry-run
    python3 scripts/mark_phantom_rows_v1.py --dry-run --source live
    python3 scripts/mark_phantom_rows_v1.py --apply            # market closed only

--dry-run is the default. --source cache is the default and reads the local
snapshot, so a dry run costs zero Sheets quota and is safe during market hours.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formulas import (  # noqa: E402
    classify_phantom_tier, PHANTOM_CONFIRMED, PHANTOM_SUSPECT,
)

MONTH = "2026-07"
CACHE_PATH = os.path.join(tempfile.gettempdir(), f"rh_measure_cache_{MONTH}.json")
RESEARCH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research")

FLAG_COL = "PhantomTicker"
FLAG_VALUE = "PHANTOM"
PP_DATAQUALITY_VALUE = "PHANTOM_TICKER"

# TASK-246: the second tier. A doubled first letter whose stripped form never
# appeared in the scanned data is likely corruption but unproven, and 16 of the
# 83 stuck July positions are exactly that. They get a mark of their own rather
# than no mark, so research can exclude them by rule and still tell the two
# groups apart. The universe is point in time, so a suspect can become confirmed
# on a later run; the value only records what was provable at marking time.
FLAG_VALUE_SUSPECT = "PHANTOM_SUSPECT"
PP_DATAQUALITY_VALUE_SUSPECT = "PHANTOM_TICKER_SUSPECT"

# tab -> (date column candidates, mark strategy)
TARGETS = {
    "post_analysis":   (("ScanDate", "Date"), "new_column"),
    "daily_snapshots": (("Date", "ScanDate"), "new_column"),
    "paper_portfolio": (("EntryDate",), "dataquality"),
}


def load_cache():
    if not os.path.exists(CACHE_PATH):
        print(f"FATAL: cache missing at {CACHE_PATH}")
        print("Run scripts/measure_phantom_coverage_v1.py --refresh --headers "
              "while the market is closed, then retry.")
        sys.exit(1)
    try:
        return json.load(open(CACHE_PATH))
    except Exception as exc:
        print(f"FATAL: cache unreadable: {exc}")
        sys.exit(1)


def load_live():
    import sheets_manager
    gc = sheets_manager._get_gc()
    if gc is None:
        print("FATAL: no Google credentials")
        sys.exit(1)
    out = {}
    for tab in TARGETS:
        ws = sheets_manager.get_worksheet(tab, month=MONTH, gc=gc)
        out[tab] = ws.get_all_values() if ws is not None else []
        print(f"  READ / {tab} / {len(out[tab])} row(s)")
    return out


def build_universe(data):
    """Every ticker seen anywhere in the loaded tabs."""
    seen = set()
    for vals in data.values():
        if not vals:
            continue
        header = vals[0]
        idx = None
        for name in ("Ticker", "ticker", "Symbol"):
            if name in header:
                idx = header.index(name)
                break
        if idx is None:
            continue
        for r in vals[1:]:
            if len(r) > idx and r[idx].strip():
                seen.add(r[idx].strip().upper())
    return seen


def plan_tab(tab, vals, universe):
    """Return (header, hits, note). hits = list of (sheet_row, ticker, date, action)."""
    if not vals:
        return [], [], "EMPTY_OR_UNREADABLE"
    header = vals[0]
    date_names, strategy = TARGETS[tab]

    if "Ticker" not in header:
        return header, [], "COL_NOT_FOUND=Ticker"
    ti = header.index("Ticker")

    di = None
    for name in date_names:
        if name in header:
            di = header.index(name)
            break
    date_label = header[di] if di is not None else "(no date column)"

    if strategy == "dataquality":
        if "DataQuality" not in header:
            return header, [], "COL_NOT_FOUND=DataQuality"
        target_col = "DataQuality"
        value_by_tier = {PHANTOM_CONFIRMED: PP_DATAQUALITY_VALUE,
                         PHANTOM_SUSPECT: PP_DATAQUALITY_VALUE_SUSPECT}
    else:
        target_col = FLAG_COL
        value_by_tier = {PHANTOM_CONFIRMED: FLAG_VALUE,
                         PHANTOM_SUSPECT: FLAG_VALUE_SUSPECT}

    hits = []
    for n, r in enumerate(vals[1:], start=2):   # sheet row number, header is row 1
        tk = r[ti].strip() if len(r) > ti else ""
        # TASK-246: both tiers are marked, each with its own value. CLEAN is absent
        # from value_by_tier on purpose, so a clean row can never be written to.
        value = value_by_tier.get(classify_phantom_tier(tk, universe))
        if value is None:
            continue
        day = r[di].strip()[:10] if (di is not None and len(r) > di) else ""
        hits.append((n, tk.upper(), day, f"{target_col}={value}"))

    note = (f"date_col={date_label} strategy={strategy} target={target_col} "
            f"column_exists={target_col in header}")
    return header, hits, note


def backup(data, hits_by_tab):
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RESEARCH_DIR, f"phantom_mark_backup_{MONTH}_{ts}.json")
    payload = {}
    for tab, hits in hits_by_tab.items():
        vals = data.get(tab) or []
        payload[tab] = {
            "header": vals[0] if vals else [],
            "rows": {str(n): vals[n - 1] for n, _, _, _ in hits if n - 1 < len(vals)},
        }
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"  BACKUP / {path} / "
          f"{sum(len(v['rows']) for v in payload.values())} row(s) captured")
    return path


def main():
    p = argparse.ArgumentParser(description="TASK-246 phantom row marker (marks only)")
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--apply", action="store_true",
                   help="actually write to Sheets (market closed only)")
    p.add_argument("--source", choices=("cache", "live"), default="cache",
                   help="cache (default, zero quota) or live")
    a = p.parse_args()

    apply_changes = a.apply
    print(f"MONTH={MONTH}  SOURCE={a.source}  MODE="
          f"{'APPLY' if apply_changes else 'DRY-RUN'}")

    data = load_live() if a.source == "live" else load_cache()
    if a.source == "cache":
        print(f"  CACHE / {CACHE_PATH}")
        for k, v in data.items():
            print(f"    {k} = {len(v)} row(s) incl header")

    universe = build_universe(data)
    print(f"UNIVERSE_DISTINCT_TICKERS={len(universe)}")

    hits_by_tab = {}
    for tab in TARGETS:
        vals = data.get(tab)
        header, hits, note = plan_tab(tab, vals or [], universe)
        hits_by_tab[tab] = hits
        print(f"\n--- {tab} ---")
        print(f"  {note}")
        print(f"  ROWS_TO_MARK={len(hits)}")
        for n, tk, day, action in hits:
            print(f"    row {n:>4}  {tk:<10} {day:<12} -> {action}")

    total = sum(len(v) for v in hits_by_tab.values())
    print(f"\nTOTAL_ROWS_TO_MARK={total}")
    for tab, hits in hits_by_tab.items():
        print(f"  {tab:<18} {len(hits)}")

    if not apply_changes:
        print("\nDRY-RUN: nothing written. Re-run with --apply --source live "
              "when the market is closed.")
        return

    if a.source != "live":
        print("\nREFUSING: --apply requires --source live, so the write is based "
              "on current sheet contents and row numbers, not a snapshot.")
        sys.exit(1)

    backup(data, hits_by_tab)
    print("\nWRITE step is intentionally not implemented in v1. The dry-run plan "
          "and the backup are the deliverable; wiring the write needs explicit "
          "approval and a read-back verification pass.")


if __name__ == "__main__":
    main()
