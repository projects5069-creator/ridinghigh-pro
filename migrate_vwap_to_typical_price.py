#!/usr/bin/env python3
"""
migrate_vwap_to_typical_price.py — Issue #11 Step B
One-time migration: rename column "VWAP" / "VWAP_Dist" → "TypicalPriceDist"
in all Google Sheets where the column appears.

Run this manually BEFORE deploying step C (which writes the new column name).

Usage:
    python3 migrate_vwap_to_typical_price.py --dry-run   # preview changes
    python3 migrate_vwap_to_typical_price.py             # live migration
"""
import sys
import os
import argparse
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_manager

# Sheets + their expected current VWAP column names
# Only sheets that actually contain a VWAP/VWAP_Dist column.
# timeline_live: schema has 17 cols, no VWAP (see issue #23)
# portfolio: different schema, no VWAP column
TARGETS = [
    ("daily_snapshots", "VWAP"),
    ("score_tracker",   "VWAP_Dist"),
    ("post_analysis",   "VWAP"),
]

NEW_NAME = "TypicalPriceDist"

def migrate_sheet(gc, month_key, tab_name, old_col_name, dry_run=False):
    print(f"\n[{month_key}] {tab_name}: looking for column '{old_col_name}'...")
    try:
        ws = sheets_manager.get_worksheet(tab_name, month=month_key, gc=gc)
        if ws is None:
            print(f"  ⚠ worksheet not found — skipping")
            return 0

        # Read only header (row 1) to find the column
        header = ws.row_values(1)
        if not header:
            print(f"  ⚠ empty sheet — skipping")
            return 0

        # Find old column
        try:
            col_idx = header.index(old_col_name)  # 0-based
        except ValueError:
            # Also check NEW_NAME — maybe already migrated
            if NEW_NAME in header:
                print(f"  ✅ already migrated (found '{NEW_NAME}')")
                return 0
            print(f"  ⚠ column '{old_col_name}' not found — header: {header}")
            return 0

        col_letter = gspread_col_letter(col_idx + 1)
        print(f"  → found at column {col_letter} (index {col_idx})")

        if dry_run:
            print(f"  DRY RUN: would rename '{old_col_name}' → '{NEW_NAME}'")
            return 1

        # Rename the header cell
        ws.update_cell(1, col_idx + 1, NEW_NAME)
        print(f"  ✅ renamed '{old_col_name}' → '{NEW_NAME}'")
        time.sleep(1)  # rate limit
        return 1
    except Exception as e:
        print(f"  ❌ error: {e}")
        return 0

def gspread_col_letter(col_num):
    """Convert column number (1-based) to letter (A, B, ..., Z, AA, AB, ...)."""
    result = ""
    while col_num > 0:
        col_num, rem = divmod(col_num - 1, 26)
        result = chr(65 + rem) + result
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing")
    args = parser.parse_args()

    print("=" * 70)
    print(f"VWAP → TypicalPriceDist Migration{' (DRY RUN)' if args.dry_run else ''}")
    print("=" * 70)

    gc = sheets_manager._get_gc()
    if gc is None:
        print("❌ Could not authenticate to Google Sheets")
        sys.exit(1)

    config = sheets_manager._load_config()
    months = list(config.keys())
    print(f"Months to process: {months}")

    total = 0
    for month_key in months:
        for tab_name, old_col in TARGETS:
            if tab_name not in config.get(month_key, {}):
                continue
            total += migrate_sheet(gc, month_key, tab_name, old_col, args.dry_run)

    print(f"\n{'=' * 70}")
    print(f"Total sheets {'previewed' if args.dry_run else 'migrated'}: {total}")
    print("=" * 70)

if __name__ == "__main__":
    main()
