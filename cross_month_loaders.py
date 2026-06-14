"""
cross_month_loaders.py
══════════════════════
Cross-month data aggregation for RidingHigh Pro Dashboard (Issue #PORT-MONTH).

Problem
───────
sheets_manager.get_worksheet(month=None) defaults to current Peru month, so
Dashboard pages (Post Analysis, Portfolio Tracker, Score Tracker, Daily
Summary) only ever see the current month — historical months registered in
sheets_config.json are invisible.

Solution
────────
This module reads from EVERY month present in sheets_config.json and
concatenates the results, with last-write-wins dedup keyed on
(Ticker, ScanDate) for trade-like sheets and (Date) for daily_summary.

Design rules
────────────
1. Additive only — original gsheets_sync functions are NOT modified.
2. Per-month try/except — a single broken sheet must not poison the result.
3. Last-write-wins: when (key) exists in multiple months, the row from the
   most recent month wins (matters for Open positions copied across
   month rotation by monthly_rotation._copy_open_portfolio).
4. Numeric coercion runs once on the combined frame, mirroring the dtype
   handling in the legacy single-month loaders.
5. Empty months are skipped silently (no spam in dashboard logs).

Public API
──────────
    load_post_analysis_all_months()      → DataFrame
    load_portfolio_all_months()          → DataFrame
    load_score_tracker_all_months()      → DataFrame
    load_daily_summary_all_months()      → DataFrame
    get_active_months()                  → list[str]   (e.g. ["2026-04","2026-05","2026-06"])

Each loader returns an empty DataFrame on total failure (never raises),
matching the contract of the legacy single-month loaders.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_manager


# ──────────────────────────────────────────────────────────────────────────────
# Numeric column maps — matched 1:1 with the legacy single-month loaders so
# downstream code (dashboard pages) sees identical dtypes.
# ──────────────────────────────────────────────────────────────────────────────

POST_ANALYSIS_NUMERIC_COLS = [
    "Score", "ScanPrice", "ScanChange%",
    "MxV", "RunUp", "RSI", "ATRX", "REL_VOL", "Gap",
    "TypicalPriceDist", "Float%", "PriceToHigh", "PriceTo52WHigh",
    "D1_Open", "D1_High", "D1_Low", "D1_Close",
    "D2_Open", "D2_High", "D2_Low", "D2_Close",
    "D3_Open", "D3_High", "D3_Low", "D3_Close",
    "D4_Open", "D4_High", "D4_Low", "D4_Close",
    "D5_Open", "D5_High", "D5_Low", "D5_Close",
    "MaxDrop%", "BestDay", "TP10_Hit", "TP15_Hit", "TP20_Hit",
    "IntraHigh", "IntraLow", "PeakScorePrice",
    "PeakScore", "DayRunUp%",
]

PORTFOLIO_NUMERIC_COLS = [
    "Score", "BuyPrice", "EntryPrice", "CurrentPrice", "Change%", "P/L", "PnL",
]

SCORE_TRACKER_NUMERIC_COLS = ["Score"]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_active_months() -> list:
    """
    Return all months registered in sheets_config.json, sorted ascending.

    "Active" = month present as a top-level key in sheets_config.json,
    regardless of whether the sheets contain data. Each loader handles
    empty sheets gracefully via per-month try/except.
    """
    try:
        config = sheets_manager._load_config()
        return sorted(config.keys())
    except Exception as e:
        print(f"[CrossMonth] ⚠️  Failed to read sheets_config.json: {e}")
        return []


def _read_one_month(tab_name: str, month: str, gc) -> pd.DataFrame:
    """
    Read a single tab from a single month. Returns empty DataFrame if the
    sheet is missing, empty, or fails. Never raises.
    """
    try:
        ws = sheets_manager.get_worksheet(tab_name, month=month, gc=gc)
        if ws is None:
            return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        # Tag with source month so callers can filter / debug if needed.
        df["_source_month"] = month
        return df
    except Exception as e:
        print(f"[CrossMonth] ⚠️  {tab_name} {month}: {e}")
        return pd.DataFrame()


def _coerce_numeric(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Coerce a list of columns to numeric, in place. Tolerates missing cols."""
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _coerce_bool(series):
    """Coerce a gspread string column to real bool.

    Handles the bool('False')==True gotcha: every non-empty string is truthy, so
    a naive astype(bool) is WRONG. True iff trimmed-lowercased in {'true','1','yes'}.
    """
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes"])


def exclude_interday_artifacts(df, flag_col="InterdayArtifact"):
    """Drop rows flagged as inter-day split/halt artifacts (TASK-180 / 173 AC#2).

    Returns (clean_df, contamination_pct, n_excluded):
      clean_df          -- df without flagged rows (a copy)
      contamination_pct -- round(n_excluded / total * 100, 2)  [row-based]
      n_excluded        -- number of rows dropped

    Backward-compatible: if df is None/empty or lacks flag_col (older sheets
    written before the detector), returns (df, 0.0, 0) unchanged -- never raises.

    Research usage::

        from cross_month_loaders import load_post_analysis_all_months, exclude_interday_artifacts
        df = load_post_analysis_all_months()
        clean, contamination_pct, n = exclude_interday_artifacts(df)
        print(f"excluded {n} artifact rows ({contamination_pct}% contamination); {len(clean)} clean rows")
    """
    if df is None or df.empty or flag_col not in df.columns:
        return (df, 0.0, 0)
    is_artifact = _coerce_bool(df[flag_col])
    n_excluded  = int(is_artifact.sum())
    total       = len(df)
    contamination_pct = round(n_excluded / total * 100, 2) if total > 0 else 0.0
    clean_df = df[~is_artifact].copy()
    return (clean_df, contamination_pct, n_excluded)


def _dedup_last_wins(df: pd.DataFrame, keys: list) -> pd.DataFrame:
    """
    Drop duplicates by `keys`, keeping the LAST occurrence.

    Why last-wins: months are concatenated in chronological order
    (oldest → newest). When the same (Ticker, ScanDate) appears in two
    months — e.g. an Open position copied from April to May by
    monthly_rotation._copy_open_portfolio — the May row reflects the
    latest known state and should override April.
    """
    missing = [k for k in keys if k not in df.columns]
    if missing:
        # If any key column is missing we cannot safely dedup; return as-is.
        return df
    return df.drop_duplicates(subset=keys, keep="last").reset_index(drop=True)


def _load_all_months(
    tab_name: str,
    dedup_keys: list = None,
    numeric_cols: list = None,
    sort_cols: list = None,
    score_version_filter: str = None,
) -> pd.DataFrame:
    """
    Generic cross-month loader.
      tab_name              — e.g. "post_analysis", "portfolio", "score_tracker", "daily_summary"
      dedup_keys            — columns used for last-wins dedup (None = no dedup)
      numeric_cols          — columns to coerce to numeric after concat
      sort_cols             — final sort order (None = no sort)
      score_version_filter  — if set (e.g. "v2"), keep only rows where
                              score_version equals this value. Rows without
                              the column are KEPT (older sheets pre-tag).
                              Set to None to keep everything.
    """
    months = get_active_months()
    if not months:
        return pd.DataFrame()

    gc = sheets_manager._get_gc()
    if gc is None:
        return pd.DataFrame()

    frames = []
    for month in months:
        m_df = _read_one_month(tab_name, month, gc)
        if not m_df.empty:
            frames.append(m_df)

    if not frames:
        return pd.DataFrame()

    # Align columns across months (older months may have fewer columns)
    all_cols = []
    for f in frames:
        for c in f.columns:
            if c not in all_cols:
                all_cols.append(c)
    aligned = [f.reindex(columns=all_cols) for f in frames]

    combined = pd.concat(aligned, ignore_index=True)

    # Optional score_version filter — applied BEFORE numeric coercion / dedup
    # so we don't waste cycles on rows that will be discarded.
    if score_version_filter and "score_version" in combined.columns:
        before = len(combined)
        # Keep rows that match the filter OR have empty/missing score_version
        # (legacy rows pre-tagging — caller can opt out by setting filter to None)
        sv_str = combined["score_version"].astype(str).str.strip()
        mask = (
            (sv_str == score_version_filter) |
            (sv_str == "") |
            (sv_str == "nan") |
            (combined["score_version"].isna())
        )
        combined = combined[mask].reset_index(drop=True)
        print(f"[CrossMonth] {tab_name}: score_version filter '{score_version_filter}' "
              f"kept {len(combined)}/{before} rows")

    if numeric_cols:
        combined = _coerce_numeric(combined, numeric_cols)

    if dedup_keys:
        combined = _dedup_last_wins(combined, dedup_keys)

    if sort_cols:
        existing_sort = [c for c in sort_cols if c in combined.columns]
        if existing_sort:
            combined = combined.sort_values(existing_sort, ignore_index=True)

    return combined


# ──────────────────────────────────────────────────────────────────────────────
# Public loaders
# ──────────────────────────────────────────────────────────────────────────────

def load_post_analysis_all_months(score_version: str = "v2") -> pd.DataFrame:
    """
    Cross-month replacement for gsheets_sync.load_post_analysis_from_sheets().

    Concatenates post_analysis from every registered month with last-wins
    dedup on (Ticker, ScanDate). Matches the dtype contract of the
    single-month loader (numeric cols cast, rounded to 2 decimals).

    score_version: "v2" (default) keeps only rows tagged v2 in the
                   score_version column. Pass None to disable filtering.
                   Per ADR-004 (commit bf2892b, 2026-05-02), only v2 rows
                   are valid for scoring analyses.
    """
    df = _load_all_months(
        tab_name="post_analysis",
        dedup_keys=["Ticker", "ScanDate"],
        numeric_cols=POST_ANALYSIS_NUMERIC_COLS,
        sort_cols=["ScanDate", "Ticker"],
        score_version_filter=score_version,
    )
    if df.empty:
        return df
    # Match legacy: round numeric cols to 2 decimals
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].round(2)
    return df


def load_portfolio_all_months() -> pd.DataFrame:
    """
    Cross-month replacement for gsheets_sync.load_portfolio_from_sheets().

    Dedup key (Ticker, ScanDate) handles month-rotation carryover: when
    monthly_rotation copies an Open position from April → May, the May row
    is later updated with TP/SL status, so May wins over April for the
    same key.
    """
    return _load_all_months(
        tab_name="portfolio",
        dedup_keys=["Ticker", "ScanDate"],
        numeric_cols=PORTFOLIO_NUMERIC_COLS,
        sort_cols=["ScanDate", "Ticker"],
    )


def load_score_tracker_all_months() -> pd.DataFrame:
    """
    Cross-month replacement for the score_tracker read in dashboard.py
    score_tracker_page._load_data().

    Dedup key (Ticker, ScanDate, ScanTime) — same Score sample at the same
    minute should not appear twice if the boundary copy ever doubles a row.
    """
    return _load_all_months(
        tab_name="score_tracker",
        dedup_keys=["Ticker", "ScanDate", "ScanTime"],
        numeric_cols=SCORE_TRACKER_NUMERIC_COLS,
        sort_cols=["ScanDate", "Ticker", "ScanTime"],
    )


def load_daily_summary_all_months() -> pd.DataFrame:
    """
    Cross-month loader for daily_summary.

    Dedup key (Date) — one summary row per day; if a day appears in two
    months (shouldn't happen but guards corruption), latest wins.
    """
    return _load_all_months(
        tab_name="daily_summary",
        dedup_keys=["Date"],
        numeric_cols=None,   # daily_summary cols vary; let pages cast as they need
        sort_cols=["Date"],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Module self-test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("cross_month_loaders.py — self-test")
    print("=" * 60)
    months = get_active_months()
    print(f"\n📅 Active months in sheets_config.json: {months}")

    if not months:
        print("❌ No months found. Aborting.")
        sys.exit(1)

    print("\n── Post Analysis ──")
    pa = load_post_analysis_all_months()
    print(f"   Total rows: {len(pa)}")
    if not pa.empty and "_source_month" in pa.columns:
        per_month = pa["_source_month"].value_counts().sort_index()
        for m, n in per_month.items():
            print(f"   {m}: {n} rows")

    print("\n── Portfolio ──")
    port = load_portfolio_all_months()
    print(f"   Total rows: {len(port)}")
    if not port.empty and "_source_month" in port.columns:
        per_month = port["_source_month"].value_counts().sort_index()
        for m, n in per_month.items():
            print(f"   {m}: {n} rows")
    if not port.empty and "Status" in port.columns:
        status_counts = port["Status"].value_counts()
        for s, n in status_counts.items():
            print(f"   Status='{s}': {n}")

    print("\n── Score Tracker ──")
    st = load_score_tracker_all_months()
    print(f"   Total rows: {len(st)}")

    print("\n── Daily Summary ──")
    ds = load_daily_summary_all_months()
    print(f"   Total rows: {len(ds)}")

    print("\n✅ Self-test complete.")
