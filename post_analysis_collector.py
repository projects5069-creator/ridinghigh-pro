#!/usr/bin/env python3
"""
RidingHigh Pro - Post Analysis Collector v5
Collects comprehensive data for every stock with Score >= 60.

NEW in v5:
  - D0_Open/High/Low from Yahoo Finance
  - D0_Drop%_from_High 
  - RealFloat, RealFloat_M, Sector, Industry, MarketCapCategory
  - Price_vs_SMA20, Consecutive_Up, DaysSinceIPO
  - FirstScanTime, LastScanTime, ScanCount
  - ScoreAtFirst, ScoreAtLast, ScoreMax, ScoreMin, ScoreStd
  - Removed: Float% (was wrong formula)
"""

import argparse
import pandas as pd
from datetime import datetime, timedelta
from data_provider import get_data_provider, get_fundamentals_provider
import pytz
import sys
import os
import time

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets
from formulas import (
    calculate_mxv,
    calculate_runup,
    calculate_atrx,
    calculate_gap,
    calculate_typical_price_dist,
    calculate_rel_vol,
    calculate_score,
)
from utils import (
    is_trading_day,
    is_day_complete,
    get_trading_days_after,
    calculate_stats,
    validate_stock_data,
    PERU_TZ,
)
from config import MIN_SCORE_DISPLAY

CATALYST_CATEGORIES = [
    "merger_acquisition", "fda_approval", "clinical_trial",
    "marketing_announcement", "earnings_report", "regulatory_compliance",
    "lawsuit", "share_dilution", "reverse_split", "no_clear_reason"
]

MIN_SCORE   = MIN_SCORE_DISPLAY
DAYS_FORWARD = 5


# ── Catalyst analysis (unchanged from v4) ────────────────────────────────────
def fetch_finviz_news(ticker: str, scan_date: str) -> list:
    import urllib.request, re
    from datetime import datetime, timedelta
    scan_dt   = datetime.strptime(scan_date, "%Y-%m-%d")
    date_from = scan_dt - timedelta(days=30)
    date_to   = scan_dt + timedelta(days=1)
    for attempt in range(1, 4):
        try:
            url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
            dates  = re.findall(r'width="130"[^>]*>\s*(.*?)\s*</td>', html)
            titles = re.findall(r'class="tab-link-news"[^>]*>\s*(.*?)\s*</a>', html)
            print(f"[Catalyst] {ticker}: found {len(dates)} dates, {len(titles)} titles in HTML")
            relevant = []
            for date_str, title in zip(dates, titles):
                try:
                    d = date_str.strip()
                    # Finviz shows time (e.g. "06:15AM") for same-day news — treat as scan_date
                    if re.match(r'^\d{1,2}:\d{2}', d):
                        pub_dt = scan_dt
                    else:
                        pub_dt = datetime.strptime(d[:9], "%b-%d-%y")
                    if date_from <= pub_dt <= date_to:
                        relevant.append(title.strip().lower())
                except Exception as parse_err:
                    print(f"[Catalyst] {ticker}: date parse failed '{date_str}' → {parse_err}")
                    continue
            print(f"[Catalyst] {ticker}: {len(relevant)} relevant headlines in window {date_from.date()}–{date_to.date()}")
            return relevant
        except Exception as e:
            print(f"[Collector] FINVIZ attempt {attempt}/3 failed: {e}")
            time.sleep(2)
    return []


def analyze_catalyst(ticker: str, scan_date: str) -> dict:
    KEYWORDS = {
        "merger_acquisition":     ["merger","acquisition","acquires","acquired","buyout","takeover","to buy","to acquire"],
        "fda_approval":           ["fda approved","fda approval","fda clearance","fda grants","orphan drug","breakthrough designation","nda approved"],
        "clinical_trial":         ["phase 1","phase 2","phase 3","clinical trial","topline data","trial results"],
        "marketing_announcement": ["partnership","collaboration agreement","license agreement","commercialization","strategic alliance"],
        "earnings_report":        ["earnings report","quarterly results","q1 results","q2 results","q3 results","q4 results","revenue report"],
        "regulatory_compliance":  ["nasdaq compliance","regained compliance","deficiency notice","bid price","non-compliance"],
        "lawsuit":                ["class action","sec charges","sec investigation","securities fraud","lawsuit filed"],
        "share_dilution":         ["public offering","private placement","at-the-market","atm offering","registered direct","capital raise"],
        "reverse_split":          ["reverse stock split","reverse split","1-for-","share consolidation"],
        "no_clear_reason":        []
    }
    headlines = fetch_finviz_news(ticker, scan_date)
    if not headlines:
        result = {f"cat_{k}": 0 for k in CATALYST_CATEGORIES}
        result["cat_no_clear_reason"] = 1
        return result
    combined  = " ".join(headlines)
    cats      = {}
    any_found = False
    for category, keywords in KEYWORDS.items():
        if category == "no_clear_reason": continue
        found = any(kw in combined for kw in keywords)
        cats[f"cat_{category}"] = 1 if found else 0
        if found: any_found = True
    cats["cat_no_clear_reason"] = 0 if any_found else 1
    return cats


# ── OHLC fetch ────────────────────────────────────────────────────────────────
# get_trading_days_after imported from utils
# is_day_complete imported from utils


def is_complete(existing_row: pd.Series, trading_days: list) -> bool:
    """Row is complete when every past trading day has a non-null D{i}_Close."""
    for i, day in enumerate(trading_days, 1):
        if not is_day_complete(day):
            break   # this day and beyond are not yet settled
        val = existing_row.get(f"D{i}_Close", None)
        if val is None or str(val).strip() in ["", "nan", "None"]:
            return False
    return True


def fetch_ohlc_for_days(ticker: str, trading_days: list) -> dict:
    """Fetch D1-D5 OHLC via data_provider (Issue #9 Phase 2 — was yfinance)."""
    provider = get_data_provider()
    for attempt in range(1, 6):
        try:
            # Fetch enough daily bars to cover the trading_days range.
            end_dt = datetime.strptime(trading_days[-1], "%Y-%m-%d") + timedelta(days=3)
            # 15 daily bars buffer covers 5 trading days + weekends
            bars = provider.get_daily_bars(ticker, days=15, end_date=end_dt)
            if bars.empty:
                time.sleep(2); continue
            # Provider returns DatetimeIndex; convert to YYYY-MM-DD strings
            bars = bars.copy()
            bars.index = pd.to_datetime(bars.index).strftime("%Y-%m-%d")
            result = {}
            for i, day in enumerate(trading_days, 1):
                if day in bars.index:
                    row = bars.loc[day]
                    result[f"D{i}_Open"]  = round(float(row["open"]),  4)
                    result[f"D{i}_High"]  = round(float(row["high"]),  4)
                    result[f"D{i}_Low"]   = round(float(row["low"]),   4)
                    result[f"D{i}_Close"] = round(float(row["close"]), 4)
                else:
                    for suffix in ["Open","High","Low","Close"]:
                        result[f"D{i}_{suffix}"] = None
            return result
        except Exception as e:
            print(f"[Collector] {ticker} attempt {attempt} error: {e}")
            time.sleep(2)
    return {}


# calculate_stats imported from utils


# ── NEW: D0 OHLC + fundamental data ──────────────────────────────────────────
def fetch_d0_and_fundamental(ticker: str, scan_date: str) -> dict:
    """
    Fetch D0 OHLC + SMA20 + Consecutive_Up + fundamentals.

    Hybrid strategy (Issue #9 Phase 2):
    - Prices (D0, SMA20, Consecutive_Up) → data_provider (Alpaca)
    - Fundamentals (floatShares, sector, etc.) → fundamentals_provider (yfinance)
    """
    result = {}
    prices_provider = get_data_provider()
    fund_provider = get_fundamentals_provider()
    scan_dt = datetime.strptime(scan_date, "%Y-%m-%d")

    # ── Prices: D0 OHLC + SMA20 + Consecutive_Up ──────────────────────
    try:
        # Fetch ~60 days of history ending 2 days after scan_date
        end_dt = scan_dt + timedelta(days=2)
        bars = prices_provider.get_daily_bars(ticker, days=60, end_date=end_dt)
        if not bars.empty:
            bars = bars.copy()
            bars.index = pd.to_datetime(bars.index).strftime("%Y-%m-%d")

            # D0 OHLC
            if scan_date in bars.index:
                row = bars.loc[scan_date]
                result["D0_Open"] = round(float(row["open"]), 4)
                result["D0_High"] = round(float(row["high"]), 4)
                result["D0_Low"]  = round(float(row["low"]),  4)
                if float(row["high"]) > 0:
                    result["D0_Drop%_from_High"] = round(
                        (float(row["close"]) - float(row["high"])) / float(row["high"]) * 100, 2)

            # SMA20
            hist_before = bars[bars.index <= scan_date]
            if len(hist_before) >= 20:
                sma20 = hist_before["close"].iloc[-20:].mean()
                scan_close = hist_before["close"].iloc[-1]
                result["Price_vs_SMA20"] = round(
                    (float(scan_close) - float(sma20)) / float(sma20) * 100, 2)

            # Consecutive up days
            hist_pre = bars[bars.index < scan_date]
            if len(hist_pre) >= 2:
                consec, closes = 0, hist_pre["close"].values
                for i in range(len(closes)-1, 0, -1):
                    if closes[i] > closes[i-1]: consec += 1
                    else: break
                result["Consecutive_Up"] = consec
    except Exception as e:
        print(f"[Collector] D0/SMA error for {ticker}: {e}")

    # ── Fundamentals from yfinance (via fund_provider) ────────────────
    try:
        fund = fund_provider.get_fundamentals(ticker)
        if fund:
            float_shares = fund.get("float_shares")
            if float_shares:
                result["RealFloat"]   = int(float_shares)
                result["RealFloat_M"] = round(float_shares / 1_000_000, 2)
            result["Sector"]   = fund.get("sector") or ""
            result["Industry"] = fund.get("industry") or ""
            mc = fund.get("market_cap", 0) or 0
            result["MarketCapCategory"] = (
                "Micro" if mc < 300_000_000
                else ("Small" if mc < 2_000_000_000 else "Mid+")
            )
            # DaysSinceIPO from ipo_epoch (added in Phase 2 prep)
            ipo_epoch = fund.get("ipo_epoch")
            if ipo_epoch:
                result["DaysSinceIPO"] = (scan_dt - datetime.fromtimestamp(ipo_epoch)).days
    except Exception as e:
        print(f"[Collector] Fundamentals error for {ticker}: {e}")

    return result


# ── NEW: timeline stats ───────────────────────────────────────────────────────
def fetch_timeline_stats(ticker: str, scan_date: str, tl_df: pd.DataFrame) -> dict:
    result = {}
    try:
        day = tl_df[(tl_df["Ticker"] == ticker) & (tl_df["Date"] == scan_date)].copy()
        if day.empty: return result
        day["Score"] = pd.to_numeric(day["Score"], errors="coerce")
        day = day.dropna(subset=["Score"])
        if day.empty: return result
        if "ScanTime" in day.columns:
            times = day["ScanTime"].tolist()
            result["FirstScanTime"] = times[0]
            result["LastScanTime"]  = times[-1]
        result["ScanCount"]    = len(day)
        result["ScoreAtFirst"] = round(day["Score"].iloc[0], 2)
        result["ScoreAtLast"]  = round(day["Score"].iloc[-1], 2)
        result["ScoreMax"]     = round(day["Score"].max(), 2)
        result["ScoreMin"]     = round(day["Score"].min(), 2)
        result["ScoreStd"]     = round(day["Score"].std(), 2)
        # Build metrics dict from peak row and compute scores fresh using formulas.py
        # (replaces the old copy-from-peak-row logic; ensures scores match current formulas)
        peak_row = day.loc[day["Score"].idxmax()]

        def _safe(field, default=0.0):
            if field not in peak_row.index:
                return default
            v = pd.to_numeric(peak_row[field], errors="coerce")
            return default if pd.isna(v) else float(v)

        peak_metrics = {
            "mxv":                _safe("MxV"),
            "run_up":             _safe("RunUp"),
            "atrx":               _safe("ATRX"),
            "rsi":                _safe("RSI"),
            "rel_vol":            _safe("REL_VOL"),
            "gap":                _safe("Gap"),
            "typical_price_dist": _safe("TypicalPriceDist"),
            "change":             _safe("Change"),
            "float_pct":          _safe("Float%"),
            "price_to_high":      _safe("PriceToHigh"),
            "price_to_52w_high":  _safe("PriceTo52WHigh"),
        }

        # Compute all 9 scores fresh from the peak row's metrics
        # Score_B..I, EntryScore removed in Issue #34
    except Exception as e:
        print(f"[Collector] Timeline error for {ticker} {scan_date}: {e}")
    return result


# is_trading_day imported from utils


# ── Main ──────────────────────────────────────────────────────────────────────
def run(target_date: str = None):
    run_start = datetime.now(PERU_TZ)
    if target_date:
        print(f"[Collector] Starting post-analysis collector v5 (backfill: {target_date})...")
    else:
        print(f"[Collector] Starting post-analysis collector v5 at {run_start.strftime('%Y-%m-%d %H:%M:%S')} Peru time...")
        today = run_start.date()
        if not is_trading_day(today):
            print(f"[Collector] ⛔ {today} not a trading day — skipping.")
            return

    import sheets_manager
    gc = sheets_manager._get_gc()
    if gc is None:
        print("[Collector] ❌ Cannot connect to Google Sheets — GOOGLE_CREDENTIALS_JSON env var missing or invalid")
        return
    print("[Collector] ✅ Google Sheets connected")

    today_str  = run_start.strftime("%Y-%m-%d")          # always the real calendar date
    target_str = target_date if target_date else today_str  # date being processed

    # Load snapshots
    ws = sheets_manager.get_worksheet("daily_snapshots", gc=gc)
    if ws is None:
        print("[Collector] ❌ daily_snapshots worksheet not found — check sheets_config.json")
        return
    data = ws.get_all_values()
    snapshots_df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
    if not snapshots_df.empty:
        snapshots_df["Score"] = pd.to_numeric(snapshots_df.get("Score", 0), errors="coerce")
    print(f"[Collector] daily_snapshots: {len(snapshots_df)} rows")

    # ── Fallback: if daily_snapshots has no rows for today, use timeline_live ──
    has_target_in_snap = (not snapshots_df.empty and
                          not snapshots_df[snapshots_df.get("Date", pd.Series(dtype=str)) == target_str].empty)
    if not has_target_in_snap:
        print(f"[Collector] ⚠️ No rows for {target_str} in daily_snapshots — falling back to timeline_live")
        ws_tl_fb = sheets_manager.get_worksheet("timeline_live", gc=gc)
        tl_raw_fb = ws_tl_fb.get_all_values() if ws_tl_fb else []
        if len(tl_raw_fb) > 1:
            tl_fb = pd.DataFrame(tl_raw_fb[1:], columns=tl_raw_fb[0])
            # Sheet header may be stale — enforce canonical column names
            if len(tl_fb.columns) == len(sheets_manager.TIMELINE_LIVE_COLS):
                tl_fb.columns = sheets_manager.TIMELINE_LIVE_COLS
            tl_fb["Score"] = pd.to_numeric(tl_fb["Score"], errors="coerce")
            tl_target = tl_fb[tl_fb["Date"] == target_str].copy()
            if not tl_target.empty:
                # Peak-score row per ticker from timeline_live
                peak = tl_target.sort_values("Score", ascending=False).drop_duplicates("Ticker").reset_index(drop=True)
                # When backfilling a specific date, use peak rows directly (don't concat
                # with today's daily_snapshots which has different columns / shape).
                if target_date:
                    snapshots_df = peak
                else:
                    snapshots_df = pd.concat([snapshots_df, peak], ignore_index=True)
                print(f"[Collector] ✅ Added {len(peak)} tickers from timeline_live fallback")
            else:
                print(f"[Collector] ❌ timeline_live also has no rows for {target_str}")
        else:
            print("[Collector] ❌ timeline_live is empty")

    if snapshots_df.empty:
        print("[Collector] ❌ No snapshot data available — skipping")
        return

    if target_date:
        snapshots_df = snapshots_df[snapshots_df.get("Date", pd.Series(dtype=str)) == target_str]
        print(f"[Collector] Filtered to {len(snapshots_df)} rows for {target_str}")
    else:
        today_rows = snapshots_df[snapshots_df.get("Date", pd.Series(dtype=str)) == today_str]
        print(f"[Collector] Today ({today_str}) rows available: {len(today_rows)}")

    candidates = snapshots_df[snapshots_df["Score"] >= MIN_SCORE].copy()
    print(f"[Collector] {len(candidates)} stocks with score >= {MIN_SCORE}")
    if candidates.empty:
        print(f"[Collector] ⚠️ No candidates found — check that daily_snapshots has Score>={MIN_SCORE_DISPLAY} stocks")
        return

    # Load timeline_live for stats
    print("[Collector] Loading timeline_live...")
    ws_tl   = sheets_manager.get_worksheet("timeline_live", gc=gc)
    tl_data = ws_tl.get_all_values() if ws_tl else []
    tl_df   = pd.DataFrame(tl_data[1:], columns=tl_data[0]) if len(tl_data) > 1 else pd.DataFrame()
    # Sheet header may be stale — enforce canonical column names
    if not tl_df.empty and len(tl_df.columns) == len(sheets_manager.TIMELINE_LIVE_COLS):
        tl_df.columns = sheets_manager.TIMELINE_LIVE_COLS

    existing_df = load_post_analysis_from_sheets()
    new_rows    = []

    for _, row in candidates.iterrows():
        ticker     = str(row.get("Ticker", "")).strip()
        scan_date  = str(row.get("Date", "")).strip()
        score      = float(row.get("Score", 0))
        scan_price = pd.to_numeric(row.get("Price", 0), errors="coerce") or 0

        if not ticker or not scan_date: continue
        is_today = (scan_date == today_str)   # True only for the real calendar today

        trading_days = get_trading_days_after(scan_date, DAYS_FORWARD)
        existing_match = pd.DataFrame()
        if not existing_df.empty and "Ticker" in existing_df.columns:
            existing_match = existing_df[
                (existing_df["Ticker"] == ticker) & (existing_df["ScanDate"] == scan_date)]

        if not existing_match.empty and is_complete(existing_match.iloc[0], trading_days):
            print(f"[Collector] Complete: {ticker} {scan_date} — skipping")
            continue

        # מניות של היום — נכנסות עם ScanPrice בלבד, בלי OHLC
        if is_today and not existing_match.empty:
            print(f"[Collector] Today's stock already exists: {ticker} {scan_date} — skipping")
            continue

        print(f"[Collector] Processing {ticker} {scan_date}...")
        # Only fetch OHLC for days that are fully settled (strictly before today Peru TZ)
        available_days = [d for d in trading_days if is_day_complete(d)]
        ohlc  = fetch_ohlc_for_days(ticker, available_days) if available_days and not is_today else {}
        stats = calculate_stats(scan_price, ohlc)

        # Raw metric fields copied from daily_snapshots.
        # Score_B-I removed in Issue #34.
        metric_fields = ["MxV", "RunUp", "RSI", "ATRX", "REL_VOL", "Gap", "TypicalPriceDist",
                         "PriceToHigh", "PriceTo52WHigh", "Float%"]
        metrics = {f: round(pd.to_numeric(row.get(f, None), errors="coerce"), 2)
                   for f in metric_fields}

        # ── Raw inputs for metric validation & future regression ──────────────
        raw_inputs = {}

        for field, col in [("Volume_raw",           "Volume"),
                           ("MarketCap_raw",         "MarketCap"),
                           ("AvgVolume_raw",         "AvgVolume"),
                           ("FloatShares_raw",       "FloatShares"),
                           ("SharesOutstanding_raw", "SharesOutstanding")]:
            val = pd.to_numeric(row.get(col, None), errors="coerce")
            raw_inputs[field] = int(val) if pd.notna(val) and val > 0 else None

        for field, col in [("Open_price_raw", "Open_price"),
                           ("PrevClose_raw",  "PrevClose"),
                           ("High_today_raw", "High_today"),
                           ("Low_today_raw",  "Low_today"),
                           ("TypicalPrice_raw", "TypicalPrice"),
                           ("ATR14_raw",      "ATR14_raw"),
                           ("Week52High_raw", "Week52High")]:
            val = pd.to_numeric(row.get(col, None), errors="coerce")
            raw_inputs[field] = round(float(val), 4) if pd.notna(val) else None

        # Cross-validation recalculations
        try:
            mc  = raw_inputs.get("MarketCap_raw") or 0
            vol = raw_inputs.get("Volume_raw") or 0
            pr  = float(row.get("Price", 0) or 0)
            if mc > 0:
                raw_inputs["MxV_calc"] = round(calculate_mxv(mc, pr, vol), 2)
        except: pass
        try:
            avg_vol = raw_inputs.get("AvgVolume_raw") or 0
            if avg_vol > 0 and vol > 0:
                raw_inputs["REL_VOL_calc"] = round(calculate_rel_vol(vol, avg_vol), 2)
        except: pass
        try:
            op = raw_inputs.get("Open_price_raw") or 0
            if op > 0 and pr > 0:
                raw_inputs["RunUp_calc"] = round(calculate_runup(pr, op), 2)
        except: pass
        try:
            pc = raw_inputs.get("PrevClose_raw") or 0
            op = raw_inputs.get("Open_price_raw") or 0
            if pc > 0 and op > 0:
                raw_inputs["Gap_calc"] = round(calculate_gap(op, pc), 2)
        except: pass
        try:
            h   = raw_inputs.get("High_today_raw") or 0
            l   = raw_inputs.get("Low_today_raw") or 0
            atr = raw_inputs.get("ATR14_raw") or 0
            if atr > 0 and h > 0 and l > 0:
                raw_inputs["ATRX_calc"] = round(calculate_atrx(h, l, atr), 2)
        except: pass
        try:
            vp = raw_inputs.get("TypicalPrice_raw") or 0
            if vp > 0 and pr > 0:
                # Note: uses pre-calculated TypicalPrice_raw, different from formulas.calculate_typical_price_dist
                raw_inputs["TypicalPriceDist_calc"] = round(((pr / vp) - 1) * 100, 2)
        except: pass

        # D0 + fundamental (לא למניות של היום — עוד לא יש נתונים)
        d0_fund = fetch_d0_and_fundamental(ticker, scan_date) if not is_today else {}

        # Timeline stats
        tl_stats = fetch_timeline_stats(ticker, scan_date, tl_df) if not tl_df.empty else {}

        # Catalyst (לא למניות של היום — חוסך זמן)
        if existing_match.empty and not is_today:
            catalyst_data = analyze_catalyst(ticker, scan_date)
        elif not existing_match.empty:
            catalyst_data = {f"cat_{cat}": existing_match.iloc[0].get(f"cat_{cat}", 0)
                             for cat in CATALYST_CATEGORIES}
        else:
            catalyst_data = {f"cat_{cat}": 0 for cat in CATALYST_CATEGORIES}

        # Issue #19: validate data quality before writing
        audit_flag = validate_stock_data(
            price=scan_price,
            week52high=raw_inputs.get("Week52High_raw"),
            atr14=raw_inputs.get("ATR14_raw"),
            high_today=raw_inputs.get("High_today_raw"),
            low_today=raw_inputs.get("Low_today_raw"),
            open_price=raw_inputs.get("Open_price_raw"),
            avg_volume=raw_inputs.get("AvgVolume_raw"),
        )

        new_row = {
            "Ticker":      ticker,
            "ScanDate":    scan_date,
            "Score":       round(float(score), 2),
            "ScanPrice":   round(float(scan_price), 2),
            "ScanChange%": round(pd.to_numeric(row.get("Change", 0), errors="coerce"), 2),
            **metrics,
            **raw_inputs,
            **catalyst_data,
            **{k: round(v, 2) if isinstance(v, float) else v for k, v in ohlc.items()},
            **{k: round(v, 2) if isinstance(v, float) else v for k, v in stats.items()},
            **d0_fund,
            **tl_stats,
            "audit_flag": audit_flag,
        }
        new_rows.append(new_row)
        time.sleep(0.3)

    if not new_rows:
        print("[Collector] No new rows to save"); return

    new_df = pd.DataFrame(new_rows)
    save_post_analysis_to_sheets(new_df)
    print(f"[Collector] ✅ Saved/updated {len(new_rows)} rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post Analysis Collector")
    parser.add_argument("--date", type=str, default=None,
                        help="Backfill a specific date (YYYY-MM-DD). Skips trading-day check.")
    args = parser.parse_args()
    run(target_date=args.date)
