"""
morning_health_check.py v2 - 2026-04-17
בדיקת בריאות בוקר של מערכת RidingHigh Pro.
Read-only - לא עושה שינויים.

עדכון v2:
- Test 3 כעת בודק ATRX מ-score_tracker (זמין בכל הבוקר)
- Test 3b בודק ATRX מ-daily_snapshots (זמין רק אחרי 14:59)
- Test 5 כעת בודק את כל 9 הציונים
"""
import sys
import os
from datetime import datetime
import pandas as pd
import pytz

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

PERU_TZ = pytz.timezone("America/Lima")
NOW = datetime.now(PERU_TZ)
TODAY = NOW.strftime("%Y-%m-%d")

print("=" * 70)
print(f"🌅 RidingHigh Pro - Morning Health Check v2")
print(f"⏰ {NOW.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print("=" * 70)

# TEST 1: Google Sheets access
print("\n[TEST 1] Google Sheets access...")
try:
    import sheets_manager
    gc = sheets_manager._get_gc()
    if gc is None:
        print("  ❌ FAIL: No Google credentials")
        sys.exit(1)
    print("  ✅ OK: Credentials loaded")
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

# TEST 2: timeline_live - today's scans
print("\n[TEST 2] timeline_live - today's scans...")
today_rows = pd.DataFrame()
try:
    ws = sheets_manager.get_worksheet("timeline_live", gc=gc)
    data = ws.get_all_values()
    if len(data) <= 1:
        print("  ⚠️  EMPTY: timeline_live has no data")
    else:
        df = pd.DataFrame(data[1:], columns=data[0])
        today_rows = df[df["Date"] == TODAY] if "Date" in df.columns else pd.DataFrame()
        print(f"  📊 Total rows: {len(df):,}")
        print(f"  📊 Today's rows: {len(today_rows):,}")
        if len(today_rows) == 0:
            hour = NOW.hour
            if hour < 8 or (hour == 8 and NOW.minute < 30):
                print("  ℹ️  Market not open yet (08:30 Peru)")
            else:
                print("  ⚠️  WARNING: No scans today!")
        else:
            if "ScanTime" in today_rows.columns:
                latest = today_rows["ScanTime"].iloc[-1]
                tickers_today = today_rows["Ticker"].nunique()
                print(f"  ✅ Latest scan: {latest}")
                print(f"  ✅ Unique tickers: {tickers_today}")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# TEST 3: ATRX from score_tracker (morning)
print("\n[TEST 3] ATRX values from score_tracker (morning check)...")
try:
    ws_st = sheets_manager.get_worksheet("score_tracker", gc=gc)
    data_st = ws_st.get_all_values()
    if len(data_st) <= 1:
        print("  ⚠️  EMPTY: score_tracker has no data")
    else:
        df_st = pd.DataFrame(data_st[1:], columns=data_st[0])
        today_st = df_st[df_st["Date"] == TODAY] if "Date" in df_st.columns else pd.DataFrame()
        print(f"  📊 Total rows in score_tracker: {len(df_st):,}")
        print(f"  📊 Today's rows: {len(today_st):,}")
        
        if len(today_st) > 0 and "ATRX" in today_st.columns:
            atrx_vals = pd.to_numeric(today_st["ATRX"], errors="coerce").dropna()
            if len(atrx_vals) > 0:
                max_atrx = atrx_vals.max()
                zero_count = (atrx_vals == 0).sum()
                over_10 = (atrx_vals > 10).sum()
                print(f"  📊 ATRX today: min={atrx_vals.min():.2f}, mean={atrx_vals.mean():.2f}, max={max_atrx:.2f}")
                print(f"  📊 Rows ATRX > 10: {over_10} (yfinance bug indicator)")
                print(f"  📊 Rows ATRX == 0 (validation blocked): {zero_count}")
                
                if over_10 > 0:
                    print(f"  ⚠️  WARNING: {over_10} rows with ATRX > 10")
                elif zero_count > 0:
                    print(f"  ✅ Validation working: {zero_count} rows caught as bad data")
                else:
                    print(f"  ✅ OK: All ATRX values in normal range")
            else:
                print("  ℹ️  No valid ATRX values yet")
        else:
            print("  ℹ️  No ATRX column or no data yet in score_tracker")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

# TEST 3b: ATRX from daily_snapshots (afternoon)
print("\n[TEST 3b] ATRX values from daily_snapshots (afternoon check)...")
try:
    ws_ds = sheets_manager.get_worksheet("daily_snapshots", gc=gc)
    data_ds = ws_ds.get_all_values()
    if len(data_ds) <= 1:
        print("  ⚠️  EMPTY: daily_snapshots has no data")
    else:
        df_ds = pd.DataFrame(data_ds[1:], columns=data_ds[0])
        today_ds = df_ds[df_ds["Date"] == TODAY] if "Date" in df_ds.columns else pd.DataFrame()
        
        print(f"  📊 Total rows in daily_snapshots: {len(df_ds):,}")
        print(f"  📊 Today's rows: {len(today_ds):,}")
        
        if len(today_ds) > 0 and "ATRX" in today_ds.columns:
            atrx_vals = pd.to_numeric(today_ds["ATRX"], errors="coerce").dropna()
            if len(atrx_vals) > 0:
                print(f"  📊 ATRX today: min={atrx_vals.min():.2f}, mean={atrx_vals.mean():.2f}, max={atrx_vals.max():.2f}")
                over_10 = (atrx_vals > 10).sum()
                if over_10 > 0:
                    print(f"  ⚠️  WARNING: {over_10} rows with ATRX > 10")
                else:
                    print(f"  ✅ OK: All ATRX values normal")
            else:
                print("  ℹ️  No valid ATRX values")
        elif len(today_ds) == 0:
            hour = NOW.hour
            if hour < 15:
                print(f"  ℹ️  daily_snapshots writes at 14:59 Peru (current: {NOW.strftime('%H:%M')})")
            else:
                print("  ⚠️  WARNING: daily_snapshots should be written by now!")
        else:
            print("  ℹ️  No ATRX column")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

# TEST 4: REL_VOL cap
print("\n[TEST 4] REL_VOL cap (should be ≤ 100)...")
try:
    if "REL_VOL" in today_rows.columns and len(today_rows) > 0:
        rv_vals = pd.to_numeric(today_rows["REL_VOL"], errors="coerce").dropna()
        if len(rv_vals) > 0:
            max_rv = rv_vals.max()
            over_100 = (rv_vals > 100).sum()
            at_cap = (rv_vals == 100).sum()
            print(f"  📊 REL_VOL: mean={rv_vals.mean():.2f}, max={max_rv:.2f}")
            print(f"  📊 Rows at cap (=100): {at_cap}")
            if max_rv > 100:
                print(f"  ❌ FAIL: {over_100} rows exceed cap!")
            else:
                print(f"  ✅ OK: All ≤ 100 (cap working)")
        else:
            print("  ℹ️  No REL_VOL data yet")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

# TEST 5: All 9 scores distribution
print("\n[TEST 5] All 9 Scores distribution today...")
try:
    if len(today_rows) > 0:
        score_cols = ["Score", "Score_B", "Score_C", "Score_D", "Score_E",
                      "Score_F", "Score_G", "Score_H", "Score_I"]
        print(f"  📊 Per-Score statistics:")
        print(f"  {'Score':<12} {'min':>8} {'mean':>8} {'max':>8} {'>100':>6}")
        print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*6}")
        all_good = True
        for sc in score_cols:
            if sc in today_rows.columns:
                sv = pd.to_numeric(today_rows[sc], errors="coerce").dropna()
                if len(sv) > 0:
                    max_val = sv.max()
                    over_100 = (sv > 100).sum()
                    status = "✅" if max_val <= 100 else "❌"
                    if max_val > 100:
                        all_good = False
                    print(f"  {status} {sc:<10} {sv.min():>8.2f} {sv.mean():>8.2f} {max_val:>8.2f} {over_100:>6}")
                else:
                    print(f"  ℹ️  {sc:<10} (no data)")
            else:
                print(f"  ⚠️  {sc:<10} (column missing!)")
        if all_good:
            print(f"\n  ✅ OK: All 9 scores in valid range (0-100)")
        else:
            print(f"\n  ❌ FAIL: Some scores exceed 100!")
    else:
        print("  ℹ️  No data yet")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

# TEST 6: post_analysis integrity
print("\n[TEST 6] post_analysis - audit_flag check...")
try:
    ws_pa = sheets_manager.get_worksheet("post_analysis", gc=gc)
    data_pa = ws_pa.get_all_values()
    if len(data_pa) <= 1:
        print("  ⚠️  EMPTY")
    else:
        cols = data_pa[0]
        n_rows = len(data_pa) - 1
        has_audit = "audit_flag" in cols
        has_recalc = "Score_recalc_date" in cols
        print(f"  📊 Total rows: {n_rows}")
        print(f"  {'✅' if has_audit else '❌'} audit_flag: {'present' if has_audit else 'MISSING'}")
        print(f"  {'✅' if has_recalc else '❌'} Score_recalc_date: {'present' if has_recalc else 'MISSING'}")
        if has_audit:
            audit_idx = cols.index("audit_flag")
            audit_vals = [row[audit_idx] for row in data_pa[1:] if len(row) > audit_idx]
            from collections import Counter
            counts = Counter(audit_vals)
            print(f"  📊 Breakdown:")
            for flag, count in counts.most_common():
                print(f"     {flag or '(empty)'}: {count}")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# TEST 7: Backups
print("\n[TEST 7] Backup files...")
backups = [
    "post_analysis_backup_2026-04-16_1855.csv",
    "post_analysis_backup_recalc_2026-04-16_2005.csv",
]
for bkp in backups:
    path = os.path.expanduser(f"~/RidingHighPro/{bkp}")
    if os.path.exists(path):
        print(f"  ✅ {bkp}")
    else:
        print(f"  ⚠️  MISSING: {bkp}")

# TEST 8: Quarantine folder
print("\n[TEST 8] Quarantine folder...")
quarantine = os.path.expanduser("~/RidingHighPro/גיבוי זמני")
if os.path.exists(quarantine):
    files = [f for f in os.listdir(quarantine) if f.endswith(".py")]
    print(f"  ✅ Exists, {len(files)} .py files quarantined")
    critical = ["recalculate_scores.py", "fix_weights.py", "fix_score.py"]
    for c in critical:
        if c in files:
            print(f"     ✅ {c} safely quarantined")
        else:
            print(f"     ⚠️  {c} NOT in quarantine")
else:
    print(f"  ⚠️  Missing!")

print("\n" + "=" * 70)
print(f"✅ Check completed at {NOW.strftime('%H:%M:%S')} Peru")
print("=" * 70)
