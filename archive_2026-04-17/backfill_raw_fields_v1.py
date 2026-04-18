#!/usr/bin/env python3
"""
RidingHigh Pro - Backfill raw fields for historical PA records
Fetches: Open_price, PrevClose, High_today, Low_today, VWAP_price,
         ATR14_raw, Week52High, AvgVolume, FloatShares, SharesOutstanding
for all 80 existing PA rows from Yahoo Finance.
"""

import os, sys, json, time
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

SPREADSHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
SCOPES = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
CSV_PATH = os.path.expanduser("~/Downloads/Post_Analysis_enriched_v2.csv")

def get_client():
    import gspread
    from google.oauth2.service_account import Credentials
    creds_path = os.path.expanduser("~/RidingHighPro/google_credentials.json")
    if os.path.exists(creds_path):
        return gspread.authorize(Credentials.from_service_account_file(creds_path, scopes=SCOPES))
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        return gspread.authorize(Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES))
    raise Exception("No credentials found")

def col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n-1, 26)
        s = chr(65+r) + s
    return s

def write_sheet(ws, df):
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    r = f"A1:{col_letter(len(data[0]))}{len(data)}"
    ws.clear()
    ws.update(range_name=r, values=data)
    print(f"   Written {r} ({len(data)-1} rows × {len(data[0])} cols)")

def fetch_raw_for_date(ticker: str, scan_date: str) -> dict:
    """Fetch raw fields for a specific ticker on a specific scan date."""
    result = {}
    try:
        scan_dt = datetime.strptime(scan_date, "%Y-%m-%d")
        start   = (scan_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        end     = (scan_dt + timedelta(days=2)).strftime("%Y-%m-%d")

        hist = yf.download(ticker, start=start, end=end,
                           progress=False, auto_adjust=True)
        if hist.empty:
            return result

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        hist.index = pd.to_datetime(hist.index).strftime("%Y-%m-%d")

        if scan_date not in hist.index:
            return result

        idx      = hist.index.tolist().index(scan_date)
        current  = hist.loc[scan_date]
        prev_idx = idx - 1
        if prev_idx >= 0:
            prev_date = hist.index[prev_idx]
            result["PrevClose_raw"] = round(float(hist.loc[prev_date]["Close"]), 4)

        result["Open_price_raw"] = round(float(current["Open"]),  4)
        result["High_today_raw"] = round(float(current["High"]),  4)
        result["Low_today_raw"]  = round(float(current["Low"]),   4)
        result["VWAP_price_raw"] = round(
            (float(current["High"]) + float(current["Low"]) + float(current["Close"])) / 3, 4)

        # ATR14
        if len(hist) >= 14:
            try:
                from ta.volatility import AverageTrueRange
                hist_slice = hist.iloc[:idx+1]
                atr_vals = AverageTrueRange(
                    high=hist_slice["High"], low=hist_slice["Low"],
                    close=hist_slice["Close"], window=14
                ).average_true_range()
                if not atr_vals.empty and pd.notna(atr_vals.iloc[-1]):
                    result["ATR14_raw"] = round(float(atr_vals.iloc[-1]), 4)
            except: pass

        # ATRX_calc from raw
        try:
            h = result.get("High_today_raw", 0)
            l = result.get("Low_today_raw", 0)
            atr = result.get("ATR14_raw", 0)
            if atr > 0:
                result["ATRX_calc"] = round((h - l) / atr, 2)
        except: pass

        # RunUp_calc
        try:
            op = result.get("Open_price_raw", 0)
            cl = float(current["Close"])
            if op > 0:
                result["RunUp_calc"] = round(((cl - op) / op) * 100, 2)
        except: pass

        # Gap_calc
        try:
            pc = result.get("PrevClose_raw", 0)
            op = result.get("Open_price_raw", 0)
            if pc > 0 and op > 0:
                result["Gap_calc"] = round(((op - pc) / pc) * 100, 2)
        except: pass

        # VWAP_calc
        try:
            vp = result.get("VWAP_price_raw", 0)
            cl = float(current["Close"])
            if vp > 0:
                result["VWAP_calc"] = round(((cl / vp) - 1) * 100, 2)
        except: pass

    except Exception as e:
        print(f"   ⚠️  {ticker} {scan_date} hist error: {e}")

    # Info fields (static — date doesn't matter much)
    try:
        info = yf.Ticker(ticker).info
        w52 = info.get("fiftyTwoWeekHigh", None)
        if w52:
            result["Week52High_raw"] = round(float(w52), 4)
        avg_vol = info.get("averageVolume", None)
        if avg_vol:
            result["AvgVolume_raw"] = int(avg_vol)
        float_sh = info.get("floatShares", None)
        if float_sh:
            result["FloatShares_raw"] = int(float_sh)
        shares = info.get("sharesOutstanding", None)
        if shares:
            result["SharesOutstanding_raw"] = int(shares)

        # REL_VOL_calc
        try:
            vol = result.get("Volume_raw_from_snap", 0)
            if avg_vol and avg_vol > 0 and vol > 0:
                result["REL_VOL_calc"] = round(vol / avg_vol, 2)
        except: pass

    except Exception as e:
        print(f"   ⚠️  {ticker} info error: {e}")

    return result


def run():
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found: {CSV_PATH}"); sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    print(f"📂 Loaded: {len(df)} rows, {len(df.columns)} cols")

    # Fields to backfill
    backfill_fields = [
        "Open_price_raw","PrevClose_raw","High_today_raw","Low_today_raw",
        "VWAP_price_raw","ATR14_raw","Week52High_raw","AvgVolume_raw",
        "FloatShares_raw","SharesOutstanding_raw",
        "ATRX_calc","RunUp_calc","Gap_calc","VWAP_calc","REL_VOL_calc"
    ]

    # Add missing columns
    for col in backfill_fields:
        if col not in df.columns:
            df[col] = None

    # Only backfill rows where Open_price_raw is missing
    missing_mask = df["Open_price_raw"].isna() | (df["Open_price_raw"] == "") | (df["Open_price_raw"] == "None")
    to_fill = df[missing_mask].copy()
    print(f"📊 Rows needing backfill: {len(to_fill)}")

    for i, (idx, row) in enumerate(to_fill.iterrows()):
        ticker    = row["Ticker"]
        scan_date = row["ScanDate"]
        print(f"[{i+1}/{len(to_fill)}] {ticker} {scan_date}...", end=" ", flush=True)

        # Pass Volume for REL_VOL_calc
        raw = fetch_raw_for_date(ticker, scan_date)
        raw["Volume_raw_from_snap"] = pd.to_numeric(row.get("Volume_raw", 0), errors="coerce") or 0

        # Re-run REL_VOL_calc with volume
        try:
            avg_vol = raw.get("AvgVolume_raw", 0) or 0
            vol     = raw.get("Volume_raw_from_snap", 0) or 0
            if avg_vol > 0 and vol > 0:
                raw["REL_VOL_calc"] = round(vol / avg_vol, 2)
        except: pass

        # Write to df
        for field, val in raw.items():
            if field == "Volume_raw_from_snap":
                continue
            if field in df.columns:
                df.at[idx, field] = val

        filled = sum(1 for f in backfill_fields if raw.get(f) is not None)
        print(f"✅ {filled} fields")
        time.sleep(0.5)

    # Save locally
    out_path = os.path.expanduser("~/Downloads/Post_Analysis_enriched_v3.csv")
    df.to_csv(out_path, index=False)
    print(f"\n💾 Saved: {out_path}")
    print(f"   Cols: {len(df.columns)} | Rows: {len(df)}")

    # Upload to Sheets
    print("\n🔌 Uploading to Google Sheets...")
    gc = get_client()
    ws = gc.open_by_key(SPREADSHEET_ID).worksheet("post_analysis")
    write_sheet(ws, df)
    print("✅ Upload complete!")


if __name__ == "__main__":
    run()
