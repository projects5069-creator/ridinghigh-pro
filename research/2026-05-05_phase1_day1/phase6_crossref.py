#!/usr/bin/env python3
"""
Phase 6 — DropsLab Cross-Reference
Match RidingHigh detections to DropsLab confirmed drops.
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Load data
outcomes = pd.read_pickle('/tmp/research/outcomes.pkl')
dropslab_raw = pd.read_pickle('/tmp/research/df_dropslab_raw.pkl')
dropslab_post = pd.read_pickle('/tmp/research/df_dropslab_post.pkl')

print(f"RidingHigh outcomes: {len(outcomes)} rows")
print(f"DropsLab raw: {len(dropslab_raw)} rows")
print(f"DropsLab post: {len(dropslab_post)} rows")

# ═══════════════════════════════════════════════════════════════════════
# Prepare data
# ═══════════════════════════════════════════════════════════════════════

# RidingHigh: Ticker + ScanDate
rh = outcomes[['Ticker', 'ScanDate', 'Score', 'MxV', 'RunUp', 'RSI', 'ATRX',
               'REL_VOL', 'ScanPrice', 'drop_max_pct', 'hit_tp10', 'hit_sl7',
               'net_outcome']].copy()
rh['Ticker'] = rh['Ticker'].str.strip().str.upper()
rh['ScanDate'] = pd.to_datetime(rh['ScanDate'], errors='coerce')

# DropsLab raw: ticker + date
dl_raw = dropslab_raw.copy()
dl_raw.columns = [c.strip() for c in dl_raw.columns]
if 'ticker' in dl_raw.columns:
    dl_raw['ticker'] = dl_raw['ticker'].str.strip().str.upper()
if 'date' in dl_raw.columns:
    dl_raw['date'] = pd.to_datetime(dl_raw['date'], errors='coerce')

# DropsLab post
dl_post = dropslab_post.copy()
dl_post.columns = [c.strip() for c in dl_post.columns]
if 'ticker' in dl_post.columns:
    dl_post['ticker'] = dl_post['ticker'].str.strip().str.upper()
if 'scan_date' in dl_post.columns:
    dl_post['scan_date'] = pd.to_datetime(dl_post['scan_date'], errors='coerce')

# Convert numeric columns in DropsLab
for col in ['pct_change', 'close', 'volume', 'market_cap', 'rsi_14',
            'volume_ratio', 'gap_down_pct', 'intraday_reversal_pct',
            'pct_from_52w_high', 'pct_from_52w_low', 'beta',
            'max_recovery_5d_pct', 'max_further_drop_5d_pct',
            'd1_pct', 'd2_pct', 'd3_pct', 'd4_pct', 'd5_pct',
            'scan_pct_change']:
    if col in dl_raw.columns:
        dl_raw[col] = pd.to_numeric(dl_raw[col], errors='coerce')
    if col in dl_post.columns:
        dl_post[col] = pd.to_numeric(dl_post[col], errors='coerce')

print(f"\nRH date range: {rh['ScanDate'].min()} → {rh['ScanDate'].max()}")
print(f"DL raw date range: {dl_raw['date'].min()} → {dl_raw['date'].max()}")
print(f"DL post date range: {dl_post['scan_date'].min()} → {dl_post['scan_date'].max()}")

# Unique tickers
rh_tickers = set(rh['Ticker'].dropna())
dl_tickers = set(dl_raw['ticker'].dropna()) if 'ticker' in dl_raw.columns else set()
common_tickers = rh_tickers & dl_tickers
print(f"\nRH unique tickers: {len(rh_tickers)}")
print(f"DL unique tickers: {len(dl_tickers)}")
print(f"Common tickers: {len(common_tickers)}")

if common_tickers:
    print(f"Sample common: {list(common_tickers)[:20]}")

# ═══════════════════════════════════════════════════════════════════════
# Match: RidingHigh detection → DropsLab drop
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("CROSS-REFERENCE: RH Detection → DL Drop")
print("=" * 60)

matches = []

for _, rh_row in rh.iterrows():
    ticker = rh_row['Ticker']
    scan_date = rh_row['ScanDate']

    if pd.isna(ticker) or pd.isna(scan_date):
        continue

    # Look for this ticker in DropsLab within -5 to +10 days of RH scan
    dl_ticker = dl_raw[dl_raw['ticker'] == ticker] if 'ticker' in dl_raw.columns else pd.DataFrame()

    for _, dl_row in dl_ticker.iterrows():
        drop_date = dl_row['date']
        if pd.isna(drop_date):
            continue

        days_diff = (drop_date - scan_date).days

        # RH detected pump BEFORE DropsLab detected drop (0 to 10 days later)
        # OR same day
        # OR DropsLab detected first (-5 to 0 days)
        if -5 <= days_diff <= 10:
            match = {
                'ticker': ticker,
                'rh_scan_date': scan_date,
                'dl_drop_date': drop_date,
                'days_rh_to_dl': days_diff,
                'rh_score': rh_row['Score'],
                'rh_mxv': rh_row['MxV'],
                'rh_runup': rh_row['RunUp'],
                'rh_scan_price': rh_row['ScanPrice'],
                'rh_max_drop': rh_row['drop_max_pct'],
                'rh_hit_tp10': rh_row['hit_tp10'],
                'rh_outcome': rh_row['net_outcome'],
            }

            # Add DropsLab metrics
            for col in ['pct_change', 'close', 'volume', 'market_cap',
                        'gap_down_pct', 'intraday_reversal_pct', 'rsi_14',
                        'volume_ratio', 'sector', 'market_cap_category']:
                if col in dl_row.index:
                    match[f'dl_{col}'] = dl_row[col]

            # Also check DropsLab post for this ticker
            dl_post_row = dl_post[
                (dl_post['ticker'] == ticker) &
                (dl_post['scan_date'] == drop_date)
            ]
            if len(dl_post_row) > 0:
                post = dl_post_row.iloc[0]
                for col in ['max_recovery_5d_pct', 'max_further_drop_5d_pct',
                            'pattern_tag', 'd5_pct']:
                    if col in post.index:
                        match[f'dl_post_{col}'] = post[col]

            matches.append(match)

matches_df = pd.DataFrame(matches)
print(f"\nTotal matches found: {len(matches_df)}")

if len(matches_df) > 0:
    print(f"\nDays from RH detection to DL drop:")
    print(matches_df['days_rh_to_dl'].value_counts().sort_index())

    # Analysis: Was RH detection predictive of DL outcome?
    print(f"\nRH outcome when matched with DL:")
    print(matches_df['rh_outcome'].value_counts())

    print(f"\nRH hit_tp10 rate in matched: {matches_df['rh_hit_tp10'].mean():.1%}")

    if 'dl_post_pattern_tag' in matches_df.columns:
        print(f"\nDL pattern tags for RH-matched stocks:")
        print(matches_df['dl_post_pattern_tag'].value_counts())

    # Compare RH Score for matched vs unmatched
    matched_tickers = set(matches_df['ticker'])
    rh_matched = rh[rh['Ticker'].isin(matched_tickers)]
    rh_unmatched = rh[~rh['Ticker'].isin(matched_tickers)]

    print(f"\nRH Score comparison:")
    print(f"  Matched with DL (n={len(rh_matched)}): "
          f"mean={rh_matched['Score'].mean():.1f}, med={rh_matched['Score'].median():.1f}")
    print(f"  Not in DL (n={len(rh_unmatched)}): "
          f"mean={rh_unmatched['Score'].mean():.1f}, med={rh_unmatched['Score'].median():.1f}")

    print(f"\nTP10 hit rate:")
    print(f"  Matched: {rh_matched['hit_tp10'].mean():.1%}")
    print(f"  Unmatched: {rh_unmatched['hit_tp10'].mean():.1%}")

    # Day-0 matches (same day)
    day0 = matches_df[matches_df['days_rh_to_dl'] == 0]
    print(f"\nSame-day matches (RH scan → DL drop same day): {len(day0)}")
    if len(day0) > 0:
        print(f"  These are stocks that pumped AND dropped 10%+ on the same day")
        print(f"  RH detected the pump, DL detected the drop")
        print(f"  Avg RH Score: {day0['rh_score'].mean():.1f}")

    # RH detected BEFORE DL (days_rh_to_dl > 0)
    rh_first = matches_df[matches_df['days_rh_to_dl'] > 0]
    print(f"\nRH detected BEFORE DL drop (predictive): {len(rh_first)}")
    if len(rh_first) > 0:
        print(f"  Avg days lead: {rh_first['days_rh_to_dl'].mean():.1f}")
        print(f"  These stocks pumped, then crashed {rh_first['days_rh_to_dl'].mean():.1f} days later")

    # Save
    matches_df.to_csv('/tmp/research/cross_reference.csv', index=False)
    print(f"\n✅ Saved cross_reference.csv: {len(matches_df)} matches")
else:
    print("\n⚠️ No matches found between RH and DL datasets")

    # Still analyze overlap potential
    print("\nChecking if date ranges overlap...")
    rh_dates = set(rh['ScanDate'].dropna().dt.strftime('%Y-%m-%d'))
    dl_dates = set(dl_raw['date'].dropna().dt.strftime('%Y-%m-%d'))
    common_dates = rh_dates & dl_dates
    print(f"  RH dates: {len(rh_dates)}")
    print(f"  DL dates: {len(dl_dates)}")
    print(f"  Common dates: {len(common_dates)}")

    # Save empty cross_reference with explanation
    pd.DataFrame({'note': ['No matches found - check date ranges and ticker overlap']}).to_csv(
        '/tmp/research/cross_reference.csv', index=False)

# Checkpoint
with open('/tmp/research/checkpoints/phase6_done.txt', 'w') as f:
    f.write(f"Phase 6 completed at {datetime.now().isoformat()}\n")
    f.write(f"Matches found: {len(matches_df) if len(matches_df) > 0 else 0}\n")
    f.write(f"Common tickers: {len(common_tickers)}\n")
print("\n✅ Phase 6 checkpoint saved")
