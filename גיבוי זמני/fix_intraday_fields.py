"""
fix_intraday_fields.py — חד-פעמי
מתקן IntraDay_TP10 / SL_Hit_D0 / MinToClose על שורות שיש להן
IntraHigh + IntraLow + ScanPrice אבל השדות החדשים ריקים.

IntraDay_TP10 ו-SL_Hit_D0 דורשים רק IntraHigh+IntraLow+ScanPrice.
MinToClose דורש גם PeakScoreTime — ידולג אם חסר.
"""
import sys
sys.path.insert(0, ".")

import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets


def _is_missing(v):
    if v is None: return True
    if isinstance(v, float) and pd.isna(v): return True
    return str(v).strip() in ("", "nan", "None")


def fix_row(row):
    changes = {}

    # IntraDay_TP10 + SL_Hit_D0 דורשים רק IntraHigh/IntraLow/ScanPrice
    try:
        intra_high = float(row["IntraHigh"])
        intra_low  = float(row["IntraLow"])
        scan_price = float(row["ScanPrice"])
    except (ValueError, TypeError):
        return changes

    if scan_price <= 0:
        return changes

    if _is_missing(row.get("IntraDay_TP10")):
        changes["IntraDay_TP10"] = 1 if intra_low <= scan_price * 0.90 else 0

    if _is_missing(row.get("SL_Hit_D0")):
        changes["SL_Hit_D0"] = 1 if intra_high >= scan_price * 1.07 else 0

    # MinToClose דורש גם PeakScoreTime
    if _is_missing(row.get("MinToClose")):
        peak_time = str(row.get("PeakScoreTime", "")).strip()
        if peak_time and not _is_missing(peak_time):
            try:
                peak_dt  = pd.Timestamp(f"2000-01-01 {peak_time}")
                close_dt = pd.Timestamp("2000-01-01 15:00")
                changes["MinToClose"] = max(0, int((close_dt - peak_dt).total_seconds() / 60))
            except Exception as e:
                print(f"  MinToClose parse error for '{peak_time}': {e}")

    return changes


def main():
    print("טוען post_analysis מ-Sheets...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("אין נתונים — יוצא.")
        return

    print(f"סה״כ שורות: {len(df)}")

    for col in ["IntraDay_TP10", "SL_Hit_D0", "MinToClose"]:
        if col not in df.columns:
            df[col] = None

    updated_rows = []

    for idx, row in df.iterrows():
        # מינימום הכרחי: IntraHigh + IntraLow + ScanPrice
        if any(_is_missing(row.get(c)) for c in ["IntraHigh", "IntraLow", "ScanPrice"]):
            continue

        changes = fix_row(row)
        if not changes:
            continue

        ticker    = str(row.get("Ticker", "")).strip()
        scan_date = str(row.get("ScanDate", "")).strip()
        print(f"  {ticker} {scan_date}: {list(changes.keys())}")
        for col, val in changes.items():
            df.at[idx, col] = val
        updated_rows.append(idx)

    print(f"\nעדכון {len(updated_rows)} שורות.")

    if not updated_rows:
        print("אין מה לעדכן — יוצא.")
        return

    save_post_analysis_to_sheets(df.loc[updated_rows])
    print("✅ נשמר ל-Sheets.")


if __name__ == "__main__":
    main()
