#!/usr/bin/env python3
"""
validate_score_v3_static_v1.py
══════════════════════════════════════════════════════════════════
Backtest Claude's Score v3-static against historical post_analysis.

Methodology (NO overfitting):
  1. Load all post_analysis records (Apr+May 2026)
  2. Compute Score-v3-static + Score-current (v14.6) for each
  3. 5-fold cross-validation: split data into 5 folds
  4. For each fold:
     - Pick top-N by each score in the test fold
     - Simulate $1000/trade, TP=-10%, SL=+7%
     - Report win rate, total PnL, avg PnL/trade
  5. Compare v3-static vs v14.6 head-to-head

OUTPUT:
  ~/RidingHighPro/validation_v3static_results.txt
══════════════════════════════════════════════════════════════════

Run from: ~/RidingHighPro/
  python3 validate_score_v3_static_v1.py
"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# ────────────────────────────────────────────────────────────
# Score v3-static (Claude's design)
# ────────────────────────────────────────────────────────────

WEIGHTS_V3 = {
    "Float_pct": 30, "Gap": 25, "ATRX": 15,
    "MarketCap": 15, "REL_VOL": 10, "RSI": 5,
}

def s_float_pct(v):
    if pd.isna(v): return 0
    if v < 2:    return 0
    if v < 5:    return 20
    if v < 10:   return 40
    if v < 20:   return 60
    if v < 50:   return 80
    return 100

def s_gap(v):
    if pd.isna(v): return 0
    a = abs(v)
    if a > 50:   return 0
    if a > 30:   return 30
    if a > 15:   return 60
    if a > 5:    return 90
    return 100

def s_atrx(v):
    if pd.isna(v): return 0
    if v < 1.0:  return 0
    if v < 1.5:  return 25
    if v < 2.0:  return 50
    if v < 2.5:  return 70
    if v < 3.0:  return 85
    return 100

def s_marketcap(v_m):
    if pd.isna(v_m): return 0
    if v_m > 500:   return 10
    if v_m > 200:   return 40
    if v_m > 100:   return 60
    if v_m > 50:    return 80
    if v_m > 20:    return 100
    if v_m > 10:    return 80
    return 50

def s_rel_vol(v):
    if pd.isna(v): return 0
    if v < 1:    return 0
    if v < 2:    return 25
    if v < 3:    return 50
    if v < 5:    return 75
    if v < 10:   return 90
    return 100

def s_rsi(v):
    if pd.isna(v): return 50
    if v < 50:   return 30
    if v < 60:   return 50
    if v < 70:   return 80
    if v < 85:   return 100
    if v < 95:   return 70
    return 40

def score_v3_static(row):
    s = 0.0
    s += s_float_pct(row.get('Float%'))    * WEIGHTS_V3['Float_pct'] / 100
    s += s_gap(row.get('Gap'))             * WEIGHTS_V3['Gap'] / 100
    s += s_atrx(row.get('ATRX'))           * WEIGHTS_V3['ATRX'] / 100
    s += s_marketcap(row.get('MarketCap_M')) * WEIGHTS_V3['MarketCap'] / 100
    s += s_rel_vol(row.get('REL_VOL'))     * WEIGHTS_V3['REL_VOL'] / 100
    s += s_rsi(row.get('RSI'))             * WEIGHTS_V3['RSI'] / 100
    return round(s, 2)

def passes_filters(row):
    f = row.get('Float%')
    if pd.isna(f) or f < 2: return False
    mcap = row.get('MarketCap_M')
    if pd.isna(mcap) or mcap > 1000 or mcap < 5: return False
    atrx = row.get('ATRX')
    if pd.isna(atrx) or atrx < 1.0: return False
    rv = row.get('REL_VOL')
    if pd.isna(rv) or rv < 1.5: return False
    return True

# ────────────────────────────────────────────────────────────
# Load post_analysis from sheets
# ────────────────────────────────────────────────────────────

def load_data():
    import sheets_manager
    gc = sheets_manager._get_gc()

    config = json.load(open(os.path.expanduser("~/RidingHighPro/sheets_config.json")))
    months = sorted(config.keys())
    print(f"Available months: {months}")

    all_dfs = []
    for month in months:
        try:
            ws = sheets_manager.get_worksheet("post_analysis", month=month, gc=gc)
            data = ws.get_all_values()
            if len(data) < 2: continue
            df = pd.DataFrame(data[1:], columns=data[0])
            df['_month'] = month
            print(f"  {month}: {len(df)} rows")
            all_dfs.append(df)
        except Exception as e:
            print(f"  {month}: ERROR {e}")
    df = pd.concat(all_dfs, ignore_index=True)
    print(f"Combined: {len(df)} rows")
    return df

# ────────────────────────────────────────────────────────────
# Trade simulation
# ────────────────────────────────────────────────────────────

def simulate_trade(row, position=1000):
    """
    Short position: $1000 borrowed, TP=-10% drop, SL=+7% rise.
    SL takes priority if both triggered same day.
    Uses MaxDrop% and MaxRise% from post_analysis.
    """
    max_drop = pd.to_numeric(row.get('MaxDrop%'), errors='coerce')
    max_rise = pd.to_numeric(row.get('MaxRise%'), errors='coerce')

    if pd.isna(max_drop) and pd.isna(max_rise):
        return None, "no_data"
    max_drop = max_drop if not pd.isna(max_drop) else 0
    max_rise = max_rise if not pd.isna(max_rise) else 0

    hit_tp = max_drop <= -10
    hit_sl = max_rise >= 7

    if hit_sl: return -70, "SL"   # short loses 7% -> -$70
    if hit_tp: return +100, "TP"  # short wins 10% -> +$100
    # Closed at end of D5 with whatever the move was
    final = pd.to_numeric(row.get('drop_d5_close'), errors='coerce')
    if pd.isna(final):
        # Approximate: use max_drop / 2 as conservative close
        return -max_drop * 10, "neutral"
    return -final * 10, "neutral"  # short: drop is profit

# ────────────────────────────────────────────────────────────
# Cross-validation backtest
# ────────────────────────────────────────────────────────────

def backtest_score(df, score_col, top_pct=0.5, n_folds=5):
    """
    For each fold, pick top top_pct by score, simulate trades.
    Returns: list of (fold_id, n_trades, n_tp, n_sl, n_neutral, total_pnl)
    """
    df = df.copy().sample(frac=1, random_state=42).reset_index(drop=True)
    fold_size = len(df) // n_folds
    results = []

    for fold in range(n_folds):
        test_start = fold * fold_size
        test_end = test_start + fold_size if fold < n_folds-1 else len(df)
        test = df.iloc[test_start:test_end].copy()

        # Apply filters
        test['_pass'] = test.apply(passes_filters, axis=1)
        test_filtered = test[test['_pass']].copy()

        # Pick top N% by score
        n_pick = max(1, int(len(test_filtered) * top_pct))
        picks = test_filtered.nlargest(n_pick, score_col)

        # Simulate
        n_tp = n_sl = n_neutral = 0
        total_pnl = 0
        for _, r in picks.iterrows():
            pnl, outcome = simulate_trade(r)
            if pnl is None: continue
            total_pnl += pnl
            if outcome == "TP": n_tp += 1
            elif outcome == "SL": n_sl += 1
            else: n_neutral += 1

        n_total = n_tp + n_sl + n_neutral
        results.append({
            'fold': fold,
            'n_trades': n_total,
            'n_tp': n_tp,
            'n_sl': n_sl,
            'n_neutral': n_neutral,
            'win_rate': n_tp / n_total if n_total else 0,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / n_total if n_total else 0,
        })
    return results

# ────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("VALIDATION: Score v3-static vs Score v14.6 (current)")
    print("=" * 70)

    df = load_data()

    # Coerce numeric
    numeric_cols = ['Score', 'Float%', 'Gap', 'ATRX', 'REL_VOL', 'RSI',
                    'MarketCap', 'MaxDrop%', 'ScanPrice',
                    'D1_High', 'D2_High', 'D3_High', 'D4_High', 'D5_High',
                    'D0_High', 'IntraHigh',
                    'SL_Hit_D0', 'SL_Hit_D5', 'IntraDay_SL',
                    'D5_Close']
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Compute MaxRise% from D0-D5 Highs vs ScanPrice
    high_cols = [c for c in ['IntraHigh', 'D1_High', 'D2_High', 'D3_High', 'D4_High', 'D5_High']
                 if c in df.columns]
    if high_cols and 'ScanPrice' in df.columns:
        max_high = df[high_cols].max(axis=1)
        df['MaxRise%'] = (max_high - df['ScanPrice']) / df['ScanPrice'] * 100
    else:
        # Fallback: use SL columns
        df['MaxRise%'] = np.nan

    # Compute drop_d5_close if not present
    if 'D5_Close' in df.columns and 'ScanPrice' in df.columns:
        df['drop_d5_close'] = (df['D5_Close'] - df['ScanPrice']) / df['ScanPrice'] * 100

    # MarketCap to millions
    if 'MarketCap' in df.columns:
        df['MarketCap_M'] = df['MarketCap'] / 1_000_000

    # Compute new score
    df['Score_v3static'] = df.apply(score_v3_static, axis=1)

    # Stats
    print(f"\nData: {len(df)} rows")
    print(f"  with MaxDrop%:  {df['MaxDrop%'].notna().sum()}")
    print(f"  with MaxRise%:  {df['MaxRise%'].notna().sum()}")
    print(f"  passes filters: {df.apply(passes_filters, axis=1).sum()}")

    # Score distributions
    print(f"\nScore distributions:")
    print(f"  v14.6: mean={df['Score'].mean():.2f}, std={df['Score'].std():.2f}")
    print(f"  v3-st: mean={df['Score_v3static'].mean():.2f}, std={df['Score_v3static'].std():.2f}")

    # Drop rows without outcomes
    df_valid = df[df['MaxDrop%'].notna() & df['MaxRise%'].notna()].copy()
    print(f"\nValid for backtest: {len(df_valid)} rows")

    # Backtest at 3 different top-N levels
    for top_pct in [0.3, 0.5, 1.0]:
        print(f"\n{'─'*70}")
        print(f"Top {int(top_pct*100)}% picks per fold")
        print(f"{'─'*70}")

        for score_col in ['Score', 'Score_v3static']:
            results = backtest_score(df_valid, score_col, top_pct=top_pct, n_folds=5)
            avg_wr = np.mean([r['win_rate'] for r in results])
            avg_pnl = np.mean([r['avg_pnl'] for r in results])
            total_trades = sum(r['n_trades'] for r in results)
            total_tp = sum(r['n_tp'] for r in results)
            total_sl = sum(r['n_sl'] for r in results)
            total_pnl = sum(r['total_pnl'] for r in results)
            print(f"  {score_col:>15}: trades={total_trades}, TP={total_tp}, SL={total_sl}, "
                  f"win_rate={avg_wr*100:.1f}%, avg_pnl=${avg_pnl:.2f}, total_pnl=${total_pnl:.2f}")

    # Tier analysis (no CV -- descriptive only)
    print(f"\n{'─'*70}")
    print("Score tier analysis (descriptive, all data)")
    print(f"{'─'*70}")

    for score_col in ['Score', 'Score_v3static']:
        print(f"\n{score_col}:")
        tiers = [(0,40), (40,60), (60,80), (80,100)]
        for low, high in tiers:
            sub = df_valid[(df_valid[score_col] >= low) & (df_valid[score_col] < high)]
            if len(sub) == 0: continue
            tp_rate = (sub['MaxDrop%'] <= -10).mean() * 100
            sl_rate = (sub['MaxRise%'] >= 7).mean() * 100
            avg_drop = sub['MaxDrop%'].mean()
            print(f"  [{low:>3}-{high:<3}] n={len(sub):>3}  TP10={tp_rate:>5.1f}%  "
                  f"SL7={sl_rate:>5.1f}%  avg_drop={avg_drop:+.2f}%")

    # Save full output
    out_path = os.path.expanduser("~/RidingHighPro/validation_v3static_results.csv")
    df_valid[['Ticker','ScanDate','Score','Score_v3static','MaxDrop%','MaxRise%']].to_csv(
        out_path, index=False)
    print(f"\nSaved: {out_path}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

if __name__ == "__main__":
    main()
