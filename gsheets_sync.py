"""
RidingHigh Pro - Google Sheets Sync Module
New architecture: one Google Sheets file per logical tab, per month.
Sheet IDs managed by sheets_manager.py / sheets_config.json.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

# Legacy single-spreadsheet ID kept for backward-compat data access
LEGACY_SPREADSHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
SPREADSHEET_ID = LEGACY_SPREADSHEET_ID   # alias so old imports don't break

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Tab name constants (each is now a separate Spreadsheet)
TAB_TIMELINE_LIVE  = "timeline_live"
TAB_DAILY_SNAPSHOT = "daily_snapshots"
TAB_DAILY_SUMMARY  = "daily_summary"
TAB_POST_ANALYSIS  = "post_analysis"
TAB_PORTFOLIO      = "portfolio"
TAB_PORTFOLIO_LIVE = "portfolio_live"
TAB_SCORE_TRACKER  = "score_tracker"

# Kept for imports that still reference TAB_TIMELINE (old archive)
TAB_TIMELINE = TAB_TIMELINE_LIVE


def _get_client():
    """Return an authenticated gspread client via sheets_manager."""
    return sheets_manager._get_gc()


def get_gsheets_client():
    return _get_client()


def _get_ws(tab_name: str, gc=None, month: str = None):
    """Shortcut: return the worksheet for tab_name (current month by default)."""
    return sheets_manager.get_worksheet(tab_name, month=month, gc=gc)


def _get_post_analysis_ws(gc=None):
    """
    Return the post_analysis worksheet with explicit tab fallback.
    Priority: tab "post_analysis" → tab "גיליון1" → sheet1.
    Handles spreadsheets created with default Hebrew tab names.
    """
    if gc is None:
        gc = _get_client()
    ws = sheets_manager.get_worksheet(TAB_POST_ANALYSIS, gc=gc)
    if ws is None:
        return None
    # If sheet1 is empty but a named tab might exist, try "גיליון1" explicitly
    try:
        data = ws.get_all_values()
        if len(data) <= 1:
            # sheet1 is empty — check if a "גיליון1" tab actually has data
            import gspread
            config = sheets_manager._load_config()
            month = datetime.now().strftime("%Y-%m")
            pa_id = config.get(month, {}).get(TAB_POST_ANALYSIS)
            if pa_id:
                sp = gc.open_by_key(pa_id)
                for candidate in ["post_analysis", "גיליון1"]:
                    try:
                        cws = sp.worksheet(candidate)
                        cdata = cws.get_all_values()
                        if len(cdata) > 1:
                            return cws
                    except gspread.exceptions.WorksheetNotFound:
                        pass
    except Exception:
        pass
    return ws


def _get_or_create_sheet(spreadsheet, tab_name):
    """Legacy helper — used only when a raw spreadsheet object is already open."""
    try:
        return spreadsheet.worksheet(tab_name)
    except Exception:
        return spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)


def get_or_create_sheet(spreadsheet, tab_name):
    return _get_or_create_sheet(spreadsheet, tab_name)


def _df_to_sheet(ws, df, include_index=False):
    """
    Write a DataFrame to a worksheet (full overwrite).
    Safe pattern: write data first, then trim excess rows — never clears before writing.
    """
    if include_index:
        df = df.reset_index()
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    # Write data starting from A1 (overwrites existing content)
    ws.update("A1", data)
    # Trim stale rows below the new data (handles shrinking datasets)
    try:
        total_rows = ws.row_count
        new_last   = len(data)
        if total_rows > new_last:
            ws.delete_rows(new_last + 1, total_rows)
    except Exception:
        pass  # trim failure is non-critical; data is already written correctly


# ── Snapshot ──────────────────────────────────────────────────────────────────

def save_snapshot_to_sheets(df: pd.DataFrame) -> bool:
    try:
        gc = _get_client()
        ws = sheets_manager.get_worksheet(TAB_DAILY_SNAPSHOT, gc=gc)
        if ws is None:
            return False

        today = datetime.now().strftime("%Y-%m-%d")
        df = df.copy()
        df.insert(0, "Date", today)

        existing = ws.get_all_values()
        if len(existing) <= 1:
            _df_to_sheet(ws, df)
        else:
            existing_df = pd.DataFrame(existing[1:], columns=existing[0])
            if today in existing_df.get("Date", pd.Series()).values:
                other_days = existing_df[existing_df["Date"] != today]
                combined = pd.concat([other_days, df], ignore_index=True)
                _df_to_sheet(ws, combined)
            else:
                ws.append_rows(df.astype(str).values.tolist())

        print(f"[GSheets] ✅ Snapshot saved for {today}")
        return True

    except Exception as e:
        print(f"[GSheets] snapshot error: {e}")
        return False


# ── Timeline (dates / per-date load) — now uses daily_snapshots ───────────────

def save_timeline_to_sheets(df: pd.DataFrame, date: str = None) -> bool:
    """Deprecated: timeline_archive removed. No-op."""
    print("[GSheets] save_timeline_to_sheets: timeline_archive removed — no-op")
    return True


def load_timeline_dates_from_sheets() -> list:
    """Return sorted list of dates available in daily_snapshots (current month)."""
    try:
        gc = _get_client()
        ws = sheets_manager.get_worksheet(TAB_DAILY_SNAPSHOT, gc=gc)
        if ws is None:
            return []

        data = ws.get_all_values()
        if len(data) <= 1:
            return []

        df = pd.DataFrame(data[1:], columns=data[0])
        if "Date" not in df.columns:
            return []

        return sorted(df["Date"].unique().tolist(), reverse=True)

    except Exception as e:
        print(f"[GSheets] load dates error: {e}")
        return []


def load_timeline_from_sheets(date: str):
    """Load snapshot data for a specific date from daily_snapshots."""
    try:
        gc = _get_client()
        ws = sheets_manager.get_worksheet(TAB_DAILY_SNAPSHOT, gc=gc)
        if ws is None:
            return None

        data = ws.get_all_values()
        if len(data) <= 1:
            return None

        df = pd.DataFrame(data[1:], columns=data[0])
        if "Date" not in df.columns:
            return None

        day_df = df[df["Date"] == date].drop(columns=["Date"], errors="ignore")
        if day_df.empty:
            return None

        if "Ticker" in day_df.columns:
            day_df = day_df.set_index("Ticker")

        for col in day_df.columns:
            day_df[col] = pd.to_numeric(day_df[col], errors="coerce")

        return day_df.round(2)

    except Exception as e:
        print(f"[GSheets] load timeline error: {e}")
        return None


# ── Portfolio ─────────────────────────────────────────────────────────────────

def save_portfolio_to_sheets(df: pd.DataFrame) -> bool:
    try:
        gc = _get_client()
        ws = sheets_manager.get_worksheet(TAB_PORTFOLIO, gc=gc)
        if ws is None:
            return False
        _df_to_sheet(ws, df)
        print("[GSheets] ✅ Portfolio saved")
        return True

    except Exception as e:
        print(f"[GSheets] portfolio error: {e}")
        return False


def load_portfolio_from_sheets():
    try:
        gc = _get_client()
        ws = sheets_manager.get_worksheet(TAB_PORTFOLIO, gc=gc)
        if ws is None:
            return None

        data = ws.get_all_values()
        if len(data) <= 1:
            return None

        df = pd.DataFrame(data[1:], columns=data[0])
        if df.empty:
            return None

        for col in ["Score", "BuyPrice", "CurrentPrice", "Change%", "P/L"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    except Exception as e:
        print(f"[GSheets] load portfolio error: {e}")
        return None


# ── Post Analysis ─────────────────────────────────────────────────────────────

def save_post_analysis_to_sheets(df: pd.DataFrame) -> bool:
    """
    Append-only upsert — NEVER overwrites historical data.
    Key: Ticker + ScanDate.
    Logic:
      1. Read existing rows from current sheet.
      2. If current sheet is empty, seed from legacy RidingHigh-Data spreadsheet.
      3. Upsert: rows whose (Ticker, ScanDate) match incoming are replaced;
         all other existing rows are preserved unchanged.
      4. Write combined result (sort by ScanDate, Ticker).
    """
    KEY = ["Ticker", "ScanDate"]
    try:
        gc = _get_client()
        ws = _get_post_analysis_ws(gc=gc)
        if ws is None:
            return False

        # ── Step 1: load existing ─────────────────────────────────────────
        raw = ws.get_all_values()
        if len(raw) > 1 and raw[0]:
            existing_df = pd.DataFrame(raw[1:], columns=raw[0])
        else:
            existing_df = pd.DataFrame()

        # Safety: if the sheet returned empty but has row_count > 50, something
        # is wrong (quota blip / wrong tab). Abort rather than overwrite history.
        try:
            if existing_df.empty and ws.row_count > 50:
                raise RuntimeError(
                    f"[GSheets] ⚠️ post_analysis sheet has {ws.row_count} rows but "
                    f"get_all_values() returned empty — aborting to protect history."
                )
        except Exception as _row_count_err:
            # row_count unavailable (API error) — re-raise only if it's our RuntimeError
            if "aborting to protect history" in str(_row_count_err):
                raise

        # ── Step 2: seed from legacy if current sheet is empty ────────────
        if existing_df.empty:
            try:
                legacy_ws = gc.open_by_key(LEGACY_SPREADSHEET_ID).worksheet("post_analysis")
                legacy_raw = legacy_ws.get_all_values()
                if len(legacy_raw) > 1:
                    existing_df = pd.DataFrame(legacy_raw[1:], columns=legacy_raw[0])
                    print(f"[GSheets] Seeded {len(existing_df)} rows from legacy spreadsheet")
            except Exception as seed_err:
                print(f"[GSheets] Legacy seed skipped: {seed_err}")

        # ── Step 3: upsert ────────────────────────────────────────────────
        if existing_df.empty or not all(k in existing_df.columns for k in KEY) \
                              or not all(k in df.columns for k in KEY):
            # No existing history — safe to write incoming as-is
            combined = df.copy()
            preserved = 0
        else:
            all_cols = list(existing_df.columns)
            for col in df.columns:
                if col not in all_cols:
                    all_cols.append(col)

            existing_df  = existing_df.reindex(columns=all_cols)
            df_reindexed = df.reindex(columns=all_cols)

            incoming_keys = set(zip(df["Ticker"], df["ScanDate"]))
            existing_keep = existing_df[
                ~existing_df.apply(
                    lambda r: (r["Ticker"], r["ScanDate"]) in incoming_keys, axis=1
                )
            ]
            combined  = pd.concat([existing_keep, df_reindexed], ignore_index=True)
            preserved = len(existing_keep)

        # ── Step 4: sort and write ────────────────────────────────────────
        if "ScanDate" in combined.columns:
            combined = combined.sort_values(["ScanDate", "Ticker"], ignore_index=True)

        _df_to_sheet(ws, combined)
        print(
            f"[GSheets] ✅ Post analysis saved "
            f"({len(df)} upserted, {preserved} preserved, {len(combined)} total)"
        )
        return True

    except Exception as e:
        print(f"[GSheets] post analysis save error: {e}")
        return False


def load_post_analysis_from_sheets() -> pd.DataFrame:
    try:
        gc = _get_client()
        ws = _get_post_analysis_ws(gc=gc)
        if ws is None:
            return pd.DataFrame()

        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()

        df = pd.DataFrame(data[1:], columns=data[0])

        numeric_cols = [
            "Score", "ScanPrice", "ScanChange%",
            "MxV", "RunUp", "RSI", "ATRX", "REL_VOL", "Gap", "VWAP", "Float%",
            "PriceToHigh", "PriceTo52WHigh",
            "D1_Open", "D1_High", "D1_Low", "D1_Close",
            "D2_Open", "D2_High", "D2_Low", "D2_Close",
            "D3_Open", "D3_High", "D3_Low", "D3_Close",
            "D4_Open", "D4_High", "D4_Low", "D4_Close",
            "D5_Open", "D5_High", "D5_Low", "D5_Close",
            "MaxDrop%", "BestDay", "TP10_Hit", "TP15_Hit", "TP20_Hit",
            "IntraHigh", "IntraLow", "PeakScorePrice",
            "PeakScore", "DayRunUp%",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        num_cols = df.select_dtypes(include="number").columns
        df[num_cols] = df[num_cols].round(2)
        return df

    except Exception as e:
        print(f"[GSheets] post analysis load error: {e}")
        return pd.DataFrame()
