#!/usr/bin/env python3
"""
migrate_timeline_add_columns.py — Issue #23
One-time migration: add 8 dynamic metric columns to timeline_live header.

Columns added (after REL_VOL):
  Change, RSI, ATRX, Gap, TypicalPriceDist, PriceToHigh, PriceTo52WHigh, Float%

Usage:
    python3 migrate_timeline_add_columns.py --dry-run
    python3 migrate_timeline_add_columns.py
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_manager

NEW_COLUMNS = [
    "Change", "RSI", "ATRX", "Gap",
    "TypicalPriceDist", "PriceToHigh", "PriceTo52WHigh", "Float%"
]


def gspread_col_letter(col_num):
    result = ""
    while col_num > 0:
        col_num, rem = divmod(col_num - 1, 26)
        result = chr(65 + rem) + result
    return result


def migrate_timeline(gc, month_key, dry_run):
    print(f"\n[{month_key}] timeline_live:")
    try:
        ws = sheets_manager.get_worksheet("timeline_live", month=month_key, gc=gc)
        if ws is None:
            print("  ⚠ worksheet not found — skipping")
            return 0
        header = ws.row_values(1)
        if not header:
            print("  ⚠ empty sheet — skipping")
            return 0

        existing_new = [c for c in NEW_COLUMNS if c in header]
        missing_new = [c for c in NEW_COLUMNS if c not in header]

        if not missing_new:
            print(f"  ✅ already migrated (all {len(NEW_COLUMNS)} new columns exist)")
            return 0

        if existing_new:
            print(f"  ⚠ partial state — {len(existing_new)} already exist: {existing_new}")
            print(f"  Will add only missing: {missing_new}")

        first_new_col = len(header) + 1
        last_new_col = first_new_col + len(missing_new) - 1
        first_letter = gspread_col_letter(first_new_col)
        last_letter = gspread_col_letter(last_new_col)

        print(f"  Current header has {len(header)} columns")
        print(f"  Will add {len(missing_new)} columns at {first_letter}..{last_letter}")

        if dry_run:
            print(f"  DRY RUN: would add: {missing_new}")
            return 1

        # Write new column headers in a single batch
        range_str = f"{first_letter}1:{last_letter}1"
        ws.update(range_name=range_str, values=[missing_new])
        print(f"  ✅ added {len(missing_new)} columns")
        return 1
    except Exception as e:
        print(f"  ❌ error: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print(f"timeline_live column expansion{' (DRY RUN)' if args.dry_run else ''}")
    print("=" * 70)

    gc = sheets_manager._get_gc()
    if gc is None:
        print("❌ Could not authenticate")
        sys.exit(1)

    config = sheets_manager._load_config()
    total = 0
    for month_key in config.keys():
        if "timeline_live" in config.get(month_key, {}):
            total += migrate_timeline(gc, month_key, args.dry_run)

    print(f"\n{'=' * 70}")
    print(f"Total {'previewed' if args.dry_run else 'migrated'}: {total}")


if __name__ == "__main__":
    main()
