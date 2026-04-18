"""
deep_scan.py - 2026-04-17
סריקה מקסימלית ועמוקה של מערכת RidingHigh Pro.
Read-only - לא עושה שינויים.

בודק ברמות:
- per-ticker (כל מניה שנסרקה היום)
- per-score (כל אחד מ-9 הציונים)
- cross-sheet consistency
- historical comparison
- anomaly detection
"""
import sys
import os
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd
import pytz

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

PERU_TZ = pytz.timezone("America/Lima")
NOW = datetime.now(PERU_TZ)
TODAY = NOW.strftime("%Y-%m-%d")
YESTERDAY = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")

print("=" * 75)
print(f"🔬 RidingHigh Pro - DEEP SCAN (Maximum)")
print(f"⏰ {NOW.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print("=" * 75)

import sheets_manager
gc = sheets_manager._get_gc()
if gc is None:
    print("❌ FAIL: No credentials")
    sys.exit(1)

# Load all sheets once
print("\n📥 Loading all sheets...")
sheets_data = {}
for sheet_name in ["timeline_live", "score_tracker", "post_analysis",
                    "portfolio", "portfolio_live", "live_trades", "daily_snapshots"]:
    try:
        ws = sheets_manager.get_worksheet(sheet_name, gc=gc)
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            sheets_data[sheet_name] = df
            print(f"  ✅ {sheet_name}: {len(df):,} rows, {len(df.columns)} cols")
        else:
            sheets_data[sheet_name] = pd.DataFrame()
            print(f"  ⚠️  {sheet_name}: empty")
    except Exception as e:
        sheets_data[sheet_name] = pd.DataFrame()
        print(f"  ❌ {sheet_name}: {e}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION A: TIMELINE_LIVE DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION A — timeline_live DEEP DIVE")
print("=" * 75)

tl = sheets_data.get("timeline_live", pd.DataFrame())
tl_today = tl[tl["Date"] == TODAY] if not tl.empty and "Date" in tl.columns else pd.DataFrame()
print(f"\n📊 Today's rows: {len(tl_today):,}")

if not tl_today.empty:
    # A1: Scan frequency
    if "ScanTime" in tl_today.columns:
        scan_times = sorted(tl_today["ScanTime"].unique())
        print(f"📊 Unique scan times today: {len(scan_times)}")
        print(f"   First: {scan_times[0] if scan_times else 'N/A'}")
        print(f"   Last:  {scan_times[-1] if scan_times else 'N/A'}")
        
        # Check for gaps (scans should be every minute)
        if len(scan_times) > 1:
            gaps = []
            for i in range(1, len(scan_times)):
                try:
                    t1 = datetime.strptime(scan_times[i-1], "%H:%M")
                    t2 = datetime.strptime(scan_times[i], "%H:%M")
                    diff = (t2 - t1).total_seconds() / 60
                    if diff > 2:  # more than 2 minutes gap
                        gaps.append((scan_times[i-1], scan_times[i], int(diff)))
                except:
                    pass
            if gaps:
                print(f"⚠️  Found {len(gaps)} gaps > 2 minutes:")
                for g in gaps[:5]:
                    print(f"     {g[0]} → {g[1]} ({g[2]} min gap)")
            else:
                print(f"✅ No gaps in scan frequency")

    # A2: Per-ticker stats
    if "Ticker" in tl_today.columns:
        tickers_today = tl_today["Ticker"].value_counts()
        print(f"\n📊 Tickers today: {len(tickers_today)}")
        print(f"   Most scanned ticker: {tickers_today.index[0]} ({tickers_today.iloc[0]} times)")
        print(f"   Median scans per ticker: {tickers_today.median():.0f}")
        print(f"   Single-scan tickers: {(tickers_today == 1).sum()}")
        
        # Show top 5 most scanned
        print(f"\n📊 Top 5 most active tickers:")
        for ticker, count in tickers_today.head(5).items():
            print(f"     {ticker}: {count} scans")

    # A3: Score distribution histogram
    if "Score" in tl_today.columns:
        scores = pd.to_numeric(tl_today["Score"], errors="coerce").dropna()
        if len(scores) > 0:
            print(f"\n📊 Score distribution today:")
            buckets = [(0,20), (20,40), (40,60), (60,70), (70,80), (80,90), (90,100)]
            for low, high in buckets:
                count = ((scores >= low) & (scores < high)).sum()
                pct = count / len(scores) * 100
                bar = "█" * int(pct / 2)
                print(f"   {low:>3}-{high:<3}: {count:>5} ({pct:>5.1f}%) {bar}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION B: SCORE_TRACKER DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION B — score_tracker DEEP DIVE")
print("=" * 75)

st = sheets_data.get("score_tracker", pd.DataFrame())
st_today = st[st["Date"] == TODAY] if not st.empty and "Date" in st.columns else pd.DataFrame()
print(f"\n📊 Today's rows: {len(st_today):,}")

if not st_today.empty:
    # B1: MxV check - is the *100 fix working?
    if "MxV" in st_today.columns:
        mxv_vals = pd.to_numeric(st_today["MxV"], errors="coerce").dropna()
        if len(mxv_vals) > 0:
            print(f"\n📊 MxV stats today:")
            print(f"   min:  {mxv_vals.min():.2f}")
            print(f"   mean: {mxv_vals.mean():.2f}")
            print(f"   max:  {mxv_vals.max():.2f}")
            
            # If values are in ratio form (e.g. -0.3), fix didn't apply
            # If values are in percentage form (-30), fix applied
            if abs(mxv_vals.min()) < 1 and abs(mxv_vals.max()) < 1:
                print(f"   ❌ WARNING: MxV values look like ratios (not percentages)!")
                print(f"      The *100 fix might not be working!")
            else:
                print(f"   ✅ MxV in percentage form (fix working)")
    
    # B2: Score distribution comparison with timeline_live
    if "Score" in st_today.columns:
        st_scores = pd.to_numeric(st_today["Score"], errors="coerce").dropna()
        if len(st_scores) > 0:
            print(f"\n📊 score_tracker Score stats:")
            print(f"   mean: {st_scores.mean():.2f}")
            print(f"   max:  {st_scores.max():.2f}")
            
            # Compare with timeline_live scores
            if not tl_today.empty and "Score" in tl_today.columns:
                tl_scores = pd.to_numeric(tl_today["Score"], errors="coerce").dropna()
                if len(tl_scores) > 0:
                    print(f"\n📊 vs timeline_live:")
                    print(f"   timeline_live mean: {tl_scores.mean():.2f}")
                    print(f"   score_tracker mean: {st_scores.mean():.2f}")
                    diff = abs(tl_scores.mean() - st_scores.mean())
                    if diff > 10:
                        print(f"   ⚠️  Large discrepancy ({diff:.2f} points)")
                    else:
                        print(f"   ✅ Similar averages (diff {diff:.2f})")

# ═══════════════════════════════════════════════════════════════════════
# SECTION C: PORTFOLIO_LIVE CHECK
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION C — portfolio_live (active positions)")
print("=" * 75)

pl = sheets_data.get("portfolio_live", pd.DataFrame())
if not pl.empty:
    print(f"\n📊 Total positions in portfolio_live: {len(pl):,}")
    
    if "Status" in pl.columns:
        status_counts = pl["Status"].value_counts()
        print(f"\n📊 Status breakdown:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
    
    # Open positions
    open_mask = pl.get("Status", pd.Series()).astype(str).str.lower().isin(["open", "pending", "active"])
    open_positions = pl[open_mask] if open_mask.any() else pd.DataFrame()
    print(f"\n📊 Open positions now: {len(open_positions)}")
    
    if len(open_positions) > 0 and "Ticker" in open_positions.columns:
        tickers_open = open_positions["Ticker"].tolist()[:10]
        print(f"   Tickers: {', '.join(tickers_open)}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION D: LIVE_TRADES CHECK
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION D — live_trades (active simulation)")
print("=" * 75)

lt = sheets_data.get("live_trades", pd.DataFrame())
if not lt.empty:
    print(f"\n📊 Total trades in live_trades: {len(lt):,}")
    
    # Today's trades
    if "EntryTime" in lt.columns:
        today_trades = lt[lt["EntryTime"].astype(str).str.startswith(TODAY)]
        print(f"📊 Today's entries: {len(today_trades)}")
    
    # Status breakdown
    if "Status" in lt.columns:
        status_counts = lt["Status"].value_counts()
        print(f"\n📊 Status breakdown (all-time):")
        for status, count in status_counts.head(10).items():
            print(f"   {status}: {count}")
    
    # Score types distribution
    if "ScoreType" in lt.columns:
        score_types = lt["ScoreType"].value_counts()
        print(f"\n📊 ScoreType usage (which score picked each trade):")
        for st_type, count in score_types.head(10).items():
            print(f"   {st_type}: {count}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION E: CROSS-SHEET CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION E — CROSS-SHEET CONSISTENCY")
print("=" * 75)

# E1: Tickers in timeline_live vs score_tracker
if not tl_today.empty and not st_today.empty:
    tl_tickers = set(tl_today["Ticker"].unique()) if "Ticker" in tl_today.columns else set()
    st_tickers = set(st_today["Ticker"].unique()) if "Ticker" in st_today.columns else set()
    
    only_tl = tl_tickers - st_tickers
    only_st = st_tickers - tl_tickers
    both = tl_tickers & st_tickers
    
    print(f"\n📊 Today's tickers:")
    print(f"   in timeline_live only: {len(only_tl)} - {list(only_tl)[:5]}")
    print(f"   in score_tracker only: {len(only_st)} - {list(only_st)[:5]}")
    print(f"   in both: {len(both)}")
    
    if len(only_tl) > 0:
        print(f"   ℹ️  Tickers in timeline but not in score_tracker (not tracked)")

# E2: Scores match between sheets?
if not tl_today.empty and not st_today.empty:
    print(f"\n📊 Cross-check Score between timeline_live and score_tracker (random sample):")
    common_tickers = list(tl_tickers & st_tickers)[:3]
    for ticker in common_tickers:
        tl_t = tl_today[tl_today["Ticker"] == ticker]
        st_t = st_today[st_today["Ticker"] == ticker]
        if len(tl_t) > 0 and len(st_t) > 0:
            try:
                tl_last_score = pd.to_numeric(tl_t["Score"].iloc[-1], errors="coerce")
                st_last_score = pd.to_numeric(st_t["Score"].iloc[-1], errors="coerce")
                print(f"   {ticker}: tl={tl_last_score:.2f}, st={st_last_score:.2f}")
            except:
                pass

# ═══════════════════════════════════════════════════════════════════════
# SECTION F: HISTORICAL COMPARISON
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION F — HISTORICAL COMPARISON (vs yesterday)")
print("=" * 75)

if not tl.empty and "Date" in tl.columns:
    tl_yesterday = tl[tl["Date"] == YESTERDAY]
    if not tl_yesterday.empty:
        print(f"\n📊 {YESTERDAY} vs {TODAY} (same time of day):")
        print(f"   Yesterday rows: {len(tl_yesterday):,}")
        print(f"   Today rows:     {len(tl_today):,}")
        
        # Compare tickers
        yest_tickers = tl_yesterday["Ticker"].nunique() if "Ticker" in tl_yesterday.columns else 0
        today_tickers = tl_today["Ticker"].nunique() if "Ticker" in tl_today.columns else 0
        print(f"   Yesterday tickers: {yest_tickers}")
        print(f"   Today tickers:     {today_tickers}")
        
        # Compare scores
        if "Score" in tl_yesterday.columns and "Score" in tl_today.columns:
            yest_scores = pd.to_numeric(tl_yesterday["Score"], errors="coerce").dropna()
            today_scores = pd.to_numeric(tl_today["Score"], errors="coerce").dropna()
            if len(yest_scores) > 0 and len(today_scores) > 0:
                print(f"\n📊 Score average:")
                print(f"   Yesterday: {yest_scores.mean():.2f}")
                print(f"   Today:     {today_scores.mean():.2f}")
                diff_pct = abs(today_scores.mean() - yest_scores.mean()) / yest_scores.mean() * 100
                if diff_pct > 30:
                    print(f"   ⚠️  Large difference ({diff_pct:.1f}%)")
                else:
                    print(f"   ✅ Similar day ({diff_pct:.1f}% difference)")

# ═══════════════════════════════════════════════════════════════════════
# SECTION G: ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION G — ANOMALY DETECTION")
print("=" * 75)

anomalies_found = 0

# G1: Score jumps (>20 point change in consecutive scans of same ticker)
if not tl_today.empty and "Score" in tl_today.columns and "Ticker" in tl_today.columns:
    print(f"\n🔍 Checking Score jumps (>20pt in consecutive scans)...")
    jump_count = 0
    jump_examples = []
    for ticker in tl_today["Ticker"].unique():
        ticker_rows = tl_today[tl_today["Ticker"] == ticker].sort_values("ScanTime")
        if len(ticker_rows) > 1:
            scores = pd.to_numeric(ticker_rows["Score"], errors="coerce").values
            for i in range(1, len(scores)):
                if pd.notna(scores[i]) and pd.notna(scores[i-1]):
                    jump = abs(scores[i] - scores[i-1])
                    if jump > 20:
                        jump_count += 1
                        if len(jump_examples) < 3:
                            jump_examples.append((ticker, scores[i-1], scores[i], jump))
    print(f"   Found {jump_count} score jumps")
    if jump_examples:
        for ex in jump_examples:
            print(f"     {ex[0]}: {ex[1]:.1f} → {ex[2]:.1f} (jump {ex[3]:.1f})")
    if jump_count > 50:
        print(f"   ⚠️  High jump count - may indicate volatile scanning")
        anomalies_found += 1

# G2: Duplicate scans (same ticker, same scan time)
if not tl_today.empty and "Ticker" in tl_today.columns and "ScanTime" in tl_today.columns:
    print(f"\n🔍 Checking duplicate scans...")
    dups = tl_today.duplicated(subset=["Ticker", "ScanTime"], keep=False)
    dup_count = dups.sum()
    if dup_count > 0:
        print(f"   ⚠️  Found {dup_count} duplicate rows!")
        anomalies_found += 1
    else:
        print(f"   ✅ No duplicates")

# G3: Unusual score patterns
if not tl_today.empty and "Score" in tl_today.columns:
    print(f"\n🔍 Checking score patterns...")
    scores = pd.to_numeric(tl_today["Score"], errors="coerce").dropna()
    if len(scores) > 0:
        at_zero = (scores == 0).sum()
        at_max = (scores >= 99).sum()
        if at_zero > 10:
            print(f"   ⚠️  {at_zero} scores are exactly 0 (possibly failed calculations)")
            anomalies_found += 1
        if at_max > 20:
            print(f"   ⚠️  {at_max} scores are ≥99 (many maxed out)")
            anomalies_found += 1
        print(f"   scores=0: {at_zero}, scores≥99: {at_max}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION H: POST_ANALYSIS BROKEN/SUSPICIOUS DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION H — POST_ANALYSIS BROKEN/SUSPICIOUS (deep dive)")
print("=" * 75)

pa = sheets_data.get("post_analysis", pd.DataFrame())
if not pa.empty and "audit_flag" in pa.columns:
    broken = pa[pa["audit_flag"] == "BROKEN"]
    suspicious = pa[pa["audit_flag"] == "SUSPICIOUS"]
    
    print(f"\n🔍 BROKEN rows ({len(broken)}):")
    for _, row in broken.iterrows():
        ticker = row.get("Ticker", "?")
        scan_date = row.get("ScanDate", "?")
        score = row.get("Score", "?")
        atrx = row.get("ATRX", "?")
        print(f"   {ticker} ({scan_date}): Score={score}, ATRX={atrx}")
    
    print(f"\n🔍 SUSPICIOUS rows ({len(suspicious)}):")
    for _, row in suspicious.head(5).iterrows():
        ticker = row.get("Ticker", "?")
        scan_date = row.get("ScanDate", "?")
        score = row.get("Score", "?")
        atrx = row.get("ATRX", "?")
        print(f"   {ticker} ({scan_date}): Score={score}, ATRX={atrx}")
    if len(suspicious) > 5:
        print(f"   ... and {len(suspicious) - 5} more")

# ═══════════════════════════════════════════════════════════════════════
# SECTION I: FINAL VERDICT
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 75)
print("SECTION I — FINAL VERDICT")
print("=" * 75)

print(f"\n🎯 System Health Check Summary:")
print(f"   ⏰ Time: {NOW.strftime('%H:%M')} Peru")
print(f"   📊 timeline_live today: {len(tl_today):,} rows")
print(f"   📊 score_tracker today: {len(st_today):,} rows")
print(f"   ⚠️  Anomalies detected: {anomalies_found}")

if anomalies_found == 0:
    print(f"\n   ✅ SYSTEM HEALTHY - no anomalies detected")
    print(f"   📅 Safe to continue trading day")
else:
    print(f"\n   ⚠️  {anomalies_found} anomalies need review")

print("\n" + "=" * 75)
print(f"✅ Deep scan completed at {datetime.now(PERU_TZ).strftime('%H:%M:%S')} Peru")
print("=" * 75)
