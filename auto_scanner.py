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
from utils import (
    get_peru_time,
    is_trading_day,
    is_market_hours,
    parse_market_cap,
    parse_volume,
    get_market_cap_smart,
)
from formulas import (
    calculate_mxv,
    calculate_runup,
    calculate_atrx,
    validate_atrx,
    calculate_gap,
    calculate_typical_price_dist,
    calculate_vwap_dist,
    calculate_rel_vol,
    calculate_float_pct,
    calculate_scan_change,
    calculate_score,
    calculate_score_b,
    calculate_score_c,
    calculate_score_d,
    calculate_score_e,
    calculate_score_f,
    calculate_score_g,
    calculate_score_h,
    calculate_score_i,
    calculate_entry_score,
)
from config import (
    TP_THRESHOLD_FRAC,
    SL_THRESHOLD_FRAC,
    TRADE_ENTRY_MIN_SCORE,
    MIN_SCORE_DISPLAY,
    ENTRY_CUTOFF_HOUR_PERU,
)

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

PERU_TZ = pytz.timezone("America/Lima")  # kept for backward compat
# get_peru_time imported from utils

# is_market_hours imported from utils

def is_snapshot_time():
    now = get_peru_time()
    return dt_time(14, 55) <= now.time() < dt_time(15, 5)

# is_trading_day imported from utils

# ── Google Sheets client ─────────────────────────────────────────────────────
# get_gsheets_client removed — use sheets_manager._get_gc() directly
get_gsheets_client = sheets_manager._get_gc  # alias for backward compat

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

# parse_market_cap and parse_volume imported from utils

# get_market_cap_smart imported from utils

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
        market_cap, shares = get_market_cap_smart(
            ticker, finviz_mc=finviz_mc, shares_cache=_shares_cache
        )
        if market_cap and market_cap > 0:
            _mc_cache[ticker] = int(market_cap)
        if shares and shares > 0 and ticker not in _shares_cache:
            _shares_cache[ticker] = int(shares)
        if market_cap is None and ticker in _mc_cache:
            market_cap = _mc_cache[ticker]
        if market_cap is None and ticker in _shares_cache and price > 0:
            market_cap = int(_shares_cache[ticker] * price)
            _mc_cache[ticker] = market_cap
        if not market_cap or market_cap == 0: return None

        rsi = 50; atrx = 0; rel_vol = 1.0; run_up = 0
        gap = 0; typical_price_dist = 0; price_to_high = 0
        price_to_52w_high = 0; float_pct = 0
        shares_outstanding = _shares_cache.get(ticker, 0)
        # Raw variables for metric validation
        open_price = 0; prev_close = 0; atr14_raw = 0
        high_today = 0; low_today = 0; typical_price = 0
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
                        atrx = calculate_atrx(current["High"], current["Low"], atr)
                        atrx = validate_atrx(atrx, atr, price)
                        atr14_raw = round(float(atr), 4)  # raw ATR14
                    except: pass

                try:
                    avg_vol = info.get('averageVolume', volume)
                    # calculate_rel_vol already caps at config.REL_VOL_CAP
                    rel_vol = calculate_rel_vol(volume, avg_vol)
                except: pass

                try:
                    open_price = round(float(current['Open']), 4)
                    run_up = calculate_runup(price, current['Open'])
                except: pass

                try:
                    prev_close = round(float(previous['Close']), 4)
                    gap = calculate_gap(current['Open'], previous['Close'])
                except: pass

                try:
                    high_today = round(float(current['High']), 4)
                    low_today  = round(float(current['Low']), 4)
                    typical_price = round((current['High'] + current['Low'] + price) / 3, 4)
                    typical_price_dist = calculate_typical_price_dist(price, current['High'], current['Low'])
                except: pass

                # Fallback: if daily bar hasn't updated high yet, use price as high.
                # This means no reversal signal yet — EntryScore will be low intentionally.
                if high_today <= price:
                    high_today = price

                try:
                    price_to_high  = ((price - high_today) / high_today * 100) if high_today > 0 else 0
                except: pass

                try:
                    week52_high       = float(info.get('fiftyTwoWeekHigh', price))
                    h52               = week52_high
                    price_to_52w_high = ((price - h52) / h52) * 100 if h52 > 0 else 0
                except: pass

                if shares_outstanding == 0:
                    shares_outstanding = info.get('sharesOutstanding', int(market_cap / price) if price > 0 else 0)

                try:
                    fs = info.get('floatShares', 0) or 0
                    float_pct = calculate_float_pct(fs, shares_outstanding)
                except: pass

        except: pass

        mxv = calculate_mxv(market_cap, price, volume)
        metrics = {
            'mxv': mxv, 'price_to_52w_high': price_to_52w_high,
            'price_to_high': price_to_high, 'rel_vol': rel_vol,
            'rsi': rsi, 'atrx': atrx, 'run_up': run_up,
            'float_pct': float_pct, 'gap': gap, 'typical_price_dist': typical_price_dist,
            'change': change,
        }
        score   = calculate_score(metrics)
        score_i = calculate_score_i(metrics)
        score_b = calculate_score_b(metrics)
        score_c = calculate_score_c(metrics)
        score_d = calculate_score_d(metrics)
        score_e = calculate_score_e(metrics)
        score_f = calculate_score_f(metrics)
        score_g = calculate_score_g(metrics)
        score_h = calculate_score_h(metrics)

        # EntryScore — real-time short entry signal
        # Gate: any of the 9 scores >= MIN_SCORE_DISPLAY
        entry_score = 0
        max_score_any = max(score, score_b, score_c, score_d, score_e,
                            score_f, score_g, score_h, score_i)
        if max_score_any >= MIN_SCORE_DISPLAY:
            entry_score = calculate_entry_score(
                current_price=price,
                intra_high=high_today,
                scan_price=open_price,    # today's open = pump baseline
                typical_price=typical_price,
                now_peru=get_peru_time()
            )

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
            'Score_I':       round(score_i, 2),
            'Score_B':       round(score_b, 2),
            'Score_C':       round(score_c, 2),
            'Score_D':       round(score_d, 2),
            'Score_E':       round(score_e, 2),
            'Score_F':       round(score_f, 2),
            'Score_G':       round(score_g, 2),
            'Score_H':       round(score_h, 2),
            'EntryScore':    round(entry_score, 2),
            'MxV':           round(mxv, 2),
            'RunUp':         round(run_up, 2),
            'RSI':           round(rsi, 2),
            'ATRX':          round(atrx, 2),
            'REL_VOL':       round(rel_vol, 2),
            'Gap':           round(gap, 2),
            'TypicalPriceDist': round(typical_price_dist, 2),
            'PriceToHigh':   round(price_to_high, 2),
            'PriceTo52WHigh':round(price_to_52w_high, 2),
            'Float%':        round(float_pct, 2),
            # ── Raw inputs — for metric validation & future regression ─────────
            'Open_price':       open_price,
            'PrevClose':        prev_close,
            'High_today':       high_today,
            'Low_today':        low_today,
            'TypicalPrice':     typical_price,
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
        print("❌ No results — still running portfolio_live / live_trades update")
        try:
            gc2 = get_gsheets_client()
            if gc2:
                update_portfolio_live(gc2, now_peru)
                update_live_trades(gc2, now_peru, results=[])
        except Exception as e:
            print(f"⚠️ no-results path error: {e}")
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

            # ── Portfolio: add Score>=TRADE_ENTRY_MIN_SCORE positions ────────
            ws_port = sheets_manager.get_worksheet("portfolio", gc=gc)
            high_score = results_df[results_df['Score'].astype(float) >= TRADE_ENTRY_MIN_SCORE].copy()
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

    # ── Live Trades: track intraday short entries (always runs) ───────────────
    try:
        _gc3 = locals().get("gc") or get_gsheets_client()
        if _gc3:
            update_live_trades(_gc3, now_peru, results=results)
    except Exception as e:
        print(f"⚠️ live_trades final update error: {e}")

    # ── Score Tracker: record metrics every 5 minutes (minutes 00,05,10...) ───
    if now_peru.minute % 5 == 0:
        try:
            _gc2 = locals().get("gc") or get_gsheets_client()
            if _gc2:
                sync_score_tracker(_gc2, now_peru)
        except Exception as e:
            print(f"⚠️ score_tracker sync error: {e}")
    else:
        print(f"⏭ score_tracker skipped (minute={now_peru.minute}, next at :{(now_peru.minute//5+1)*5:02d})")


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
    בכל ריצה — מעדכן RunningHigh/RunningLow לכל מניה עם Status=Open ב-portfolio.
    מקור: portfolio sheet (לא post_analysis) — עוקב גם אחרי מניות שלא נסרקות היום.
    RunningHigh כולל את ה-High של הנר היומי (לא רק Close).
    אם RunningHigh >= SL  → SL ❌
    אם RunningLow  <= TP10 → TP10 ✅
    אם שניהם נגעו → SL גובר (שורט)
    """
    TP_PCT = TP_THRESHOLD_FRAC
    SL_PCT = SL_THRESHOLD_FRAC

    try:
        # ── Source of truth: portfolio sheet, Status=Open, last 7 days ──────────
        ws_port = sheets_manager.get_worksheet("portfolio", gc=gc)
        if ws_port is None:
            return
        port_raw = ws_port.get_all_values()
        if len(port_raw) <= 1:
            return

        port_df = pd.DataFrame(port_raw[1:], columns=port_raw[0])
        port_df["BuyPrice"] = pd.to_numeric(port_df.get("BuyPrice", 0), errors="coerce")

        cutoff = (now_peru - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
        if "Date" in port_df.columns:
            port_df = port_df[port_df["Date"] >= cutoff]

        open_pos = port_df[port_df.get("Status", pd.Series(dtype=str)) == "Open"].copy() \
            if "Status" in port_df.columns else port_df.copy()

        if open_pos.empty:
            print("📈 No open portfolio positions to track")
            return

        # ── Load existing portfolio_live ─────────────────────────────────────
        ws_pl  = sheets_manager.get_worksheet("portfolio_live", gc=gc)
        pl_raw = ws_pl.get_all_values() if ws_pl else []
        PL_COLS = ["Ticker", "ScanDate", "EntryPrice", "TP10_Price", "SL_Price",
                   "RunningHigh", "RunningLow", "CurrentPrice", "Status", "LastUpdated"]
        if len(pl_raw) > 1:
            pl_df = pd.DataFrame(pl_raw[1:], columns=pl_raw[0])
            for col in ["EntryPrice", "RunningHigh", "RunningLow",
                        "TP10_Price", "SL_Price", "CurrentPrice"]:
                if col in pl_df.columns:
                    pl_df[col] = pd.to_numeric(pl_df[col], errors="coerce")
        else:
            pl_df = pd.DataFrame(columns=PL_COLS)

        scan_time = now_peru.strftime("%Y-%m-%d %H:%M")

        for _, row in open_pos.iterrows():
            ticker     = str(row.get("Ticker", "")).strip()
            scan_date  = str(row.get("Date", "")).strip()
            scan_price = float(row.get("BuyPrice", 0) or 0)

            if not ticker or scan_price <= 0:
                continue

            tp10_price = round(scan_price * (1 - TP_PCT), 4)
            sl_price   = round(scan_price * (1 + SL_PCT), 4)

            # Find existing row in portfolio_live
            mask = (
                (pl_df["Ticker"] == ticker) & (pl_df["ScanDate"] == scan_date)
                if not pl_df.empty and "Ticker" in pl_df.columns and "ScanDate" in pl_df.columns
                else pd.Series([False] * len(pl_df), dtype=bool)
            )

            # Skip already-closed positions
            if mask.any():
                cur_status = str(pl_df.at[pl_df[mask].index[0], "Status"])
                if "TP10" in cur_status or "SL" in cur_status:
                    continue

            # Fetch live price + intraday high (catches SL even if price pulled back)
            try:
                hist = yf.Ticker(ticker).history(period="1d")
                if hist.empty:
                    continue
                live_price  = round(float(hist.iloc[-1]["Close"]), 2)
                intra_high  = round(float(hist.iloc[-1]["High"]),  2)
            except Exception:
                continue

            # Update running high/low
            if mask.any():
                idx       = pl_df[mask].index[0]
                prev_high = pl_df.at[idx, "RunningHigh"]
                prev_low  = pl_df.at[idx, "RunningLow"]
                prev_high = float(prev_high) if pd.notna(prev_high) else live_price
                prev_low  = float(prev_low)  if pd.notna(prev_low)  else live_price
                new_high  = max(prev_high, live_price, intra_high)
                new_low   = min(prev_low,  live_price)
            else:
                new_high = max(live_price, intra_high)
                new_low  = live_price

            sl_hit = new_high >= sl_price
            tp_hit = new_low  <= tp10_price

            if sl_hit:
                status = "SL ❌"     # short: SL always takes priority
            elif tp_hit:
                status = "TP10 ✅"
            else:
                status = "Pending ⏳"

            new_row = {
                "Ticker": ticker, "ScanDate": scan_date,
                "EntryPrice": scan_price, "TP10_Price": tp10_price, "SL_Price": sl_price,
                "RunningHigh": new_high, "RunningLow": new_low,
                "CurrentPrice": live_price, "Status": status, "LastUpdated": scan_time,
            }

            if mask.any():
                for col, val in new_row.items():
                    if col in pl_df.columns:
                        pl_df.at[pl_df[mask].index[0], col] = val
            else:
                pl_df = pd.concat([pl_df, pd.DataFrame([new_row])], ignore_index=True)

        # Ensure column order
        for col in PL_COLS:
            if col not in pl_df.columns:
                pl_df[col] = ""
        pl_df = pl_df[PL_COLS]

        df_to_sheet(ws_pl, pl_df)
        print(f"📈 portfolio_live updated: {len(open_pos)} open positions tracked")

    except Exception as e:
        print(f"⚠️ portfolio_live error: {e}")


SCORE_TYPES = ["Score", "Score_B", "Score_C", "Score_D", "Score_E", "Score_F", "Score_G", "Score_H", "Score_I"]

LIVE_TRADES_COLS = [
    "EntryTime", "Ticker", "EntryPrice", "IntraHigh", "ScoreType", "Score", "EntryScore",
    "TP10_Price", "SL_Price", "CurrentPrice", "RunningHigh", "RunningLow",
    "Status", "ExitTime", "PnL_pct",
]

def update_live_trades(gc, now_peru, results=None):
    """
    בכל ריצה (כל דקה):
    1. קורא live_trades הקיים
    2. לכל שורה Pending — מושך מחיר חי, מעדכן RunningHigh/RunningLow, בודק TP/SL
    3. לכל מניה בתוצאות הסריקה — לכל ציון >= 70 מוסיף שורה נפרדת עם ScoreType
       מניה יכולה להופיע עד 9 פעמים (פעם לכל ציון שעובר 70)
    קריטריון: ScoreType >= 70 AND שוק פתוח
    """
    ENTRY_MIN_SCORE = TRADE_ENTRY_MIN_SCORE
    TP_PCT = TP_THRESHOLD_FRAC
    SL_PCT = SL_THRESHOLD_FRAC

    try:
        today     = now_peru.strftime("%Y-%m-%d")
        scan_time = now_peru.strftime("%Y-%m-%d %H:%M")

        ws = sheets_manager.get_worksheet("live_trades", gc=gc)
        if ws is None:
            print("⚠️ live_trades worksheet not found — check Drive quota or sheets_config.json")
            print(f"   Hint: run 'python3 monthly_rotation.py' or free Drive storage and retry")
            return

        raw = ws.get_all_values()
        if len(raw) > 1:
            lt_df = pd.DataFrame(raw[1:], columns=raw[0])
            for col in ["EntryPrice", "IntraHigh", "Score", "EntryScore",
                        "TP10_Price", "SL_Price", "CurrentPrice",
                        "RunningHigh", "RunningLow", "PnL_pct"]:
                if col in lt_df.columns:
                    lt_df[col] = pd.to_numeric(lt_df[col], errors="coerce")
        else:
            lt_df = pd.DataFrame(columns=LIVE_TRADES_COLS)

        # ── Step 1: update existing Pending rows ──────────────────────────────
        pending_mask = lt_df["Status"] == "Pending" if "Status" in lt_df.columns else pd.Series([], dtype=bool)
        for idx in lt_df[pending_mask].index:
            ticker     = str(lt_df.at[idx, "Ticker"])
            entry_price = float(lt_df.at[idx, "EntryPrice"])
            tp10_price  = float(lt_df.at[idx, "TP10_Price"])
            sl_price    = float(lt_df.at[idx, "SL_Price"])
            prev_high   = lt_df.at[idx, "RunningHigh"]
            prev_low    = lt_df.at[idx, "RunningLow"]

            try:
                hist = yf.Ticker(ticker).history(period="1d")
                if hist.empty:
                    continue
                live_price = round(float(hist.iloc[-1]["Close"]), 2)
                intra_high = round(float(hist.iloc[-1]["High"]), 2)
            except:
                continue

            prev_high = float(prev_high) if pd.notna(prev_high) else live_price
            prev_low  = float(prev_low)  if pd.notna(prev_low)  else live_price
            new_high  = max(prev_high, live_price, intra_high)
            new_low   = min(prev_low,  live_price)

            sl_hit = new_high >= sl_price
            tp_hit = new_low  <= tp10_price

            if sl_hit:
                status     = "SL"
                exit_time  = scan_time
                pnl        = round((entry_price - sl_price) / entry_price * 100, 2)  # negative (loss for short)
            elif tp_hit:
                status     = "TP10"
                exit_time  = scan_time
                pnl        = round((entry_price - tp10_price) / entry_price * 100, 2)  # positive (profit for short)
            else:
                status     = "Pending"
                exit_time  = ""
                pnl        = round((entry_price - live_price) / entry_price * 100, 2)

            lt_df.at[idx, "CurrentPrice"] = live_price
            lt_df.at[idx, "IntraHigh"]    = intra_high
            lt_df.at[idx, "RunningHigh"]  = new_high
            lt_df.at[idx, "RunningLow"]   = new_low
            lt_df.at[idx, "Status"]       = status
            lt_df.at[idx, "ExitTime"]     = exit_time
            lt_df.at[idx, "PnL_pct"]      = pnl

        # ── Step 2: add new entries from current scan results ─────────────────
        if now_peru.hour >= ENTRY_CUTOFF_HOUR_PERU:
            print(f"⏰ live_trades: past entry cutoff ({ENTRY_CUTOFF_HOUR_PERU}:00 Peru) — tracking existing pending only, no new entries")
        if results and is_market_hours() and now_peru.hour < ENTRY_CUTOFF_HOUR_PERU:
            # Build dedup sets: one entry per (Ticker, day)
            pending_today = set()   # tickers currently Pending — don't double-enter
            closed_today  = set()   # tickers already TP10/SL today — no re-entry
            if "EntryTime" in lt_df.columns and not lt_df.empty:
                today_rows = lt_df[lt_df["EntryTime"].str.startswith(today)]
                if not today_rows.empty:
                    pending_today = set(
                        today_rows[today_rows["Status"] == "Pending"]["Ticker"].astype(str)
                    )
                    closed_today = set(
                        today_rows[today_rows["Status"].isin(["TP10", "SL"])]["Ticker"].astype(str)
                    )

            for r in results:
                ticker      = str(r.get("Ticker", ""))
                price       = float(r.get("Price", 0) or 0)
                entry_score = float(r.get("EntryScore", 0) or 0)
                intra_high  = float(r.get("High_today", price) or price)

                if price <= 0:
                    continue
                if ticker in pending_today:
                    continue  # already has an open trade
                if ticker in closed_today:
                    continue  # already closed TP10/SL today — no re-entry

                # Use only main Score v2 — research 22/4/2026: max(variants) triggered toxic Score_I trades (0/11 wins)
                best_type = "Score"
                best_val  = float(r.get("Score", 0) or 0)
                if best_val < ENTRY_MIN_SCORE:
                    continue

                tp10_price = round(price * (1 - TP_PCT), 4)
                sl_price   = round(price * (1 + SL_PCT), 4)

                new_trade = {
                    "EntryTime":    scan_time,
                    "Ticker":       ticker,
                    "EntryPrice":   price,
                    "IntraHigh":    intra_high,
                    "ScoreType":    best_type,
                    "Score":        round(best_val, 2),
                    "EntryScore":   round(entry_score, 2),
                    "TP10_Price":   tp10_price,
                    "SL_Price":     sl_price,
                    "CurrentPrice": price,
                    "RunningHigh":  intra_high,
                    "RunningLow":   price,
                    "Status":       "Pending",
                    "ExitTime":     "",
                    "PnL_pct":      0.0,
                }
                lt_df = pd.concat([lt_df, pd.DataFrame([new_trade])], ignore_index=True)
                pending_today.add(ticker)
                print(f"⚡ live_trades: new entry {ticker}[{best_type}] @ {price} (Score={best_val})")

        # enforce column order, fill missing columns
        for col in LIVE_TRADES_COLS:
            if col not in lt_df.columns:
                lt_df[col] = ""
        lt_df = lt_df[LIVE_TRADES_COLS]

        df_to_sheet(ws, lt_df)
        n_pending = int((lt_df["Status"] == "Pending").sum()) if "Status" in lt_df.columns else 0
        print(f"⚡ live_trades updated: {len(lt_df)} rows, {n_pending} pending")

    except Exception as e:
        print(f"⚠️ live_trades error: {e}")


def sync_score_tracker(gc, now_peru):
    """
    Record Score + metrics every 5 minutes for portfolio stocks in D1/D2/D3 window.
    Runs inside auto_scanner (called only when now_peru.minute % 5 == 0).
    Columns: Date, ScanTime, Ticker, ScanDate, Price, Score, MxV, RunUp, REL_VOL, RSI, ATRX,
             Gap, VWAP_Dist, Volume, High, Low, Open, PrevClose
    """
    try:
        import yfinance as yf
        from ta.momentum import RSIIndicator
        from ta.volatility import AverageTrueRange

        today     = now_peru.strftime("%Y-%m-%d")
        scan_time = now_peru.strftime("%H:%M")

        # Which portfolio stocks are in D1/D2/D3 window today?
        ws_port  = sheets_manager.get_worksheet("portfolio", gc=gc)
        port_raw = ws_port.get_all_values() if ws_port else []
        if len(port_raw) <= 1:
            return
        port_df = pd.DataFrame(port_raw[1:], columns=port_raw[0])

        _tdays_after = sheets_manager.trading_days_after

        active = set()
        for _, r in port_df.iterrows():
            sd = str(r.get("Date", "")).strip()
            tk = str(r.get("Ticker", "")).strip()
            if sd and tk:
                try:
                    # D0 (entry day) + D1/D2/D3
                    if today == sd or today in _tdays_after(sd, 3):
                        active.add((tk, sd))
                except Exception:
                    pass

        if not active:
            return

        COLS = ["Date","ScanTime","Ticker","ScanDate","Price","Score",
                "MxV","RunUp","REL_VOL","RSI","ATRX",
                "Gap","TypicalPriceDist","Volume","High","Low","Open","PrevClose"]
        new_rows = []
        for ticker, scan_date in sorted(active):
            try:
                stock = yf.Ticker(ticker)
                hist  = stock.history(period="60d")
                if hist.empty or len(hist) < 2:
                    continue
                info     = stock.info
                current  = hist.iloc[-1]
                previous = hist.iloc[-2]
                price      = round(float(current["Close"]), 2)
                high       = round(float(current["High"]), 2)
                low        = round(float(current["Low"]), 2)
                open_price = round(float(current["Open"]), 2)
                prev_close = round(float(previous["Close"]), 2)
                volume     = int(current["Volume"])
                mkt_cap    = info.get("marketCap", 0)
                if not mkt_cap:
                    continue

                rsi = 50.0; atrx = 0.0; rel_vol = 1.0; run_up = 0.0
                try:
                    rsi = float(RSIIndicator(hist["Close"], 14).rsi().iloc[-1])
                except Exception: pass
                try:
                    atr  = float(AverageTrueRange(hist["High"],hist["Low"],hist["Close"],14).average_true_range().iloc[-1])
                    atrx = calculate_atrx(high, low, atr)
                    atrx = validate_atrx(atrx, atr, price)
                except Exception: pass
                try:
                    avg_vol = info.get("averageVolume", volume)
                    # calculate_rel_vol already caps at config.REL_VOL_CAP
                    rel_vol = calculate_rel_vol(volume, avg_vol)
                except Exception: pass
                try:
                    run_up = calculate_runup(price, open_price)
                except Exception: pass

                gap = 0.0
                try:
                    gap = calculate_gap(open_price, prev_close)
                except Exception: pass

                typical_price_dist = 0.0
                try:
                    typical_price_dist = calculate_typical_price_dist(price, high, low)
                except Exception: pass

                mxv   = calculate_mxv(mkt_cap, price, volume)
                change_pct = calculate_scan_change(price, prev_close)
                score = calculate_score({
                    'mxv': mxv, 'run_up': run_up, 'atrx': atrx,
                    'rsi': rsi, 'typical_price_dist': typical_price_dist,
                    'change': change_pct, 'rel_vol': rel_vol,
                })

                new_rows.append({
                    "Date": today, "ScanTime": scan_time,
                    "Ticker": ticker, "ScanDate": scan_date,
                    "Price":     price,
                    "Score":     round(score,     2),
                    "MxV":       round(mxv,        2),
                    "RunUp":     round(run_up,     2),
                    "REL_VOL":   round(rel_vol,    2),
                    "RSI":       round(rsi,        2),
                    "ATRX":      round(atrx,       2),
                    "Gap":       round(gap,         2),
                    "TypicalPriceDist": round(typical_price_dist, 2),
                    "Volume":    volume,
                    "High":      high,
                    "Low":       low,
                    "Open":      open_price,
                    "PrevClose": prev_close,
                })
            except Exception as e:
                print(f"  [ScoreTracker] {ticker}: {e}")

        if not new_rows:
            return

        new_df = pd.DataFrame(new_rows)[COLS]
        ws_st  = sheets_manager.get_worksheet("score_tracker", gc=gc)
        if not ws_st:
            return

        # Only read the header row (A1:R1) — avoids downloading thousands of rows
        header = ws_st.row_values(1)
        if header == COLS:
            ws_st.append_rows(new_df.astype(str).values.tolist())
        else:
            # First run or old schema — rewrite with full header
            ws_st.clear()
            ws_st.update("A1", [COLS] + new_df.astype(str).values.tolist())

        print(f"[ScoreTracker] ✅ {len(new_rows)} rows at {scan_time}")

    except Exception as e:
        print(f"[ScoreTracker] ⚠️ {e}")


def run_eod():
    """
    End-of-day job: runs after market close (16:00 Peru / 21:00 UTC).
    Ensures today's portfolio + daily_summary are saved even if the
    14:55-15:05 snapshot window was missed due to GitHub Actions throttling.
    """
    import sys
    now_peru = get_peru_time()
    today    = now_peru.strftime("%Y-%m-%d")
    print(f"\n📅 EOD Snapshot — {today} {now_peru.strftime('%H:%M')} Peru")

    gc = get_gsheets_client()
    if gc is None:
        print("❌ No Google credentials"); return

    # ── Read today's timeline_live ────────────────────────────────────────────
    ws_tl = sheets_manager.get_worksheet("timeline_live", gc=gc)
    if ws_tl is None:
        print("❌ timeline_live not found"); return
    tl_raw = ws_tl.get_all_values()
    if len(tl_raw) <= 1:
        print("❌ timeline_live is empty"); return

    tl_df = pd.DataFrame(tl_raw[1:], columns=tl_raw[0])
    today_tl = tl_df[tl_df["Date"] == today].copy()
    if today_tl.empty:
        print(f"❌ No timeline_live rows for {today}"); return

    for col in ["Score", "Price", "MxV", "RunUp", "REL_VOL"]:
        if col in today_tl.columns:
            today_tl[col] = pd.to_numeric(today_tl[col], errors="coerce")

    print(f"📊 {len(today_tl)} timeline rows for today, {today_tl['Ticker'].nunique()} tickers")

    # ── Portfolio: save Score>=TRADE_ENTRY_MIN_SCORE stocks (skip if already saved)
    try:
        ws_port = sheets_manager.get_worksheet("portfolio", gc=gc)
        high_score = today_tl[today_tl["Score"] >= TRADE_ENTRY_MIN_SCORE].copy()

        # Use peak score per ticker
        best = (high_score.sort_values("Score", ascending=False)
                .drop_duplicates("Ticker"))

        existing_port = ws_port.get_all_values()
        ex_port = pd.DataFrame()
        existing_keys = set()
        if len(existing_port) > 1:
            ex_port = pd.DataFrame(existing_port[1:], columns=existing_port[0])
            existing_keys = set(ex_port["PositionKey"].values) if "PositionKey" in ex_port.columns else set()

        new_positions = []
        for _, row in best.iterrows():
            key = f"{row['Ticker']}_{today}"
            if key not in existing_keys:
                new_positions.append({
                    "PositionKey": key,
                    "Date":        today,
                    "Ticker":      row["Ticker"],
                    "Score":       round(float(row["Score"]), 2),
                    "BuyPrice":    round(float(row.get("Price", 0) or 0), 2),
                    "Status":      "Open",
                })

        if new_positions:
            new_port_df   = pd.DataFrame(new_positions)
            combined_port = pd.concat([ex_port, new_port_df], ignore_index=True) if not ex_port.empty else new_port_df
            df_to_sheet(ws_port, combined_port)
            print(f"💼 Portfolio: added {len(new_positions)} new stocks")
        else:
            print("💼 Portfolio: already up to date")
    except Exception as e:
        print(f"⚠️ portfolio EOD error: {e}")

    # ── Daily summary ──────────────────────────────────────────────────────────
    try:
        _save_daily_summary(gc, today, ws_tl)
    except Exception as e:
        print(f"⚠️ daily_summary EOD error: {e}")

    print("✅ EOD snapshot complete")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--eod":
        run_eod()
    else:
        run_scan()
