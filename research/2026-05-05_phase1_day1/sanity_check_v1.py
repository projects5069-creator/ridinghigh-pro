#!/usr/bin/env python3
"""
sanity_check_v1.py
══════════════════════════════════════════════════════════════════
Verify the EDA v2 findings by showing RAW DATA.
No summaries. No averaging. Just the actual numbers.

Outputs to stdout — copy back to Claude.
══════════════════════════════════════════════════════════════════
Run: cd ~/RidingHighPro && python3 sanity_check_v1.py
"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
import numpy as np

def main():
    import sheets_manager
    gc = sheets_manager._get_gc()
    config = json.load(open(os.path.expanduser("~/RidingHighPro/sheets_config.json")))

    all_dfs = []
    for month in sorted(config.keys()):
        try:
            ws = sheets_manager.get_worksheet("post_analysis", month=month, gc=gc)
            data = ws.get_all_values()
            if len(data) < 2: continue
            df = pd.DataFrame(data[1:], columns=data[0])
            df['_month'] = month
            all_dfs.append(df)
        except Exception:
            pass
    df = pd.concat(all_dfs, ignore_index=True)

    NUM = ['Score', 'Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI', 'MxV', 'RunUp',
           'MarketCap', 'ScanPrice',
           'D5_Close', 'D1_Close',
           'MaxDrop%',
           'IntraHigh', 'D0_High', 'D1_High', 'D2_High', 'D3_High', 'D4_High', 'D5_High']
    for c in NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df['net_d5_pct'] = (df['D5_Close'] - df['ScanPrice']) / df['ScanPrice'] * 100
    high_cols = [c for c in ['IntraHigh', 'D0_High', 'D1_High', 'D2_High',
                              'D3_High', 'D4_High', 'D5_High'] if c in df.columns]
    df['MaxRise%'] = (df[high_cols].max(axis=1) - df['ScanPrice']) / df['ScanPrice'] * 100

    # Dedup
    df_dedup = df.sort_values(['Ticker', 'ScanDate']).drop_duplicates('Ticker', keep='first')

    print("=" * 75)
    print("SANITY CHECK")
    print("=" * 75)
    print(f"Total rows: {len(df)}")
    print(f"After dedup: {len(df_dedup)}")
    print(f"With both D5_Close + Highs: {df_dedup.dropna(subset=['net_d5_pct', 'MaxRise%']).shape[0]}")

    v = df_dedup.dropna(subset=['net_d5_pct', 'MaxRise%']).copy()
    v['_dropped'] = v['MaxDrop%'] <= -10
    v['_rose'] = v['MaxRise%'] >= 7

    # ─────────────────────────────────────────────────────────────────
    # 1. PURE LONGS — show raw rows, not summary
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("PURE LONGS — every single row (sorted by net_d5_pct desc)")
    print("=" * 75)
    pure_longs = v[(v['_dropped'] == False) & (v['_rose'] == True)].copy()
    pure_longs = pure_longs.sort_values('net_d5_pct', ascending=False)
    cols = ['Ticker', 'ScanDate', 'ScanPrice', 'D5_Close', 'net_d5_pct',
            'MaxDrop%', 'MaxRise%', 'Score', 'RSI', 'MarketCap']
    cols = [c for c in cols if c in pure_longs.columns]

    print(f"\nN = {len(pure_longs)}")
    if len(pure_longs) > 0:
        print(f"net_d5_pct: mean={pure_longs['net_d5_pct'].mean():.1f}%, "
              f"median={pure_longs['net_d5_pct'].median():.1f}%, "
              f"min={pure_longs['net_d5_pct'].min():.1f}%, "
              f"max={pure_longs['net_d5_pct'].max():.1f}%")
        print(f"\nQuantiles: q10={pure_longs['net_d5_pct'].quantile(0.10):.1f}%, "
              f"q25={pure_longs['net_d5_pct'].quantile(0.25):.1f}%, "
              f"q75={pure_longs['net_d5_pct'].quantile(0.75):.1f}%, "
              f"q90={pure_longs['net_d5_pct'].quantile(0.90):.1f}%")
        print(f"\nAll rows:")
        print(pure_longs[cols].to_string(index=False))

    # ─────────────────────────────────────────────────────────────────
    # 2. PURE SHORTS — show raw rows
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("PURE SHORTS — every single row (sorted by net_d5_pct asc)")
    print("=" * 75)
    pure_shorts = v[(v['_dropped'] == True) & (v['_rose'] == False)].copy()
    pure_shorts = pure_shorts.sort_values('net_d5_pct', ascending=True)
    print(f"\nN = {len(pure_shorts)}")
    if len(pure_shorts) > 0:
        print(f"net_d5_pct: mean={pure_shorts['net_d5_pct'].mean():.1f}%, "
              f"median={pure_shorts['net_d5_pct'].median():.1f}%, "
              f"min={pure_shorts['net_d5_pct'].min():.1f}%, "
              f"max={pure_shorts['net_d5_pct'].max():.1f}%")
        print(f"\nAll rows:")
        print(pure_shorts[cols].to_string(index=False))

    # ─────────────────────────────────────────────────────────────────
    # 3. WHIPSAW — sorted by net_d5
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("WHIPSAW — dropped 10%+ AND rose 7%+ (the messy majority)")
    print("=" * 75)
    whipsaw = v[(v['_dropped'] == True) & (v['_rose'] == True)].copy()
    whipsaw = whipsaw.sort_values('net_d5_pct')
    print(f"\nN = {len(whipsaw)}")
    if len(whipsaw) > 0:
        print(f"net_d5_pct: mean={whipsaw['net_d5_pct'].mean():.1f}%, "
              f"median={whipsaw['net_d5_pct'].median():.1f}%, "
              f"min={whipsaw['net_d5_pct'].min():.1f}%, "
              f"max={whipsaw['net_d5_pct'].max():.1f}%")
        print(f"\nNet outcome:")
        print(f"  D5 < -5% (short net winner): {(whipsaw['net_d5_pct'] < -5).sum()}")
        print(f"  D5 between -5% and +5% (flat): {((whipsaw['net_d5_pct']>=-5)&(whipsaw['net_d5_pct']<=5)).sum()}")
        print(f"  D5 > +5% (long net winner): {(whipsaw['net_d5_pct'] > 5).sum()}")

    # ─────────────────────────────────────────────────────────────────
    # 4. ScanPrice distribution — penny stock check
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("PRICE DISTRIBUTION — penny stock check")
    print("=" * 75)
    print(f"ScanPrice stats:")
    print(f"  min:    ${v['ScanPrice'].min():.4f}")
    print(f"  q10:    ${v['ScanPrice'].quantile(0.10):.2f}")
    print(f"  q25:    ${v['ScanPrice'].quantile(0.25):.2f}")
    print(f"  median: ${v['ScanPrice'].median():.2f}")
    print(f"  q75:    ${v['ScanPrice'].quantile(0.75):.2f}")
    print(f"  q90:    ${v['ScanPrice'].quantile(0.90):.2f}")
    print(f"  max:    ${v['ScanPrice'].max():.2f}")
    print(f"\nUnder $1 (penny):  {(v['ScanPrice'] < 1).sum()} / {len(v)}")
    print(f"Under $5:          {(v['ScanPrice'] < 5).sum()} / {len(v)}")
    print(f"Over $10:          {(v['ScanPrice'] >= 10).sum()} / {len(v)}")

    # In pure longs specifically
    if len(pure_longs) > 0:
        print(f"\nPure longs price profile:")
        print(f"  Under $1:  {(pure_longs['ScanPrice'] < 1).sum()} / {len(pure_longs)}")
        print(f"  Under $5:  {(pure_longs['ScanPrice'] < 5).sum()} / {len(pure_longs)}")
        print(f"  Over $5:   {(pure_longs['ScanPrice'] >= 5).sum()} / {len(pure_longs)}")

    # ─────────────────────────────────────────────────────────────────
    # 5. Where does net_d5 actually sit? (full distribution)
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("FULL NET_D5 DISTRIBUTION")
    print("=" * 75)
    print(f"All {len(v)} rows by net_d5_pct buckets:")
    bins = [(-200, -50), (-50, -25), (-25, -10), (-10, -5),
            (-5, 0), (0, 5), (5, 10), (10, 25), (25, 50), (50, 999)]
    for lo, hi in bins:
        sub = v[(v['net_d5_pct'] >= lo) & (v['net_d5_pct'] < hi)]
        bar = '█' * len(sub)
        print(f"  [{lo:>5}% to {hi:>5}%]  n={len(sub):>3}  {bar}")

if __name__ == "__main__":
    main()
