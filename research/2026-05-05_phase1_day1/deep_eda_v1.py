#!/usr/bin/env python3
"""
deep_eda_v1.py
══════════════════════════════════════════════════════════════════
Deep EDA on post_analysis BEFORE building any score.

Goals:
  1. Understand WHY low-Score tier had high TP rate
  2. Detect ticker leakage (repeat-stock bias)
  3. Verify MaxDrop% / MaxRise% reference points
  4. Find bimodal patterns hidden by mean-AUC analysis
  5. Identify the actual sweet spot for each metric

Output: ~/RidingHighPro/eda_findings.txt + 6 plots
══════════════════════════════════════════════════════════════════
Run from: ~/RidingHighPro/
  python3 deep_eda_v1.py
"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

OUT_TXT = os.path.expanduser("~/RidingHighPro/eda_findings.txt")
OUT_DIR = os.path.expanduser("~/RidingHighPro/eda_plots")
os.makedirs(OUT_DIR, exist_ok=True)

LINES = []
def log(msg=""):
    print(msg)
    LINES.append(msg)

# ─────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────
def load_data():
    import sheets_manager
    gc = sheets_manager._get_gc()
    config = json.load(open(os.path.expanduser("~/RidingHighPro/sheets_config.json")))
    months = sorted(config.keys())
    all_dfs = []
    for month in months:
        try:
            ws = sheets_manager.get_worksheet("post_analysis", month=month, gc=gc)
            data = ws.get_all_values()
            if len(data) < 2: continue
            df = pd.DataFrame(data[1:], columns=data[0])
            df['_month'] = month
            all_dfs.append(df)
            log(f"  {month}: {len(df)} rows")
        except Exception as e:
            log(f"  {month}: ERROR {e}")
    return pd.concat(all_dfs, ignore_index=True)

# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main():
    log("=" * 70)
    log("DEEP EDA — post_analysis")
    log(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 70)

    df = load_data()
    log(f"Total rows: {len(df)}")

    # Coerce numeric
    NUM_COLS = ['Score', 'Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV', 'RunUp',
                'VWAP', 'Volume', 'MarketCap', 'ScanPrice',
                'MaxDrop%', 'D0_High', 'D1_High', 'D2_High', 'D3_High', 'D4_High',
                'D5_High', 'D0_Drop%', 'IntraHigh',
                'D1_Open', 'D1_Close', 'D5_Close',
                'TP10_Hit', 'SL_Hit_D5', 'SL_Hit_D0']
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # ─── 1. Verify MaxDrop% reference point ───────────────────────────────
    log("\n" + "=" * 70)
    log("1. MaxDrop% / MaxRise% REFERENCE POINT VERIFICATION")
    log("=" * 70)
    if all(c in df.columns for c in ['ScanPrice', 'D1_Close', 'MaxDrop%']):
        sample = df.dropna(subset=['ScanPrice', 'D1_Close', 'MaxDrop%']).head(20)
        log("\nSample 20 rows — checking if MaxDrop% matches (low - ScanPrice)/ScanPrice:")
        log(f"{'Ticker':<8} {'ScanPx':>8} {'D1_Cls':>8} {'MaxDrop%':>10} {'expected_min':>12}")
        for _, r in sample.iterrows():
            implied = (r['D1_Close'] - r['ScanPrice']) / r['ScanPrice'] * 100
            log(f"{str(r.get('Ticker','?')):<8} {r['ScanPrice']:>8.2f} {r['D1_Close']:>8.2f} "
                f"{r['MaxDrop%']:>10.2f} {implied:>12.2f}")

    # Compute MaxRise% from highs
    high_cols = [c for c in ['IntraHigh', 'D0_High', 'D1_High', 'D2_High', 'D3_High',
                              'D4_High', 'D5_High'] if c in df.columns]
    log(f"\nHigh columns available: {high_cols}")
    if high_cols and 'ScanPrice' in df.columns:
        df['_MaxHigh'] = df[high_cols].max(axis=1)
        df['MaxRise%_calc'] = (df['_MaxHigh'] - df['ScanPrice']) / df['ScanPrice'] * 100
        log(f"MaxRise%_calc: median={df['MaxRise%_calc'].median():.2f}, "
            f"mean={df['MaxRise%_calc'].mean():.2f}")

    # ─── 2. TICKER LEAKAGE — same stock multiple times? ──────────────────
    log("\n" + "=" * 70)
    log("2. TICKER LEAKAGE — repeat stocks in dataset")
    log("=" * 70)
    if 'Ticker' in df.columns:
        ticker_counts = df['Ticker'].value_counts()
        repeats = ticker_counts[ticker_counts > 1]
        log(f"Unique tickers: {df['Ticker'].nunique()}")
        log(f"Tickers appearing >1 time: {len(repeats)}")
        log(f"Top 10 most repeated:")
        for t, c in repeats.head(10).items():
            sub = df[df['Ticker'] == t]
            tp_rate = (sub['MaxDrop%'] <= -10).mean() * 100 if 'MaxDrop%' in sub.columns else 0
            avg_score = sub['Score'].mean() if 'Score' in sub.columns else 0
            log(f"  {t:<8} appeared {c}x | avg Score={avg_score:.1f} | TP10 rate={tp_rate:.0f}%")

    # ─── 3. THE LOW-SCORE MYSTERY ────────────────────────────────────────
    log("\n" + "=" * 70)
    log("3. WHY DID LOW-SCORE TIER HAVE HIGH TP RATE?")
    log("=" * 70)
    if 'Score' in df.columns and 'MaxDrop%' in df.columns:
        df_valid = df.dropna(subset=['Score', 'MaxDrop%']).copy()
        for low, high in [(0, 40), (40, 60), (60, 80), (80, 100)]:
            tier = df_valid[(df_valid['Score'] >= low) & (df_valid['Score'] < high)]
            if len(tier) == 0: continue
            tp = (tier['MaxDrop%'] <= -10).mean() * 100
            log(f"\n  Score [{low}-{high}]: n={len(tier)}, TP10={tp:.1f}%")
            log(f"    MaxDrop% mean={tier['MaxDrop%'].mean():.2f}, median={tier['MaxDrop%'].median():.2f}")
            for col in ['Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV']:
                if col in tier.columns:
                    log(f"    {col:>10} mean={tier[col].mean():>10.2f}, median={tier[col].median():>10.2f}")

    # ─── 4. BIMODAL DETECTION — outcomes split by metric quartiles ───────
    log("\n" + "=" * 70)
    log("4. METRIC QUARTILES vs OUTCOMES (bimodal detection)")
    log("=" * 70)
    if 'MaxDrop%' in df.columns:
        df_valid = df.dropna(subset=['MaxDrop%']).copy()
        df_valid['hit_tp10'] = (df_valid['MaxDrop%'] <= -10).astype(int)

        for metric in ['Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV', 'RunUp',
                       'MarketCap', 'ScanPrice']:
            if metric not in df_valid.columns: continue
            mvals = df_valid[metric].dropna()
            if len(mvals) < 20: continue
            try:
                q = pd.qcut(mvals, q=4, duplicates='drop')
                grouped = df_valid.loc[mvals.index].groupby(q, observed=True)['hit_tp10']
                rates = grouped.mean() * 100
                counts = grouped.count()
                log(f"\n  {metric}:")
                for bucket, rate in rates.items():
                    n = counts[bucket]
                    log(f"    {str(bucket):<25} TP10={rate:>5.1f}%  (n={n})")
            except Exception as e:
                log(f"    {metric}: error {e}")

    # ─── 5. SL vs TP timing — both hit, what's the order? ────────────────
    log("\n" + "=" * 70)
    log("5. WHEN BOTH TP10 AND SL7 HIT — which came first?")
    log("=" * 70)
    if all(c in df.columns for c in ['SL_Hit_D0', 'SL_Hit_D5', 'TP10_Hit']):
        log(f"SL_Hit_D0 distribution: {df['SL_Hit_D0'].value_counts().to_dict()}")
        log(f"SL_Hit_D5 distribution: {df['SL_Hit_D5'].value_counts().to_dict()}")
        log(f"TP10_Hit distribution: {df['TP10_Hit'].value_counts().to_dict()}")

        # Cross-tab
        if 'TP10_Hit' in df.columns and 'SL_Hit_D5' in df.columns:
            df['_tp'] = (df['TP10_Hit'] == 1) | (df['TP10_Hit'] == 'TRUE') | (df['TP10_Hit'] == True)
            df['_sl'] = (df['SL_Hit_D5'] == 1) | (df['SL_Hit_D5'] == 'TRUE') | (df['SL_Hit_D5'] == True)
            log(f"\nCrosstab TP10 × SL_D5:")
            log(str(pd.crosstab(df['_tp'], df['_sl'], margins=True)))

    # ─── 6. PLOTS ────────────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("6. GENERATING PLOTS")
    log("=" * 70)
    try:
        df_v = df.dropna(subset=['MaxDrop%']).copy()
        df_v['hit_tp10'] = (df_v['MaxDrop%'] <= -10).astype(int)

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        for ax, metric in zip(axes.flat,
                              ['Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV']):
            if metric not in df_v.columns:
                ax.set_visible(False); continue
            tp = df_v[df_v['hit_tp10'] == 1][metric].dropna()
            no = df_v[df_v['hit_tp10'] == 0][metric].dropna()
            if len(tp) == 0 or len(no) == 0:
                ax.set_visible(False); continue
            bins = 20
            ax.hist(no, bins=bins, alpha=0.5, label=f'No TP (n={len(no)})', color='red')
            ax.hist(tp, bins=bins, alpha=0.5, label=f'TP10 (n={len(tp)})', color='green')
            ax.set_title(metric)
            ax.legend(fontsize=8)
        plt.tight_layout()
        plot_path = os.path.join(OUT_DIR, "metric_distributions.png")
        plt.savefig(plot_path, dpi=80)
        plt.close()
        log(f"  Saved: {plot_path}")
    except Exception as e:
        log(f"  Plot error: {e}")

    # ─── 7. RAW DATA OF "low-score winners" ──────────────────────────────
    log("\n" + "=" * 70)
    log("7. RAW DUMP — low-Score winners (Score<40 AND MaxDrop% <= -10)")
    log("=" * 70)
    if all(c in df.columns for c in ['Score', 'MaxDrop%']):
        df_v = df.dropna(subset=['Score', 'MaxDrop%'])
        winners_low = df_v[(df_v['Score'] < 40) & (df_v['MaxDrop%'] <= -10)]
        log(f"Found {len(winners_low)} low-score winners")
        cols_show = [c for c in ['Ticker', 'ScanDate', 'Score', 'Float%', 'Gap',
                                  'ATRX', 'REL_VOL', 'RSI', 'MxV', 'MarketCap',
                                  'MaxDrop%'] if c in winners_low.columns]
        log(winners_low[cols_show].to_string(index=False))

    # Save
    with open(OUT_TXT, 'w') as f:
        f.write('\n'.join(LINES))
    log(f"\n\n✅ Saved findings to: {OUT_TXT}")
    log(f"✅ Plots in: {OUT_DIR}/")

if __name__ == "__main__":
    main()
