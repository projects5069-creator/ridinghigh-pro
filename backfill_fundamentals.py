"""
backfill_fundamentals.py — חד-פעמי
ממלא Sector / Industry / RealFloat / RealFloat_M /
Price_vs_SMA20 / Consecutive_Up / DaysSinceIPO / MarketCapCategory
לשורות ב-post_analysis שחסר להן Sector.
משתמש ב-fetch_d0_and_fundamental מ-post_analysis_collector.
"""
import sys, time
sys.path.insert(0, ".")

import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets
from post_analysis_collector import fetch_d0_and_fundamental


FUND_COLS = ["Sector", "Industry", "RealFloat", "RealFloat_M",
             "Price_vs_SMA20", "Consecutive_Up", "DaysSinceIPO", "MarketCapCategory"]


from utils import _is_missing


def main():
    print("טוען post_analysis מ-Sheets...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("אין נתונים."); return

    print(f"סה״כ שורות: {len(df)}")

    for col in FUND_COLS:
        if col not in df.columns:
            df[col] = None

    # שורות שחסר להן Sector
    needs_fund = df[df["Sector"].apply(_is_missing)].copy()
    print(f"שורות ללא Sector: {len(needs_fund)}")

    if needs_fund.empty:
        print("אין מה לעדכן."); return

    updated_indices = []

    for idx, row in needs_fund.iterrows():
        ticker    = str(row.get("Ticker", "")).strip()
        scan_date = str(row.get("ScanDate", "")).strip()

        if not ticker or not scan_date:
            continue

        print(f"  {ticker} {scan_date}...", end=" ", flush=True)
        data = fetch_d0_and_fundamental(ticker, scan_date)

        fund_found = {k: v for k, v in data.items() if k in FUND_COLS and not _is_missing(v)}
        if not fund_found:
            print("⚠️  אין נתוני fundamentals")
            time.sleep(0.5)
            continue

        for col, val in fund_found.items():
            df.at[idx, col] = val

        sector = fund_found.get("Sector", "?")
        sma20  = fund_found.get("Price_vs_SMA20", "?")
        print(f"✅ Sector={sector} SMA20={sma20}")
        updated_indices.append(idx)
        time.sleep(0.5)

    print(f"\nעדכנו {len(updated_indices)} שורות.")

    if not updated_indices:
        print("אין שינויים."); return

    save_post_analysis_to_sheets(df.loc[updated_indices])
    print("✅ נשמר ל-Sheets.")


if __name__ == "__main__":
    main()
