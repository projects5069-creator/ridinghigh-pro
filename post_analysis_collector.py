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
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import sys
import os
import time

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets

PERU_TZ = pytz.timezone("America/Lima")

CATALYST_CATEGORIES = [
    "merger_acquisition", "fda_approval", "clinical_trial",
    "marketing_announcement", "earnings_report", "regulatory_compliance",
    "lawsuit", "share_dilution", "reverse_split", "no_clear_reason"
]

MIN_SCORE   = 60
DAYS_FORWARD = 5

SCORE_SUBTYPES = ["Score_B", "Score_C", "Score_D", "Score_E", "Score_F", "Score_G", "Score_H", "Score_I"]


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
def get_trading_days_after(scan_date_str: str, n: int) -> list:
    import sheets_manager
    return sheets_manager.trading_days_after(scan_date_str, n)


def is_day_complete(date_str: str) -> bool:
    """
    True when the full trading day for date_str has closed (market close = 15:00 Peru).
    - Past weekdays: always complete.
    - Today: complete only after 15:00 Peru.
    - Future or weekends: never complete.
    """
    now_peru  = datetime.now(PERU_TZ)
    today     = now_peru.date()
    day       = datetime.strptime(date_str, "%Y-%m-%d").date()
    if day.weekday() >= 5:
        return False
    if day < today:
        return True
    if day == today:
        return now_peru.hour >= 15   # after market close
    return False


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
    for attempt in range(1, 6):
        try:
            start   = trading_days[0]
            end_dt  = datetime.strptime(trading_days[-1], "%Y-%m-%d") + timedelta(days=3)
            hist    = yf.download(ticker, start=start, end=end_dt.strftime("%Y-%m-%d"),
                                  progress=False, auto_adjust=True)
            if hist.empty:
                time.sleep(2); continue
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            hist.index = pd.to_datetime(hist.index).strftime("%Y-%m-%d")
            result = {}
            for i, day in enumerate(trading_days, 1):
                if day in hist.index:
                    row = hist.loc[day]
                    result[f"D{i}_Open"]  = round(float(row["Open"]), 4)
                    result[f"D{i}_High"]  = round(float(row["High"]), 4)
                    result[f"D{i}_Low"]   = round(float(row["Low"]), 4)
                    result[f"D{i}_Close"] = round(float(row["Close"]), 4)
                else:
                    for suffix in ["Open","High","Low","Close"]:
                        result[f"D{i}_{suffix}"] = None
            return result
        except Exception as e:
            print(f"[Collector] {ticker} attempt {attempt} error: {e}")
            time.sleep(2)
    return {}


def calculate_stats(scan_price: float, ohlc: dict) -> dict:
    lows = [(i, ohlc[f"D{i}_Low"]) for i in range(1,6) if ohlc.get(f"D{i}_Low") is not None]
    if not lows or scan_price <= 0:
        return {"MaxDrop%": None, "BestDay": None, "TP10_Hit": None, "TP15_Hit": None, "TP20_Hit": None, "D1_Gap%": None}
    best_day, min_low = min(lows, key=lambda x: x[1])
    max_drop = round((min_low - scan_price) / scan_price * 100, 2)
    d1_open  = ohlc.get("D1_Open")
    d1_gap   = round((d1_open - scan_price) / scan_price * 100, 2) if d1_open and scan_price > 0 else None
    return {
        "MaxDrop%": max_drop, "BestDay": best_day,
        "TP10_Hit": 1 if min_low <= scan_price * 0.90 else 0,
        "TP15_Hit": 1 if min_low <= scan_price * 0.85 else 0,
        "TP20_Hit": 1 if min_low <= scan_price * 0.80 else 0,
        "D1_Gap%":  d1_gap,
        "SL7_Hit_D1": 1 if ohlc.get("D1_High") and ohlc["D1_High"] >= scan_price * 1.07 else 0,
        "IntraDay_SL": 1 if any(ohlc.get(f"D{i}_High", 0) and ohlc[f"D{i}_High"] >= scan_price * 1.07 for i in range(1,6)) else 0,
    }


# ── NEW: D0 OHLC + fundamental data ──────────────────────────────────────────
def fetch_d0_and_fundamental(ticker: str, scan_date: str) -> dict:
    result = {}
    try:
        stock  = yf.Ticker(ticker)
        scan_dt = datetime.strptime(scan_date, "%Y-%m-%d")
        start  = (scan_dt - timedelta(days=60)).strftime("%Y-%m-%d")
        end    = (scan_dt + timedelta(days=2)).strftime("%Y-%m-%d")
        hist   = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        hist.index = pd.to_datetime(hist.index).strftime("%Y-%m-%d")

        # D0 OHLC
        if scan_date in hist.index:
            row = hist.loc[scan_date]
            result["D0_Open"] = round(float(row["Open"]), 4)
            result["D0_High"] = round(float(row["High"]), 4)
            result["D0_Low"]  = round(float(row["Low"]), 4)
            if float(row["High"]) > 0:
                result["D0_Drop%_from_High"] = round(
                    (float(row["Close"]) - float(row["High"])) / float(row["High"]) * 100, 2)

        # SMA20
        hist_before = hist[hist.index <= scan_date]
        if len(hist_before) >= 20:
            sma20 = hist_before["Close"].iloc[-20:].mean()
            scan_close = hist_before["Close"].iloc[-1]
            result["Price_vs_SMA20"] = round(
                (float(scan_close) - float(sma20)) / float(sma20) * 100, 2)

        # Consecutive up days
        hist_pre = hist[hist.index < scan_date]
        if len(hist_pre) >= 2:
            consec, closes = 0, hist_pre["Close"].values
            for i in range(len(closes)-1, 0, -1):
                if closes[i] > closes[i-1]: consec += 1
                else: break
            result["Consecutive_Up"] = consec

        # Fundamental from Yahoo
        info = stock.info
        float_shares = info.get("floatShares", None)
        if float_shares:
            result["RealFloat"]   = int(float_shares)
            result["RealFloat_M"] = round(float_shares / 1_000_000, 2)
        result["Sector"]   = info.get("sector", "")
        result["Industry"] = info.get("industry", "")
        mc = info.get("marketCap", 0) or 0
        result["MarketCapCategory"] = "Micro" if mc < 300_000_000 else ("Small" if mc < 2_000_000_000 else "Mid+")
        ipo = info.get("firstTradeDateEpochUtc", None)
        if ipo:
            result["DaysSinceIPO"] = (scan_dt - datetime.fromtimestamp(ipo)).days

    except Exception as e:
        print(f"[Collector] D0/fundamental error for {ticker}: {e}")
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
        # Score_B-I from the peak-score row
        peak_row = day.loc[day["Score"].idxmax()]
        for st in SCORE_SUBTYPES:
            if st in peak_row.index:
                val = pd.to_numeric(peak_row[st], errors="coerce")
                if pd.notna(val):
                    result[st] = round(float(val), 2)
    except Exception as e:
        print(f"[Collector] Timeline error for {ticker} {scan_date}: {e}")
    return result


def is_trading_day(date=None):
    if date is None: date = datetime.now(PERU_TZ).date()
    try:
        import pandas_market_calendars as mcal
        nyse = mcal.get_calendar("NASDAQ")
        return not nyse.schedule(start_date=date.strftime("%Y-%m-%d"),
                                  end_date=date.strftime("%Y-%m-%d")).empty
    except Exception:
        return date.weekday() < 5


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
        print("[Collector] ⚠️ No candidates found — check that daily_snapshots has Score>=60 stocks")
        return

    # Load timeline_live for stats
    print("[Collector] Loading timeline_live...")
    ws_tl   = sheets_manager.get_worksheet("timeline_live", gc=gc)
    tl_data = ws_tl.get_all_values() if ws_tl else []
    tl_df   = pd.DataFrame(tl_data[1:], columns=tl_data[0]) if len(tl_data) > 1 else pd.DataFrame()
    # Sheet header may be stale — enforce canonical column names so Score_B-I are accessible
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

        # Score metrics
        metric_fields = ["MxV", "RunUp", "RSI", "ATRX", "REL_VOL", "Gap", "VWAP",
                         "PriceToHigh", "PriceTo52WHigh", "Float%",
                         "Score_I", "Score_B", "Score_C", "Score_D",
                         "Score_E", "Score_F", "Score_G", "Score_H"]
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
                           ("VWAP_price_raw", "VWAP_price"),
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
                raw_inputs["MxV_calc"] = round(((mc - (pr * vol)) / mc) * 100, 2)
        except: pass
        try:
            avg_vol = raw_inputs.get("AvgVolume_raw") or 0
            if avg_vol > 0 and vol > 0:
                raw_inputs["REL_VOL_calc"] = round(vol / avg_vol, 2)
        except: pass
        try:
            op = raw_inputs.get("Open_price_raw") or 0
            if op > 0 and pr > 0:
                raw_inputs["RunUp_calc"] = round(((pr - op) / op) * 100, 2)
        except: pass
        try:
            pc = raw_inputs.get("PrevClose_raw") or 0
            op = raw_inputs.get("Open_price_raw") or 0
            if pc > 0 and op > 0:
                raw_inputs["Gap_calc"] = round(((op - pc) / pc) * 100, 2)
        except: pass
        try:
            h   = raw_inputs.get("High_today_raw") or 0
            l   = raw_inputs.get("Low_today_raw") or 0
            atr = raw_inputs.get("ATR14_raw") or 0
            if atr > 0 and h > 0 and l > 0:
                raw_inputs["ATRX_calc"] = round((h - l) / atr, 2)
        except: pass
        try:
            vp = raw_inputs.get("VWAP_price_raw") or 0
            if vp > 0 and pr > 0:
                raw_inputs["VWAP_calc"] = round(((pr / vp) - 1) * 100, 2)
        except: pass

        # D0 + fundamental (לא למניות של היום — עוד לא יש נתונים)
        d0_fund = fetch_d0_and_fundamental(ticker, scan_date) if not is_today else {}

        # Timeline stats (also populates Score_B-I from peak row)
        tl_stats = fetch_timeline_stats(ticker, scan_date, tl_df) if not tl_df.empty else {}

        # Enrich metrics with Score_B-I from timeline peak row (overrides NaN from daily_snapshots)
        for st in SCORE_SUBTYPES:
            if st in tl_stats:
                metrics[st] = tl_stats.pop(st)

        # Catalyst (לא למניות של היום — חוסך זמן)
        if existing_match.empty and not is_today:
            catalyst_data = analyze_catalyst(ticker, scan_date)
        elif not existing_match.empty:
            catalyst_data = {f"cat_{cat}": existing_match.iloc[0].get(f"cat_{cat}", 0)
                             for cat in CATALYST_CATEGORIES}
        else:
            catalyst_data = {f"cat_{cat}": 0 for cat in CATALYST_CATEGORIES}

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
