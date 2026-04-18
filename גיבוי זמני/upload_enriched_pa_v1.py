#!/usr/bin/env python3
"""
RidingHigh Pro - Upload Enriched Post Analysis to Google Sheets
Replaces post_analysis tab with Post_Analysis_enriched_v1.csv
Uses safe upsert — existing rows not in CSV are preserved.
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


def get_or_create_sheet(spreadsheet, tab_name):
    try:
        return spreadsheet.worksheet(tab_name)
    except Exception:
        return spreadsheet.add_worksheet(title=tab_name, rows=2000, cols=50)


def df_to_sheet(ws, df):
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    ws.clear()
    ws.update(data)


def run():
    # ── Load CSV ─────────────────────────────────────────────────────────────
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found at: {CSV_PATH}")
        sys.exit(1)

    new_df = pd.read_csv(CSV_PATH)
    print(f"📂 Loaded CSV: {len(new_df)} rows, {len(new_df.columns)} columns")

    # ── Connect to Sheets ────────────────────────────────────────────────────
    print("🔌 Connecting to Google Sheets...")
    gc = get_client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = get_or_create_sheet(sh, TAB_POST_ANALYSIS)
    print(f"✅ Connected — tab: '{TAB_POST_ANALYSIS}'")

    # ── Load existing data ───────────────────────────────────────────────────
    existing = ws.get_all_values()

    if len(existing) <= 1:
        # Sheet empty — just write
        df_to_sheet(ws, new_df)
        print(f"✅ Written fresh: {len(new_df)} rows")
        return

    existing_df = pd.DataFrame(existing[1:], columns=existing[0])
    print(f"📊 Existing rows in sheet: {len(existing_df)}")

    KEY = ["Ticker", "ScanDate"]

    if not all(k in existing_df.columns for k in KEY):
        # No key columns — full overwrite
        df_to_sheet(ws, new_df)
        print(f"✅ Full overwrite: {len(new_df)} rows")
        return

    # ── Safe upsert ──────────────────────────────────────────────────────────
    # Build unified column list
    all_cols = list(existing_df.columns)
    for col in new_df.columns:
        if col not in all_cols:
            all_cols.append(col)

    existing_df  = existing_df.reindex(columns=all_cols)
    new_df_reind = new_df.reindex(columns=all_cols)

    # Remove rows that will be replaced
    incoming_keys = set(zip(new_df[KEY[0]], new_df[KEY[1]]))
    keep = existing_df[
        ~existing_df.apply(lambda r: (r[KEY[0]], r[KEY[1]]) in incoming_keys, axis=1)
    ]

    combined = pd.concat([keep, new_df_reind], ignore_index=True)

    if "ScanDate" in combined.columns:
        combined = combined.sort_values(["ScanDate", "Ticker"], ignore_index=True)

    df_to_sheet(ws, combined)
    print(f"✅ Upsert complete:")
    print(f"   • {len(new_df)} rows upserted (enriched)")
    print(f"   • {len(keep)} rows preserved (untouched)")
    print(f"   • {len(combined)} total rows in sheet")


if __name__ == "__main__":
    run()
