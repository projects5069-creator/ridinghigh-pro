#!/usr/bin/env python3
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import pandas as pd
from datetime import datetime, timedelta
import pytz
PERU_TZ = pytz.timezone("America/Lima")
COLS = ["Date","ScanTime","Ticker","ScanDate","Price","Score","MxV","RunUp","RSI","ATRX","REL_VOL","Gap","VWAP"]
def trading_days_after(s, n=3):
    d = datetime.strptime(s, "%Y-%m-%d")
    days = []
    while len(days) < n:
        d += timedelta(days=1)
        if d.weekday() < 5: days.append(d.strftime("%Y-%m-%d"))
    return days
def run():
    from gsheets_sync import _get_client, SPREADSHEET_ID
    gc = _get_client()
    if gc is None: print("ERROR: no connection"); return
    sh = gc.open_by_key(SPREADSHEET_ID)
    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    print(f"[ScoreTracker] {today}")
    port_data = sh.worksheet("portfolio").get_all_values()
    if len(port_data) <= 1: print("no portfolio"); return
    port_df = pd.DataFrame(port_data[1:], columns=port_data[0])
    active = set()
    for _, r in port_df.iterrows():
        sd = str(r.get("Date","")).strip(); tk = str(r.get("Ticker","")).strip()
        if sd and tk:
            try:
                if today in trading_days_after(sd, 3): active.add((tk, sd))
            except: pass
    if not active: print(f"no active stocks for {today}"); return
    print(f"tracking: {active}")
    tl_data = sh.worksheet("timeline_live").get_all_values()
    if len(tl_data) <= 1: print("no timeline"); return
    tl_df = pd.DataFrame(tl_data[1:], columns=tl_data[0])
    tickers = {t for t,_ in active}
    today_tl = tl_df[(tl_df["Date"]==today)&(tl_df["Ticker"].isin(tickers))].copy()
    if today_tl.empty: print("no rows today"); return
    t2sd = {t:sd for t,sd in active}
    today_tl["ScanDate"] = today_tl["Ticker"].map(t2sd)
    for col in COLS:
        if col not in today_tl.columns: today_tl[col] = ""
    today_tl = today_tl[COLS].copy()
    print(f"{len(today_tl)} rows")
    try:
        ws = sh.worksheet("score_tracker")
        ex = ws.get_all_values()
        if len(ex) > 1:
            ex_df = pd.DataFrame(ex[1:], columns=ex[0])
            ex_df = ex_df[~((ex_df["Date"]==today)&(ex_df["Ticker"].isin(tickers)))]
            combined = pd.concat([ex_df, today_tl], ignore_index=True)
        else:
            combined = today_tl
    except:
        ws = sh.add_worksheet(title="score_tracker", rows=50000, cols=20)
        combined = today_tl
    combined = combined.fillna("").astype(str)
    ws.clear()
    ws.update([list(combined.columns)] + combined.values.tolist())
    print(f"saved {len(combined)} rows")
if __name__ == "__main__": run()
