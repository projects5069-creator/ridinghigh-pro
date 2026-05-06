#!/usr/bin/env python3
"""
deep_eda_v2.py
══════════════════════════════════════════════════════════════════
Answer the 4 critical questions:

1. What is the NET move of low-Score-tier stocks at D5_Close vs ScanPrice?
   (If significantly negative → short works. If positive → LONG opportunity.)
2. What is the NET move of high-Score-tier stocks?
3. Is there a subset of "pure shorts" — stocks that NEVER hit SL?
4. Is there a subset of "pure longs" — stocks that DROPPED but BOUNCED above ScanPrice?

Outputs:
  ~/RidingHighPro/eda_v2_findings.txt
  ~/RidingHighPro/eda_v2_plots/  (3 PNGs)

══════════════════════════════════════════════════════════════════
Run from: ~/RidingHighPro/
  python3 deep_eda_v2.py
"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

OUT_TXT = os.path.expanduser("~/RidingHighPro/eda_v2_findings.txt")
OUT_DIR = os.path.expanduser("~/RidingHighPro/eda_v2_plots")
os.makedirs(OUT_DIR, exist_ok=True)

LINES = []
def log(msg=""):
    print(msg)
    LINES.append(msg)

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
def main():
    log("=" * 72)
    log("DEEP EDA #2 — LONG vs SHORT — net moves analysis")
    log(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 72)

    df = load_data()
    log(f"Total rows: {len(df)}")

    NUM = ['Score', 'Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV', 'RunUp',
           'MarketCap', 'ScanPrice',
           'MaxDrop%',
           'D0_High', 'D0_Low', 'D0_Close',
           'D1_Open', 'D1_High', 'D1_Low', 'D1_Close',
           'D2_High', 'D2_Low', 'D2_Close',
           'D3_High', 'D3_Low', 'D3_Close',
           'D4_High', 'D4_Low', 'D4_Close',
           'D5_High', 'D5_Low', 'D5_Close',
           'IntraHigh', 'IntraLow']
    for c in NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # ── Compute derived columns ──────────────────────────────────────────
    if 'ScanPrice' in df.columns and 'D5_Close' in df.columns:
        df['net_d5_pct'] = (df['D5_Close'] - df['ScanPrice']) / df['ScanPrice'] * 100
    if 'ScanPrice' in df.columns and 'D1_Close' in df.columns:
        df['net_d1_pct'] = (df['D1_Close'] - df['ScanPrice']) / df['ScanPrice'] * 100

    high_cols = [c for c in ['IntraHigh', 'D0_High', 'D1_High', 'D2_High',
                              'D3_High', 'D4_High', 'D5_High'] if c in df.columns]
    if high_cols and 'ScanPrice' in df.columns:
        df['MaxRise%'] = (df[high_cols].max(axis=1) - df['ScanPrice']) / df['ScanPrice'] * 100

    log(f"\nCoverage:")
    for col in ['MaxDrop%', 'MaxRise%', 'net_d5_pct', 'net_d1_pct']:
        if col in df.columns:
            log(f"  {col}: {df[col].notna().sum()} / {len(df)} non-null")

    # ── DEDUPLICATE BY TICKER (keep FIRST scan only — avoids leakage) ────
    log("\n" + "=" * 72)
    log("DEDUPLICATION — keep first scan per ticker")
    log("=" * 72)
    if 'Ticker' in df.columns and 'ScanDate' in df.columns:
        df_sorted = df.sort_values(['Ticker', 'ScanDate'])
        df_dedup = df_sorted.drop_duplicates('Ticker', keep='first').copy()
        log(f"Before dedup: {len(df)} rows")
        log(f"After dedup:  {len(df_dedup)} rows ({df_dedup['Ticker'].nunique()} unique tickers)")
    else:
        df_dedup = df.copy()
        log("No Ticker col — skipping dedup")

    # ════════════════════════════════════════════════════════════════════
    # QUESTION 1 & 2: Net move by Score tier (DEDUP)
    # ════════════════════════════════════════════════════════════════════
    log("\n" + "=" * 72)
    log("Q1+Q2 — NET MOVE BY SCORE TIER (deduplicated, first scan per ticker)")
    log("=" * 72)
    if 'Score' in df_dedup.columns and 'net_d5_pct' in df_dedup.columns:
        df_v = df_dedup.dropna(subset=['Score', 'net_d5_pct']).copy()
        log(f"\nN with both Score and D5_Close: {len(df_v)}")

        for low, high, label in [(0, 40, "LOW    "), (40, 60, "MID-LO "),
                                  (60, 80, "MID-HI "), (80, 101, "HIGH   ")]:
            t = df_v[(df_v['Score'] >= low) & (df_v['Score'] < high)]
            if len(t) == 0: continue
            log(f"\n  Score {label} [{low}-{high}]: n={len(t)}")
            log(f"    NET move @ D5_Close:  mean={t['net_d5_pct'].mean():+6.2f}%  median={t['net_d5_pct'].median():+6.2f}%")
            if 'net_d1_pct' in t.columns:
                t1 = t.dropna(subset=['net_d1_pct'])
                if len(t1) > 0:
                    log(f"    NET move @ D1_Close:  mean={t1['net_d1_pct'].mean():+6.2f}%  median={t1['net_d1_pct'].median():+6.2f}%")
            log(f"    MaxDrop%:  mean={t['MaxDrop%'].mean():+6.2f}%  median={t['MaxDrop%'].median():+6.2f}%")
            if 'MaxRise%' in t.columns:
                log(f"    MaxRise%:  mean={t['MaxRise%'].mean():+6.2f}%  median={t['MaxRise%'].median():+6.2f}%")

            # What % closed below ScanPrice at D5?
            n_neg = (t['net_d5_pct'] < 0).sum()
            n_pos = (t['net_d5_pct'] > 0).sum()
            log(f"    D5 < ScanPrice (loss for long, win for short): {n_neg}/{len(t)} = {n_neg/len(t)*100:.0f}%")
            log(f"    D5 > ScanPrice (win for long, loss for short):  {n_pos}/{len(t)} = {n_pos/len(t)*100:.0f}%")

    # ════════════════════════════════════════════════════════════════════
    # QUESTION 3: Pure shorts — stocks that NEVER bounced 7%+
    # ════════════════════════════════════════════════════════════════════
    log("\n" + "=" * 72)
    log("Q3 — PURE SHORTS (MaxRise% < 7% — no SL hit ever)")
    log("=" * 72)
    if 'MaxRise%' in df_dedup.columns and 'MaxDrop%' in df_dedup.columns:
        v = df_dedup.dropna(subset=['MaxRise%', 'MaxDrop%']).copy()
        pure_shorts = v[v['MaxRise%'] < 7]
        log(f"\nTotal: {len(v)}")
        log(f"Pure shorts (MaxRise% < 7%): {len(pure_shorts)} ({len(pure_shorts)/len(v)*100:.0f}%)")
        if len(pure_shorts) > 0:
            log(f"  MaxDrop%:        mean={pure_shorts['MaxDrop%'].mean():+6.2f}%, median={pure_shorts['MaxDrop%'].median():+6.2f}%")
            if 'net_d5_pct' in pure_shorts.columns:
                log(f"  net_d5_pct:      mean={pure_shorts['net_d5_pct'].mean():+6.2f}%, median={pure_shorts['net_d5_pct'].median():+6.2f}%")
            log(f"\n  Profile of pure shorts (means):")
            for col in ['Score', 'Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV', 'RunUp', 'MarketCap']:
                if col in pure_shorts.columns:
                    p = pure_shorts[col].mean()
                    o = v[v['MaxRise%'] >= 7][col].mean() if (v['MaxRise%'] >= 7).any() else float('nan')
                    diff = p - o if not pd.isna(o) else 0
                    flag = "⭐" if abs(diff) > abs(o) * 0.3 else "  "
                    log(f"    {flag} {col:>10}: pure_shorts={p:>9.2f}  others={o:>9.2f}  diff={diff:+8.2f}")

    # ════════════════════════════════════════════════════════════════════
    # QUESTION 4: Pure longs — dropped but bounced positively
    # ════════════════════════════════════════════════════════════════════
    log("\n" + "=" * 72)
    log("Q4 — PURE LONGS (D5_Close > ScanPrice — net positive after pump)")
    log("=" * 72)
    if 'net_d5_pct' in df_dedup.columns:
        v = df_dedup.dropna(subset=['net_d5_pct']).copy()
        pure_longs = v[v['net_d5_pct'] > 5]   # net +5% or more by D5
        big_longs = v[v['net_d5_pct'] > 10]   # net +10% or more
        log(f"\nTotal: {len(v)}")
        log(f"Net positive >5%  by D5: {len(pure_longs)} ({len(pure_longs)/len(v)*100:.0f}%)")
        log(f"Net positive >10% by D5: {len(big_longs)}  ({len(big_longs)/len(v)*100:.0f}%)")
        if len(pure_longs) > 0:
            log(f"\n  Profile of net-positive (>5%) (means):")
            others = v[v['net_d5_pct'] <= 5]
            for col in ['Score', 'Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV', 'RunUp', 'MarketCap']:
                if col in pure_longs.columns:
                    p = pure_longs[col].mean()
                    o = others[col].mean() if len(others) > 0 else float('nan')
                    diff = p - o if not pd.isna(o) else 0
                    flag = "⭐" if abs(diff) > abs(o) * 0.3 else "  "
                    log(f"    {flag} {col:>10}: long={p:>9.2f}  others={o:>9.2f}  diff={diff:+8.2f}")

    # ════════════════════════════════════════════════════════════════════
    # 5: Two-by-two matrix — drop AND rise behavior
    # ════════════════════════════════════════════════════════════════════
    log("\n" + "=" * 72)
    log("Q5 — 2x2 MATRIX: dropped 10%+ × rose 7%+")
    log("=" * 72)
    if 'MaxDrop%' in df_dedup.columns and 'MaxRise%' in df_dedup.columns:
        v = df_dedup.dropna(subset=['MaxDrop%', 'MaxRise%']).copy()
        v['_dropped'] = v['MaxDrop%'] <= -10
        v['_rose'] = v['MaxRise%'] >= 7

        log(f"\n                        MaxRise<7%   MaxRise>=7%")
        for dropped in [True, False]:
            d_label = "MaxDrop>=10% " if dropped else "MaxDrop<10%  "
            sub = v[v['_dropped'] == dropped]
            n_no_rise = (sub['_rose'] == False).sum()
            n_rise = (sub['_rose'] == True).sum()
            log(f"    {d_label}            {n_no_rise:>5}      {n_rise:>5}")

        log(f"\nGroup analysis (net_d5 mean):")
        for dropped, rose, label in [(True, False, "DROPPED ONLY (pure short ⭐)"),
                                       (True, True, "DROPPED + ROSE (whipsaw)"),
                                       (False, True, "ROSE ONLY (pure long ⭐)"),
                                       (False, False, "neither (range-bound)")]:
            sub = v[(v['_dropped'] == dropped) & (v['_rose'] == rose)]
            if len(sub) == 0:
                log(f"  {label:<30}: n=0")
                continue
            net_mean = sub['net_d5_pct'].mean() if 'net_d5_pct' in sub.columns else float('nan')
            log(f"  {label:<30}: n={len(sub):>3}, net_d5_mean={net_mean:+.2f}%")

    # ════════════════════════════════════════════════════════════════════
    # PLOTS
    # ════════════════════════════════════════════════════════════════════
    log("\n" + "=" * 72)
    log("PLOTS")
    log("=" * 72)
    try:
        if 'net_d5_pct' in df_dedup.columns:
            v = df_dedup.dropna(subset=['net_d5_pct'])

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.hist(v['net_d5_pct'], bins=50, edgecolor='black')
            ax.axvline(0, color='red', linestyle='--', label='ScanPrice (entry)')
            ax.axvline(-10, color='green', linestyle='--', label='Short TP')
            ax.axvline(7, color='orange', linestyle='--', label='Short SL / Long TP')
            ax.set_xlabel('Net move at D5_Close (% from ScanPrice)')
            ax.set_ylabel('Count')
            ax.set_title(f'Distribution of net moves @ D5_Close (n={len(v)} unique tickers)')
            ax.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(OUT_DIR, 'net_d5_distribution.png'), dpi=80)
            plt.close()
            log(f"  Saved: net_d5_distribution.png")

            # Per-tier
            if 'Score' in v.columns:
                fig, axes = plt.subplots(2, 2, figsize=(14, 10))
                for ax, (low, high) in zip(axes.flat, [(0,40),(40,60),(60,80),(80,101)]):
                    t = v[(v['Score'] >= low) & (v['Score'] < high)]
                    if len(t) == 0:
                        ax.set_visible(False); continue
                    ax.hist(t['net_d5_pct'], bins=20, edgecolor='black', alpha=0.7)
                    ax.axvline(0, color='red', linestyle='--')
                    ax.axvline(t['net_d5_pct'].mean(), color='blue', linestyle='-',
                               label=f'mean={t["net_d5_pct"].mean():.1f}%')
                    ax.set_title(f'Score [{low}-{high}], n={len(t)}')
                    ax.set_xlabel('net_d5_pct')
                    ax.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(OUT_DIR, 'net_d5_by_tier.png'), dpi=80)
                plt.close()
                log(f"  Saved: net_d5_by_tier.png")

            # 2x2 quadrants visualization
            if 'MaxDrop%' in df_dedup.columns and 'MaxRise%' in df_dedup.columns:
                v2 = df_dedup.dropna(subset=['MaxDrop%', 'MaxRise%'])
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.scatter(v2['MaxRise%'], v2['MaxDrop%'], alpha=0.5)
                ax.axhline(-10, color='green', linestyle='--', label='Short TP line')
                ax.axvline(7, color='orange', linestyle='--', label='Short SL line')
                ax.set_xlabel('MaxRise% (highest point above ScanPrice)')
                ax.set_ylabel('MaxDrop% (lowest point below ScanPrice)')
                ax.set_title(f'Drop vs Rise — every point is one stock (n={len(v2)})')
                ax.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(OUT_DIR, 'drop_vs_rise_scatter.png'), dpi=80)
                plt.close()
                log(f"  Saved: drop_vs_rise_scatter.png")
    except Exception as e:
        log(f"  Plot error: {e}")

    # Save findings
    with open(OUT_TXT, 'w') as f:
        f.write('\n'.join(LINES))
    log(f"\n\n✅ Saved findings to: {OUT_TXT}")
    log(f"✅ Plots in: {OUT_DIR}/")

if __name__ == "__main__":
    main()
