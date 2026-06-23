#!/usr/bin/env python3
"""
create_agent_sheets.py
──────────────────────
Creates the Agent Google Sheets (see AGENT_SHEET_NAMES) in the current (or specified) month's
Drive folder. Follows the exact same pattern as prepare_next_month.py:
  - OAuth user-owned creation (SA has 0 GB quota)
  - Service Account shared as Editor
  - Idempotent: skips if sheet already exists
  - Updates sheets_config.json with new IDs

Usage:
    python -m agent.setup.create_agent_sheets              # create for current month
    python -m agent.setup.create_agent_sheets --month 2026-06  # specific month
    python -m agent.setup.create_agent_sheets --dry-run    # preview only
"""

import argparse
import json
import os
import sys
from datetime import datetime

import pytz

PERU_TZ = pytz.timezone("America/Lima")

# Add repo root to path so we can import sheets_manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import sheets_manager


# ── Agent sheet definitions ──────────────────────────────────────────────────

AGENT_SHEET_NAMES = [
    "decision_log",
    "paper_portfolio",
    "score_analytics",
    "postmortems",
    "sentinel_events",
    "system_events",
    "market_context",
    "news_findings",
    "pending_suggestions",
    "config_history",
    "borrow_data",
    "borrow_coverage",
    "agent_scorecard",
    "weekly_summary",
    "skip_summary",
]

# Headers for each sheet (see AGENT_SHEET_HEADERS below for exact column counts)
AGENT_SHEET_HEADERS = {
    "decision_log": [
        # Identity (5)
        "DecisionID", "Timestamp", "Ticker", "SignalSource", "AgentMode",
        # Action (3)
        "Action", "Reason", "SkipReason",
        # Signal data (7)
        "Price", "Volume", "MarketCap", "Float", "Open", "High", "Low",
        # Metrics (9)
        "Score", "MxV", "RunUp", "ATRX", "RSI", "TypicalPriceDist", "REL_VOL",
        "PriceVsSMA20", "ScanChange", "FloatPct",
        # Decision timing (1)
        "DecisionTimeMs",
        # Quality (1)
        "ConfidenceScore",
        # Tradability (4)
        "IsShortable", "BorrowFee", "BorrowAvailable", "LocateStatus",
        # Position calc (4)
        "PositionSizeUSD", "Quantity", "TPPrice", "SLPrice",
        # Safety (4)
        "ExistingPosition", "BuyingPower",
        "ColdStartConcurrentLeft", "ColdStartDailyLeft",
        # Execution (3)
        "OrderID", "OrderStatus", "ExecutionPrice",
    ],  # 41 columns

    "paper_portfolio": [
        # Identity (4)
        "PositionID", "Ticker", "EntryDate", "EntryTime",
        # Entry (4)
        "EntryPrice", "Quantity", "PositionSizeUSD", "Side",
        # Orders (5)
        "EntryOrderID", "TPOrderID", "SLOrderID", "TPPrice", "SLPrice",
        # Current state (4)
        "CurrentPrice", "UnrealizedPnL", "UnrealizedPnLPct", "Status",
        # Exit (4)
        "ExitPrice", "ExitDate", "ExitTime", "ExitReason",
        # Results (2)
        "RealizedPnL", "RealizedPnLPct",
        # Meta (2)
        "LastUpdated", "DataQuality",
    ],  # 25 columns

    "score_analytics": [
        # Identity (3)
        "Date", "AnalysisType", "Period",
        # Performance (5)
        "TotalTrades", "WinRate", "TotalPnL", "AvgPnL", "MedianPnL",
        # Score tiers (4)
        "WinRate_60_70", "WinRate_70_80", "WinRate_80_90", "WinRate_90_plus",
        # Metric correlations (7)
        "Corr_MxV", "Corr_RunUp", "Corr_ATRX", "Corr_RSI",
        "Corr_TypicalPriceDist", "Corr_ScanChange", "Corr_REL_VOL",
        # Top insights (4)
        "StrongestPredictor", "WeakestPredictor", "SurpriseFinding", "Recommendation",
        # Meta (2)
        "SampleSize", "GeneratedAt",
    ],  # 25 columns

    "postmortems": [
        # Identity (3)
        "PostmortemID", "PositionID", "Ticker",
        # Entry context (4)
        "EntryDate", "EntryPrice", "ScoreAtEntry", "MetricsAtEntry",
        # Outcome (4)
        "ExitDate", "ExitPrice", "PnLPct", "ExitReason",
        # Analysis (4)
        "DurationHours", "MaxFavorable", "MaxAdverse", "AutoLessons",
        # Meta (2)
        "GeneratedAt", "ScoreVersion",
    ],  # 17 columns

    "sentinel_events": [
        "Timestamp", "EventType", "Severity", "Component", "Message", "Details", "ActionTaken"
    ],
    "system_events": [
        # All (7)
        "Timestamp", "EventType", "Severity", "Component", "Message",
        "Details", "ActionTaken",
    ],  # 7 columns

    "market_context": [
        # All (11)
        "Timestamp", "SPY_Open", "SPY_Close", "SPY_Direction",
        "IWM_Open", "IWM_Close", "IWM_Direction",
        "VIX_Close", "VIX_Level", "Market_Regime", "Errors",
    ],  # 11 columns

    "news_findings": [
        # All (11)
        "Timestamp", "Ticker", "Has_Material_News", "EDGAR_Filing_Count",
        "EDGAR_Latest_Form", "EDGAR_Latest_Date", "EDGAR_All_Filings",
        "Finnhub_News_Count", "Finnhub_Latest_Headline", "Finnhub_All_News", "Errors",
    ],  # 11 columns

    "pending_suggestions": [
        # Identity (3)
        "SuggestionID", "GeneratedDate", "WeekOf",
        # Content (4)
        "Type", "Description", "Reasoning", "Confidence",
        # Impact (3)
        "AffectedMetric", "CurrentValue", "ProposedValue",
        # Status (3)
        "Status", "UserResponse", "ResponseDate",
        # Meta (1)
        "SampleSize",
    ],  # 14 columns

    "config_history": [
        # All (10)
        "ChangeID", "Timestamp", "ChangedBy", "ChangeType",
        "Parameter", "OldValue", "NewValue", "Reason",
        "SuggestionID", "ApprovedBy",
    ],  # 10 columns

    "borrow_data": [
        # All (9)
        "Ticker", "CheckDate", "CheckTime", "IsShortable",
        "IsETB", "IsHTB", "BorrowFeePct", "SharesAvailable",
        "Source",
    ],  # 9 columns

    "borrow_coverage": [
        # All (8) — TASK-172 daily borrow coverage of the scanned universe
        "CheckDate", "CheckTime", "ScannedUniverse", "WithBorrowData",
        "PctWithBorrowData", "ShortableCount", "PctShortable", "Source",
    ],  # 8 columns

    "agent_scorecard": [
        # All (7)
        "Date", "Agent", "Facts", "Anomaly_Count", "Anomaly_High",
        "Anomaly_Detail", "Generated_At",
    ],  # 7 columns

        "monthly_summary": [
        # Period (1) — SINGLE tab monthly_summary (MonthOf=YYYY-MM carries the year), one row per month
        "MonthOf",
        # Performance (7)
        "Trades", "Wins", "Losses", "WinRate", "TotalPnL", "AvgWin", "AvgLoss",
        # Activity (5)
        "Enters", "Skips", "TickersChecked", "Anomalies", "Conflicts",
        # Insight + meta (3)
        "Conclusion", "SampleSizeFlag", "GeneratedAt",
    ],  # 16 columns — NOT in AGENT_SHEET_NAMES (per-year, special-purpose host RH-Summaries)

    "weekly_summary": [
        # Period (1)
        "WeekOf",
        # Performance — sourced from review_completed_trades + summarize (7)
        "Trades", "Wins", "Losses", "WinRate", "TotalPnL", "AvgWin", "AvgLoss",
        # Activity — sourced from existing weekly_summary() dict (5)
        "Enters", "Skips", "TickersChecked", "Anomalies", "Conflicts",
        # Insight + meta (3)
        "Conclusion", "SampleSizeFlag", "GeneratedAt",
    ],  # 16 columns

    "skip_summary": [
        # Run identity (2) — TASK-125: per-run aggregated SKIP counts by reason
        "Timestamp", "RunID",
        # Aggregation (5)
        "SkipReason", "Count", "Tickers", "ScoreMin", "ScoreMax",
    ],  # 7 columns
}


# ── Main logic ───────────────────────────────────────────────────────────────

def _get_month_key(month_arg: str = None, next_month: bool = False) -> str:
    """Return month key (YYYY-MM).

    - month_arg: explicit YYYY-MM (takes priority)
    - next_month: if True, compute next month (same logic as prepare_next_month.py)
    - default: current month in Peru timezone
    """
    if month_arg:
        # Validate format
        datetime.strptime(month_arg, "%Y-%m")
        return month_arg

    now = datetime.now(PERU_TZ)
    if next_month:
        # Same logic as prepare_next_month.py
        if now.month == 12:
            return f"{now.year + 1:04d}-01"
        return f"{now.year:04d}-{now.month + 1:02d}"

    return now.strftime("%Y-%m")


def _already_done(month_key: str) -> bool:
    """True if sheets_config.json already has all agent sheets for month_key."""
    config = sheets_manager._load_config()
    if month_key not in config:
        return False
    return all(name in config[month_key] for name in AGENT_SHEET_NAMES)


def _set_headers(gc, sheet_id: str, headers: list):
    """Write header row to sheet1 of a spreadsheet."""
    try:
        spreadsheet = gc.open_by_key(sheet_id)
        ws = spreadsheet.sheet1
        ws.update("A1", [headers])
    except Exception as e:
        print(f"      ⚠️ Could not set headers: {e}")


def create_agent_sheets(month_key: str, dry_run: bool = False):
    """Create all agent sheets (len(AGENT_SHEET_NAMES)) for the given month."""
    print(f"\n{'='*60}")
    print(f"  Agent Sheets Setup — {month_key}  {'(DRY-RUN)' if dry_run else ''}")
    print(f"{'='*60}")

    # Check idempotency
    if _already_done(month_key):
        print(f"\n✅ All {len(AGENT_SHEET_NAMES)} agent sheets already exist for {month_key}")
        config = sheets_manager._load_config()
        for name in AGENT_SHEET_NAMES:
            print(f"   {name}: {config[month_key][name]}")
        return config[month_key]

    if dry_run:
        print(f"\n[DRY-RUN] Would create the following sheets in folder {month_key}:")
        for name in AGENT_SHEET_NAMES:
            col_count = len(AGENT_SHEET_HEADERS[name])
            print(f"   RH-{month_key}-{name} ({col_count} columns)")
        print(f"\n[DRY-RUN] Would update sheets_config.json with {len(AGENT_SHEET_NAMES)} new IDs")
        print(f"[DRY-RUN] No changes made.")
        return None

    # Get authenticated clients
    # OAuth for file/folder creation (user-owned, same as prepare_next_month.py)
    drive_oauth = sheets_manager._get_drive_service_oauth()
    if drive_oauth is None:
        print("❌ No OAuth credentials available (needed for file creation)")
        sys.exit(1)

    # SA client for writing headers (SA has write access to shared sheets)
    gc = sheets_manager._get_gc()
    if gc is None:
        print("❌ No Google credentials available (Service Account)")
        sys.exit(1)

    # Find or create monthly folder under ROOT_FOLDER_ID via OAuth
    ROOT_FOLDER_ID = "1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh"
    print(f"\n📁 Locating folder for {month_key} under ROOT_FOLDER_ID...")
    q = (
        f"name='{month_key}' and '{ROOT_FOLDER_ID}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    res = drive_oauth.files().list(q=q, fields="files(id)").execute()
    folders = res.get("files", [])

    if folders:
        folder_id = folders[0]["id"]
        print(f"   Found existing folder: {folder_id}")
    else:
        folder_meta = {
            "name": month_key,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [ROOT_FOLDER_ID],
        }
        folder = drive_oauth.files().create(body=folder_meta, fields="id").execute()
        folder_id = folder["id"]
        sheets_manager._share_with_service_account(drive_oauth, folder_id)
        print(f"   Created new folder: {folder_id}")

    # Create each sheet
    print(f"\n📄 Creating {len(AGENT_SHEET_NAMES)} Agent Sheets:")
    config = sheets_manager._load_config()
    month_cfg = config.get(month_key, {})
    created_ids = {}

    for name in AGENT_SHEET_NAMES:
        # Check if already exists in config
        if name in month_cfg:
            print(f"   🔗 {name}: already in config → {month_cfg[name]}")
            created_ids[name] = month_cfg[name]
            continue

        # Check if file exists in Drive folder (by name)
        display_name = f"RH-{month_key}-{name}"
        q = (
            f"name='{display_name}' and '{folder_id}' in parents "
            f"and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        )
        res = drive_oauth.files().list(q=q, fields="files(id)").execute()
        existing = res.get("files", [])

        if existing:
            sheet_id = existing[0]["id"]
            print(f"   🔗 {name}: found in Drive → {sheet_id}")
        else:
            # Create via OAuth (user-owned), then share with SA
            sheet_meta = {
                "name": display_name,
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "parents": [folder_id],
            }
            sheet = drive_oauth.files().create(body=sheet_meta, fields="id").execute()
            sheet_id = sheet["id"]
            sheets_manager._share_with_service_account(drive_oauth, sheet_id)
            print(f"   ✅ {name}: created → {sheet_id}")

        created_ids[name] = sheet_id

        # Set headers
        headers = AGENT_SHEET_HEADERS[name]
        _set_headers(gc, sheet_id, headers)
        print(f"      Headers set ({len(headers)} columns)")

    # Update sheets_config.json
    print(f"\n💾 Updating sheets_config.json...")
    config = sheets_manager._load_config()  # reload fresh
    if month_key not in config:
        config[month_key] = {}
    config[month_key].update(created_ids)
    sheets_manager._save_config(config)
    print(f"   ✅ Added {len(created_ids)} agent sheet IDs to {month_key}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  ✅ Agent Sheets Setup Complete — {month_key}")
    print(f"{'='*60}")
    print(f"\n📋 Sheet IDs:")
    for name, sid in created_ids.items():
        print(f"   {name}: {sid}")

    return created_ids


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Create the Agent Google Sheets for a given month"
    )
    parser.add_argument(
        "--month", type=str, default=None,
        help="Month to create sheets for (YYYY-MM). Default: current month."
    )
    parser.add_argument(
        "--next-month", action="store_true",
        help="Create sheets for next Peru month (use in monthly cron)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be created without making changes."
    )
    args = parser.parse_args()

    month_key = _get_month_key(args.month, next_month=args.next_month)
    create_agent_sheets(month_key, dry_run=args.dry_run)

    # TASK-91 scope-1: fail LOUD if any agent sheet is missing after creation.
    # A partial/failed run must abort so the workflow never commits an incomplete
    # sheets_config (the silent gap that left June with 9 sheets on 1/5).
    if not args.dry_run:
        _cfg = sheets_manager._load_config()
        _missing = [n for n in AGENT_SHEET_NAMES if n not in _cfg.get(month_key, {})]
        if _missing:
            print(f"\n❌ TASK-91: {len(_missing)}/{len(AGENT_SHEET_NAMES)} agent sheet(s) "
                  f"missing for {month_key} after creation: {_missing}")
            sys.exit(1)
        print(f"\n✅ TASK-91: verified all {len(AGENT_SHEET_NAMES)} agent sheets for {month_key}")


if __name__ == "__main__":
    main()
