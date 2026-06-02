"""Phase 1: Data Inventory — read all sheets, catalog columns, rows, date ranges, missing values."""
import json
import time
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

CREDS_PATH = "/Users/adilevy/RidingHighPro/google_credentials.json"
CONFIG_PATH = "/Users/adilevy/RidingHighPro/sheets_config.json"
DROPSLAB_ID = "1XM-qId7HAwEu-8-1GGHcy3RoyyAnsYshjZfDrKFnTMI"
DROPSLAB_TAB = "DropsLab-Data"
OUTPUT = "/tmp/research/data_inventory.txt"

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
gc = gspread.authorize(creds)

with open(CONFIG_PATH) as f:
    config = json.load(f)

def safe_float(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except:
        return None

def analyze_sheet(sheet_id, tab_name, label):
    try:
        ss = gc.open_by_key(sheet_id)
        # Try exact tab name first, then first sheet
        try:
            ws = ss.worksheet(tab_name)
        except:
            ws = ss.sheet1
            tab_name = ws.title
        data = ws.get_all_values()
    except Exception as e:
        return {"label": label, "error": str(e)}

    if len(data) < 2:
        return {"label": label, "rows": len(data)-1, "columns": [], "error": "no data rows"}

    headers = data[0]
    rows = data[1:]
    n_rows = len(rows)

    col_info = []
    for i, h in enumerate(headers):
        vals = [r[i] if i < len(r) else "" for r in rows]
        non_empty = [v for v in vals if v.strip()]
        missing_pct = (1 - len(non_empty) / n_rows) * 100 if n_rows > 0 else 100

        numerics = [safe_float(v) for v in non_empty]
        numerics = [x for x in numerics if x is not None]
        dtype = "numeric" if len(numerics) > len(non_empty) * 0.7 and len(non_empty) > 0 else "text"

        outlier_count = 0
        if dtype == "numeric" and len(numerics) > 10:
            arr = np.array(numerics)
            q1, q3 = np.percentile(arr, [25, 75])
            iqr = q3 - q1
            if iqr > 0:
                outlier_count = int(np.sum((arr < q1 - 1.5*iqr) | (arr > q3 + 1.5*iqr)))

        col_info.append({"name": h, "dtype": dtype, "missing_pct": round(missing_pct,1), "outlier_count": outlier_count})

    date_cols = [h for h in headers if any(k in h.lower() for k in ["date","scandate","time","timestamp"])]
    date_range = {}
    for dc in date_cols:
        idx = headers.index(dc)
        vals = sorted(set(r[idx] for r in rows if idx < len(r) and r[idx].strip()))
        if vals:
            date_range[dc] = {"min": vals[0], "max": vals[-1]}

    key_cols = []
    if "Ticker" in headers:
        key_cols.append(headers.index("Ticker"))
    for dc in date_cols[:1]:
        key_cols.append(headers.index(dc))

    dup_count = 0
    if len(key_cols) >= 2:
        keys = set()
        for r in rows:
            k = tuple(r[i] if i < len(r) else "" for i in key_cols)
            if k in keys:
                dup_count += 1
            keys.add(k)

    return {"label": label, "tab": tab_name, "rows": n_rows, "columns": col_info, "date_range": date_range, "duplicate_keys": dup_count}

results = []

# Focus on key sheets for research: post_analysis (all months), timeline_live, score_tracker, daily_snapshots, DropsLab
# Read post_analysis from all months first (most important)
key_sheets = ["post_analysis", "daily_snapshots", "timeline_live", "score_tracker", "daily_summary", "portfolio"]

for month in sorted(config.keys()):
    sheets = config[month]
    for sheet_name in key_sheets:
        if sheet_name not in sheets:
            continue
        sheet_id = sheets[sheet_name]
        label = f"RidingHigh/{month}/{sheet_name}"
        print(f"Reading {label}...", flush=True)
        info = analyze_sheet(sheet_id, sheet_name, label)
        results.append(info)
        time.sleep(1.5)

# DropsLab
print("Reading DropsLab...", flush=True)
info = analyze_sheet(DROPSLAB_ID, DROPSLAB_TAB, "DropsLab/DropsLab-Data")
results.append(info)

# Write inventory
with open(OUTPUT, "w") as f:
    f.write("=" * 80 + "\n")
    f.write("DATA INVENTORY — RidingHigh Pro Deep Research\n")
    f.write("=" * 80 + "\n\n")

    for r in results:
        f.write(f"\n{'─' * 60}\n")
        f.write(f"Sheet: {r['label']}\n")
        if 'tab' in r:
            f.write(f"Tab: {r.get('tab','')}\n")
        f.write(f"{'─' * 60}\n")

        if "error" in r:
            f.write(f"  ERROR: {r['error']}\n")
            continue

        f.write(f"  Rows: {r['rows']}\n")
        f.write(f"  Duplicate keys: {r['duplicate_keys']}\n")

        if r.get("date_range"):
            for col, rng in r["date_range"].items():
                f.write(f"  Date range ({col}): {rng['min']} .. {rng['max']}\n")

        f.write(f"\n  {'Column':<30} {'Type':<10} {'Missing%':<10} {'Outliers':<10}\n")
        f.write(f"  {'─'*30} {'─'*10} {'─'*10} {'─'*10}\n")
        for c in r["columns"]:
            f.write(f"  {c['name']:<30} {c['dtype']:<10} {c['missing_pct']:<10} {c['outlier_count']:<10}\n")

    f.write(f"\n\n{'=' * 80}\nEND OF INVENTORY\n")

print(f"\nInventory saved to {OUTPUT}")
print(f"Total sheets analyzed: {len(results)}")
print(f"Errors: {sum(1 for r in results if 'error' in r)}")

# Save checkpoint
with open("/tmp/research/checkpoints/phase1.done", "w") as f:
    f.write("done\n")
