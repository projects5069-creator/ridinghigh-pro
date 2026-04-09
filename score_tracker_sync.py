#!/usr/bin/env python3
"""
RidingHigh Pro - Score Tracker Sync
Runs every minute during market hours (08:30-15:00 Peru).
Scans portfolio stocks that are within 3 trading days of entry.
Saves one row per stock per minute to score_tracker sheet.
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))

import pandas as pd
from datetime import datetime, timedelta
import pytz

PERU_TZ = pytz.timezone("America/Lima")

def is_market_hours():
    now = datetime.now(PERU_TZ)
    if now.weekday() >= 5: return False
    t = now.time()
    from datetime import time
    return time(8, 30) <= t <= time(15, 0)

def trading_days_after(scan_date_str, n=3):
    d = datetime.strptime(scan_date_str, "%Y-%m-%d")
    days = []
    while len(days) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days.append(d.strftime("%Y-%m-%d"))
    return days

def scan_ticker(ticker):
    """Scan a single ticker and return score + metrics. Same logic as auto_scanner."""
    try:
        import yfinance as yf
        from ta.momentum import RSIIndicator
        from ta.volatility import AverageTrueRange
        import requests
        from bs4 import BeautifulSoup

        # Fetch price from FINVIZ
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        price = None
        change = None
        volume = None
        market_cap = None

        try:
            price_tag = soup.find("strong", {"class": "quote-price_strong"})
            if price_tag:
                price = float(price_tag.text.strip().replace(",",""))
        except: pass

        if not price:
            try:
                table = soup.find("table", {"class": "snapshot-table2"})
                if table:
                    cells = table.find_all("td")
                    for i, cell in enumerate(cells):
                        if "Price" in cell.text and i+1 < len(cells):
                            price = float(cells[i+1].text.strip().replace(",",""))
                        if "Change" in cell.text and i+1 < len(cells):
                            change_str = cells[i+1].text.strip().replace("%","")
                            change = float(change_str)
                        if "Volume" in cell.text and i+1 < len(cells):
                            v = cells[i+1].text.strip().replace(",","")
                            volume = int(v) if v.isdigit() else None
                        if "Market Cap" in cell.text and i+1 < len(cells):
                            mc_str = cells[i+1].text.strip()
                            if mc_str.endswith("B"): market_cap = float(mc_str[:-1]) * 1e9
                            elif mc_str.endswith("M"): market_cap = float(mc_str[:-1]) * 1e6
            except: pass

        stock = yf.Ticker(ticker)
        hist  = stock.history(period="60d")
        if hist.empty or len(hist) < 2: return None

        info     = stock.info
        current  = hist.iloc[-1]
        previous = hist.iloc[-2]

        if not price:
            price = float(current["Close"])
        if not volume:
            volume = int(current["Volume"])
        if not market_cap:
            market_cap = info.get("marketCap", price * info.get("sharesOutstanding", 0))
        if not market_cap or market_cap == 0:
            return None

        if not change:
            change = ((price - float(previous["Close"])) / float(previous["Close"])) * 100

        rsi = 50; atrx = 0; rel_vol = 1.0; run_up = 0
        gap = 0; vwap_dist = 0
        open_price = 0; prev_close = 0; atr14_raw = 0
        high_today = 0; low_today = 0; vwap_price = 0

        if len(hist) >= 14:
            try:
                rsi_vals = RSIIndicator(close=hist["Close"], window=14).rsi()
                if not rsi_vals.empty and not pd.isna(rsi_vals.iloc[-1]):
                    rsi = float(rsi_vals.iloc[-1])
            except: pass

            try:
                atr_vals = AverageTrueRange(
                    high=hist["High"], low=hist["Low"],
                    close=hist["Close"], window=14
                ).average_true_range()
                atr = float(atr_vals.iloc[-1]) if not atr_vals.empty else float(current["High"] - current["Low"])
                atrx = (float(current["High"]) - float(current["Low"])) / atr if atr > 0 else 0
                atr14_raw = round(atr, 4)
            except: pass

        try:
            avg_vol = info.get("averageVolume", volume)
            rel_vol = volume / avg_vol if avg_vol > 0 else 1.0
        except: pass

        try:
            open_price = round(float(current["Open"]), 4)
            run_up = ((price - float(current["Open"])) / float(current["Open"])) * 100
        except: pass

        try:
            prev_close = round(float(previous["Close"]), 4)
            gap = ((float(current["Open"]) - float(previous["Close"])) / float(previous["Close"])) * 100
        except: pass

        try:
            high_today  = round(float(current["High"]), 4)
            low_today   = round(float(current["Low"]), 4)
            vwap_price  = round((float(current["High"]) + float(current["Low"]) + price) / 3, 4)
            vwap_dist   = ((price / vwap_price) - 1) * 100 if vwap_price > 0 else 0
        except: pass

        mxv = (market_cap - price * volume) / market_cap if market_cap > 0 else 0

        # Calculate score (same weights as auto_scanner)
        score = 0
        if mxv < 0:   score += min(abs(mxv) / 50, 1) * 30
        if run_up > 0: score += min(run_up / 50, 1) * 20
        score += min(rel_vol / 2, 1) * 20
        if rsi > 80:  score += 10
        else:         score += (rsi / 80) * 10
        score += min(atrx / 3, 1) * 10
        if gap < 15:  score += min((15 - gap) / 15, 1) * 5
        if vwap_dist > 0: score += min(vwap_dist / 15, 1) * 5

        return {
            "Price":   round(price, 2),
            "Score":   round(score, 2),
            "MxV":     round(mxv, 2),
            "RunUp":   round(run_up, 2),
            "RSI":     round(rsi, 2),
            "ATRX":    round(atrx, 2),
            "REL_VOL": round(rel_vol, 2),
            "Gap":     round(gap, 2),
            "VWAP":    round(vwap_dist, 2),
        }
    except Exception as e:
        print(f"  [!] {ticker}: {e}")
        return None


def run():
    if not is_market_hours():
        print("[ScoreTracker] Outside market hours — skipping")
        return

    from gsheets_sync import _get_client, SPREADSHEET_ID
    gc = _get_client()
    if gc is None:
        print("[ScoreTracker] ERROR: Cannot connect to Google Sheets"); return

    sh = gc.open_by_key(SPREADSHEET_ID)
    now_peru = datetime.now(PERU_TZ)
    today    = now_peru.strftime("%Y-%m-%d")
    scan_time = now_peru.strftime("%H:%M")
    print(f"[ScoreTracker] {today} {scan_time}")

    # Load portfolio — find stocks within 3 trading days of entry
    port_data = sh.worksheet("portfolio").get_all_values()
    if len(port_data) <= 1:
        print("[ScoreTracker] No portfolio data"); return

    port_df = pd.DataFrame(port_data[1:], columns=port_data[0])
    active_pairs = set()
    for _, r in port_df.iterrows():
        sd = str(r.get("Date", "")).strip()
        tk = str(r.get("Ticker", "")).strip()
        if sd and tk:
            try:
                if today in trading_days_after(sd, 3):
                    active_pairs.add((tk, sd))
            except: pass

    if not active_pairs:
        print(f"[ScoreTracker] No active stocks for {today}"); return

    print(f"[ScoreTracker] Scanning {len(active_pairs)} stocks: {[t for t,_ in active_pairs]}")

    # Scan each ticker
    new_rows = []
    for ticker, scan_date in active_pairs:
        metrics = scan_ticker(ticker)
        if metrics is None:
            print(f"  [!] {ticker}: scan failed"); continue
        row = {
            "Date":     today,
            "ScanTime": scan_time,
            "Ticker":   ticker,
            "ScanDate": scan_date,
        }
        row.update(metrics)
        new_rows.append(row)
        print(f"  ✅ {ticker} Score={metrics['Score']:.2f} Price={metrics['Price']}")

    if not new_rows:
        print("[ScoreTracker] No rows to save"); return

    new_df = pd.DataFrame(new_rows)

    # Append only (don't clear history)
    COLS = ["Date","ScanTime","Ticker","ScanDate","Price","Score","MxV","RunUp","RSI","ATRX","REL_VOL","Gap","VWAP"]
    for col in COLS:
        if col not in new_df.columns: new_df[col] = ""
    new_df = new_df[COLS]

    try:
        ws = sh.worksheet("score_tracker")
        ex = ws.get_all_values()
        if len(ex) > 1:
            # Just append -- no clear -- preserve history
            ws.append_rows(new_df.fillna("").astype(str).values.tolist())
        else:
            ws.update([list(new_df.columns)] + new_df.fillna("").astype(str).values.tolist())
    except:
        ws = sh.add_worksheet(title="score_tracker", rows=100000, cols=20)
        ws.update([list(new_df.columns)] + new_df.fillna("").astype(str).values.tolist())

    print(f"[ScoreTracker] ✅ Appended {len(new_rows)} rows")


if __name__ == "__main__":
    run()
