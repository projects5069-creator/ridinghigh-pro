"""
RidingHigh Pro - Monthly Google Sheets Manager

One Google Sheets file per logical tab, organized in monthly Drive folders.
Sheet IDs cached in ~/RidingHighPro/sheets_config.json.

Folder structure (under ROOT_FOLDER_ID):
  2026-04/
    RH-2026-04-timeline_live
    RH-2026-04-daily_snapshots
    RH-2026-04-daily_summary
    RH-2026-04-post_analysis
    RH-2026-04-portfolio
    RH-2026-04-portfolio_live
    RH-2026-04-score_tracker
  2026-05/
    ...
"""

import os
import json
from datetime import datetime

ROOT_FOLDER_ID = "1LKJwf4ryvGa1Cvgs6ZC8JIfuQdgZE4_p"
LEGACY_SPREADSHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"

# Config is looked up in two places:
#   1. Same directory as this file (works in repo-based envs: Streamlit Cloud, GitHub Actions)
#   2. ~/RidingHighPro/ (local Mac fallback)
_REPO_CONFIG_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheets_config.json")
_LOCAL_CONFIG_PATH = os.path.expanduser("~/RidingHighPro/sheets_config.json")
CONFIG_PATH = _REPO_CONFIG_PATH  # canonical write target

SHEET_NAMES = [
    "timeline_live",
    "daily_snapshots",
    "daily_summary",
    "post_analysis",
    "portfolio",
    "portfolio_live",
    "score_tracker",
]

# timeline_live is slimmed to exactly these columns
TIMELINE_LIVE_COLS = ["Date", "ScanTime", "Ticker", "Price", "Score", "Score_I", "Score_B", "Score_C", "Score_D", "Score_E", "Score_F", "Score_G", "Score_H", "EntryScore", "MxV", "RunUp", "REL_VOL"]

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


# ── Config helpers ────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Check repo dir first (Streamlit Cloud / GitHub Actions), then local ~/RidingHighPro/."""
    for path in [_REPO_CONFIG_PATH, _LOCAL_CONFIG_PATH]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


def _save_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_gc():
    """Return an authenticated gspread client, or None."""
    import gspread
    from google.oauth2.service_account import Credentials

    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
            return gspread.authorize(creds)
    except Exception:
        pass

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        import json as _json
        creds = Credentials.from_service_account_info(
            _json.loads(creds_json), scopes=SCOPES)
        return gspread.authorize(creds)

    creds_path = os.path.expanduser("~/RidingHighPro/google_credentials.json")
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return gspread.authorize(creds)

    return None


def _get_drive_service(gc):
    """Build a Drive v3 service from the gspread client's credentials."""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "google-api-python-client required for Drive folder operations. "
            "Install with: pip install google-api-python-client"
        )
    # gspread 6.x stores credentials at gc.http_client.auth
    creds = getattr(gc, "auth", None) or gc.http_client.auth
    return build("drive", "v3", credentials=creds)


# ── Drive / sheet creation ────────────────────────────────────────────────────

def _get_root_folder_id(drive_svc) -> str:
    """
    Return the root parent folder ID to use.
    Tries ROOT_FOLDER_ID first; if inaccessible, falls back to creating
    a 'RidingHigh-Data' folder in the service account's own Drive root.
    """
    if ROOT_FOLDER_ID:
        try:
            drive_svc.files().get(fileId=ROOT_FOLDER_ID, fields="id").execute()
            return ROOT_FOLDER_ID
        except Exception:
            print(f"[SheetsManager] ⚠️ ROOT_FOLDER_ID not accessible — using service account root")

    # Find or create top-level RidingHigh-Data folder
    q = "name='RidingHigh-Data' and 'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    res = drive_svc.files().list(q=q, fields="files(id)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]

    meta = {"name": "RidingHigh-Data", "mimeType": "application/vnd.google-apps.folder"}
    folder = drive_svc.files().create(body=meta, fields="id").execute()
    folder_id = folder["id"]
    print(f"[SheetsManager] Created RidingHigh-Data folder → {folder_id}")
    return folder_id


def _get_or_create_monthly_folder(drive_svc, month_key: str) -> str:
    """Return Drive folder ID for month_key, creating it under the root folder if needed."""
    root_id = _get_root_folder_id(drive_svc)

    q = (
        f"name='{month_key}' and '{root_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    res = drive_svc.files().list(q=q, fields="files(id)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]

    meta = {
        "name": month_key,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [root_id],
    }
    folder = drive_svc.files().create(body=meta, fields="id").execute()
    folder_id = folder["id"]
    print(f"[SheetsManager] Created folder {month_key} → {folder_id}")
    return folder_id


def _create_sheet_in_folder(gc, drive_svc, display_name: str, folder_id: str) -> str:
    """Create a Google Sheets file directly inside folder_id via Drive API."""
    meta = {
        "name": display_name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id],
    }
    file = drive_svc.files().create(body=meta, fields="id").execute()
    sheet_id = file["id"]
    print(f"[SheetsManager] Created {display_name} → {sheet_id}")
    return sheet_id


def _ensure_month(month_key: str) -> dict:
    """
    Ensure all SHEET_NAMES exist for month_key.
    Creates missing sheets, saves config incrementally. Returns month config dict.
    """
    config = _load_config()
    month_cfg = config.get(month_key, {})

    if all(name in month_cfg for name in SHEET_NAMES):
        return month_cfg

    gc = _get_gc()
    if gc is None:
        raise RuntimeError("[SheetsManager] No Google credentials available")

    drive_svc = _get_drive_service(gc)
    folder_id = _get_or_create_monthly_folder(drive_svc, month_key)

    for name in SHEET_NAMES:
        if name not in month_cfg:
            display = f"RH-{month_key}-{name}"
            sheet_id = _create_sheet_in_folder(gc, drive_svc, display, folder_id)
            month_cfg[name] = sheet_id
            config[month_key] = month_cfg
            _save_config(config)

    print(f"[SheetsManager] ✅ All sheets ready for {month_key}")
    return month_cfg


# ── Public API ────────────────────────────────────────────────────────────────

def get_sheet_id(tab_name: str, month: str = None) -> str:
    """
    Return the Google Sheets ID for tab_name in the given month.
    month defaults to current month (YYYY-MM). Auto-creates sheets if missing.
    """
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    config = _load_config()
    if month in config and tab_name in config[month]:
        return config[month][tab_name]

    month_cfg = _ensure_month(month)
    return month_cfg[tab_name]


def get_worksheet(tab_name: str, month: str = None, gc=None):
    """
    Return the first gspread Worksheet for tab_name in the given month.
    Pass gc to reuse an existing authenticated client. Auto-creates if needed.
    """
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    sheet_id = get_sheet_id(tab_name, month)

    if gc is None:
        gc = _get_gc()
    if gc is None:
        return None

    return gc.open_by_key(sheet_id).sheet1


def load_config() -> dict:
    """Return the full sheets_config.json contents."""
    return _load_config()


def register_sheets(month: str, sheet_ids: dict):
    """
    Manually register pre-created sheet IDs for a month.
    sheet_ids: {tab_name: spreadsheet_id, ...}  — must cover all SHEET_NAMES.

    Example:
        sheets_manager.register_sheets("2026-04", {
            "timeline_live":   "1abc...",
            "daily_snapshots": "1def...",
            ...
        })
    """
    missing = [n for n in SHEET_NAMES if n not in sheet_ids]
    if missing:
        raise ValueError(f"Missing sheet IDs for: {missing}")
    config = _load_config()
    config[month] = {name: sheet_ids[name] for name in SHEET_NAMES}
    _save_config(config)
    print(f"[SheetsManager] ✅ Registered {len(SHEET_NAMES)} sheets for {month}")
    print(f"[SheetsManager] Config written to {CONFIG_PATH}")


def ensure_monthly_setup(month: str = None) -> dict:
    """
    Public entry point: ensure all sheets exist for the given month.
    Defaults to current month. Prints progress and returns the month's config.
    """
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    print(f"[SheetsManager] Bootstrapping sheets for {month}...")
    cfg = _ensure_month(month)
    print(f"[SheetsManager] sheets_config.json written to {CONFIG_PATH}")
    for name, sid in cfg.items():
        print(f"  {name}: {sid}")
    return cfg


def trading_days_after(date_str: str, n: int = 3) -> list:
    """Return the next n trading weekdays after date_str (YYYY-MM-DD)."""
    from datetime import timedelta
    d = datetime.strptime(date_str, "%Y-%m-%d")
    days = []
    while len(days) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days.append(d.strftime("%Y-%m-%d"))
    return days
