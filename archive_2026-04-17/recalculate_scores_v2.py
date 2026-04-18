"""
Recalculate all 9 Score variants (Score, Score_B-I) in post_analysis
using the corrected ATRX_calc values and current formulas from auto_scanner.py.

Only recalculates CLEAN and SUSPICIOUS rows (per audit).
BROKEN and NO_DATA rows are left untouched.

Usage:
  python recalculate_scores_v2.py            # dry-run
  python recalculate_scores_v2.py --apply    # write to sheet
"""
import sys
from datetime import datetime

import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets
from auto_scanner import (
    calculate_score,
    calculate_score_i,
    calculate_score_b,
    calculate_score_c,
    calculate_score_d,
    calculate_score_e,
    calculate_score_f,
    calculate_score_g,
    calculate_score_h,
)
from quick_audit import audit_row, classify

SCORE_FUNCS = {
    "Score":   calculate_score,
    "Score_I": calculate_score_i,
    "Score_B": calculate_score_b,
    "Score_C": calculate_score_c,
    "Score_D": calculate_score_d,
    "Score_E": calculate_score_e,
    "Score_F": calculate_score_f,
    "Score_G": calculate_score_g,
    "Score_H": calculate_score_h,
}


def build_metrics(row):
    """Build the metrics dict expected by calculate_score* functions.

    Uses ATRX_calc (verified correct) instead of ATRX.
    Uses the raw metric columns already present in post_analysis.
    """
    def safe(val):
        try:
            v = float(val)
            return v if pd.notna(v) else 0
        except (TypeError, ValueError):
            return 0

    return {
        'mxv':       safe(row.get("MxV")),
        'run_up':    safe(row.get("RunUp")),
        'atrx':      safe(row.get("ATRX_calc")),   # <-- corrected value
        'rsi':       safe(row.get("RSI")),
        'rel_vol':   safe(row.get("REL_VOL")),
        'gap':       safe(row.get("Gap")),
        'vwap_dist': safe(row.get("VWAP")),
        'change':    safe(row.get("ScanChange%")),
    }


def main():
    apply = "--apply" in sys.argv

    print("Loading post_analysis...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("No data found.")
        return
    print(f"Loaded {len(df)} rows")

    # ── Backup ────────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_path = f"post_analysis_backup_recalc_{ts}.csv"
    df.to_csv(backup_path, index=False)
    print(f"Backup saved: {backup_path}")

    # ── Column name check ────────────────────────────────────────────
    required_cols = ["MxV", "RunUp", "ATRX_calc", "RSI", "REL_VOL",
                     "Gap", "VWAP", "ScanChange%"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"\nERROR: missing columns in sheet: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        return
    print(f"All {len(required_cols)} required columns found.")

    # ── Ensure numeric ────────────────────────────────────────────────
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── Audit each row ───────────────────────────────────────────────
    print("\nRunning audit...")
    for i, row in df.iterrows():
        failures = audit_row(row)
        df.at[i, "audit_flag"] = classify(failures)

    audit_counts = df["audit_flag"].value_counts()
    for status in ["CLEAN", "SUSPICIOUS", "BROKEN", "NO_DATA"]:
        print(f"  {status:<12}  {audit_counts.get(status, 0):>4}")

    recalc_mask = df["audit_flag"].isin(["CLEAN", "SUSPICIOUS"])
    skip_mask = ~recalc_mask
    n_recalc = recalc_mask.sum()
    n_skip = skip_mask.sum()
    print(f"\n  Will recalculate:  {n_recalc}")
    print(f"  Will skip:         {n_skip}  (BROKEN + NO_DATA)")

    # ── Input integrity (recalc rows only) ────────────────────────────
    recalc_df = df[recalc_mask]
    print(f"\nInput integrity (recalc rows only, n={n_recalc}):")
    for col in required_cols:
        nonzero = (recalc_df[col] != 0).sum()
        print(f"  {col:<14}  {nonzero:>4}/{n_recalc} rows have data")

    # ── Recalculate ──────────────────────────────────────────────────
    for score_name in SCORE_FUNCS:
        if score_name not in df.columns:
            df[score_name] = 0.0
        df[f"{score_name}_old"] = pd.to_numeric(df[score_name], errors="coerce")
        df[f"{score_name}_new"] = df[f"{score_name}_old"].copy()  # default: keep old

    # Only recalc CLEAN + SUSPICIOUS rows
    for i in df[recalc_mask].index:
        metrics = build_metrics(df.loc[i])
        for score_name, func in SCORE_FUNCS.items():
            df.at[i, f"{score_name}_new"] = func(metrics)

    # ── Compare ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RECALCULATION RESULTS (CLEAN + SUSPICIOUS only)")
    print("=" * 70)

    print(f"\n{'Score':<10} {'Old Mean':>10} {'New Mean':>10} {'Diff':>8} "
          f"{'Old Max':>9} {'New Max':>9} {'Changed':>8}")
    print("-" * 70)

    for score_name in SCORE_FUNCS:
        old = df.loc[recalc_mask, f"{score_name}_old"]
        new = df.loc[recalc_mask, f"{score_name}_new"]
        diff = (new - old).abs()
        changed = (diff > 0.01).sum()

        print(f"{score_name:<10} {old.mean():>10.2f} {new.mean():>10.2f} "
              f"{(new.mean() - old.mean()):>+8.2f} "
              f"{old.max():>9.2f} {new.max():>9.2f} {changed:>8}")

    # ── Top 10 biggest changes (by Score, recalc rows only) ──────────
    df["Score_diff"] = (df[f"Score_new"] - df[f"Score_old"]).abs()
    top10 = df[recalc_mask].nlargest(10, "Score_diff")

    print(f"\nTop 10 biggest Score changes:")
    print(f"{'Ticker':<8} {'ScanDate':<12} {'Flag':<6} {'Old':>8} {'New':>8} {'Diff':>8} "
          f"{'ATRX_calc':>10}")

    for _, r in top10.iterrows():
        print(f"{r.get('Ticker','?'):<8} {r.get('ScanDate','?'):<12} "
              f"{r.get('audit_flag','?'):<6} "
              f"{r['Score_old']:>8.2f} {r['Score_new']:>8.2f} "
              f"{r['Score_diff']:>+8.2f} "
              f"{r.get('ATRX_calc', 0):>10.2f}")

    # ── Apply or dry-run ─────────────────────────────────────────────
    if not apply:
        print(f"\n*** DRY RUN — no changes written. Run with --apply to execute. ***")
        return

    # Write new values into the actual columns (for recalc rows)
    for score_name in SCORE_FUNCS:
        df[score_name] = df[f"{score_name}_new"]

    # Add recalc timestamp (only for recalculated rows)
    recalc_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    df.loc[recalc_mask, "Score_recalc_date"] = recalc_ts

    # Drop temp columns before saving
    drop_cols = [c for c in df.columns if c.endswith("_old") or c.endswith("_new")
                 or c == "Score_diff"]
    df = df.drop(columns=drop_cols)

    print(f"\nSaving to sheets...")
    ok = save_post_analysis_to_sheets(df)
    if ok:
        print(f"Done. {n_recalc} rows recalculated, {n_skip} skipped.")
    else:
        print("ERROR: save failed")


if __name__ == "__main__":
    main()
