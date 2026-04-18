"""
Score Backtest: compare v1, v2, v3 scoring formulas against MaxDrop%.

Reads post_analysis data and computes three score versions per row,
then measures which one best predicts MaxDrop%.

Usage:
  python score_backtest.py
"""
import pandas as pd
import numpy as np
from gsheets_sync import load_post_analysis_from_sheets


# ═══════════════════════════════════════════════════════════════════════
# Score v1 — KB documented (commit 77e3964, 4-Apr-2026)
#   MxV=30%/cap50, RunUp=20%/cap50, REL_VOL=20%/cap2x,
#   RSI=10%/linear80, ATRX=10%/cap3, Gap=5%/inverse15, VWAP=5%/cap15
# ═══════════════════════════════════════════════════════════════════════
def score_v1(mxv, run_up, rel_vol, rsi, atrx, gap, vwap, change):
    score = 0

    # MxV — 30% — cap 50
    if mxv < 0:
        score += min(abs(mxv) / 50, 1) * 30

    # RunUp — 20% — cap 50%
    if run_up > 0:
        score += min(run_up / 50, 1) * 20

    # REL_VOL — 20% — cap 2x
    score += min(rel_vol / 2, 1) * 20

    # RSI — 10% — linear to 80
    if rsi > 80:
        score += 10
    else:
        score += (rsi / 80) * 10

    # ATRX — 10% — cap 3x
    score += min(atrx / 3, 1) * 10

    # Gap — 5% — INVERSE: small gap = better short
    if gap < 15:
        score += min((15 - gap) / 15, 1) * 5

    # VWAP — 5% — cap 15%
    if vwap > 0:
        score += min(vwap / 15, 1) * 5

    return round(score, 2)


# ═══════════════════════════════════════════════════════════════════════
# Score v2 — current code (commit f3d96ca, 11-Apr-2026)
#   MxV=25%/cap200, RunUp=25%/cap30, ATRX=20%/cap5,
#   RSI=10%/bell60-70, VWAP=10%/cap8, ScanChange=5%/cap60, REL_VOL=5%/cap15x
# ═══════════════════════════════════════════════════════════════════════
def score_v2(mxv, run_up, rel_vol, rsi, atrx, gap, vwap, change):
    score = 0

    # MxV — 25% — cap 200
    if mxv < 0:
        score += min(abs(mxv) / 200, 1) * 25

    # RunUp — 25% — cap 30%
    if run_up > 0:
        score += min(run_up / 30, 1) * 25

    # ATRX — 20% — cap 5x
    score += min(atrx / 5, 1) * 20

    # RSI — 10% — bell curve, sweet spot 60-70
    if rsi < 50:
        score += (rsi / 50) * 5
    elif rsi <= 70:
        score += 5 + ((rsi - 50) / 20) * 5
    else:
        score += max(0, 10 - ((rsi - 70) / 30) * 5)

    # VWAP — 10% — cap 8%
    if vwap > 0:
        score += min(vwap / 8, 1) * 10

    # ScanChange% — 5% — cap 60%
    if change > 0:
        score += min(change / 60, 1) * 5

    # REL_VOL — 5% — cap 15x
    score += min(rel_vol / 15, 1) * 5

    return round(score, 2)


# ═══════════════════════════════════════════════════════════════════════
# Score v3 — proposed (correlation-driven)
#   RunUp=25%/cap30, ATRX=20%/cap5, Gap=15%/inverse15,
#   MxV=15%/cap200, REL_VOL=10%/cap15x, VWAP=10%/cap8, RSI=5%/bell60-70
# ═══════════════════════════════════════════════════════════════════════
def score_v3(mxv, run_up, rel_vol, rsi, atrx, gap, vwap, change):
    score = 0

    # RunUp — 25% — cap 30%
    if run_up > 0:
        score += min(run_up / 30, 1) * 25

    # ATRX — 20% — cap 5x
    score += min(atrx / 5, 1) * 20

    # Gap — 15% — INVERSE: small gap = better short (same logic as v1)
    if gap < 15:
        score += min((15 - gap) / 15, 1) * 15

    # MxV — 15% — cap 200
    if mxv < 0:
        score += min(abs(mxv) / 200, 1) * 15

    # REL_VOL — 10% — cap 15x
    score += min(rel_vol / 15, 1) * 10

    # VWAP — 10% — cap 8%
    if vwap > 0:
        score += min(vwap / 8, 1) * 10

    # RSI — 5% — bell curve (same shape, lower weight)
    if rsi < 50:
        score += (rsi / 50) * 2.5
    elif rsi <= 70:
        score += 2.5 + ((rsi - 50) / 20) * 2.5
    else:
        score += max(0, 5 - ((rsi - 70) / 30) * 2.5)

    return round(score, 2)


def main():
    print("Loading post_analysis...")
    df = load_post_analysis_from_sheets()
    print(f"Loaded {len(df)} rows")

    # ── Prepare numeric columns ──────────────────────────────────────
    metric_cols = ["MxV", "RunUp", "REL_VOL", "RSI", "ATRX", "Gap",
                   "VWAP", "ScanChange%", "MaxDrop%"]
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows without MaxDrop% (can't evaluate)
    valid = df.dropna(subset=["MaxDrop%"]).copy()
    print(f"Rows with MaxDrop%: {len(valid)}")

    # Fill missing metrics with neutral defaults
    valid["MxV"]          = valid["MxV"].fillna(0)
    valid["RunUp"]        = valid["RunUp"].fillna(0)
    valid["REL_VOL"]      = valid["REL_VOL"].fillna(1)
    valid["RSI"]          = valid["RSI"].fillna(50)
    valid["ATRX"]         = valid["ATRX"].fillna(0)
    valid["Gap"]          = valid["Gap"].fillna(0)
    valid["VWAP"]         = valid["VWAP"].fillna(0)
    valid["ScanChange%"]  = valid["ScanChange%"].fillna(0)

    # ── Compute scores ───────────────────────────────────────────────
    for i, row in valid.iterrows():
        m   = row["MxV"]
        ru  = row["RunUp"]
        rv  = row["REL_VOL"]
        rsi = row["RSI"]
        ax  = row["ATRX"]
        g   = row["Gap"]
        vw  = row["VWAP"]
        ch  = row["ScanChange%"]

        valid.at[i, "Score_v1"] = score_v1(m, ru, rv, rsi, ax, g, vw, ch)
        valid.at[i, "Score_v2"] = score_v2(m, ru, rv, rsi, ax, g, vw, ch)
        valid.at[i, "Score_v3"] = score_v3(m, ru, rv, rsi, ax, g, vw, ch)

    # ── Analysis ─────────────────────────────────────────────────────
    drop = valid["MaxDrop%"]
    tp15 = valid.get("TP15_Hit")

    print("\n" + "=" * 70)
    print("SCORE BACKTEST RESULTS")
    print("=" * 70)

    for version in ["Score_v1", "Score_v2", "Score_v3"]:
        s = valid[version]
        r = s.corr(drop)

        # Quartiles
        q25 = s.quantile(0.25)
        q75 = s.quantile(0.75)
        bottom_q = valid[s <= q25]
        top_q    = valid[s >= q75]

        print(f"\n{'─' * 50}")
        print(f"  {version}")
        print(f"{'─' * 50}")
        print(f"  Correlation with MaxDrop%:  r = {r:.3f}")
        print(f"  Score range:  {s.min():.1f} – {s.max():.1f}  (mean {s.mean():.1f})")
        print(f"")
        print(f"  {'Quartile':<12} {'n':>4}  {'Avg MaxDrop%':>14}  {'Avg Score':>10}", end="")

        if tp15 is not None and tp15.notna().any():
            print(f"  {'TP15 hit%':>10}")
        else:
            print()

        for label, subset in [("Bottom 25%", bottom_q), ("Top 25%", top_q),
                               ("All", valid)]:
            avg_drop  = subset["MaxDrop%"].mean()
            avg_score = subset[version].mean()
            line = f"  {label:<12} {len(subset):>4}  {avg_drop:>14.2f}  {avg_score:>10.1f}"

            if tp15 is not None and tp15.notna().any():
                tp15_col = pd.to_numeric(subset.get("TP15_Hit"), errors="coerce")
                tp15_rate = tp15_col.mean() * 100 if tp15_col.notna().any() else 0
                line += f"  {tp15_rate:>9.1f}%"

            print(line)

    # ── Head-to-head: which version wins per row? ────────────────────
    print(f"\n{'─' * 50}")
    print(f"  Head-to-head (which score best predicts per row)")
    print(f"{'─' * 50}")

    # For each row, the "best" score is the one closest to predicting
    # deeper drop = higher score should correlate with more negative MaxDrop
    # So we check: top-quartile avg drop spread (top minus bottom)
    for version in ["Score_v1", "Score_v2", "Score_v3"]:
        s = valid[version]
        q25, q75 = s.quantile(0.25), s.quantile(0.75)
        top_drop = valid[s >= q75]["MaxDrop%"].mean()
        bot_drop = valid[s <= q25]["MaxDrop%"].mean()
        spread = top_drop - bot_drop
        print(f"  {version}:  top-q drop={top_drop:.1f}%  bot-q drop={bot_drop:.1f}%  "
              f"spread={spread:.1f}pp")

    # ── Score distribution comparison ────────────────────────────────
    print(f"\n{'─' * 50}")
    print(f"  Score distributions")
    print(f"{'─' * 50}")
    for version in ["Score_v1", "Score_v2", "Score_v3"]:
        s = valid[version]
        print(f"  {version}:  min={s.min():.1f}  p25={s.quantile(.25):.1f}  "
              f"median={s.median():.1f}  p75={s.quantile(.75):.1f}  max={s.max():.1f}")


if __name__ == "__main__":
    main()
