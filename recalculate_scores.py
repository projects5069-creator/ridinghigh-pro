#!/usr/bin/env python3
"""
RidingHigh Pro - Score Recalculator
Adds Score_v2 column to post_analysis sheet using fixed RunUp formula.

Change vs original:
  OLD: if run_up < 0 → score += min(abs(run_up) / 5,  1) * 5
  NEW: if run_up > 0 → score += min(run_up     / 50, 1) * 5

All other metrics unchanged.
"""

import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

SPREADSHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ── Google Sheets client ──────────────────────────────────────────────────────
def get_gsheets_client():
    import gspread
    from google.oauth2.service_account import Credentials

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)

    creds_path = os.path.expanduser("~/RidingHighPro/google_credentials.json")
    if os.path.exists(creds_path):
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return gspread.authorize(creds)

    raise Exception("No Google credentials found!")


# ── Score v2 — identical to calculate_score() except RunUp fix ───────────────
def calculate_score_v2(row):
    def safe(val):
        try:
            v = float(val)
            return v if pd.notna(v) else 0.0
        except:
            return 0.0

    mxv              = safe(row.get("MxV", 0))
    price_to_52w     = safe(row.get("PriceTo52WHigh", 0))
    price_to_high    = safe(row.get("PriceToHigh", 0))
    rel_vol          = safe(row.get("REL_VOL", 1))
    rsi              = safe(row.get("RSI", 50))
    atrx             = safe(row.get("ATRX", 0))
    run_up           = safe(row.get("RunUp", 0))
    float_pct        = safe(row.get("Float%", 0))
    gap              = safe(row.get("Gap", 0))
    vwap_dist        = safe(row.get("VWAP", 0))

    score = 0.0

    # MxV — 20%
    if mxv < 0:
        score += min(abs(mxv) / 50, 1) * 20

    # PriceTo52WHigh — 10%
    if price_to_52w > 0:
        score += min(price_to_52w / 100, 1) * 10

    # PriceToHigh — 15%
    if price_to_high < 0:
        score += min(abs(price_to_high) / 10, 1) * 15

    # REL_VOL — 15%
    score += min(rel_vol / 2, 1) * 15

    # RSI — 15%
    if rsi > 80:
        score += 15
    else:
        score += (rsi / 80) * 15

    # ATRX — 10%
    score += min(atrx / 15, 1) * 10

    # RunUp — 5% ← FIXED (was: run_up < 0, cap at 5)
    if run_up > 0:
        score += min(run_up / 50, 1) * 5

    # Float% — 5%
    score += min(float_pct / 10, 1) * 5

    # Gap — 3%
    score += min(abs(gap) / 20, 1) * 3

    # VWAP — 2%
    score += min(abs(vwap_dist) / 15, 1) * 2

    return round(score, 2)


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print("🔄 Connecting to Google Sheets...")
    gc = get_gsheets_client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("post_analysis")

    data = ws.get_all_values()
    if len(data) <= 1:
        print("❌ No data in post_analysis")
        return

    df = pd.DataFrame(data[1:], columns=data[0])
    print(f"✅ Loaded {len(df)} rows from post_analysis")

    # Calculate Score_v2 for every row
    df["Score_v2"] = df.apply(calculate_score_v2, axis=1)

    # Compare
    df["Score_orig"] = pd.to_numeric(df["Score"], errors="coerce")
    df["Score_diff"] = (df["Score_v2"] - df["Score_orig"]).round(2)

    print("\n📊 Score comparison (first 20 rows):")
    print(df[["Ticker", "ScanDate", "Score_orig", "Score_v2", "Score_diff", "RunUp"]].head(20).to_string(index=False))

    print(f"\n📈 Average original score : {df['Score_orig'].mean():.2f}")
    print(f"📈 Average Score_v2       : {df['Score_v2'].mean():.2f}")
    print(f"📈 Average difference     : {df['Score_diff'].mean():.2f}")
    print(f"📈 Rows where score went UP   : {(df['Score_diff'] > 0).sum()}")
    print(f"📈 Rows where score went DOWN : {(df['Score_diff'] < 0).sum()}")
    print(f"📈 Rows unchanged             : {(df['Score_diff'] == 0).sum()}")

    # Write Score_v2 back to sheet
    headers = data[0]
    if "Score_v2" in headers:
        col_idx = headers.index("Score_v2") + 1
        print(f"\n✏️  Updating existing Score_v2 column (col {col_idx})...")
    else:
        col_idx = len(headers) + 1
        print(f"\n✏️  Adding Score_v2 as new column {col_idx}...")
        ws.resize(rows=1000, cols=66); ws.update_cell(1, col_idx, "Score_v2")

    # Write values
    col_letter = chr(ord('A') + col_idx - 1) if col_idx <= 26 else None
    values = [[str(v)] for v in df["Score_v2"].tolist()]

    # Use batch update by column range
    from gspread.utils import rowcol_to_a1
    start = rowcol_to_a1(2, col_idx)
    end   = rowcol_to_a1(len(df) + 1, col_idx)
    ws.update(f"{start}:{end}", values)

    print(f"✅ Score_v2 written to post_analysis ({len(df)} rows)")
    print("\n🎯 Done! You can now compare Score vs Score_v2 in Google Sheets.")


if __name__ == "__main__":
    run()
