"""
score_distribution.py - 2026-04-17
ניתוח פיזור של 9 הציונים על סקאלת 0-100.

מטרה: להבין איפה הציונים באמת יושבים לפני שנחליט על rescaling.

Read-only - לא עושה שינויים.

Usage:
  python3 score_distribution.py
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import pytz

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

PERU_TZ = pytz.timezone("America/Lima")
NOW = datetime.now(PERU_TZ)
TODAY = NOW.strftime("%Y-%m-%d")

print("=" * 80)
print(f"🎯 Score Distribution Analysis - All 9 Scores")
print(f"⏰ {NOW.strftime('%Y-%m-%d %H:%M')} Peru")
print("=" * 80)

import sheets_manager
gc = sheets_manager._get_gc()
if gc is None:
    print("❌ No credentials")
    sys.exit(1)

# Load timeline_live (contains all 9 scores)
print("\n📥 Loading timeline_live...")
ws = sheets_manager.get_worksheet("timeline_live", gc=gc)
data = ws.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])
print(f"  ✅ {len(df):,} rows loaded")

# Also load post_analysis for historical comparison
print("\n📥 Loading post_analysis...")
ws_pa = sheets_manager.get_worksheet("post_analysis", gc=gc)
data_pa = ws_pa.get_all_values()
df_pa = pd.DataFrame(data_pa[1:], columns=data_pa[0])
print(f"  ✅ {len(df_pa):,} rows loaded")

# Focus on last 7 days of timeline_live (meaningful recent sample)
if "Date" in df.columns:
    last_7_days = [(NOW - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    df_recent = df[df["Date"].isin(last_7_days)]
    print(f"  📊 Last 7 days: {len(df_recent):,} rows")
else:
    df_recent = df

# Score columns to analyze
SCORE_COLS = ["Score", "Score_B", "Score_C", "Score_D", "Score_E",
              "Score_F", "Score_G", "Score_H", "Score_I"]

# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: Basic Statistics Per Score
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 1 — Basic Statistics (timeline_live, last 7 days)")
print("=" * 80)
print()
print(f"  {'Score':<12} {'Count':>7} {'Min':>7} {'Max':>7} {'Mean':>7} {'Median':>7} {'Std':>7}")
print(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")

stats_summary = {}
for sc in SCORE_COLS:
    if sc in df_recent.columns:
        vals = pd.to_numeric(df_recent[sc], errors="coerce").dropna()
        filtered = len(vals) - len(vals[(vals >= 0) & (vals <= 100)])
        vals = vals[(vals >= 0) & (vals <= 100)]
        if filtered > 0:
            print(f"    ℹ️  {sc}: Filtered out {filtered} invalid rows (<0 or >100)")
        if len(vals) > 0:
            stats_summary[sc] = {
                "count": len(vals),
                "min": vals.min(),
                "max": vals.max(),
                "mean": vals.mean(),
                "median": vals.median(),
                "std": vals.std(),
                "p25": vals.quantile(0.25),
                "p75": vals.quantile(0.75),
                "p90": vals.quantile(0.90),
            }
            print(f"  {sc:<12} {len(vals):>7} {vals.min():>7.2f} {vals.max():>7.2f} "
                  f"{vals.mean():>7.2f} {vals.median():>7.2f} {vals.std():>7.2f}")
        else:
            print(f"  {sc:<12} (no data)")
    else:
        print(f"  {sc:<12} (column missing)")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: Histogram Distribution
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 2 — Histogram Distribution (% of scans in each bucket)")
print("=" * 80)

BUCKETS = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50),
           (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]

print()
header = f"  {'Score':<10}"
for low, high in BUCKETS:
    header += f"{low:>3}-{high:<3}  "
print(header)
print(f"  {'-'*10}" + "  ".join(["-"*6 for _ in BUCKETS]))

for sc in SCORE_COLS:
    if sc not in df_recent.columns:
        continue
    vals = pd.to_numeric(df_recent[sc], errors="coerce").dropna()
    vals = vals[(vals >= 0) & (vals <= 100)]
    if len(vals) == 0:
        continue

    total = len(vals)
    line = f"  {sc:<10}"
    for low, high in BUCKETS:
        count = ((vals >= low) & (vals < high)).sum()
        pct = count / total * 100
        line += f" {pct:>5.1f}% "
    print(line)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: Visual Histogram (per score)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 3 — Visual Histogram (each bucket 0-10, 10-20, ...)")
print("=" * 80)

for sc in SCORE_COLS:
    if sc not in df_recent.columns:
        continue
    vals = pd.to_numeric(df_recent[sc], errors="coerce").dropna()
    filtered = len(vals) - len(vals[(vals >= 0) & (vals <= 100)])
    vals = vals[(vals >= 0) & (vals <= 100)]
    if len(vals) == 0:
        continue

    print(f"\n  🎯 {sc} (n={len(vals)}, filtered={filtered})")
    total = len(vals)
    for low, high in BUCKETS:
        count = ((vals >= low) & (vals < high)).sum()
        pct = count / total * 100
        bar = "█" * int(pct / 2)  # scale: 50% = 25 chars
        print(f"    {low:>3}-{high:<3}  {count:>5} ({pct:>5.1f}%) {bar}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: Percentile Analysis
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 4 — Percentiles (what score is at each %)")
print("=" * 80)

percentiles = [10, 25, 50, 75, 90, 95, 99]
print()
header = f"  {'Score':<10}"
for p in percentiles:
    header += f"p{p:>3}  "
print(header)
print(f"  {'-'*10}" + "  ".join(["-"*5 for _ in percentiles]))

for sc in SCORE_COLS:
    if sc not in df_recent.columns:
        continue
    vals = pd.to_numeric(df_recent[sc], errors="coerce").dropna()
    vals = vals[(vals >= 0) & (vals <= 100)]
    if len(vals) == 0:
        continue

    line = f"  {sc:<10}"
    for p in percentiles:
        val = vals.quantile(p / 100)
        line += f"{val:>5.1f} "
    print(line)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: Concentration Analysis
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 5 — Concentration Analysis (how 'spread out' is each score)")
print("=" * 80)

print()
print("  How much of the range (0-100) does each score ACTUALLY use?")
print(f"  {'Score':<10} {'Range Used':>12} {'%Used':>7} {'Spread Quality':<20}")
print(f"  {'-'*10} {'-'*12} {'-'*7} {'-'*20}")

for sc in SCORE_COLS:
    if sc not in df_recent.columns:
        continue
    vals = pd.to_numeric(df_recent[sc], errors="coerce").dropna()
    vals = vals[(vals >= 0) & (vals <= 100)]
    if len(vals) == 0:
        continue

    # Range used = p90 - p10 (removes outliers)
    p10 = vals.quantile(0.10)
    p90 = vals.quantile(0.90)
    range_used = p90 - p10
    pct_used = range_used / 100 * 100  # as % of total 0-100 scale
    
    # Quality assessment
    if pct_used >= 50:
        quality = "✅ Good spread"
    elif pct_used >= 30:
        quality = "🟡 Moderate spread"
    else:
        quality = "❌ Compressed!"
    
    print(f"  {sc:<10} {p10:.1f}-{p90:.1f}    {pct_used:>5.1f}%  {quality}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 6: Rescaling Potential
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 6 — Rescaling Potential (what could improve)")
print("=" * 80)

print()
print("  If we rescale each score so p10=0 and p90=100:")
print(f"  {'Score':<10} {'Current':>15} {'After Rescale':>20}")

for sc in SCORE_COLS:
    if sc not in df_recent.columns:
        continue
    vals = pd.to_numeric(df_recent[sc], errors="coerce").dropna()
    vals = vals[(vals >= 0) & (vals <= 100)]
    if len(vals) == 0:
        continue

    current_range = f"{vals.min():.1f}-{vals.max():.1f}"
    p10 = vals.quantile(0.10)
    p90 = vals.quantile(0.90)
    # After rescaling, everyone from p10 to p90 maps to 0-100
    after = f"p10→0, p90→100 (x{100/(p90-p10):.1f})" if p90 > p10 else "no spread"
    
    print(f"  {sc:<10} {current_range:>15} {after:>20}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 7: Comparison with post_analysis (historical)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("📊 SECTION 7 — post_analysis Historical (recalc'd yesterday)")
print("=" * 80)

if "audit_flag" in df_pa.columns:
    clean_pa = df_pa[df_pa["audit_flag"] == "CLEAN"]
    print(f"\n  Using {len(clean_pa)} CLEAN rows only (ground truth)")
    
    print()
    print(f"  {'Score':<10} {'Min':>7} {'Mean':>7} {'Max':>7} {'Spread':>7}")
    print(f"  {'-'*10} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    
    for sc in SCORE_COLS:
        if sc not in clean_pa.columns:
            continue
        vals = pd.to_numeric(clean_pa[sc], errors="coerce").dropna()
        if len(vals) == 0:
            continue
        spread = vals.max() - vals.min()
        print(f"  {sc:<10} {vals.min():>7.2f} {vals.mean():>7.2f} {vals.max():>7.2f} {spread:>7.2f}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 8: Summary & Recommendations
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🎯 SUMMARY & RECOMMENDATIONS")
print("=" * 80)

print("\n  Question to answer:")
print("  Does each score use the full 0-100 scale or is it compressed?")
print()

# Identify compressed scores
compressed = []
for sc in SCORE_COLS:
    if sc in stats_summary:
        s = stats_summary[sc]
        if s["max"] < 80 or s["mean"] < 30:
            compressed.append((sc, s["min"], s["max"], s["mean"]))

if compressed:
    print("  ⚠️  Compressed scores (not using full range):")
    for sc, mn, mx, me in compressed:
        print(f"     {sc}: {mn:.1f}-{mx:.1f} (mean {me:.1f})")
else:
    print("  ✅ All scores use good portion of 0-100")

print("\n  Rescaling approaches to consider:")
print("  1. Lower caps (simple) - adjust /200 to /100 etc for each metric")
print("  2. Percentile-based - daily normalization against other stocks")
print("  3. Non-linear - log/sqrt scaling for exponential distributions")

print("\n" + "=" * 80)
print(f"✅ Analysis completed at {datetime.now(PERU_TZ).strftime('%H:%M:%S')} Peru")
print("=" * 80)
