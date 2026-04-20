#!/usr/bin/env python3
"""
migrate_vwap_price_to_typical_price.py — Issue #24
One-time migration: rename column names in Google Sheets
  - VWAP_price        → TypicalPrice       (daily_snapshots)
  - VWAP_price_raw    → TypicalPrice_raw   (post_analysis)
  - VWAP_calc         → TypicalPriceDist_calc (post_analysis)

Usage:
    python3 migrate_vwap_price_to_typical_price.py --dry-run
    python3 migrate_vwap_price_to_typical_price.py
"""
import sys
import os
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_manager

# (sheet, old_column_name, new_column_name)
TARGETS = [
    ("daily_snapshots", "VWAP_price",     "TypicalPrice"),
    ("post_analysis",   "VWAP_price_raw", "TypicalPrice_raw"),
    ("post_analysis",   "VWAP_calc",      "TypicalPriceDist_calc"),
]


def gspread_col_letter(col_num):
    result = ""
    while col_num > 0:
        col_num, rem = divmod(col_num - 1, 26)
        result = chr(65 + rem) + result
    return result


def migrate_column(gc, month_key, tab_name, old_name, new_name, dry_run):
    print(f"\n[{month_key}] {tab_name}: '{old_name}' → '{new_name}'")
    try:
        ws = sheets_manager.get_worksheet(tab_name, month=month_key, gc=gc)
        if ws is None:
            print(f"  ⚠ worksheet not found — skipping")
            return 0
        header = ws.row_values(1)
        if not header:
            print(f"  ⚠ empty sheet — skipping")
            return 0
        try:
            col_idx = header.index(old_name)
        except ValueError:
            if new_name in header:
                print(f"  ✅ already migrated (found '{new_name}')")
                return 0
            print(f"  ⚠ column '{old_name}' not found")
            return 0
        col_letter = gspread_col_letter(col_idx + 1)
        print(f"  → found at column {col_letter} (index {col_idx})")
        if dry_run:
            print(f"  DRY RUN: would rename")
            return 1
        ws.update_cell(1, col_idx + 1, new_name)
        print(f"  ✅ renamed")
        time.sleep(1)
        return 1
    except Exception as e:
        print(f"  ❌ error: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print(f"VWAP_price/raw/calc → TypicalPrice migration{' (DRY RUN)' if args.dry_run else ''}")
    print("=" * 70)

    gc = sheets_manager._get_gc()
    if gc is None:
        print("❌ Could not authenticate")
        sys.exit(1)

    config = sheets_manager._load_config()
    total = 0
    for month_key in config.keys():
        for tab, old, new in TARGETS:
            if tab in config.get(month_key, {}):
                total += migrate_column(gc, month_key, tab, old, new, args.dry_run)

    print(f"\n{'=' * 70}")
    print(f"Total {'previewed' if args.dry_run else 'migrated'}: {total}")


if __name__ == "__main__":
    main()
