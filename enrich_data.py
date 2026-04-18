#!/usr/bin/env python3
"""
RidingHigh Pro - Data Enrichment Script
Adds new analytical fields to existing post_analysis records.

New fields added:
--- From Yahoo Finance (retrospective) ---
  D0_Open          : Opening price on scan day
  D0_High          : Intraday high on scan day  
  D0_Low           : Intraday low on scan day
  D0_Drop%_from_High: % drop from D0_High to D0_Close
  RealFloat        : Actual float shares (from Yahoo .info)
  RealFloat_M      : Float in millions
  Sector           : Company sector
  Industry         : Company industry
  MarketCapCategory: Micro(<300M) / Small(300M-2B) / Mid(2B+)
  Price_vs_SMA20   : % distance from 20-day SMA
  Consecutive_Up   : Consecutive up days before scan
  DaysSinceIPO     : Trading days since IPO (approximate)

--- From timeline_live (requires Google Sheets) ---
  FirstScanTime    : First time stock appeared in scan that day
  LastScanTime     : Last scan time that day
  ScanCount        : How many times scanned that day
  ScoreAtFirst     : Score at first scan
  ScoreAtLast      : Score at last scan
  ScoreMax         : Max score reached during day
  ScoreMin         : Min score reached during day
"""

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

SPREADSHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# get_gsheets_client removed — use sheets_manager._get_gc()
get_gsheets_client = sheets_manager._get_gc  # alias for backward compat


def get_yahoo_data(ticker: str, scan_date: str) -> dict:
    """Fetch retrospective Yahoo Finance data for scan date."""
    import yfinance as yf
    result = {}
    try:
        stock = yf.Ticker(ticker)
        
        # Get 60 days of history
        scan_dt = datetime.strptime(scan_date, "%Y-%m-%d")
        start = (scan_dt - timedelta(days=60)).strftime("%Y-%m-%d")
        end   = (scan_dt + timedelta(days=2)).strftime("%Y-%m-%d")
        hist  = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        hist.index = pd.to_datetime(hist.index).strftime("%Y-%m-%d")

        # D0 OHLC
        if scan_date in hist.index:
            row = hist.loc[scan_date]
            result["D0_Open"] = round(float(row["Open"]), 4)
            result["D0_High"] = round(float(row["High"]), 4)
            result["D0_Low"]  = round(float(row["Low"]), 4)
            # D0_Drop%_from_High = how much it fell from high to close
            if row["High"] > 0:
                result["D0_Drop%_from_High"] = round((float(row["Close"]) - float(row["High"])) / float(row["High"]) * 100, 2)

        # SMA20
        if len(hist) >= 20:
            hist_before = hist[hist.index <= scan_date]
            if len(hist_before) >= 20:
                sma20 = hist_before["Close"].iloc[-20:].mean()
                scan_close = hist_before["Close"].iloc[-1]
                result["Price_vs_SMA20"] = round((float(scan_close) - float(sma20)) / float(sma20) * 100, 2)

        # Consecutive up days before scan
        hist_before = hist[hist.index < scan_date]
        if len(hist_before) >= 2:
            consec = 0
            closes = hist_before["Close"].values
            for i in range(len(closes)-1, 0, -1):
                if closes[i] > closes[i-1]:
                    consec += 1
                else:
                    break
            result["Consecutive_Up"] = consec

        # Yahoo info
        info = stock.info
        
        # Real float
        float_shares = info.get("floatShares", None)
        if float_shares:
            result["RealFloat"]   = int(float_shares)
            result["RealFloat_M"] = round(float_shares / 1_000_000, 2)

        # Sector / Industry
        result["Sector"]   = info.get("sector", "")
        result["Industry"] = info.get("industry", "")

        # Market cap category
        mc = info.get("marketCap", 0) or 0
        if mc < 300_000_000:
            result["MarketCapCategory"] = "Micro"
        elif mc < 2_000_000_000:
            result["MarketCapCategory"] = "Small"
        else:
            result["MarketCapCategory"] = "Mid+"

        # Days since IPO
        ipo_date = info.get("firstTradeDateEpochUtc", None)
        if ipo_date:
            ipo_dt = datetime.fromtimestamp(ipo_date)
            scan_dt = datetime.strptime(scan_date, "%Y-%m-%d")
            result["DaysSinceIPO"] = (scan_dt - ipo_dt).days

    except Exception as e:
        print(f"  ⚠️ Yahoo error for {ticker}: {e}")

    return result


def get_timeline_data(ticker: str, scan_date: str, timeline_df: pd.DataFrame) -> dict:
    """Extract scan timeline stats from timeline_live data."""
    result = {}
    try:
        day_data = timeline_df[
            (timeline_df["Ticker"] == ticker) &
            (timeline_df["Date"] == scan_date)
        ].copy()

        if day_data.empty:
            return result

        day_data["Score"] = pd.to_numeric(day_data["Score"], errors="coerce")
        day_data = day_data.dropna(subset=["Score"])

        if "ScanTime" in day_data.columns:
            times = day_data["ScanTime"].tolist()
            result["FirstScanTime"] = times[0] if times else ""
            result["LastScanTime"]  = times[-1] if times else ""

        result["ScanCount"]  = len(day_data)
        result["ScoreAtFirst"] = round(day_data["Score"].iloc[0], 2) if len(day_data) > 0 else None
        result["ScoreAtLast"]  = round(day_data["Score"].iloc[-1], 2) if len(day_data) > 0 else None
        result["ScoreMax"]     = round(day_data["Score"].max(), 2)
        result["ScoreMin"]     = round(day_data["Score"].min(), 2)
        result["ScoreStd"]     = round(day_data["Score"].std(), 2)  # volatility of score during day

    except Exception as e:
        print(f"  ⚠️ Timeline error for {ticker} {scan_date}: {e}")

    return result


def run():
    print("🔄 Connecting to Google Sheets...")
    gc = get_gsheets_client()
    sh = gc.open_by_key(SPREADSHEET_ID)

    # Load post_analysis
    ws_pa = sh.worksheet("post_analysis")
    pa_data = ws_pa.get_all_values()
    df = pd.DataFrame(pa_data[1:], columns=pa_data[0])
    print(f"✅ Loaded {len(df)} rows from post_analysis")

    # Load timeline_live
    print("📊 Loading timeline_live...")
    ws_tl = sh.worksheet("timeline_live")
    tl_data = ws_tl.get_all_values()
    tl_df = pd.DataFrame(tl_data[1:], columns=tl_data[0]) if len(tl_data) > 1 else pd.DataFrame()
    print(f"✅ Loaded {len(tl_df)} rows from timeline_live")

    # New columns to add
    new_cols = [
        "D0_Open", "D0_High", "D0_Low", "D0_Drop%_from_High",
        "RealFloat", "RealFloat_M", "Sector", "Industry",
        "MarketCapCategory", "Price_vs_SMA20", "Consecutive_Up", "DaysSinceIPO",
        "FirstScanTime", "LastScanTime", "ScanCount",
        "ScoreAtFirst", "ScoreAtLast", "ScoreMax", "ScoreMin", "ScoreStd"
    ]

    for col in new_cols:
        if col not in df.columns:
            df[col] = None

    # Enrich each row
    print(f"\n🔬 Enriching {len(df)} records...\n")
    for idx, row in df.iterrows():
        ticker    = str(row.get("Ticker", "")).strip()
        scan_date = str(row.get("ScanDate", "")).strip()

        if not ticker or not scan_date:
            continue

        print(f"[{idx+1}/{len(df)}] {ticker} {scan_date}")

        # Yahoo data
        yahoo = get_yahoo_data(ticker, scan_date)
        for k, v in yahoo.items():
            df.at[idx, k] = v

        # Timeline data
        if not tl_df.empty:
            tl = get_timeline_data(ticker, scan_date, tl_df)
            for k, v in tl.items():
                df.at[idx, k] = v

        time.sleep(0.3)  # rate limit

    # Write back to sheet
    print("\n💾 Writing enriched data to Google Sheets...")
    
    # Resize sheet if needed
    needed_cols = len(df.columns) + 5
    if needed_cols > ws_pa.col_count:
        ws_pa.resize(rows=ws_pa.row_count, cols=needed_cols)
        print(f"   ↳ Resized sheet to {needed_cols} columns")

    # Update header row
    headers = df.columns.tolist()
    ws_pa.update("A1", [headers])

    # Update all data
    data_values = df.fillna("").astype(str).values.tolist()
    from gspread.utils import rowcol_to_a1
    end_cell = rowcol_to_a1(len(df) + 1, len(headers))
    ws_pa.update(f"A2:{end_cell}", data_values)

    print(f"✅ Done! {len(df)} rows enriched with {len(new_cols)} new columns.")
    print("\nNew columns added:")
    for col in new_cols:
        print(f"  • {col}")


if __name__ == "__main__":
    run()
