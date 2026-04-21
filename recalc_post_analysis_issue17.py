#!/usr/bin/env python3
"""
recalc_post_analysis_issue17.py — Issue #17 action 1
One-time recalc of Score, Score_B-I, and EntryScore for 29 rows in
post_analysis that have Score_recalc_date=empty/nan.

Does NOT touch the 100 rows already recalc'd on 2026-04-16.

Usage:
    python3 recalc_post_analysis_issue17.py --dry-run
    python3 recalc_post_analysis_issue17.py
"""
import sys
import os
import argparse
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_manager
from formulas import (
    calculate_score, calculate_score_b, calculate_score_c, calculate_score_d,
    calculate_score_e, calculate_score_f, calculate_score_g, calculate_score_h,
    calculate_score_i, calculate_entry_score,
)

SCORE_FNS = {
    "Score":      calculate_score,
    "Score_B":    calculate_score_b,
    "Score_C":    calculate_score_c,
    "Score_D":    calculate_score_d,
    "Score_E":    calculate_score_e,
    "Score_F":    calculate_score_f,
    "Score_G":    calculate_score_g,
    "Score_H":    calculate_score_h,
    "Score_I":    calculate_score_i,
}


def safe_float(v, default=0.0):
    try:
        if v in ("", "nan", "None", None):
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


def build_metrics(row, header):
    def idx(name):
        return header.index(name) if name in header else None
    return {
        "mxv":                safe_float(row[idx("MxV")]) if idx("MxV") is not None else 0,
        "run_up":             safe_float(row[idx("RunUp")]) if idx("RunUp") is not None else 0,
        "atrx":               safe_float(row[idx("ATRX")]) if idx("ATRX") is not None else 0,
        "rsi":                safe_float(row[idx("RSI")]) if idx("RSI") is not None else 0,
        "rel_vol":            safe_float(row[idx("REL_VOL")]) if idx("REL_VOL") is not None else 0,
        "gap":                safe_float(row[idx("Gap")]) if idx("Gap") is not None else 0,
        "typical_price_dist": safe_float(row[idx("TypicalPriceDist")]) if idx("TypicalPriceDist") is not None else 0,
        "change":             safe_float(row[idx("ScanChange%")]) if idx("ScanChange%") is not None else 0,
        "float_pct":          safe_float(row[idx("Float%")]) if idx("Float%") is not None else 0,
        "price_to_high":      safe_float(row[idx("PriceToHigh")]) if idx("PriceToHigh") is not None else 0,
        "price_to_52w_high":  safe_float(row[idx("PriceTo52WHigh")]) if idx("PriceTo52WHigh") is not None else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gc = sheets_manager._get_gc()
    config = sheets_manager._load_config()

    total_updates = 0
    for month_key in config.keys():
        if "post_analysis" not in config.get(month_key, {}):
            continue
        print(f"\n[{month_key}] post_analysis:")
        ws = sheets_manager.get_worksheet("post_analysis", month=month_key, gc=gc)
        vals = ws.get_all_values()
        header = vals[0]

        recalc_idx = header.index("Score_recalc_date") if "Score_recalc_date" in header else None
        if recalc_idx is None:
            print("  ⚠ no Score_recalc_date column — skipping")
            continue

        # Find score column indices
        score_cols = {name: header.index(name) for name in SCORE_FNS.keys() if name in header}
        entry_idx = header.index("EntryScore") if "EntryScore" in header else None

        today_str = datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d %H:%M")
        rows_to_update = []

        for row_num, row in enumerate(vals[1:], start=2):
            recalc_val = row[recalc_idx] if len(row) > recalc_idx else ""
            if recalc_val not in ("", "nan", "None"):
                continue

            metrics = build_metrics(row, header)
            ticker = row[header.index("Ticker")]
            scan_date = row[header.index("ScanDate")]

            changes = []
            for score_name, fn in SCORE_FNS.items():
                if score_name not in score_cols:
                    continue
                col_idx = score_cols[score_name]
                old = safe_float(row[col_idx])
                new = fn(metrics)
                if abs(old - new) >= 0.01:
                    changes.append((col_idx, round(new, 2), f"{score_name}: {old}→{new}"))

            # Update Score_recalc_date regardless
            changes.append((recalc_idx, today_str, f"Score_recalc_date→{today_str}"))

            print(f"  row {row_num} ({ticker} {scan_date}): {len(changes)-1} score changes")
            for _, _, msg in changes[:3]:
                print(f"    {msg}")
            if len(changes) > 4:
                print(f"    ... and {len(changes)-4} more")

            rows_to_update.append((row_num, changes))

        if args.dry_run:
            print(f"\nDRY RUN: would update {len(rows_to_update)} rows in {month_key}")
            total_updates += len(rows_to_update)
            continue

        # Batch update
        import time
        for row_num, changes in rows_to_update:
            for col_idx, new_val, _ in changes:
                ws.update_cell(row_num, col_idx + 1, new_val)
                time.sleep(0.5)  # rate limit
            total_updates += 1
            print(f"  ✅ row {row_num} updated")

    print(f"\n{'='*60}")
    print(f"Total rows {'previewed' if args.dry_run else 'updated'}: {total_updates}")


if __name__ == "__main__":
    main()
