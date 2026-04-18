"""
backfill_ohlc_weeks13_14.py — חד-פעמי
מושך D1-D5 OHLC מ-Yahoo Finance לשורות קיימות ב-post_analysis
שחסרות D1_Open, ומעדכן גם MaxDrop% / TP10_Hit / SL7_Hit_D1 / IntraDay_SL.
"""
import sys, time
sys.path.insert(0, ".")

import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets
from post_analysis_collector import (
    fetch_ohlc_for_days, calculate_stats,
    get_trading_days_after, is_day_complete, DAYS_FORWARD
)


def _is_missing(v):
    if v is None: return True
    if isinstance(v, float) and pd.isna(v): return True
    return str(v).strip() in ("", "nan", "None")


def main():
    print("טוען post_analysis מ-Sheets...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("אין נתונים — יוצא."); return

    print(f"סה״כ שורות: {len(df)}")

    # סנן: שורות שחסרות D1_Open
    if "D1_Open" not in df.columns:
        df["D1_Open"] = None
    needs_ohlc = df[df["D1_Open"].apply(_is_missing)].copy()
    print(f"שורות ללא D1_Open: {len(needs_ohlc)}")

    if needs_ohlc.empty:
        print("אין מה לעדכן."); return

    updated_indices = []

    for idx, row in needs_ohlc.iterrows():
        ticker    = str(row.get("Ticker", "")).strip()
        scan_date = str(row.get("ScanDate", "")).strip()
        scan_price = pd.to_numeric(row.get("ScanPrice", 0), errors="coerce") or 0

        if not ticker or not scan_date or scan_price <= 0:
            print(f"  [Skip] {ticker} {scan_date} — missing base fields")
            continue

        trading_days = get_trading_days_after(scan_date, DAYS_FORWARD)
        available    = [d for d in trading_days if is_day_complete(d)]

        if not available:
            print(f"  [Skip] {ticker} {scan_date} — no complete days yet")
            continue

        print(f"  {ticker} {scan_date} — fetching {len(available)} days...", end=" ", flush=True)
        ohlc = fetch_ohlc_for_days(ticker, available)

        if not ohlc:
            print("❌ no data")
            time.sleep(1)
            continue

        stats = calculate_stats(scan_price, ohlc)
        print(f"✅ MaxDrop={stats.get('MaxDrop%')} TP10={stats.get('TP10_Hit')}")

        for col, val in {**ohlc, **stats}.items():
            df.at[idx, col] = val

        updated_indices.append(idx)
        time.sleep(0.5)

    print(f"\nעדכנו {len(updated_indices)} שורות.")

    if not updated_indices:
        print("אין שינויים."); return

    save_post_analysis_to_sheets(df.loc[updated_indices])
    print("✅ נשמר ל-Sheets.")


if __name__ == "__main__":
    main()
