#!/usr/bin/env python3
"""TASK-48 2b-i — provision the RH-Summaries spreadsheet (one-time, live).

Creates a STABLE, per-NOT-rotated spreadsheet named "RH-Summaries" that hosts
the monthly summary as a SINGLE tab 'monthly_summary' (MonthOf=YYYY-MM already
carries the year, so one tab accumulates every month across all years — a
continuous multi-year trend table; no per-year split).

Mirrors the proven health-audit setup pattern:
  OAuth create -> share with service account -> add tab + headers -> save id to dotfile.

Idempotent: if the dotfile exists and opens, does nothing. Safe to re-run.

Run live (one-time):  python3 setup_summaries_sheet.py
"""
import os
import sys
from pathlib import Path

import sheets_manager as sm

SHEET_NAME = "RH-Summaries"
TAB_NAME = "monthly_summary"
DOTFILE = Path.home() / "RidingHighPro" / ".rh_summaries_sheet_id"


def _gc_or_raise():
    gc = _gc_or_raise()
    if gc is None:
        raise RuntimeError("gspread client unavailable (check service account creds)")
    return gc


def _headers():
    from agent.setup.create_agent_sheets import AGENT_SHEET_HEADERS
    return AGENT_SHEET_HEADERS["monthly_summary"]


def _existing_id():
    """Return saved spreadsheet id if the dotfile exists and opens, else None."""
    if not DOTFILE.exists():
        return None
    sid = DOTFILE.read_text().strip()
    if not sid:
        return None
    try:
        gc = _gc_or_raise()
        gc.open_by_key(sid)  # verify it really opens
        return sid
    except Exception as e:
        print(f"⚠️ dotfile id {sid} did not open ({e}); will re-provision")
        return None


def _ensure_tab(spreadsheet, headers):
    """Get-or-create the monthly_summary tab and ensure headers in row 1."""
    try:
        ws = spreadsheet.worksheet(TAB_NAME)
        print(f"  tab '{TAB_NAME}' already exists")
    except Exception:
        ws = spreadsheet.add_worksheet(title=TAB_NAME, rows=200, cols=max(16, len(headers)))
        print(f"  created tab '{TAB_NAME}'")
    # ensure headers in row 1 (idempotent: only write if row 1 is empty/mismatched)
    first_row = ws.row_values(1)
    if first_row != headers:
        ws.update("A1", [headers])
        print(f"  wrote {len(headers)} headers to row 1")
    else:
        print("  headers already correct")
    return ws


def provision():
    headers = _headers()

    existing = _existing_id()
    if existing:
        print(f"✅ RH-Summaries already provisioned (id={existing}); ensuring tab+headers")
        gc = _gc_or_raise()
        ss = gc.open_by_key(existing)
        _ensure_tab(ss, headers)
        return existing

    # Create the spreadsheet via OAuth (user-owned), same as health-audit setup
    print(f"Creating spreadsheet '{SHEET_NAME}' via OAuth ...")
    drive = sm._get_drive_service_oauth()
    if drive is None:
        raise RuntimeError("OAuth Drive service unavailable (check oauth_token.json)")
    meta = {"name": SHEET_NAME, "mimeType": "application/vnd.google-apps.spreadsheet"}
    created = drive.files().create(body=meta, fields="id").execute()
    sid = created["id"]
    print(f"  created spreadsheet id={sid}")

    # Share with the service account (so SA can write)
    sm._share_with_service_account(drive, sid)
    print("  shared with service account")

    # Open via gspread and set up the tab + headers
    gc = _gc_or_raise()
    ss = gc.open_by_key(sid)
    _ensure_tab(ss, headers)

    # Persist id to dotfile
    DOTFILE.write_text(sid)
    print(f"✅ saved id to {DOTFILE}")
    return sid


if __name__ == "__main__":
    try:
        sid = provision()
        print(f"\n✅ DONE — RH-Summaries ready (id={sid})")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{sid}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ provisioning failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
