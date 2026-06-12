#!/usr/bin/env python3
"""
⚠️ DEPRECATED 2026-06-12 (TASK-152): the PK Google-Sheets mirror is RETIRED.
The PK source-of-truth is git (versioned). The Sheet mirror went stale (last
synced 2026-05-16, showed v2.0 vs the live PK) and is redundant. Kept here only
per the §12 versioned-filenames convention; do not run it to "resync" the mirror.

sync_pk_to_sheet.py — Create the Google Sheets master backup of
the Project Knowledge document (RidingHigh_Pro_PK_v2.md).

This creates a Google Sheet titled "RidingHigh-Pro-System-Reference"
inside the RidingHigh root Drive folder. The sheet contains:
  - Tab "Content"  — the full PK content (one line per row)
  - Tab "Metadata" — sync info (version, source, timestamp)

────────────────────────────────────────────────────────────────────
WHY THIS USES OAuth, NOT Service Account
────────────────────────────────────────────────────────────────────
Google Service Accounts have **0 GB Drive storage quota**. Files
created by them (with them as owner) immediately fail with
"quota exceeded" — even on a brand-new account with 15 GB free.

The fix (used everywhere in this project):
  - Create the file via user OAuth (file is owned by user → user's quota)
  - Then share the file with the service account (Editor)
  - Service account can then read/write content; user owns storage

This script follows the exact same pattern as `prepare_next_month.py`
and `sheets_manager._create_sheet_in_folder()`.

────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────
    cd ~/RidingHighPro
    python3 sync_pk_to_sheet.py

Idempotent: if a sheet with the same name already exists in the
folder, the script offers to UPDATE it (re-sync content) instead
of creating a duplicate.

────────────────────────────────────────────────────────────────────
PREREQUISITES
────────────────────────────────────────────────────────────────────
- ~/RidingHighPro/oauth_token.json must exist
  (created via `python3 get_oauth_token.py` if missing)
- ~/RidingHighPro/google_credentials.json (for SA email lookup)
- The PK markdown file at ~/RidingHighPro/docs/RidingHigh_Pro_PK_v2.md

────────────────────────────────────────────────────────────────────
Created: 2026-05-02 (PK v2.0 generation session)
Author:  Claude (under direction of Amihay Levy)
Pattern: Mirrors prepare_next_month.py for OAuth-based sheet creation
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# ── Project setup ──────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import pytz
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Constants ──────────────────────────────────────────────────────────
SHEET_TITLE = "RidingHigh-Pro-System-Reference"
PK_FILE_PATH = SCRIPT_DIR / "docs" / "RidingHigh_Pro_PK_v2.md"
ROOT_FOLDER_ID = "1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

PERU_TZ = pytz.timezone("America/Lima")


# ════════════════════════════════════════════════════════════════════════
# OAuth helpers — mirror of prepare_next_month.py
# ════════════════════════════════════════════════════════════════════════

def load_oauth_credentials():
    """Load OAuth credentials from env var (Actions) or local file (dev).
    
    Mirrors prepare_next_month.py::load_credentials.
    """
    token_json = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if token_json:
        print("🔑 Using GOOGLE_OAUTH_TOKEN_JSON from env var")
        data = json.loads(token_json)
    else:
        token_path = SCRIPT_DIR / "oauth_token.json"
        if not token_path.exists():
            print(f"❌ OAuth token not found.")
            print(f"   Expected: {token_path}")
            print(f"   To create: python3 get_oauth_token.py")
            sys.exit(1)
        print(f"🔑 Using {token_path.name} (local)")
        with open(token_path) as f:
            data = json.load(f)

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data.get("scopes", SCOPES),
    )

    if not creds.valid:
        creds.refresh(Request())
        print("   🔄 Token refreshed")

    return creds


def get_service_account_email():
    """Return SA email from GOOGLE_CREDENTIALS_JSON env or local file.
    
    Mirrors prepare_next_month.py::get_sa_email.
    """
    sa_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if sa_json:
        return json.loads(sa_json).get("client_email")

    sa_path = SCRIPT_DIR / "google_credentials.json"
    if sa_path.exists():
        with open(sa_path) as f:
            return json.load(f).get("client_email")

    return None


def share_with_service_account(drive, file_id, sa_email):
    """Grant the service account Editor access to the file."""
    if not sa_email:
        print("   ⚠️  No SA email found — skipping share")
        return

    try:
        drive.permissions().create(
            fileId=file_id,
            body={
                "type": "user",
                "role": "writer",
                "emailAddress": sa_email,
            },
            sendNotificationEmail=False,
            fields="id",
        ).execute()
        print(f"   🤝 Shared with SA: {sa_email}")
    except Exception as e:
        print(f"   ⚠️  Share failed: {e}")


def find_existing_sheet(drive, title, parent_id):
    """Find an existing sheet by name in the given folder. Returns ID or None."""
    query = (
        f"name='{title}' and "
        f"'{parent_id}' in parents and "
        f"mimeType='application/vnd.google-apps.spreadsheet' and "
        f"trashed=false"
    )
    res = drive.files().list(q=query, fields="files(id, name)").execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def create_sheet(drive, title, parent_id):
    """Create a new Google Sheets file in parent_id via OAuth (user-owned)."""
    meta = {
        "name": title,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [parent_id],
    }
    file = drive.files().create(body=meta, fields="id").execute()
    return file["id"]


# ════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════

def now_peru_str():
    return datetime.now(PERU_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  PK Master Sheet Creator — OAuth-based                     ║")
    print(f"║  {now_peru_str():<58}║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # ── 1. Verify PK file exists ──────────────────────────────────────
    if not PK_FILE_PATH.exists():
        print(f"❌ PK file not found at {PK_FILE_PATH}")
        print(f"   Run from ~/RidingHighPro and ensure docs/RidingHigh_Pro_PK_v2.md exists.")
        sys.exit(1)

    print(f"📄 PK file: {PK_FILE_PATH}")
    print(f"   Size: {PK_FILE_PATH.stat().st_size:,} bytes")

    pk_content = PK_FILE_PATH.read_text(encoding="utf-8")
    pk_lines = pk_content.split("\n")
    print(f"   Lines: {len(pk_lines):,}\n")

    # ── 2. Authenticate via OAuth ─────────────────────────────────────
    creds = load_oauth_credentials()
    drive = build("drive", "v3", credentials=creds)
    gc = gspread.authorize(creds)

    sa_email = get_service_account_email()
    if sa_email:
        print(f"🤖 SA for sharing: {sa_email}\n")
    else:
        print("⚠️  SA email not found — sheet won't be shared with SA\n")

    # ── 3. Check for existing sheet ───────────────────────────────────
    print(f"🔍 Searching for existing '{SHEET_TITLE}' in folder {ROOT_FOLDER_ID}...")
    existing_id = find_existing_sheet(drive, SHEET_TITLE, ROOT_FOLDER_ID)

    is_update = False
    if existing_id:
        print(f"   ⚠️  Found existing sheet: {existing_id}")
        choice = input(f"   Update existing? (y/n): ").strip().lower()
        if choice == "y":
            sheet_id = existing_id
            is_update = True
            print(f"   ✅ Will update existing sheet\n")
        else:
            print(f"   ❌ Aborted. Delete the existing sheet manually if you want to recreate.")
            sys.exit(0)
    else:
        print(f"   ✅ No existing sheet — will create new\n")
        # ── 4a. Create new sheet via OAuth ────────────────────────────
        print(f"📝 Creating new sheet '{SHEET_TITLE}' (via OAuth, user-owned)...")
        sheet_id = create_sheet(drive, SHEET_TITLE, ROOT_FOLDER_ID)
        print(f"   ✅ Created. Sheet ID: {sheet_id}")
        share_with_service_account(drive, sheet_id, sa_email)
        print()

    # ── 5. Open with gspread (works because user owns it) ─────────────
    sh = gc.open_by_key(sheet_id)

    # ── 6. Set up tabs ────────────────────────────────────────────────
    existing_tabs = [ws.title for ws in sh.worksheets()]
    print(f"📋 Existing tabs: {existing_tabs}")

    # Ensure Content tab
    if "Content" not in existing_tabs:
        sh.add_worksheet(title="Content", rows=max(len(pk_lines) + 100, 1000), cols=1)
        print(f"   ➕ Added 'Content' tab")
    # Ensure Metadata tab
    if "Metadata" not in existing_tabs:
        sh.add_worksheet(title="Metadata", rows=20, cols=2)
        print(f"   ➕ Added 'Metadata' tab")
    # Remove default "Sheet1" if it exists alongside others
    if "Sheet1" in existing_tabs and len(existing_tabs) > 1:
        try:
            sh.del_worksheet(sh.worksheet("Sheet1"))
            print(f"   🗑️  Removed default 'Sheet1'")
        except Exception:
            pass
    print()

    # ── 7. Write Content tab ──────────────────────────────────────────
    ws_content = sh.worksheet("Content")
    print(f"📤 Writing {len(pk_lines):,} lines to 'Content' tab...")

    # Resize if needed
    if ws_content.row_count < len(pk_lines):
        ws_content.resize(rows=len(pk_lines) + 100)

    ws_content.clear()
    data = [[line] for line in pk_lines]
    ws_content.update(values=data, range_name="A1")
    print(f"   ✅ Content written ({len(data)} rows)\n")

    # ── 8. Write Metadata tab ─────────────────────────────────────────
    ws_meta = sh.worksheet("Metadata")
    ws_meta.clear()

    metadata = [
        ["Field", "Value"],
        ["Document title", "RidingHigh Pro — Master System Reference"],
        ["Version", "v2.0"],
        ["Last sync (Peru time)", now_peru_str()],
        ["Source file", str(PK_FILE_PATH)],
        ["Source bytes", str(PK_FILE_PATH.stat().st_size)],
        ["Source lines", str(len(pk_lines))],
        ["Sheet ID", sheet_id],
        ["Folder ID", ROOT_FOLDER_ID],
        ["Generator", "sync_pk_to_sheet.py"],
        ["Created via", "OAuth (user-owned, SA shared as Editor)"],
        ["", ""],
        ["Sync direction", "Repo → Sheets (one-way)"],
        ["Update frequency", "On every PK change (per Anti-Drift Contract §35)"],
        ["", ""],
        ["Recovery use", "If repo lost, this sheet preserves PK content"],
        ["Read-only convention", "Sheets copy is mirror; do NOT edit in place"],
    ]
    ws_meta.update(values=metadata, range_name="A1")

    # Bold header row
    try:
        ws_meta.format("A1:B1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 1.0},
        })
    except Exception as e:
        print(f"   ⚠️  Format failed (non-critical): {e}")

    print(f"   ✅ Metadata written\n")

    # ── 9. Final summary ──────────────────────────────────────────────
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"╔════════════════════════════════════════════════════════════╗")
    print(f"║  ✅ DONE                                                   ║")
    print(f"╚════════════════════════════════════════════════════════════╝")
    print(f"\n📊 Sheet:    {SHEET_TITLE}")
    print(f"🆔 ID:       {sheet_id}")
    print(f"🔗 URL:      {sheet_url}")
    print(f"📁 Folder:   {ROOT_FOLDER_ID}")
    print(f"📅 Synced:   {now_peru_str()}")
    print(f"🤝 Owner:    user OAuth (your account)")
    if sa_email:
        print(f"🤖 Editor:   {sa_email}")
    print(f"\n💡 Save this Sheet ID. Suggested addition to PK §A1:")
    print(f"   Sheet ID: {sheet_id}")
    print(f"\n💡 To re-sync after PK update, just re-run this script.")
    print(f"   It will detect the existing sheet and offer to update.\n")


if __name__ == "__main__":
    main()
