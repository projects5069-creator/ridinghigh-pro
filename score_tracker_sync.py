#!/usr/bin/env python3
"""
RidingHigh Pro - Score Tracker Sync
Runs every minute 08:30-15:00 Peru.
Tracks portfolio stocks for 3 trading days after entry.
Saves: Date, ScanTime, Ticker, ScanDate, Price, Score
"""
import sys, os, warnings
warnings.filterwarnings("ignore")

import pandas as pd
from datetime import datetime, timedelta
import pytz

PERU_TZ = pytz.timezone("America/Lima")

def is_market_hours():
    now = datetime.now(PERU_TZ)
    if now.weekday() >= 5: return False
    from datetime import time
    return time(8, 30) <= now.time() <= time(15, 0)

def trading_days_after(s, n=3):
    d = datetime.strptime(s, "%Y-%m-%d")
    days = []
    while len(days) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days.append(d.strftime("%Y-%m-%d"))
    return days

def get_score_and_price(ticker):
    try:
        import yfinance as yf
        from ta.momentum import RSIIndicator
        from ta.volatility import AverageTrueRange
        stock = yf.Ticker(ticker)
        hist = stock.history(period="60d")
        if hist.empty or len(hist) < 2: return None, None
        info = stock.info
        current = hist.iloc[-1]
        previous = hist.iloc[-2]
        price = float(current["Close"])
        volume = int(current["Volume"])
        market_cap = info.get("marketCap", 0)
        if not market_cap: return None, None
        rsi = 50; atrx = 0; rel_vol = 1.0; run_up = 0; gap = 0; vwap_dist = 0
        if len(hist) >= 14:
            try: rsi = float(RSIIndicator(hist["Close"], 14).rsi().iloc[-1])
            except: pass
            try:
                atr = float(AverageTrueRange(hist["High"], hist["Low"], hist["Close"], 14).average_true_range().iloc[-1])
                atrx = (float(current["High"]) - float(current["Low"])) / atr if atr > 0 else 0
            except: pass
        try:
            avg_vol = info.get("averageVolume", volume)
            rel_vol = volume / avg_vol if avg_vol > 0 else 1.0
        except: pass
        try: run_up = ((price - float(current["Open"])) / float(current["Open"])) * 100
        except: pass
        try: gap = ((float(current["Open"]) - float(previous["Close"])) / float(previous["Close"])) * 100
        except: pass
        try:
            vwap = (float(current["High"]) + float(current["Low"]) + price) / 3
            vwap_dist = ((price / vwap) - 1) * 100 if vwap > 0 else 0
        except: pass
        mxv = (market_cap - price * volume) / market_cap if market_cap > 0 else 0
        score = 0
        if mxv < 0: score += min(abs(mxv)/50,1)*30
        if run_up > 0: score += min(run_up/50,1)*20
        score += min(rel_vol/2,1)*20
        score += (rsi/80)*10 if rsi<=80 else 10
        score += min(atrx/3,1)*10
        if gap<15: score += min((15-gap)/15,1)*5
        if vwap_dist>0: score += min(vwap_dist/15,1)*5
        return round(price,2), round(score,2)
    except Exception as e:
        print(f"  [!] {ticker}: {e}")
        return None, None

def run():
    import sheets_manager
    now = datetime.now(PERU_TZ)
    today = now.strftime("%Y-%m-%d")
    scan_time = now.strftime("%H:%M")
    print(f"[ScoreTracker] {today} {scan_time}")

    if not is_market_hours():
        print("[ScoreTracker] Outside market hours — skipping"); return

    gc = sheets_manager._get_gc()
    if gc is None:
        print("[ScoreTracker] ❌ No Google credentials — GOOGLE_CREDENTIALS_JSON env var missing"); return
    print("[ScoreTracker] ✅ Connected to Google Sheets")

    ws_port = sheets_manager.get_worksheet("portfolio", gc=gc)
    port_data = ws_port.get_all_values() if ws_port else []
    if len(port_data) <= 1:
        print("[ScoreTracker] portfolio sheet is empty"); return
    port_df = pd.DataFrame(port_data[1:], columns=port_data[0])
    print(f"[ScoreTracker] Portfolio: {len(port_df)} rows, dates: {sorted(port_df['Date'].unique())[-3:]}")

    active = set()
    for _, r in port_df.iterrows():
        sd = str(r.get("Date","")).strip()
        tk = str(r.get("Ticker","")).strip()
        if sd and tk:
            try:
                if today in trading_days_after(sd, 3):
                    active.add((tk, sd))
            except Exception:
                pass
    if not active:
        print(f"[ScoreTracker] No active stocks for {today}"); return
    print(f"[ScoreTracker] Tracking {len(active)} stocks: {sorted(t for t,_ in active)}")
    new_rows = []
    for ticker, scan_date in sorted(active):
        price, score = get_score_and_price(ticker)
        if price is None: continue
        new_rows.append({"Date":today,"ScanTime":scan_time,"Ticker":ticker,"ScanDate":scan_date,"Price":price,"Score":score})
        print(f"  ✅ {ticker} {score:.2f}")
    if not new_rows: return
    new_df = pd.DataFrame(new_rows)[["Date","ScanTime","Ticker","ScanDate","Price","Score"]]
    ws_st = sheets_manager.get_worksheet("score_tracker", gc=gc)
    if ws_st:
        if len(ws_st.get_all_values()) > 1:
            ws_st.append_rows(new_df.astype(str).values.tolist())
        else:
            ws_st.update([list(new_df.columns)] + new_df.astype(str).values.tolist())
        print(f"✅ Saved {len(new_rows)} rows")

if __name__ == "__main__": run()
