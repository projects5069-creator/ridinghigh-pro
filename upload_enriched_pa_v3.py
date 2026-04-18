#!/usr/bin/env python3
"""Upload Post_Analysis_enriched_v2.csv to Google Sheets post_analysis tab"""

import os, sys, json
import pandas as pd

SPREADSHEET_ID  = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
SCOPES          = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
TAB             = "post_analysis"
CSV_PATH        = os.path.expanduser("~/Downloads/Post_Analysis_enriched_v2.csv")

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

def write(ws, df):
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    r = f"A1:{col_letter(len(data[0]))}{len(data)}"
    ws.clear()
    ws.update(range_name=r, values=data)
    print(f"   Written {r} ({len(data)-1} rows × {len(data[0])} cols)")

def run():
    if not os.path.exists(CSV_PATH):
        print(f"❌ Not found: {CSV_PATH}"); sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    print(f"📂 {len(df)} rows, {len(df.columns)} cols")
    gc = get_client()
    ws = gc.open_by_key(SPREADSHEET_ID).worksheet(TAB)
    print(f"✅ Connected — '{TAB}'")
    existing = ws.get_all_values()
    if len(existing) > 1:
        ex = pd.DataFrame(existing[1:], columns=existing[0])
        keys = set(zip(df['Ticker'], df['ScanDate']))
        keep = ex[~ex.apply(lambda r: (r['Ticker'],r['ScanDate']) in keys, axis=1)].copy()
        all_cols = list(ex.columns)
        for c in df.columns:
            if c not in all_cols: all_cols.append(c)
        combined = pd.concat([keep.reindex(columns=all_cols),
                              df.reindex(columns=all_cols)], ignore_index=True)
        combined = combined.sort_values(['ScanDate','Ticker'], ignore_index=True)
    else:
        combined = df
    write(ws, combined)
    print(f"✅ Done: {len(combined)} total rows")

if __name__ == "__main__":
    run()
