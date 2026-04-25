#!/usr/bin/env python3
"""
setup_health_audit_sheet.py
============================
One-time script to create the 'RidingHigh-Health-Audit' Google Sheet
with 3 tabs: History, Latest, Failed.

Uses OAuth (user credentials) for Sheet creation because the service
account has 0 GB Drive quota. After creation, shares with SA for read/write.

Run ONCE locally:
  cd ~/RidingHighPro && python3 setup_health_audit_sheet.py

After creation:
  - The Sheet ID is saved to .health_audit_sheet_id (gitignored)
  - The Sheet is shared with the service account (read/write)
"""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CREDENTIALS_FILE = REPO_ROOT / "google_credentials.json"
OAUTH_TOKEN_FILE = REPO_ROOT / "oauth_token.json"
SHEET_ID_FILE = REPO_ROOT / ".health_audit_sheet_id"
SHEET_NAME = "RidingHigh-Health-Audit"

SERVICE_ACCOUNT_EMAIL = "ridinghigh-sheets-v2@ridinghigh-pro-v2.iam.gserviceaccount.com"
USER_EMAIL = os.environ.get("USER_EMAIL", "projects5069@gmail.com")

HISTORY_HEADER = ["Timestamp", "Check ID", "Category", "Name", "Status", "Message", "Details"]


def get_oauth_creds():
    """Load user OAuth credentials for Sheet creation."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not OAUTH_TOKEN_FILE.exists():
        return None
    token_data = json.loads(OAUTH_TOKEN_FILE.read_text())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ]),
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def get_sa_client():
    """Get gspread client with service account (for reading/writing after creation)."""
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
    return gspread.authorize(creds)


def main():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        print("❌ Missing deps. Run: pip install gspread google-auth google-api-python-client")
        return 1

    if not CREDENTIALS_FILE.exists():
        print(f"❌ {CREDENTIALS_FILE} not found")
        return 1

    # SA client for checking existing sheet / writing after creation
    gc_sa = get_sa_client()

    # Check if already exists
    if SHEET_ID_FILE.exists():
        existing_id = SHEET_ID_FILE.read_text().strip()
        try:
            sh = gc_sa.open_by_key(existing_id)
            print(f"✅ Sheet already exists: {sh.title}")
            print(f"   URL: https://docs.google.com/spreadsheets/d/{existing_id}")
            print(f"   Tabs: {[ws.title for ws in sh.worksheets()]}")
            return 0
        except Exception as e:
            print(f"⚠️  Existing sheet ID is invalid ({e}) — will create new")
            SHEET_ID_FILE.unlink()

    # Create via OAuth (user credentials — no quota issue)
    oauth_creds = get_oauth_creds()
    if not oauth_creds:
        print(f"❌ oauth_token.json not found — cannot create Sheet")
        print(f"   Service account has 0 GB quota, OAuth is required for creation")
        return 1

    print(f"📝 Creating '{SHEET_NAME}' via OAuth...")
    drive_svc = build("drive", "v3", credentials=oauth_creds)

    meta = {
        "name": SHEET_NAME,
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }
    file = drive_svc.files().create(body=meta, fields="id").execute()
    sheet_id = file["id"]
    print(f"   Created with ID: {sheet_id}")

    # Share with service account (so SA can read/write)
    drive_svc.permissions().create(
        fileId=sheet_id,
        body={
            "type": "user",
            "role": "writer",
            "emailAddress": SERVICE_ACCOUNT_EMAIL,
        },
        sendNotificationEmail=False,
    ).execute()
    print(f"   Shared with SA: {SERVICE_ACCOUNT_EMAIL}")

    # Now use SA client to set up tabs (SA has full Sheets API access)
    sh = gc_sa.open_by_key(sheet_id)

    # Default sheet → rename to History
    default_ws = sh.sheet1
    default_ws.update_title("History")
    default_ws.append_row(HISTORY_HEADER)

    # Add Latest and Failed tabs
    sh.add_worksheet(title="Latest", rows=100, cols=10)
    latest_ws = sh.worksheet("Latest")
    latest_ws.append_row(HISTORY_HEADER)

    sh.add_worksheet(title="Failed", rows=100, cols=10)
    failed_ws = sh.worksheet("Failed")
    failed_ws.append_row(HISTORY_HEADER)

    # Format headers
    for ws in [default_ws, latest_ws, failed_ws]:
        try:
            ws.format("A1:G1", {"textFormat": {"bold": True},
                                "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85}})
            ws.freeze(rows=1)
        except Exception:
            pass

    # Save ID
    SHEET_ID_FILE.write_text(sheet_id)

    print(f"\n✅ Sheet created successfully!")
    print(f"   Title: {SHEET_NAME}")
    print(f"   ID: {sheet_id}")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print(f"   Sheet ID saved to: {SHEET_ID_FILE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
