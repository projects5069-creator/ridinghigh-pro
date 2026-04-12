"""
fix_sl_hits.py — חד-פעמי
מחשב SL7_Hit_D1 + IntraDay_SL על שורות שיש להן D1_High אבל חסרים שדות אלו.
"""
import sys
sys.path.insert(0, ".")

import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets


def _is_missing(v):
    if v is None: return True
    if isinstance(v, float) and pd.isna(v): return True
    return str(v).strip() in ("", "nan", "None")


def main():
    print("טוען post_analysis מ-Sheets...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("אין נתונים."); return

    print(f"סה״כ שורות: {len(df)}")

    for col in ["SL7_Hit_D1", "IntraDay_SL"]:
        if col not in df.columns:
            df[col] = None

    updated_rows = []

    for idx, row in df.iterrows():
        needs_sl7    = _is_missing(row.get("SL7_Hit_D1"))
        needs_intra  = _is_missing(row.get("IntraDay_SL"))
        if not needs_sl7 and not needs_intra:
            continue

        try:
            scan_price = float(row.get("ScanPrice", 0) or 0)
        except (ValueError, TypeError):
            continue
        if scan_price <= 0:
            continue

        changes = {}

        # SL7_Hit_D1: D1 High >= scan_price * 1.07
        if needs_sl7:
            d1_high = row.get("D1_High")
            if not _is_missing(d1_high):
                try:
                    changes["SL7_Hit_D1"] = 1 if float(d1_high) >= scan_price * 1.07 else 0
                except (ValueError, TypeError):
                    pass

        # IntraDay_SL: any of D1-D5 High >= scan_price * 1.07
        if needs_intra:
            hits = []
            for i in range(1, 6):
                dh = row.get(f"D{i}_High")
                if not _is_missing(dh):
                    try:
                        hits.append(float(dh) >= scan_price * 1.07)
                    except (ValueError, TypeError):
                        pass
            if hits:  # יש לפחות יום אחד עם נתונים
                changes["IntraDay_SL"] = 1 if any(hits) else 0

        if not changes:
            continue

        ticker    = str(row.get("Ticker", "")).strip()
        scan_date = str(row.get("ScanDate", "")).strip()
        print(f"  {ticker} {scan_date}: {changes}")
        for col, val in changes.items():
            df.at[idx, col] = val
        updated_rows.append(idx)

    print(f"\nעדכון {len(updated_rows)} שורות.")
    if not updated_rows:
        print("אין שינויים."); return

    save_post_analysis_to_sheets(df.loc[updated_rows])
    print("✅ נשמר ל-Sheets.")


if __name__ == "__main__":
    main()
