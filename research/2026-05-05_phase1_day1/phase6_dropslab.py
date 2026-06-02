"""Phase 6: DropsLab Cross-Reference."""
import json, time
import pandas as pd
import numpy as np
from scipy import stats
import gspread
from google.oauth2.service_account import Credentials

CREDS_PATH = "/Users/adilevy/RidingHighPro/google_credentials.json"
DROPSLAB_ID = "1XM-qId7HAwEu-8-1GGHcy3RoyyAnsYshjZfDrKFnTMI"
DROPSLAB_TAB = "DropsLab-Data"

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly","https://www.googleapis.com/auth/drive.readonly"]
creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
gc = gspread.authorize(creds)

# Read DropsLab
print("Reading DropsLab...", flush=True)
try:
    ss = gc.open_by_key(DROPSLAB_ID)
    # List all worksheets
    worksheets = ss.worksheets()
    print(f"Available worksheets: {[ws.title for ws in worksheets]}")
    
    # Try to find the right tab
    target_ws = None
    for ws in worksheets:
        if "data" in ws.title.lower() or "drops" in ws.title.lower():
            target_ws = ws
            break
    if target_ws is None:
        target_ws = worksheets[0]
    
    print(f"Using worksheet: {target_ws.title}")
    data = target_ws.get_all_values()
    print(f"Got {len(data)} rows (incl header)")
    
    if len(data) < 2:
        print("No data in DropsLab")
        # Save empty cross-reference
        pd.DataFrame().to_csv("/tmp/research/cross_reference.csv", index=False)
        with open("/tmp/research/checkpoints/phase6.done","w") as f:
            f.write("done - no DropsLab data\n")
        exit(0)
    
    headers = data[0]
    print(f"Columns: {headers[:10]}...")
    
    dl = pd.DataFrame(data[1:], columns=headers)
    print(f"DropsLab rows: {len(dl)}")
    
    # Find date and ticker columns
    date_cols = [c for c in dl.columns if "date" in c.lower() or "drop" in c.lower()]
    ticker_cols = [c for c in dl.columns if "ticker" in c.lower() or "symbol" in c.lower()]
    pct_cols = [c for c in dl.columns if "pct" in c.lower() or "%" in c.lower() or "drop" in c.lower() or "change" in c.lower()]
    
    print(f"Date cols: {date_cols}")
    print(f"Ticker cols: {ticker_cols}")
    print(f"Pct cols: {pct_cols}")
    
    # Load RidingHigh outcomes
    rh = pd.read_csv("/tmp/research/outcomes.csv")
    rh["ScanDate"] = pd.to_datetime(rh["ScanDate"])
    
    # Try to match based on available columns
    if len(ticker_cols) > 0 and len(date_cols) > 0:
        dl_ticker_col = ticker_cols[0]
        dl_date_col = date_cols[0]
        
        dl[dl_date_col] = pd.to_datetime(dl[dl_date_col], errors='coerce')
        
        # Match: same ticker, DropsLab date 1-5 trading days after RH scan
        matches = []
        for _, rh_row in rh.iterrows():
            ticker = rh_row["Ticker"]
            scan_date = rh_row["ScanDate"]
            
            dl_matches = dl[
                (dl[dl_ticker_col] == ticker) &
                (dl[dl_date_col] > scan_date) &
                (dl[dl_date_col] <= scan_date + pd.Timedelta(days=7))  # ~5 trading days
            ]
            
            for _, dl_row in dl_matches.iterrows():
                days_from = (dl_row[dl_date_col] - scan_date).days
                matches.append({
                    "Ticker": ticker,
                    "ScanDate_RH": scan_date,
                    "ScanScore": rh_row.get("Score"),
                    "ScanMxV": rh_row.get("MxV"),
                    "DropDate_DL": dl_row[dl_date_col],
                    "DaysFromDetection": days_from,
                    "hit_tp10_RH": rh_row.get("hit_tp10"),
                    "net_outcome_RH": rh_row.get("net_outcome"),
                })
        
        matches_df = pd.DataFrame(matches)
        print(f"\nMatches found: {len(matches_df)}")
        
        if len(matches_df) > 0:
            # Aggregate stats
            total_rh = len(rh)
            matched_tickers = matches_df["Ticker"].nunique()
            matched_rows = rh["Ticker"].isin(matches_df["Ticker"].unique()).sum()
            
            print(f"RH scans with DropsLab match: {matched_rows}/{total_rh} ({matched_rows/total_rh*100:.1f}%)")
            
            # Compare scores
            rh_matched = rh[rh["Ticker"].isin(matches_df["Ticker"].unique())]
            rh_unmatched = rh[~rh["Ticker"].isin(matches_df["Ticker"].unique())]
            
            print(f"\nScore comparison:")
            print(f"  Matched (n={len(rh_matched)}): mean Score={rh_matched['Score'].mean():.2f}")
            print(f"  Unmatched (n={len(rh_unmatched)}): mean Score={rh_unmatched['Score'].mean():.2f}")
            
            if len(rh_matched) > 5 and len(rh_unmatched) > 5:
                u_stat, p_val = stats.mannwhitneyu(rh_matched["Score"], rh_unmatched["Score"], alternative='two-sided')
                print(f"  Mann-Whitney p={p_val:.4f}")
            
            matches_df.to_csv("/tmp/research/cross_reference.csv", index=False)
        else:
            pd.DataFrame(columns=["Ticker","ScanDate_RH","DropDate_DL","DaysFromDetection"]).to_csv("/tmp/research/cross_reference.csv", index=False)
    else:
        print("Cannot identify ticker/date columns in DropsLab")
        pd.DataFrame().to_csv("/tmp/research/cross_reference.csv", index=False)

except Exception as e:
    print(f"Error reading DropsLab: {e}")
    import traceback
    traceback.print_exc()
    pd.DataFrame(columns=["note"]).assign(note=["DropsLab unavailable"]).to_csv("/tmp/research/cross_reference.csv", index=False)

with open("/tmp/research/checkpoints/phase6.done","w") as f:
    f.write("done\n")
print("\n✓ Phase 6 complete")
