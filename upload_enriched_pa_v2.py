#!/usr/bin/env python3
"""
RidingHigh Pro - Upload Enriched Post Analysis to Google Sheets v2
Fix: uses explicit range in update() to avoid cell limit error.
"""

import os
import sys
import json
import pandas as pd

SPREADSHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
TAB_POST_ANALYSIS = "post_analysis"
CSV_PATH = os.path.expanduser("~/Downloads/Post_Analysis_enriched_v1.csv")


def get_client():
    import gspread
    from google.oauth2.service_account import Credentials
    creds_path = os.path.expanduser("~/RidingHighPro/google_credentials.json")
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return gspread.authorize(creds)
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        return gspread.authorize(creds)
    raise Exception("No Google credentials found!")


def col_letter(n):
    """Convert column index (1-based) to letter, e.g. 1→A, 27→AA"""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def df_to_sheet_explicit(ws, df):
    """Write DataFrame with explicit range — avoids cell limit error."""
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    nrows = len(data)
    ncols = len(data[0])
    end_col = col_letter(ncols)
    range_str = f"A1:{end_col}{nrows}"
    ws.clear()
    ws.update(range_str, data)
    print(f"   Written to range {range_str} ({nrows} rows × {ncols} cols)")


def run():
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found: {CSV_PATH}")
        sys.exit(1)

    new_df = pd.read_csv(CSV_PATH)
    print(f"📂 Loaded CSV: {len(new_df)} rows, {len(new_df.columns)} columns")

    print("🔌 Connecting to Google Sheets...")
    gc = get_client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(TAB_POST_ANALYSIS)
    print(f"✅ Connected — tab: '{TAB_POST_ANALYSIS}'")

    existing = ws.get_all_values()
    print(f"📊 Existing rows in sheet: {max(0, len(existing)-1)}")

    KEY = ["Ticker", "ScanDate"]

    if len(existing) <= 1:
        df_to_sheet_explicit(ws, new_df)
        print(f"✅ Written fresh: {len(new_df)} rows")
        return

    existing_df = pd.DataFrame(existing[1:], columns=existing[0])

    if not all(k in existing_df.columns for k in KEY):
        df_to_sheet_explicit(ws, new_df)
        print(f"✅ Full overwrite: {len(new_df)} rows")
        return

    # ── Safe upsert ──────────────────────────────────────────────────────────
    all_cols = list(existing_df.columns)
    for col in new_df.columns:
        if col not in all_cols:
            all_cols.append(col)

    existing_df  = existing_df.reindex(columns=all_cols)
    new_df_reind = new_df.reindex(columns=all_cols)

    incoming_keys = set(zip(new_df[KEY[0]], new_df[KEY[1]]))
    keep = existing_df[
        ~existing_df.apply(lambda r: (r[KEY[0]], r[KEY[1]]) in incoming_keys, axis=1)
    ].copy()

    combined = pd.concat([keep, new_df_reind], ignore_index=True)
    if "ScanDate" in combined.columns:
        combined = combined.sort_values(["ScanDate", "Ticker"], ignore_index=True)

    df_to_sheet_explicit(ws, combined)
    print(f"✅ Upsert complete:")
    print(f"   • {len(new_df)} rows upserted (enriched)")
    print(f"   • {len(keep)} rows preserved")
    print(f"   • {len(combined)} total rows in sheet")


if __name__ == "__main__":
    run()
