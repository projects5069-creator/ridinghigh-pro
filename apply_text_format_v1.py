#!/usr/bin/env python3
"""
apply_text_format_v1.py
─────────────────────────
Sets cell number-format to TEXT on all known time-of-day columns.
Resizes sheets if needed (empty sheets may have fewer columns than schema).

Idempotent. Only changes format/dimensions, never data.

Usage:
    python apply_text_format_v1.py                    # current month
    python apply_text_format_v1.py --month 2026-06    # specific month
    python apply_text_format_v1.py --next-month       # next Peru month
    python apply_text_format_v1.py --dry-run           # preview only
"""
import argparse, json, os, sys, time
from datetime import datetime
import pytz, requests
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

PERU_TZ = pytz.timezone("America/Lima")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TIME_COLUMNS = {
    "timeline_live":    [("ScanTime", 1)],
    "daily_summary":    [("FirstScanTime", 8), ("LastScanTime", 9)],
    "post_analysis":    [("FirstScanTime", 51), ("LastScanTime", 52), ("PeakScoreTime", 62)],
    "score_tracker":    [("ScanTime", 1)],
    "live_trades":      [("ScanTime", 1)],
    "ticker_follow_up": [("ScanTime", 1)],
    "portfolio_live":   [("LastUpdated", 9)],
    "paper_portfolio":  [("EntryTime", 3), ("ExitTime", 19)],
    "borrow_data":      [("CheckTime", 2)],
}

SHEET_COLUMN_COUNTS = {
    "timeline_live": 28, "daily_snapshots": 27, "daily_summary": 10,
    "post_analysis": 105, "portfolio": 6, "portfolio_live": 10,
    "score_tracker": 7, "live_trades": 7, "ticker_follow_up": 30,
    "paper_portfolio": 25, "decision_log": 41, "score_analytics": 25,
    "postmortems": 17, "system_events": 7, "market_context": 11,
    "news_findings": 11, "pending_suggestions": 14, "config_history": 10,
    "borrow_data": 9, "agent_scorecard": 7,
}

def _next_month_key():
    now = datetime.now(PERU_TZ)
    return f"{now.year + 1:04d}-01" if now.month == 12 else f"{now.year:04d}-{now.month + 1:02d}"

def _current_month_key():
    return datetime.now(PERU_TZ).strftime("%Y-%m")

def _load_credentials():
    cj = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if cj: return Credentials.from_service_account_info(json.loads(cj), scopes=SCOPES)
    if os.path.exists("google_credentials.json"):
        return Credentials.from_service_account_file("google_credentials.json", scopes=SCOPES)
    print("No credentials"); sys.exit(1)

def _load_config():
    with open("sheets_config.json") as f: return json.load(f)

def _get_sheet_state(sid, token):
    hdrs = {"Authorization": f"Bearer {token}"}
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{sid}"
           f"?ranges=1:1&fields=sheets(properties(sheetId,gridProperties),"
           f"data(rowData(values(formattedValue))))")
    resp = requests.get(url, headers=hdrs)
    if resp.status_code != 200: raise RuntimeError(f"HTTP {resp.status_code}")
    meta = resp.json()
    sheet = meta["sheets"][0]
    props = sheet["properties"]
    grid = props.get("gridProperties", {})
    header_strs = []
    data_blocks = sheet.get("data", [])
    if data_blocks:
        rd = data_blocks[0].get("rowData", [])
        if rd: header_strs = [c.get("formattedValue", "") for c in rd[0].get("values", [])]
    return {"tab_id": props["sheetId"], "header_strs": header_strs,
            "current_cols": grid.get("columnCount", 0)}

def _resize_sheet(sid, tab_id, new_cols, token):
    hdrs = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"requests": [{"updateSheetProperties": {
        "properties": {"sheetId": tab_id, "gridProperties": {"columnCount": new_cols}},
        "fields": "gridProperties.columnCount"
    }}]}
    resp = requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}:batchUpdate",
                         headers=hdrs, json=body)
    if resp.status_code != 200: raise RuntimeError(f"Resize HTTP {resp.status_code}")

def apply_text_format(month_key, dry_run=False):
    print(f"\n{'='*60}")
    print(f"  apply_text_format_v1 — {month_key}  {'(DRY-RUN)' if dry_run else ''}")
    print(f"{'='*60}\n")
    config = _load_config()
    month_cfg = config.get(month_key, {})
    if not month_cfg: print(f"Month {month_key} not in config"); return {}
    creds = _load_credentials(); creds.refresh(Request())
    stats = {}

    for sheet_name, time_col_defs in TIME_COLUMNS.items():
        sid = month_cfg.get(sheet_name)
        if not sid:
            stats[sheet_name] = {"status": "not_in_config"}; continue
        try:
            creds.refresh(Request())
            state = _get_sheet_state(sid, creds.token)
            tab_id, header_strs, current_cols = state["tab_id"], state["header_strs"], state["current_cols"]
            has_headers = len(header_strs) > 0
            mode = "header" if has_headers else "fallback"

            need_cols = max(SHEET_COLUMN_COUNTS.get(sheet_name, 0),
                           max(idx for _, idx in time_col_defs) + 1)
            resize_msg = ""
            if current_cols < need_cols:
                if dry_run:
                    resize_msg = f" [would resize {current_cols}→{need_cols}]"
                else:
                    _resize_sheet(sid, tab_id, need_cols, creds.token)
                    resize_msg = f" [resized {current_cols}→{need_cols}]"
                    time.sleep(0.5)

            requests_list, cols_done = [], []
            for col_name, fallback_idx in time_col_defs:
                if has_headers:
                    if col_name in header_strs: col_idx = header_strs.index(col_name)
                    else: continue
                else:
                    col_idx = fallback_idx
                requests_list.append({"repeatCell": {
                    "range": {"sheetId": tab_id, "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}}},
                    "fields": "userEnteredFormat.numberFormat"
                }})
                cols_done.append(f"{col_name}(col {col_idx})")

            if not requests_list:
                stats[sheet_name] = {"status": "no_cols"}; continue
            if dry_run:
                print(f"  [DRY-RUN] {sheet_name} ({mode}): TEXT on {cols_done}{resize_msg}")
                stats[sheet_name] = {"status": "dry_run"}; continue

            creds.refresh(Request())
            h2 = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
            resp = requests.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}:batchUpdate",
                                 headers=h2, json={"requests": requests_list})
            if resp.status_code != 200:
                print(f"  ❌ {sheet_name}: HTTP {resp.status_code}"); stats[sheet_name] = {"status": "error"}; continue
            print(f"  ✅ {sheet_name} ({mode}): TEXT on {cols_done}{resize_msg}")
            stats[sheet_name] = {"status": "ok", "columns": cols_done}; time.sleep(1)
        except Exception as e:
            print(f"  ❌ {sheet_name}: {e}"); stats[sheet_name] = {"status": "exception"}

    print(f"\n{'='*60}")
    ok = sum(1 for s in stats.values() if s.get("status") == "ok")
    dry = sum(1 for s in stats.values() if s.get("status") == "dry_run")
    skp = sum(1 for s in stats.values() if s.get("status") in ("not_in_config", "no_cols"))
    err = sum(1 for s in stats.values() if s.get("status") in ("error", "exception"))
    print(f"  Summary: {ok} OK | {dry} dry-run | {skp} skipped | {err} errors")
    print(f"{'='*60}"); return stats

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", type=str, default=None)
    parser.add_argument("--next-month", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.next_month: mk = _next_month_key()
    elif args.month: mk = args.month
    else: mk = _current_month_key()
    stats = apply_text_format(mk, dry_run=args.dry_run)
    sys.exit(0 if not any(s.get("status") in ("error","exception") for s in stats.values()) else 1)

if __name__ == "__main__": main()
