"""
One-time fix: copy ATRX_calc → ATRX for all rows in post_analysis.

ATRX_calc is computed by post_analysis_collector using stored raw inputs
(High_today_raw, Low_today_raw, ATR14_raw) and is verified correct.

ATRX was written by auto_scanner during live scanning and is unreliable
due to yfinance returning bad intraday data (e.g. BATL: ATRX=70.36
instead of correct 0.32).

Usage:
  python fix_atrx.py            # dry-run — shows what would change
  python fix_atrx.py --apply    # actually writes to the sheet
"""
import sys
from datetime import datetime

import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets


def main():
    apply = "--apply" in sys.argv

    print("Loading post_analysis from sheets...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("No data found.")
        return

    print(f"Loaded {len(df)} rows")

    # ── Backup to CSV ─────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_path = f"post_analysis_backup_{ts}.csv"
    df.to_csv(backup_path, index=False)
    print(f"Backup saved: {backup_path}")

    # ── Validate columns ─────────────────────────────────────────────────
    if "ATRX_calc" not in df.columns:
        print("ERROR: ATRX_calc column not found")
        return
    if "ATRX" not in df.columns:
        print("ERROR: ATRX column not found")
        return

    # ── Analyse ──────────────────────────────────────────────────────────
    atrx_calc = pd.to_numeric(df["ATRX_calc"], errors="coerce")
    atrx_orig = pd.to_numeric(df["ATRX"], errors="coerce")

    has_calc = atrx_calc.notna()
    total_with_calc = has_calc.sum()
    print(f"Rows with valid ATRX_calc: {total_with_calc}")

    print(f"\nBefore fix:")
    print(f"  ATRX      — mean: {atrx_orig.mean():.2f}, max: {atrx_orig.max():.2f}")
    print(f"  ATRX_calc — mean: {atrx_calc.mean():.2f}, max: {atrx_calc.max():.2f}")

    # Worst offenders
    diff = (atrx_orig - atrx_calc).abs()
    worst = diff[has_calc].nlargest(10)
    if not worst.empty:
        print(f"\nTop {len(worst)} biggest differences (ATRX vs ATRX_calc):")
        for idx in worst.index:
            row = df.loc[idx]
            print(f"  {row.get('Ticker','?'):>6s}  {row.get('ScanDate','?')}  "
                  f"ATRX={atrx_orig[idx]:>8.2f}  ATRX_calc={atrx_calc[idx]:>6.2f}  "
                  f"diff={diff[idx]:>8.2f}")

    # Count actual changes
    changed = has_calc & (atrx_orig != atrx_calc)
    n_changed = changed.sum()
    print(f"\nRows to update: {n_changed}")

    if n_changed == 0:
        print("Nothing to fix — all values already match.")
        return

    # ── Apply or dry-run ─────────────────────────────────────────────────
    if not apply:
        print("\n*** DRY RUN — no changes written. Run with --apply to execute. ***")
        return

    df.loc[has_calc, "ATRX"] = atrx_calc[has_calc].round(2)

    atrx_after = pd.to_numeric(df["ATRX"], errors="coerce")
    print(f"\nAfter fix:")
    print(f"  ATRX — mean: {atrx_after.mean():.2f}, max: {atrx_after.max():.2f}")

    print("\nSaving to sheets...")
    ok = save_post_analysis_to_sheets(df)
    if ok:
        print("Done.")
    else:
        print("ERROR: save failed")


if __name__ == "__main__":
    main()
