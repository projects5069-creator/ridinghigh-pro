"""Phase 2: Outcome Computation from post_analysis sheets."""
import json, time, sys
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

CREDS_PATH = "/Users/adilevy/RidingHighPro/google_credentials.json"
CONFIG_PATH = "/Users/adilevy/RidingHighPro/sheets_config.json"

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly","https://www.googleapis.com/auth/drive.readonly"]
creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
gc = gspread.authorize(creds)

with open(CONFIG_PATH) as f:
    config = json.load(f)

# Read post_analysis from all months
all_rows = []
for month in sorted(config.keys()):
    if "post_analysis" not in config[month]:
        continue
    sheet_id = config[month]["post_analysis"]
    print(f"Reading post_analysis for {month}...", flush=True)
    try:
        ss = gc.open_by_key(sheet_id)
        ws = ss.sheet1
        data = ws.get_all_values()
        if len(data) < 2:
            print(f"  No data rows for {month}")
            continue
        headers = data[0]
        for row in data[1:]:
            d = dict(zip(headers, row))
            d["_month"] = month
            all_rows.append(d)
        print(f"  Got {len(data)-1} rows")
    except Exception as e:
        print(f"  Error: {e}")
    time.sleep(2)

print(f"\nTotal raw rows: {len(all_rows)}")

df = pd.DataFrame(all_rows)

# Convert key numeric columns
def to_float(s):
    try:
        return float(str(s).replace(",","").replace("%","").strip())
    except:
        return np.nan

numeric_cols = ["Score","MxV","RunUp","RSI","ATRX","REL_VOL","Gap","TypicalPriceDist",
                "ScanPrice","ScanChange%","Volume","MarketCap","MaxDrop%",
                "TP10_Hit","TP15_Hit","TP20_Hit","SL_Hit_D5","IntraDay_SL","SL_Hit_D0",
                "D1_Open","D1_High","D1_Low","D1_Close",
                "D2_Open","D2_High","D2_Low","D2_Close",
                "D3_Open","D3_High","D3_Low","D3_Close",
                "D4_Open","D4_High","D4_Low","D4_Close",
                "D5_Open","D5_High","D5_Low","D5_Close",
                "PeakScorePrice","IntraHigh","IntraLow","D0_Close","D0_Volume",
                "D0_Drop%","IntraDay_TP10","MinToClose",
                "Volume_raw","MarketCap_raw","Float%","PriceToHigh","PriceTo52WHigh",
                "EntryScore","ScoreMax","ScoreMin","ScoreStd","ScoreAtFirst","ScoreAtLast",
                "D1_Gap%","BestDay","DayRunUp%","Float_pct_raw",
                "D0_Open","D0_High","D0_Low","D0_Drop%_from_High",
                "Price_vs_SMA20","Consecutive_Up","RealFloat","RealFloat_M","DaysSinceIPO",
                "ScanCount","PeakScore"]

for c in numeric_cols:
    if c in df.columns:
        df[c] = df[c].apply(to_float)

# Check column existence
required = ["ScanPrice","MaxDrop%","D1_Open","D1_Close","D5_Close"]
for c in required:
    if c not in df.columns:
        print(f"MISSING COLUMN: {c}")

print(f"\nColumns available: {len(df.columns)}")
print(f"Rows with ScanPrice: {df['ScanPrice'].notna().sum()}")
print(f"Rows with MaxDrop%: {df['MaxDrop%'].notna().sum()}")

# Filter to rows with complete OHLC data (at least D1)
mask_complete = df["D1_Open"].notna() & df["ScanPrice"].notna() & df["MaxDrop%"].notna()
print(f"Rows with complete D1 data: {mask_complete.sum()}")
df_complete = df[mask_complete].copy()

# Compute outcomes
df_complete["drop_max_pct"] = df_complete["MaxDrop%"]

# Compute rise_max_pct from D1..D5 highs
high_cols = [c for c in ["D0_High","D1_High","D2_High","D3_High","D4_High","D5_High"] if c in df_complete.columns]
df_complete["max_high_d1_d5"] = df_complete[["D1_High","D2_High","D3_High","D4_High","D5_High"]].max(axis=1)
df_complete["rise_max_pct"] = (df_complete["max_high_d1_d5"] - df_complete["ScanPrice"]) / df_complete["ScanPrice"] * 100

# Also check SL columns already in sheet
if "SL_Hit_D5" in df_complete.columns:
    print(f"\nSL_Hit_D5 distribution:\n{df_complete['SL_Hit_D5'].value_counts()}")
if "SL_Hit_D0" in df_complete.columns:
    print(f"\nSL_Hit_D0 distribution:\n{df_complete['SL_Hit_D0'].value_counts()}")

df_complete["drop_d1_open"] = (df_complete["D1_Open"] - df_complete["ScanPrice"]) / df_complete["ScanPrice"] * 100
df_complete["drop_d1_close"] = (df_complete["D1_Close"] - df_complete["ScanPrice"]) / df_complete["ScanPrice"] * 100
df_complete["drop_d5_close"] = (df_complete["D5_Close"] - df_complete["ScanPrice"]) / df_complete["ScanPrice"] * 100

df_complete["hit_tp10"] = df_complete["drop_max_pct"] <= -10
df_complete["hit_sl7"] = df_complete["rise_max_pct"] >= 7

# net_outcome
def classify(row):
    if row["hit_sl7"]:
        return "SL_HIT"
    elif row["hit_tp10"]:
        return "TP_HIT"
    elif row["drop_max_pct"] <= -3:
        return "PARTIAL"
    else:
        return "OPEN"

df_complete["net_outcome"] = df_complete.apply(classify, axis=1)

# Extract Hour from FirstScanTime or PeakScoreTime
if "FirstScanTime" in df_complete.columns:
    def extract_hour(t):
        try:
            parts = str(t).split(":")
            return int(parts[0])
        except:
            return np.nan
    df_complete["Hour"] = df_complete["FirstScanTime"].apply(extract_hour)

# Select output columns
out_cols = ["Ticker","ScanDate","ScanPrice","Score","MxV","RunUp","REL_VOL","RSI",
            "ATRX","Gap","TypicalPriceDist","Volume_raw","MarketCap_raw","Hour",
            "Float%","PriceToHigh","PriceTo52WHigh","ScanChange%","DayRunUp%",
            "EntryScore","ScoreMax","ScoreMin","ScoreStd","ScanCount",
            "Sector","Industry","MarketCapCategory",
            "drop_max_pct","rise_max_pct","drop_d1_open","drop_d1_close","drop_d5_close",
            "hit_tp10","hit_sl7","net_outcome",
            "D1_Gap%","FirstScanTime","LastScanTime","PeakScoreTime"]

# Keep only columns that exist
out_cols = [c for c in out_cols if c in df_complete.columns]
df_out = df_complete[out_cols].copy()

# Rename for clarity
df_out = df_out.rename(columns={"Volume_raw": "Volume", "MarketCap_raw": "MarketCap", "TypicalPriceDist": "VWAP_dev"})

df_out.to_csv("/tmp/research/outcomes.csv", index=False)

# Sanity checks
print(f"\n{'='*60}")
print(f"SANITY CHECKS")
print(f"{'='*60}")
print(f"Total records in outcomes.csv: {len(df_out)}")
print(f"\nOutcome distribution:")
print(df_out["net_outcome"].value_counts())
tp_rate = (df_out["net_outcome"]=="TP_HIT").sum() / len(df_out) * 100
print(f"\nTP_HIT rate: {tp_rate:.1f}%")
sl_count = (df_out["net_outcome"]=="SL_HIT").sum()
print(f"SL_HIT count: {sl_count}")

print(f"\ndrop_max_pct range: {df_out['drop_max_pct'].min():.2f} .. {df_out['drop_max_pct'].max():.2f}")

# Check sanity
ok = True
if tp_rate < 30 or tp_rate > 95:
    print(f"WARNING: TP_HIT rate {tp_rate:.1f}% outside expected 60-80%")
if sl_count == 0:
    print("FAIL: No SL_HIT records!")
    ok = False
if df_out["drop_max_pct"].max() > 0.01:
    print(f"WARNING: drop_max_pct has positive values (max={df_out['drop_max_pct'].max():.2f})")

if ok:
    print("\n✓ All sanity checks passed")
    with open("/tmp/research/checkpoints/phase2.done","w") as f:
        f.write("done\n")
else:
    print("\n✗ Sanity check FAILED — investigate before proceeding")
    sys.exit(1)
