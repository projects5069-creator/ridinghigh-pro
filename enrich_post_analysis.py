"""
RidingHigh Pro - Enrich Post Analysis with Intraday Data v3
Adds:
  - IntraHigh, IntraLow, PeakScoreTime, PeakScorePrice, PeakScore, DayRunUp% (from timeline_live)
  - D0_Close, D0_Volume, D0_Drop%, IntraDay_TP10 (from Yahoo Finance)

v3: Uses sheets_manager (new multi-sheet architecture). No hardcoded local paths.
"""

import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import sheets_manager
from gsheets_sync import load_post_analysis_from_sheets, save_post_analysis_to_sheets


def _is_missing(val):
    """True if value is None, NaN, empty string, or the literal string 'nan'/'None'."""
    if val is None:
        return True
    try:
        import math
        if math.isnan(float(val)):
            return True
    except (TypeError, ValueError):
        pass
    return str(val).strip() in ("", "nan", "None")


def fetch_d0_data(ticker: str, scan_date: str) -> dict:
    """Fetch D0 (scan day) closing price and volume from Yahoo Finance."""
    for attempt in range(1, 4):
        try:
            scan_dt = datetime.strptime(scan_date, "%Y-%m-%d")
            end_dt  = scan_dt + timedelta(days=1)
            hist = yf.download(
                ticker,
                start=scan_date,
                end=end_dt.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True
            )
            if hist.empty:
                time.sleep(1)
                continue
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            hist.columns = [str(c) for c in hist.columns]
            hist.index = pd.to_datetime(hist.index).strftime("%Y-%m-%d")
            if scan_date in hist.index:
                row = hist.loc[scan_date]
                return {
                    "D0_Close":  round(float(row["Close"]), 4),
                    "D0_Volume": int(row["Volume"]),
                }
            return {}
        except Exception as e:
            print(f"[Enrich] D0 fetch attempt {attempt}/3 failed for {ticker}: {e}")
            time.sleep(2)
    return {}


def is_trading_day(date=None):
    import pytz
    if date is None:
        date = datetime.now(pytz.timezone("America/Lima")).date()
    try:
        import pandas_market_calendars as mcal
        nyse = mcal.get_calendar("NASDAQ")
        return not nyse.schedule(
            start_date=date.strftime("%Y-%m-%d"),
            end_date=date.strftime("%Y-%m-%d")
        ).empty
    except Exception:
        return date.weekday() < 5


def run(backfill: bool = False):
    print("[Enrich] Starting v3..." + (" (backfill mode)" if backfill else ""))

    if not backfill:
        import pytz
        today = datetime.now(pytz.timezone("America/Lima")).date()
        if not is_trading_day(today):
            print(f"[Enrich] ⛔ {today} is not a trading day — skipping.")
            return

    gc = sheets_manager._get_gc()
    if gc is None:
        print("[Enrich] ❌ Cannot connect to Google Sheets — credentials not found")
        return

    # ── Load timeline_live (slim 8 cols: Date, ScanTime, Ticker, Price, Score, MxV, RunUp, REL_VOL)
    print("[Enrich] Loading timeline_live...")
    ws_tl = sheets_manager.get_worksheet("timeline_live", gc=gc)
    if ws_tl is None:
        print("[Enrich] ❌ Cannot open timeline_live")
        return
    tl_raw = ws_tl.get_all_values()
    if len(tl_raw) <= 1:
        print("[Enrich] ⚠️ timeline_live is empty")
        tl = pd.DataFrame()
    else:
        tl = pd.DataFrame(tl_raw[1:], columns=tl_raw[0])
        tl["Price"] = pd.to_numeric(tl["Price"], errors="coerce")
        tl["Score"] = pd.to_numeric(tl["Score"], errors="coerce")
        print(f"[Enrich] Timeline rows loaded: {len(tl)}")

    # ── Load post_analysis ──────────────────────────────────────────────────
    pa = load_post_analysis_from_sheets()

    # Fix dtype: cast numeric cols from str to float after loading from Sheets
    numeric_cols = [
        "D0_Open","D0_Close","D1_Open","D1_High","D1_Low",
        "D1_Close","D2_Close","D3_Close","D5_Close",
        "D0_Vol","D0_Volume","MaxDrop"
    ]
    for col in numeric_cols:
        if col in pa.columns:
            pa[col] = pd.to_numeric(pa[col], errors="coerce")
    print(f"[Enrich] Post analysis rows: {len(pa)}")
    if pa.empty:
        print("[Enrich] No post analysis data — nothing to enrich")
        return

    # Ensure enrichment columns exist
    for col in ["IntraHigh", "IntraLow", "PeakScoreTime", "PeakScorePrice",
                "PeakScore", "DayRunUp%", "D0_Close", "D0_Volume", "D0_Drop%", "IntraDay_TP10",
                "SL_Hit_D0", "MinToClose"]:
        if col not in pa.columns:
            pa[col] = None
    pa["PeakScoreTime"] = pa["PeakScoreTime"].astype(object)

    TIMELINE_COLS = ["IntraHigh", "IntraLow", "PeakScoreTime", "PeakScorePrice",
                     "PeakScore", "DayRunUp%", "IntraDay_TP10", "SL_Hit_D0", "MinToClose"]
    D0_COLS       = ["D0_Close", "D0_Volume", "D0_Drop%"]

    updated = 0
    skipped = 0

    for idx, row in pa.iterrows():
        ticker     = str(row.get("Ticker", "")).strip()
        scan_date  = str(row.get("ScanDate", "")).strip()
        scan_price = pd.to_numeric(row.get("ScanPrice", 0), errors="coerce") or 0

        if not ticker or not scan_date:
            skipped += 1
            continue

        timeline_missing = any(_is_missing(row.get(c)) for c in TIMELINE_COLS)
        d0_missing       = any(_is_missing(row.get(c)) for c in D0_COLS)

        if not timeline_missing and not d0_missing:
            skipped += 1
            continue

        row_changed = False

        # ── Timeline enrichment ─────────────────────────────────────────────
        if timeline_missing and not tl.empty:
            day_tl = tl[(tl["Ticker"] == ticker) & (tl["Date"] == scan_date)]
            if not day_tl.empty:
                intra_high  = round(day_tl["Price"].max(), 2)
                intra_low   = round(day_tl["Price"].min(), 2)
                peak_idx    = day_tl["Score"].idxmax()
                peak_time   = day_tl.loc[peak_idx, "ScanTime"]
                peak_price  = round(day_tl.loc[peak_idx, "Price"], 2)
                peak_score  = round(day_tl.loc[peak_idx, "Score"], 2)
                first_price = round(day_tl.sort_values("ScanTime").iloc[0]["Price"], 2)
                run_up_pct  = round((intra_high - first_price) / first_price * 100, 2) if first_price > 0 else 0

                pa.at[idx, "IntraHigh"]      = intra_high
                pa.at[idx, "IntraLow"]       = intra_low
                pa.at[idx, "PeakScoreTime"]  = peak_time
                pa.at[idx, "PeakScorePrice"] = peak_price
                pa.at[idx, "PeakScore"]      = peak_score
                pa.at[idx, "DayRunUp%"]      = run_up_pct
                if scan_price > 0:
                    pa.at[idx, "IntraDay_TP10"] = "1" if intra_low <= scan_price * 0.90 else "0"

                # SL_Hit_D0: did price go UP 7%+ from scan price on scan day?
                if scan_price > 0:
                    pa.at[idx, "SL_Hit_D0"] = "1" if intra_high >= scan_price * 1.07 else "0"

                # MinToClose: minutes between peak score time and 15:00 close
                try:
                    peak_dt = pd.Timestamp(f"2000-01-01 {peak_time}")
                    close_dt = pd.Timestamp("2000-01-01 15:00")
                    pa.at[idx, "MinToClose"] = str(max(0, int((close_dt - peak_dt).total_seconds() / 60)))
                except:
                    pa.at[idx, "MinToClose"] = ""

                row_changed = True
            else:
                print(f"[Enrich] No timeline data for {ticker} {scan_date}")

        # ── D0 enrichment ───────────────────────────────────────────────────
        if d0_missing:
            print(f"[Enrich] Fetching D0 for {ticker} ({scan_date})...")
            d0 = fetch_d0_data(ticker, scan_date)
            if d0:
                pa.at[idx, "D0_Close"]  = d0["D0_Close"]
                pa.at[idx, "D0_Volume"] = d0["D0_Volume"]
                if scan_price > 0:
                    pa.at[idx, "D0_Drop%"] = round(
                        (d0["D0_Close"] - scan_price) / scan_price * 100, 2)
                row_changed = True
            time.sleep(0.3)

        if row_changed:
            updated += 1
        else:
            skipped += 1

    print(f"[Enrich] Updated: {updated} rows | Skipped: {skipped} rows")

    save_post_analysis_to_sheets(pa)
    print("[Enrich] ✅ Saved to post_analysis")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Post Analysis")
    parser.add_argument("--backfill", action="store_true",
                        help="Process all dates, skip trading-day guard.")
    args = parser.parse_args()
    run(backfill=args.backfill)
