#!/usr/bin/env python3
"""
backfill_ohlc.py
Fills D1-D5 OHLC + stats for all post_analysis rows where D1_Open is missing.
Run once from ~/RidingHighPro:
    python3 backfill_ohlc.py
"""

import sys, os, time
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets
import sheets_manager

PERU_TZ = pytz.timezone("America/Lima")

# ── helpers (same logic as collector) ────────────────────────────────────────

def get_trading_days_after(scan_date_str, n=5):
    return sheets_manager.trading_days_after(scan_date_str, n)

def is_day_complete(date_str):
    now_peru = datetime.now(PERU_TZ)
    today    = now_peru.date()
    day      = datetime.strptime(date_str, "%Y-%m-%d").date()
    if day.weekday() >= 5: return False
    if day < today:        return True
    if day == today:       return now_peru.hour >= 15
    return False

def fetch_ohlc(ticker, trading_days):
    available = [d for d in trading_days if is_day_complete(d)]
    if not available:
        return {}
    for attempt in range(1, 5):
        try:
            end_dt = datetime.strptime(available[-1], "%Y-%m-%d") + timedelta(days=3)
            hist   = yf.download(ticker, start=available[0],
                                 end=end_dt.strftime("%Y-%m-%d"),
                                 progress=False, auto_adjust=True)
            if hist.empty:
                time.sleep(2); continue
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            hist.index = pd.to_datetime(hist.index).strftime("%Y-%m-%d")
            result = {}
            for i, day in enumerate(trading_days, 1):
                if day in hist.index:
                    r = hist.loc[day]
                    result[f"D{i}_Open"]  = round(float(r["Open"]),  4)
                    result[f"D{i}_High"]  = round(float(r["High"]),  4)
                    result[f"D{i}_Low"]   = round(float(r["Low"]),   4)
                    result[f"D{i}_Close"] = round(float(r["Close"]), 4)
                else:
                    for s in ["Open","High","Low","Close"]:
                        result[f"D{i}_{s}"] = None
            return result
        except Exception as e:
            print(f"  ⚠️ attempt {attempt} error: {e}")
            time.sleep(2)
    return {}

def calculate_stats(scan_price, ohlc):
    lows = [(i, ohlc[f"D{i}_Low"]) for i in range(1,6)
            if ohlc.get(f"D{i}_Low") is not None]
    if not lows or scan_price <= 0:
        return {}
    best_day, min_low = min(lows, key=lambda x: x[1])
    max_drop = round((min_low - scan_price) / scan_price * 100, 2)
    d1_open  = ohlc.get("D1_Open")
    d1_gap   = round((d1_open - scan_price) / scan_price * 100, 2) if d1_open and scan_price > 0 else None
    return {
        "MaxDrop%": max_drop,
        "BestDay":  best_day,
        "TP10_Hit": 1 if min_low <= scan_price * 0.90 else 0,
        "TP15_Hit": 1 if min_low <= scan_price * 0.85 else 0,
        "TP20_Hit": 1 if min_low <= scan_price * 0.80 else 0,
        "D1_Gap%":  d1_gap,
        "SL7_Hit_D1":    1 if ohlc.get("D1_High") and ohlc["D1_High"] >= scan_price * 1.07 else 0,
        "IntraDay_SL":   1 if any(ohlc.get(f"D{i}_High", 0) and
                                   ohlc[f"D{i}_High"] >= scan_price * 1.07
                                   for i in range(1,6)) else 0,
    }

# ── main ──────────────────────────────────────────────────────────────────────

def run():
    today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    print(f"\n🔧 backfill_ohlc.py — {today_str}")
    print("Loading post_analysis from Sheets...")

    df = load_post_analysis_from_sheets()
    if df.empty:
        print("❌ post_analysis is empty"); return

    print(f"Total rows: {len(df)}")

    # Find rows missing D1_Open (excluding today — no data yet)
    d1_open_col = pd.to_numeric(df.get("D1_Open", pd.Series(dtype=float)), errors="coerce")
    mask = (d1_open_col.isna() | (d1_open_col == 0)) & (df.get("ScanDate", "") != today_str)
    missing = df[mask].copy()

    print(f"Rows missing D1_Open (excluding today): {len(missing)}")
    if missing.empty:
        print("✅ Nothing to backfill!"); return

    updated = 0
    for idx, row in missing.iterrows():
        ticker     = str(row.get("Ticker", "")).strip()
        scan_date  = str(row.get("ScanDate", "")).strip()
        scan_price = pd.to_numeric(row.get("ScanPrice", 0), errors="coerce") or 0

        if not ticker or not scan_date or scan_price <= 0:
            print(f"  ⏭ skipping {ticker} {scan_date} — missing ticker/date/price")
            continue

        trading_days = get_trading_days_after(scan_date, 5)
        available    = [d for d in trading_days if is_day_complete(d)]
        if not available:
            print(f"  ⏭ {ticker} {scan_date} — no completed days yet")
            continue

        print(f"  📥 {ticker} {scan_date} — fetching {len(available)} days ({available[0]}→{available[-1]})")
        ohlc  = fetch_ohlc(ticker, trading_days)
        stats = calculate_stats(scan_price, ohlc)

        for k, v in {**ohlc, **stats}.items():
            df.at[idx, k] = v

        updated += 1
        time.sleep(0.4)  # rate limit

    print(f"\n✅ Backfilled {updated} rows. Saving to Sheets...")
    save_post_analysis_to_sheets(df)
    print("✅ Done!")

if __name__ == "__main__":
    run()
