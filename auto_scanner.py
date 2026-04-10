#!/usr/bin/env python3
"""
RidingHigh Pro - Auto Scanner for GitHub Actions
Runs without Streamlit, saves directly to Google Sheets (new multi-sheet architecture)
"""

import os
import sys
import json
import time
import pytz
import pandas as pd
from datetime import datetime, time as dt_time

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

PERU_TZ = pytz.timezone("America/Lima")

def get_peru_time():
    return datetime.now(PERU_TZ)

def is_market_hours():
    now = get_peru_time()
    market_open  = dt_time(8, 30)
    market_close = dt_time(15, 0)
    return is_trading_day(now.date()) and market_open <= now.time() <= market_close

def is_snapshot_time():
    now = get_peru_time()
    return dt_time(14, 55) <= now.time() < dt_time(15, 5)

def is_trading_day(date=None):
    """
    Returns True if the given date (default: today Peru time) is a NASDAQ trading day.
    Checks weekends + US market holidays via pandas_market_calendars.
    Falls back to weekday-only check if library unavailable.
    """
    if date is None:
        date = get_peru_time().date()
    try:
        import pandas_market_calendars as mcal
        nyse = mcal.get_calendar("NASDAQ")
        schedule = nyse.schedule(
            start_date=date.strftime("%Y-%m-%d"),
            end_date=date.strftime("%Y-%m-%d")
        )
        return not schedule.empty
    except ImportError:
        # Fallback: weekday only (no holiday detection)
        print("[Scanner] ⚠️ pandas_market_calendars not installed — using weekday-only check")
        return date.weekday() < 5

# ── Google Sheets client ─────────────────────────────────────────────────────
def get_gsheets_client():
    return sheets_manager._get_gc()

def df_to_sheet(ws, df):
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    ws.clear()
    ws.update(data)

# ── Market Cap cache ─────────────────────────────────────────────────────────
_mc_cache = {}

def load_mc_cache():
    global _mc_cache
    cache_path = os.path.expanduser("~/RidingHighPro/data/market_cap_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                _mc_cache = json.load(f)
        except:
            _mc_cache = {}

def save_mc_cache():
    cache_path = os.path.expanduser("~/RidingHighPro/data/market_cap_cache.json")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        with open(cache_path, 'w') as f:
            json.dump(_mc_cache, f)
    except:
        pass

# ── Scanner logic (mirrors dashboard.py exactly) ─────────────────────────────
import yfinance as yf
from finvizfinance.screener.overview import Overview
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

_shares_cache = {}

def parse_market_cap(s):
    try:
        if pd.isna(s) or s == '-': return None
        s = str(s).replace(',', '')
        if 'B' in s: return float(s.replace('B','')) * 1_000_000_000
        if 'M' in s: return float(s.replace('M','')) * 1_000_000
        return float(s)
    except: return None

def parse_volume(s):
    try:
        if pd.isna(s) or s == '-': return None
        s = str(s).replace(',', '')
        if 'M' in s: return int(float(s.replace('M','')) * 1_000_000)
        if 'K' in s: return int(float(s.replace('K','')) * 1_000)
        return int(float(s))
    except: return None

def get_market_cap_smart(ticker, price, finviz_mc=None):
    if finviz_mc and finviz_mc > 0:
        _mc_cache[ticker] = int(finviz_mc)
        return int(finviz_mc)

    try:
        stock = yf.Ticker(ticker)
        mc = stock.info.get('marketCap', None)
        if mc and mc > 0:
            _mc_cache[ticker] = int(mc)
            return int(mc)
    except: pass

    try:
        if ticker not in _shares_cache:
            shares = yf.Ticker(ticker).info.get('sharesOutstanding', None)
            if shares and shares > 0:
                _shares_cache[ticker] = int(shares)
        if ticker in _shares_cache and price > 0:
            mc = int(_shares_cache[ticker] * price)
            _mc_cache[ticker] = mc
            return mc
    except: pass

    if ticker in _mc_cache:
        return _mc_cache[ticker]

    return None

def calculate_mxv(market_cap, price, volume):
    try:
        if market_cap == 0: return 0
        return ((market_cap - (price * volume)) / market_cap) * 100
    except: return 0

def calculate_score(metrics):
    score = 0

    # MxV — 30% — more negative = stronger pump signal
    try:
        if metrics['mxv'] < 0:
            score += min(abs(metrics['mxv']) / 50, 1) * 30
    except: pass

    # RunUp — 20% — rose from open = pump in progress
    try:
        if metrics['run_up'] > 0:
            score += min(metrics['run_up'] / 50, 1) * 20
    except: pass

    # REL_VOL — 20% — higher relative volume = more unusual activity
    try:
        score += min(metrics['rel_vol'] / 2, 1) * 20
    except: pass

    # RSI — 10% — overbought = short candidate
    try:
        if metrics['rsi'] > 80: score += 10
        else: score += (metrics['rsi'] / 80) * 10
    except: pass

    # ATRX — 10% — today range / ATR = how many times bigger than normal
    try:
        score += min(metrics['atrx'] / 3, 1) * 10
    except: pass

    # Gap — 5% — small gap = no catalyst = better short
    try:
        if metrics['gap'] < 15:
            score += min((15 - metrics['gap']) / 15, 1) * 5
    except: pass

    # VWAP — 5% — price above VWAP = extended
    try:
        if metrics['vwap_dist'] > 0:
            score += min(metrics['vwap_dist'] / 15, 1) * 5
    except: pass

    return round(score, 2)

def analyze_ticker(ticker, finviz_row):
    try:
        price = float(finviz_row.get('Price', None))
        if pd.isna(price) or price < 2: return None

        change = float(finviz_row.get('Change', None))
        if pd.isna(change): return None
        change = change * 100

        volume = parse_volume(finviz_row.get('Volume', None))
        if not volume or volume == 0: return None

        finviz_mc = parse_market_cap(finviz_row.get('Market Cap', None))
        market_cap = get_market_cap_smart(ticker, price, finviz_mc)
        if not market_cap or market_cap == 0: return None

        rsi = 50; atrx = 0; rel_vol = 1.0; run_up = 0
        gap = 0; vwap_dist = 0; price_to_high = 0
        price_to_52w_high = 0; float_pct = 0
        shares_outstanding = _shares_cache.get(ticker, 0)
        # Raw variables for metric validation
        open_price = 0; prev_close = 0; atr14_raw = 0
        high_today = 0; low_today = 0; vwap_price = 0
        week52_high = 0

        try:
            stock = yf.Ticker(ticker)
            hist  = stock.history(period='60d')

            if not hist.empty and len(hist) >= 2:
                info    = stock.info
                current  = hist.iloc[-1]
                previous = hist.iloc[-2]

                if len(hist) >= 14:
                    try:
                        rsi_vals = RSIIndicator(close=hist['Close'], window=14).rsi()
                        if not rsi_vals.empty and not pd.isna(rsi_vals.iloc[-1]):
                            rsi = rsi_vals.iloc[-1]
                    except: pass

                    try:
                        atr_vals = AverageTrueRange(
                            high=hist['High'], low=hist['Low'],
                            close=hist['Close'], window=14
                        ).average_true_range()
                        atr = atr_vals.iloc[-1] if not atr_vals.empty else current['High'] - current['Low']
                        atrx = (current["High"] - current["Low"]) / atr if atr > 0 else 0
                        atr14_raw = round(float(atr), 4)  # raw ATR14
                    except: pass

                try:
                    avg_vol = info.get('averageVolume', volume)
                    rel_vol = volume / avg_vol if avg_vol > 0 else 1.0
                except: pass

                try:
                    open_price = round(float(current['Open']), 4)
                    run_up = ((price - current['Open']) / current['Open']) * 100
                except: pass

                try:
                    prev_close = round(float(previous['Close']), 4)
                    gap = ((current['Open'] - previous['Close']) / previous['Close']) * 100
                except: pass

                try:
                    high_today = round(float(current['High']), 4)
                    low_today  = round(float(current['Low']), 4)
                    vwap_price = round((current['High'] + current['Low'] + price) / 3, 4)
                    vwap_dist  = ((price / vwap_price) - 1) * 100 if vwap_price > 0 else 0
                except: pass

                try:
                    high_today     = round(float(current['High']), 4) if high_today == 0 else high_today
                    price_to_high  = ((price - current['High']) / current['High']) * 100
                except: pass

                try:
                    week52_high       = float(info.get('fiftyTwoWeekHigh', price))
                    h52               = week52_high
                    price_to_52w_high = ((price - h52) / h52) * 100 if h52 > 0 else 0
                except: pass

                if shares_outstanding == 0:
                    shares_outstanding = info.get('sharesOutstanding', int(market_cap / price) if price > 0 else 0)

                try:
                    float_pct = (volume / shares_outstanding * 100) if shares_outstanding > 0 else 0
                except: pass

        except: pass

        mxv = calculate_mxv(market_cap, price, volume)
        metrics = {
            'mxv': mxv, 'price_to_52w_high': price_to_52w_high,
            'price_to_high': price_to_high, 'rel_vol': rel_vol,
            'rsi': rsi, 'atrx': atrx, 'run_up': run_up,
            'float_pct': float_pct, 'gap': gap, 'vwap_dist': vwap_dist,
        }
        score = calculate_score(metrics)

        # AvgVolume & FloatShares (already fetched above if available)
        avg_volume   = int(yf.Ticker(ticker).info.get('averageVolume',   0) or 0) if 'stock' not in dir() else 0
        float_shares = int(yf.Ticker(ticker).info.get('floatShares',     0) or 0) if 'stock' not in dir() else 0
        try:
            if 'stock' in dir() and stock:
                avg_volume   = int(stock.info.get('averageVolume',   0) or 0)
                float_shares = int(stock.info.get('floatShares',     0) or 0)
        except: pass

        return {
            # ── Core ──────────────────────────────────────────────────────────
            'Ticker':    ticker,
            'Price':     round(price, 2),
            'Change':    round(change, 2),
            'Volume':    int(volume),
            'MarketCap': int(market_cap),
            # ── Computed score metrics ─────────────────────────────────────────
            'Score':         round(score, 2),
            'MxV':           round(mxv, 2),
            'RunUp':         round(run_up, 2),
            'RSI':           round(rsi, 2),
            'ATRX':          round(atrx, 2),
            'REL_VOL':       round(rel_vol, 2),
            'Gap':           round(gap, 2),
            'VWAP':          round(vwap_dist, 2),
            'PriceToHigh':   round(price_to_high, 2),
            'PriceTo52WHigh':round(price_to_52w_high, 2),
            'Float%':        round(float_pct, 2),
            # ── Raw inputs — for metric validation & future regression ─────────
            'Open_price':       open_price,
            'PrevClose':        prev_close,
            'High_today':       high_today,
            'Low_today':        low_today,
            'VWAP_price':       vwap_price,
            'ATR14_raw':        atr14_raw,
            'Week52High':       round(week52_high, 4),
            'SharesOutstanding':int(shares_outstanding),
            'AvgVolume':        avg_volume,
            'FloatShares':      float_shares,
        }
    except: return None

def fetch_finviz():
    try:
        fviz = Overview()
        fviz.set_filter(filters_dict={'Price': 'Over $2', 'Performance': 'Today +15%'})
        df = fviz.screener_view()
        if df is None or df.empty: return None
        return df.sort_values(by='Change', ascending=False)
    except Exception as e:
        print(f"FINVIZ error: {e}")
        return None

def run_scan():
    print(f"\n🚀 RidingHigh Pro Auto-Scanner")
    now_peru = get_peru_time()
    print(f"⏰ Peru time: {now_peru.strftime('%Y-%m-%d %H:%M:%S')}")

    if not is_market_hours():
        print("⛔ Outside market hours, skipping.")
        return

    load_mc_cache()

    print("🔍 Fetching FINVIZ...")
    finviz_df = fetch_finviz()
    if finviz_df is None:
        print("❌ No stocks from FINVIZ")
        return

    print(f"📊 Analyzing {len(finviz_df)} stocks...")
    results = []
    scanned_tickers = set()
    for idx, row in finviz_df.iterrows():
        ticker = row['Ticker']
        scanned_tickers.add(ticker)
        data = analyze_ticker(ticker, row)
        if data:
            results.append(data)
            print(f"  ✅ {ticker}: {data['Score']}")
        time.sleep(0.1)

    # ── Scan tracked tickers not in FINVIZ ──────────────────────────────────
    try:
        gc = get_gsheets_client()
        ws_tl = sheets_manager.get_worksheet("timeline_live", gc=gc)
        tl_data = ws_tl.get_all_values() if ws_tl else []
        if len(tl_data) > 1:
            tl_df = pd.DataFrame(tl_data[1:], columns=tl_data[0])
            today_str = now_peru.strftime('%Y-%m-%d')
            tracked = set(tl_df[tl_df['Date'] == today_str]['Ticker'].unique())
            missing = tracked - scanned_tickers
            if missing:
                print(f"📌 Tracking {len(missing)} missing tickers...")
                for ticker in missing:
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period='60d')
                        if hist.empty or len(hist) < 2:
                            continue
                        info = stock.info
                        price = hist.iloc[-1]['Close']
                        prev = hist.iloc[-2]['Close']
                        change = ((price - prev) / prev) * 100
                        volume = int(hist.iloc[-1]['Volume'])
                        finviz_row = {'Price': price, 'Change': change/100, 'Volume': str(volume), 'Market Cap': None}
                        data = analyze_ticker(ticker, finviz_row)
                        if data:
                            results.append(data)
                            print(f"  📌 {ticker}: {data['Score']}")
                        time.sleep(0.2)
                    except:
                        pass
    except:
        pass

    if not results:
        print("❌ No results — still running portfolio_live update")
        # Even with no scan results, update portfolio_live (live prices for pending stocks)
        try:
            gc2 = get_gsheets_client()
            if gc2:
                update_portfolio_live(gc2, now_peru)
        except Exception as e:
            print(f"⚠️ portfolio_live (no-results path) error: {e}")
        return

    results = sorted(results, key=lambda x: x['Score'], reverse=True)
    save_mc_cache()

    # ── Save to Google Sheets (new multi-sheet architecture) ─────────────────
    try:
        if 'gc' not in dir() or gc is None:
            gc = get_gsheets_client()
        scan_time = now_peru.strftime('%H:%M')
        today     = now_peru.strftime('%Y-%m-%d')

        results_df = pd.DataFrame(results)

        # ── timeline_live: 8 slim columns only, append-only ──────────────────
        ws_timeline = sheets_manager.get_worksheet("timeline_live", gc=gc)
        slim_cols = sheets_manager.TIMELINE_LIVE_COLS  # ["Date","ScanTime","Ticker","Price","Score","MxV","RunUp","REL_VOL"]
        data_cols = [c for c in slim_cols if c not in ("Date", "ScanTime")]
        new_rows = results_df.reindex(columns=data_cols)
        new_rows.insert(0, 'ScanTime', scan_time)
        new_rows.insert(0, 'Date', today)
        new_rows = new_rows[slim_cols]  # enforce exact column order

        existing_tl = ws_timeline.get_all_values()
        if len(existing_tl) <= 1:
            df_to_sheet(ws_timeline, new_rows)
        else:
            ws_timeline.append_rows(new_rows.astype(str).values.tolist())

        # ── Daily snapshot at 14:59 ───────────────────────────────────────────
        if is_snapshot_time():
            ws_snap = sheets_manager.get_worksheet("daily_snapshots", gc=gc)
            snap_df = results_df.copy()
            snap_df.insert(0, 'Date', today)
            existing_snap = ws_snap.get_all_values()
            if len(existing_snap) <= 1:
                df_to_sheet(ws_snap, snap_df)
            else:
                ex_snap = pd.DataFrame(existing_snap[1:], columns=existing_snap[0])
                other = ex_snap[ex_snap['Date'] != today]
                combined_snap = pd.concat([other, snap_df], ignore_index=True)
                df_to_sheet(ws_snap, combined_snap)
            print("📸 Daily snapshot saved!")

            # ── Portfolio: add Score>=60 positions ───────────────────────────
            ws_port = sheets_manager.get_worksheet("portfolio", gc=gc)
            high_score = results_df[results_df['Score'].astype(float) >= 60].copy()
            if not high_score.empty:
                existing_port = ws_port.get_all_values()
                ex_port = pd.DataFrame()
                existing_keys = set()
                if len(existing_port) > 1:
                    ex_port = pd.DataFrame(existing_port[1:], columns=existing_port[0])
                    existing_keys = set(ex_port['PositionKey'].values) if 'PositionKey' in ex_port.columns else set()
                new_positions = []
                for _, row in high_score.iterrows():
                    key = f"{row['Ticker']}_{today}"
                    if key not in existing_keys:
                        new_positions.append({
                            'PositionKey': key, 'Date': today, 'Ticker': row['Ticker'],
                            'Score': round(float(row['Score']), 2),
                            'BuyPrice': round(float(row['Price']), 2), 'Status': 'Open'
                        })
                if new_positions:
                    new_port_df = pd.DataFrame(new_positions)
                    combined_port = pd.concat([ex_port, new_port_df], ignore_index=True) if not ex_port.empty else new_port_df
                    df_to_sheet(ws_port, combined_port)
                    print(f"💼 Portfolio saved! {len(new_positions)} new stocks")

            # ── daily_summary: one row per ticker, peak stats from today's TL ─
            _save_daily_summary(gc, today, ws_timeline)

        print(f"✅ Saved {len(results)} stocks at {scan_time}")

    except Exception as e:
        print(f"❌ Google Sheets error: {e}")

    # ── Update RunningHigh/RunningLow for Pending stocks (always runs) ────────
    try:
        _gc = locals().get("gc") or get_gsheets_client()
        if _gc:
            update_portfolio_live(_gc, now_peru)
    except Exception as e:
        print(f"⚠️ portfolio_live final update error: {e}")


def _save_daily_summary(gc, today: str, ws_timeline):
    """Build and upsert daily_summary: one row per ticker with peak-score stats."""
    try:
        tl_raw = ws_timeline.get_all_values()
        if len(tl_raw) <= 1:
            return
        tl_df = pd.DataFrame(tl_raw[1:], columns=tl_raw[0])
        today_tl = tl_df[tl_df["Date"] == today].copy()
        if today_tl.empty:
            return

        for col in ["Score", "Price", "MxV", "RunUp", "REL_VOL"]:
            if col in today_tl.columns:
                today_tl[col] = pd.to_numeric(today_tl[col], errors="coerce")

        summary_rows = []
        for ticker, grp in today_tl.groupby("Ticker"):
            grp = grp.sort_values("ScanTime")
            peak_idx = grp["Score"].idxmax()
            peak_row = grp.loc[peak_idx]
            summary_rows.append({
                "Date":          today,
                "Ticker":        ticker,
                "Score":         round(float(grp["Score"].max()), 2),
                "Price":         round(float(peak_row.get("Price", 0) or 0), 2),
                "MxV":           round(float(peak_row.get("MxV", 0) or 0), 2),
                "RunUp":         round(float(peak_row.get("RunUp", 0) or 0), 2),
                "REL_VOL":       round(float(peak_row.get("REL_VOL", 0) or 0), 2),
                "ScanCount":     len(grp),
                "FirstScanTime": grp["ScanTime"].iloc[0] if "ScanTime" in grp.columns else "",
                "LastScanTime":  grp["ScanTime"].iloc[-1] if "ScanTime" in grp.columns else "",
            })

        if not summary_rows:
            return

        ws_ds = sheets_manager.get_worksheet("daily_summary", gc=gc)
        summary_df = pd.DataFrame(summary_rows)
        existing_ds = ws_ds.get_all_values()
        if len(existing_ds) <= 1:
            df_to_sheet(ws_ds, summary_df)
        else:
            ex_ds = pd.DataFrame(existing_ds[1:], columns=existing_ds[0])
            other = ex_ds[ex_ds["Date"] != today]
            combined = pd.concat([other, summary_df], ignore_index=True)
            df_to_sheet(ws_ds, combined)
        print(f"📊 Daily summary saved ({len(summary_rows)} tickers)")
    except Exception as e:
        print(f"⚠️ daily_summary error: {e}")


def update_portfolio_live(gc, now_peru):
    """
    בכל ריצה (כל דקה) — מעדכן RunningHigh/RunningLow למניות Pending.
    RunningHigh = מקסימום מחיר שנראה מאז הכניסה
    RunningLow  = מינימום מחיר שנראה מאז הכניסה
    אם RunningHigh >= SL  → SL ❌
    אם RunningLow  <= TP10 → TP10 ✅
    אם שניהם נגעו → Pending (לא יודעים הסדר, ממתינים לנתון יומי)
    """
    TP_PCT = 0.10
    SL_PCT = 0.07

    try:
        # טעון post_analysis
        ws_pa  = sheets_manager.get_worksheet("post_analysis", gc=gc)
        if ws_pa is None:
            return
        pa_raw = ws_pa.get_all_values()
        if len(pa_raw) <= 1:
            return

        pa_df = pd.DataFrame(pa_raw[1:], columns=pa_raw[0])
        pa_df["ScanPrice"] = pd.to_numeric(pa_df.get("ScanPrice", 0), errors="coerce")
        pa_df["D1_High"]   = pd.to_numeric(pa_df.get("D1_High",  ""), errors="coerce")

        # Only track stocks within last 7 calendar days (avoids scanning 90+ historical rows)
        cutoff = (now_peru - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        pa_df  = pa_df[pa_df.get("ScanDate", pd.Series(dtype=str)) >= cutoff]

        # מניות Pending = אין D1_High עדיין
        pending = pa_df[pa_df["D1_High"].isna() & pa_df["ScanPrice"].notna()].copy()
        if pending.empty:
            print("📈 No pending stocks to track")
            return

        # טעון portfolio_live הקיים
        ws_pl  = sheets_manager.get_worksheet("portfolio_live", gc=gc)
        pl_raw = ws_pl.get_all_values() if ws_pl else []
        if len(pl_raw) > 1:
            pl_df = pd.DataFrame(pl_raw[1:], columns=pl_raw[0])
            for col in ["EntryPrice","RunningHigh","RunningLow","TP10_Price","SL_Price"]:
                if col in pl_df.columns:
                    pl_df[col] = pd.to_numeric(pl_df[col], errors="coerce")
        else:
            pl_df = pd.DataFrame(columns=[
                "Ticker","ScanDate","EntryPrice","TP10_Price","SL_Price",
                "RunningHigh","RunningLow","CurrentPrice","Status","LastUpdated"
            ])

        scan_time = now_peru.strftime('%Y-%m-%d %H:%M')

        for _, row in pending.iterrows():
            ticker     = str(row.get("Ticker", ""))
            scan_date  = str(row.get("ScanDate", ""))
            scan_price = float(row["ScanPrice"])
            tp10_price = round(scan_price * (1 - TP_PCT), 4)
            sl_price   = round(scan_price * (1 + SL_PCT), 4)

            # מחיר חי
            try:
                hist = yf.Ticker(ticker).history(period="1d")
                if hist.empty:
                    continue
                live_price = round(float(hist.iloc[-1]["Close"]), 2)
            except:
                continue

            # מצא שורה קיימת
            mask = (pl_df["Ticker"] == ticker) & (pl_df["ScanDate"] == scan_date)

            if mask.any():
                idx = pl_df[mask].index[0]
                # לא לעדכן מניות שכבר יצאו
                cur_status = str(pl_df.at[idx, "Status"])
                if "TP10" in cur_status or "SL" in cur_status:
                    continue
                prev_high = pl_df.at[idx, "RunningHigh"]
                prev_low  = pl_df.at[idx, "RunningLow"]
                prev_high = float(prev_high) if pd.notna(prev_high) else live_price
                prev_low  = float(prev_low)  if pd.notna(prev_low)  else live_price
                new_high  = max(prev_high, live_price)
                new_low   = min(prev_low,  live_price)
            else:
                new_high = live_price
                new_low  = live_price

            # קבע סטטוס
            sl_hit = new_high >= sl_price
            tp_hit = new_low  <= tp10_price

            if sl_hit and tp_hit:
                status = "SL ❌"   # בשורט — SL גובר (המחיר עלה קודם או באותו הרגע)
            elif sl_hit:
                status = "SL ❌"
            elif tp_hit:
                status = "TP10 ✅"
            else:
                status = "Pending ⏳"

            new_row = {
                "Ticker": ticker, "ScanDate": scan_date,
                "EntryPrice": scan_price, "TP10_Price": tp10_price, "SL_Price": sl_price,
                "RunningHigh": new_high, "RunningLow": new_low,
                "CurrentPrice": live_price, "Status": status, "LastUpdated": scan_time
            }

            if mask.any():
                for col, val in new_row.items():
                    if col in pl_df.columns:
                        pl_df.at[pl_df[mask].index[0], col] = val
            else:
                pl_df = pd.concat([pl_df, pd.DataFrame([new_row])], ignore_index=True)

        df_to_sheet(ws_pl, pl_df)
        print(f"📈 portfolio_live updated: {len(pending)} pending stocks")

    except Exception as e:
        print(f"⚠️ portfolio_live error: {e}")


if __name__ == "__main__":
    run_scan()
