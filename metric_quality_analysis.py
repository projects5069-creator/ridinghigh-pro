"""
metric_quality_analysis.py v2 - 2026-04-17
ניתוח מקיף של כל המדדים במערכת - מה באמת מנבא שורט מוצלח.

בדיקה של 28 מדדים:
- 8 מדדים טכניים קלאסיים
- 4 מדדים מבניים (SMA, Consecutive Up, Days since IPO, Float)
- 5 מדדי סריקה (ScanCount, ScoreMax/Min/Std, EntryScore)
- 10 catalysts
- 1 MarketCapCategory

Read-only.
"""
import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import pytz
from collections import Counter

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

PERU_TZ = pytz.timezone("America/Lima")
NOW = datetime.now(PERU_TZ)

print("=" * 80)
print(f"🔬 Metric Quality Analysis v2 - ALL 28 Metrics")
print(f"⏰ {NOW.strftime('%Y-%m-%d %H:%M')} Peru")
print("=" * 80)

# Load post_analysis
import sheets_manager
gc = sheets_manager._get_gc()
print("\n📥 Loading post_analysis...")
ws = sheets_manager.get_worksheet("post_analysis", gc=gc)
data = ws.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])
print(f"  ✅ {len(df)} rows")

# Filter CLEAN rows
if "audit_flag" in df.columns:
    df = df[df["audit_flag"] == "CLEAN"]
    print(f"  ✅ Filtered to CLEAN: {len(df)} rows")

# ═══════════════════════════════════════════════════════════════════════
# Define ALL metrics
# ═══════════════════════════════════════════════════════════════════════
TECHNICAL = {
    "MxV": "Market Cap vs Volume (negative = pump)",
    "RunUp": "Intraday rise %",
    "ATRX": "Volatility ratio",
    "RSI": "Relative Strength Index",
    "VWAP": "Distance from VWAP",
    "ScanChange%": "Change % vs prev close",
    "REL_VOL": "Volume relative to avg",
    "Gap": "Opening gap %",
}

STRUCTURAL = {
    "Price_vs_SMA20": "Price vs 20-day SMA %",
    "Consecutive_Up": "Consecutive up days",
    "DaysSinceIPO": "Days since IPO",
    "RealFloat_M": "Float in millions",
}

SCAN_METRICS = {
    "ScanCount": "Times scanned today",
    "ScoreMax": "Max Score today",
    "ScoreMin": "Min Score today",
    "ScoreStd": "Score volatility",
    "EntryScore": "Entry timing score",
}

CATALYSTS = [f"cat_{c}" for c in [
    "merger_acquisition", "fda_approval", "clinical_trial",
    "marketing_announcement", "earnings_report", "regulatory_compliance",
    "lawsuit", "share_dilution", "reverse_split", "no_clear_reason"
]]

ALL_NUMERIC_METRICS = {**TECHNICAL, **STRUCTURAL, **SCAN_METRICS}
ALL_NUMERIC_METRICS.update({c: f"Catalyst: {c.replace('cat_','')}" for c in CATALYSTS})

# Convert to numeric
outcomes = ["MaxDrop%", "TP10_Hit", "TP15_Hit", "TP20_Hit", "SL7_Hit_D1"]
all_cols = list(ALL_NUMERIC_METRICS.keys()) + outcomes
for col in all_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ═══════════════════════════════════════════════════════════════════════
# Which metrics exist in the data?
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📋 METRIC INVENTORY")
print("=" * 80)

available = []
unavailable = []
for col, desc in ALL_NUMERIC_METRICS.items():
    if col in df.columns:
        n_valid = df[col].dropna().count()
        if n_valid > 0:
            available.append((col, desc, n_valid))
        else:
            unavailable.append((col, "column exists but empty"))
    else:
        unavailable.append((col, "column missing"))

print(f"\n  ✅ Available metrics with data: {len(available)}")
print(f"  ❌ Unavailable: {len(unavailable)}")

if unavailable:
    print("\n  Missing metrics:")
    for col, reason in unavailable[:10]:
        print(f"    ❌ {col}: {reason}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: Correlation with MaxDrop%
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 1 — Correlation with MaxDrop%")
print("=" * 80)
print()
print("  Interpretation:")
print("  • Negative (-) = metric higher → bigger DROP (good for shorts)")
print("  • Positive (+) = metric higher → smaller drop (bad)")
print()

if "MaxDrop%" not in df.columns:
    print("  ❌ No MaxDrop% column")
else:
    md = df["MaxDrop%"].dropna()
    print(f"  Sample: n={len(md)}, mean={md.mean():.2f}%, median={md.median():.2f}%")
    print()
    
    correlations = []
    for col, desc in ALL_NUMERIC_METRICS.items():
        if col not in df.columns:
            continue
        valid = df[[col, "MaxDrop%"]].dropna()
        if len(valid) < 15:
            continue
        corr = valid[col].corr(valid["MaxDrop%"])
        if pd.notna(corr):
            correlations.append((col, desc, corr, len(valid)))
    
    # Sort by absolute correlation strength
    correlations.sort(key=lambda x: abs(x[2]), reverse=True)
    
    print(f"  {'Metric':<25} {'Corr':>8} {'n':>5} {'Strength':<12} {'Direction':<22}")
    print(f"  {'-'*25} {'-'*8} {'-'*5} {'-'*12} {'-'*22}")
    
    for col, desc, corr, n in correlations:
        abs_corr = abs(corr)
        if abs_corr >= 0.25:
            strength = "🟢 STRONG"
        elif abs_corr >= 0.15:
            strength = "🟡 Moderate"
        elif abs_corr >= 0.08:
            strength = "⚪ Weak"
        else:
            strength = "❌ Noise"
        
        if abs_corr < 0.08:
            direction = "(random)"
        elif corr < 0:
            direction = "↑ more → more drop ✓"
        else:
            direction = "↑ more → less drop ✗"
        
        print(f"  {col:<25} {corr:>+8.3f} {n:>5} {strength:<12} {direction}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: Win Rate by Metric Quintile (Continuous metrics only)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 2 — Win Rate by Metric Quintile (TP10 Hit)")
print("=" * 80)
print()
print("  Q1 = lowest 20%, Q5 = highest 20%")
print("  Good metric: clear pattern (Q5 much higher or lower than Q1)")
print()

if "TP10_Hit" in df.columns:
    print(f"  {'Metric':<25} {'Q1':>7} {'Q2':>7} {'Q3':>7} {'Q4':>7} {'Q5':>7} {'Diff':>7} {'Pattern':<18}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*18}")
    
    # Only continuous metrics (not catalysts which are 0/1)
    for col, desc in {**TECHNICAL, **STRUCTURAL, **SCAN_METRICS}.items():
        if col not in df.columns:
            continue
        valid = df[[col, "TP10_Hit"]].dropna()
        if len(valid) < 25:
            continue
        try:
            valid["quintile"] = pd.qcut(valid[col], q=5, labels=[1,2,3,4,5], duplicates='drop')
            win_rates = valid.groupby("quintile", observed=True)["TP10_Hit"].mean() * 100
            if len(win_rates) < 5:
                continue
            
            q1, q5 = win_rates.iloc[0], win_rates.iloc[-1]
            diff = q5 - q1
            
            if diff > 15:
                pattern = "🟢 ↑ strong"
            elif diff > 5:
                pattern = "🟡 ↑ weak"
            elif diff > -5:
                pattern = "⚪ flat"
            elif diff > -15:
                pattern = "🟠 ↓ weak"
            else:
                pattern = "🔴 ↓ strong"
            
            line = f"  {col:<25}"
            for q in [1, 2, 3, 4, 5]:
                if q in win_rates.index:
                    line += f" {win_rates[q]:>5.1f}% "
                else:
                    line += f" {'—':>5}  "
            line += f" {diff:>+6.1f} {pattern}"
            print(line)
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: Catalyst Analysis - Binary Metrics
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🎪 SECTION 3 — Catalysts (Win Rate when present vs absent)")
print("=" * 80)
print()

if "TP10_Hit" in df.columns:
    print(f"  {'Catalyst':<30} {'With':>10} {'Without':>10} {'Diff':>8} {'Impact':<15}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8} {'-'*15}")
    
    for col in CATALYSTS:
        if col not in df.columns:
            continue
        valid = df[[col, "TP10_Hit"]].dropna()
        if len(valid) < 15:
            continue
        
        with_cat = valid[valid[col] == 1]
        without_cat = valid[valid[col] == 0]
        
        if len(with_cat) < 3:
            continue
        
        wr_with = with_cat["TP10_Hit"].mean() * 100 if len(with_cat) > 0 else 0
        wr_without = without_cat["TP10_Hit"].mean() * 100 if len(without_cat) > 0 else 0
        diff = wr_with - wr_without
        
        if diff > 10:
            impact = "🟢 Big boost"
        elif diff > 3:
            impact = "🟡 Small boost"
        elif diff > -3:
            impact = "⚪ Neutral"
        elif diff > -10:
            impact = "🟠 Small drag"
        else:
            impact = "🔴 Big drag"
        
        name = col.replace("cat_", "")
        print(f"  {name:<30} {wr_with:>7.1f}%({len(with_cat):>2}) {wr_without:>7.1f}%({len(without_cat):>2}) {diff:>+7.1f}  {impact}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: Sector Analysis
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🏢 SECTION 4 — Win Rate by Sector")
print("=" * 80)
print()

if "Sector" in df.columns and "TP10_Hit" in df.columns:
    valid = df[["Sector", "TP10_Hit"]].dropna()
    if len(valid) >= 10:
        sector_stats = valid.groupby("Sector").agg(
            n=("TP10_Hit", "count"),
            wr=("TP10_Hit", lambda x: x.mean() * 100)
        ).sort_values("wr", ascending=False)
        
        print(f"  {'Sector':<30} {'n':>4} {'Win Rate':>10}")
        print(f"  {'-'*30} {'-'*4} {'-'*10}")
        for sector, row in sector_stats.iterrows():
            if row["n"] >= 5:
                name = str(sector)[:28] if sector else "(empty)"
                print(f"  {name:<30} {int(row['n']):>4} {row['wr']:>8.1f}%")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: Market Cap Category
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("💰 SECTION 5 — Win Rate by Market Cap Category")
print("=" * 80)
print()

if "MarketCapCategory" in df.columns and "TP10_Hit" in df.columns:
    valid = df[["MarketCapCategory", "TP10_Hit"]].dropna()
    if len(valid) >= 10:
        cat_stats = valid.groupby("MarketCapCategory").agg(
            n=("TP10_Hit", "count"),
            wr=("TP10_Hit", lambda x: x.mean() * 100)
        ).sort_values("wr", ascending=False)
        
        print(f"  {'Category':<15} {'n':>4} {'Win Rate':>10}")
        print(f"  {'-'*15} {'-'*4} {'-'*10}")
        for cat, row in cat_stats.iterrows():
            name = str(cat) if cat else "(empty)"
            print(f"  {name:<15} {int(row['n']):>4} {row['wr']:>8.1f}%")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 6: Top Winners vs Losers profile
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🏆 SECTION 6 — Profile: Top 15 Winners vs Top 15 Losers")
print("=" * 80)
print()

if "MaxDrop%" in df.columns:
    sorted_df = df.dropna(subset=["MaxDrop%"]).sort_values("MaxDrop%")
    winners = sorted_df.head(15)
    losers = sorted_df.tail(15)
    
    print(f"  WINNERS: avg drop = {winners['MaxDrop%'].mean():.2f}%")
    print(f"  LOSERS:  avg drop = {losers['MaxDrop%'].mean():.2f}%")
    print()
    
    print(f"  {'Metric':<20} {'Winners':>12} {'Losers':>12} {'Diff':>10}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*10}")
    
    profile_cols = list(TECHNICAL.keys()) + list(STRUCTURAL.keys()) + ["EntryScore", "Score"]
    for col in profile_cols:
        if col not in df.columns:
            continue
        w_vals = pd.to_numeric(winners[col], errors="coerce").dropna()
        l_vals = pd.to_numeric(losers[col], errors="coerce").dropna()
        if len(w_vals) >= 5 and len(l_vals) >= 5:
            w_mean = w_vals.mean()
            l_mean = l_vals.mean()
            diff = w_mean - l_mean
            print(f"  {col:<20} {w_mean:>12.2f} {l_mean:>12.2f} {diff:>+10.2f}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 7: TOP RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🎯 SECTION 7 — FINAL RANKING")
print("=" * 80)

if correlations:
    strong = [x for x in correlations if abs(x[2]) >= 0.15]
    moderate = [x for x in correlations if 0.08 <= abs(x[2]) < 0.15]
    weak = [x for x in correlations if abs(x[2]) < 0.08]
    
    print(f"\n  🟢 STRONG PREDICTORS ({len(strong)}) - use these heavily:")
    for col, desc, corr, n in strong:
        direction = "shorter" if corr < 0 else "LONGER (inverted!)"
        print(f"    {col}: r={corr:+.3f} ({direction}, n={n})")
    
    print(f"\n  🟡 MODERATE PREDICTORS ({len(moderate)}) - useful support:")
    for col, desc, corr, n in moderate:
        direction = "shorter" if corr < 0 else "LONGER (inverted!)"
        print(f"    {col}: r={corr:+.3f} ({direction}, n={n})")
    
    print(f"\n  ⚪ WEAK / NOISE ({len(weak)}) - consider removing:")
    for col, desc, corr, n in weak[:10]:
        print(f"    {col}: r={corr:+.3f} (n={n})")

print("\n" + "=" * 80)
print(f"✅ Analysis completed at {datetime.now(PERU_TZ).strftime('%H:%M:%S')} Peru")
print("=" * 80)
