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

import pytz

PERU_TZ = pytz.timezone("America/Lima")

ROOT_FOLDER_ID = "1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh"
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
    "live_trades",
    "ticker_follow_up",
]

# timeline_live columns — expanded for research mode (Issue #38a)
TIMELINE_LIVE_COLS = [
    # Meta
    "Date", "ScanTime", "Ticker",
    # Core price/volume
    "Price", "Volume", "MarketCap",
    # Derived score
    "Score",
    # Computed metrics (11)
    "MxV", "RunUp", "REL_VOL", "Change", "RSI", "ATRX", "Gap",
    "TypicalPriceDist", "PriceToHigh", "PriceTo52WHigh", "Float%",
    # Raw inputs (10)
    "Open_price", "PrevClose", "High_today", "Low_today",
    "TypicalPrice", "ATR14_raw", "Week52High",
    "SharesOutstanding", "AvgVolume", "FloatShares",
]

# ticker_follow_up — 3-day post-pump tracking (Issue #38b)
# Same 28 fields as timeline_live + 2 tracking columns (FollowDay, ScanDate)
TICKER_FOLLOW_UP_COLS = [
    # Meta + tracking
    "Date", "ScanTime", "Ticker",
    "FollowDay", "ScanDate",
    # Core price/volume
    "Price", "Volume", "MarketCap",
    # Derived score
    "Score",
    # Computed metrics (11)
    "MxV", "RunUp", "REL_VOL", "Change", "RSI", "ATRX", "Gap",
    "TypicalPriceDist", "PriceToHigh", "PriceTo52WHigh", "Float%",
    # Raw inputs (10)
    "Open_price", "PrevClose", "High_today", "Low_today",
    "TypicalPrice", "ATR14_raw", "Week52High",
    "SharesOutstanding", "AvgVolume", "FloatShares",
]

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

    # TASK-215: dedicated auto_scan SA to end 429 contention on the shared SA.
    # ⚠️ BLAST-RADIUS: _get_gc is shared by ~20 modules. This branch must stay
    # no-op for everyone EXCEPT auto_scan. SAFETY = GOOGLE_CREDENTIALS_JSON_AS is
    # injected ONLY in auto_scan.yml — NEVER in any other workflow. Empty/absent
    # falls through to the shared SA (truthy-guard, same pattern as TASK-58 _HA).
    creds_json_as = os.environ.get("GOOGLE_CREDENTIALS_JSON_AS")
    if creds_json_as:
        import json as _json
        creds = Credentials.from_service_account_info(
            _json.loads(creds_json_as), scopes=SCOPES)
        return gspread.authorize(creds)

    # agent_minute dedicated SA to end 429 contention on the shared SA (live A/B
    # 2026-07-01: agent_minute 37-61x/run "429 Read requests per minute per user"
    # on the shared SA while auto_scan on _AS stayed clean the same minutes).
    # Mirror of TASK-215 (_AS) / TASK-58 (_HA).
    # ⚠️ BLAST-RADIUS: _get_gc is shared by ~20 modules. This branch must stay
    # no-op for everyone EXCEPT agent_minute. SAFETY = GOOGLE_CREDENTIALS_JSON_AM
    # is injected ONLY in agent_minute.yml — NEVER in any other workflow.
    # Empty/absent falls through to the shared SA (truthy-guard, same as _AS/_HA).
    creds_json_am = os.environ.get("GOOGLE_CREDENTIALS_JSON_AM")
    if creds_json_am:
        import json as _json
        _info_am = _json.loads(creds_json_am)
        # DIAGNOSTIC (2026-07-01): expose which SA agent_minute actually uses.
        # client_email is an identifier, NOT a secret (private_key is never printed).
        print(f"[_get_gc] selected _AM SA: client_email={_info_am.get('client_email')}", flush=True)
        creds = Credentials.from_service_account_info(_info_am, scopes=SCOPES)
        return gspread.authorize(creds)

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        import json as _json
        _info_shared = _json.loads(creds_json)
        # DIAGNOSTIC (2026-07-01): expose the shared SA on fallthrough (client_email
        # only — never the private_key).
        print(f"[_get_gc] selected shared SA: client_email={_info_shared.get('client_email')}", flush=True)
        creds = Credentials.from_service_account_info(_info_shared, scopes=SCOPES)
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


SERVICE_ACCOUNT_EMAIL = "ridinghigh-sheets-v2@ridinghigh-pro-v2.iam.gserviceaccount.com"


def _get_oauth_creds():
    """Load user OAuth credentials. Used ONLY for creating new sheets/folders.
    Service account has 0 GB quota, so creation must use user's OAuth.
    """
    import json as _json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_json = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if token_json:
        token_data = _json.loads(token_json)
    else:
        token_path = os.path.join(os.path.dirname(__file__), "oauth_token.json")
        if not os.path.exists(token_path):
            return None
        with open(token_path) as f:
            token_data = _json.load(f)

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


def _get_drive_service_oauth():
    """Drive API client using user OAuth (for file/folder creation)."""
    from googleapiclient.discovery import build
    creds = _get_oauth_creds()
    if not creds:
        return None
    return build("drive", "v3", credentials=creds)


def _share_with_service_account(drive_oauth, file_id):
    """Grant the service account Editor access to a file/folder."""
    drive_oauth.permissions().create(
        fileId=file_id,
        body={
            "type": "user",
            "role": "writer",
            "emailAddress": SERVICE_ACCOUNT_EMAIL,
        },
        sendNotificationEmail=False,
    ).execute()


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

    # Find or create top-level RidingHigh-Data folder via OAuth
    drive_oauth = _get_drive_service_oauth()
    if drive_oauth:
        q = "name='RidingHigh-Data' and 'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        res = drive_oauth.files().list(q=q, fields="files(id)").execute()
        files = res.get("files", [])
        if files:
            return files[0]["id"]

        meta = {"name": "RidingHigh-Data", "mimeType": "application/vnd.google-apps.folder"}
        folder = drive_oauth.files().create(body=meta, fields="id").execute()
        folder_id = folder["id"]
        _share_with_service_account(drive_oauth, folder_id)
        print(f"[SheetsManager] Created RidingHigh-Data folder → {folder_id} (via OAuth)")
        return folder_id

    raise RuntimeError("[SheetsManager] ROOT_FOLDER_ID not accessible and no OAuth credentials. "
                      "Run OAuth setup first.")


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

    # Create via OAuth (user-owned) to bypass SA 0 GB quota
    drive_oauth = _get_drive_service_oauth()
    if not drive_oauth:
        raise RuntimeError("[SheetsManager] OAuth credentials required to create folders. "
                          "Run OAuth setup first.")

    meta = {
        "name": month_key,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [root_id],
    }
    folder = drive_oauth.files().create(body=meta, fields="id").execute()
    folder_id = folder["id"]
    _share_with_service_account(drive_oauth, folder_id)
    print(f"[SheetsManager] Created folder {month_key} → {folder_id} (via OAuth)")
    return folder_id


def _create_sheet_in_folder(gc, drive_svc, display_name: str, folder_id: str) -> str:
    """Create a Google Sheets file inside folder_id via user OAuth."""
    drive_oauth = _get_drive_service_oauth()
    if not drive_oauth:
        raise RuntimeError("[SheetsManager] OAuth credentials required to create sheets. "
                          "Run OAuth setup first.")

    meta = {
        "name": display_name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id],
    }
    file = drive_oauth.files().create(body=meta, fields="id").execute()
    sheet_id = file["id"]
    _share_with_service_account(drive_oauth, sheet_id)
    print(f"[SheetsManager] Created {display_name} → {sheet_id} (via OAuth)")
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
        month = datetime.now(PERU_TZ).strftime("%Y-%m")

    config = _load_config()
    if month in config and tab_name in config[month]:
        return config[month][tab_name]

    month_cfg = _ensure_month(month)
    return month_cfg[tab_name]


# ════════════════════════════════════════════════════════════════════
# Quota resilience: retry helper + short-lived read cache (#N18 / 1א)
# ════════════════════════════════════════════════════════════════════

import time as _time

_RETRY_MAX = 3
_RETRY_BACKOFF_BASE = 2          # seconds: 2, 4, 8
# TASK-105 (light Option 1): the paper_portfolio entry-write gets one extra
# retry vs reads. safe_append_row dedups by PositionID before each retry, so
# the extra attempt cannot double-write. Isolated to appends to bound blast
# radius — reads keep _RETRY_MAX.
_APPEND_RETRY_MAX = 4
_SHEET_CACHE_TTL = 60            # seconds — short, for batch reads (weekly_summary)
_sheet_values_cache = {}         # {(tab_name, month): (timestamp, rows)}


def _is_quota_error(exc) -> bool:
    """True if an exception looks like a Google Sheets 429 / quota error."""
    msg = str(exc).lower()
    return ("429" in msg or "quota" in msg
            or "resource_exhausted" in msg or "rate limit" in msg)


def _with_retry(fn, *args, **kwargs):
    """Run fn(*args, **kwargs) with exponential backoff on quota (429) errors.

    Matches the retry pattern in agent/execution/order_manager.py.
    Non-quota errors are raised immediately (no point retrying those).
    """
    last_error = None
    for attempt in range(_RETRY_MAX):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = e
            if not _is_quota_error(e):
                raise  # not a quota error — fail fast
            if attempt < _RETRY_MAX - 1:
                wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                print(f"[sheets_manager] quota 429 — retry {attempt+1}/{_RETRY_MAX} "
                      f"after {wait}s: {e}")
                _time.sleep(wait)
    print(f"[sheets_manager] all {_RETRY_MAX} retries exhausted: {last_error}")
    raise last_error


# ── Per-tab read counter (TASK-58): mirror of the write counter, for
#    measuring reads/run before vs after read-reduction. In-process (resets
#    each orchestrator run via reset_read_counts()). Counts only actual API
#    fetches (cache hits are free and not counted).
_read_counts = {}


def record_read(tab_name):
    """Record one actual API read for a tab (cache miss). Best-effort."""
    _read_counts[tab_name] = _read_counts.get(tab_name, 0) + 1


def get_read_counts() -> dict:
    """Return a copy of the per-tab API-read counts for this process."""
    return dict(_read_counts)


def reset_read_counts():
    """Reset the per-tab read counter (call at the start of a run)."""
    _read_counts.clear()


def get_sheet_values(tab_name: str, month: str = None):
    """Return all rows of a worksheet, with 60s cache + 429 retry.

    Use this instead of get_worksheet(x).get_all_values() anywhere the
    same sheet may be read repeatedly in a short window (e.g. the Critic's
    weekly_summary, which reads 7 sheets x 5 days). The cache collapses
    those repeats into one API call per sheet per 60s window.
    """
    key = (tab_name, month)
    now = _time.time()
    cached = _sheet_values_cache.get(key)
    if cached is not None and (now - cached[0]) < _SHEET_CACHE_TTL:
        return cached[1]
    record_read(tab_name)  # TASK-58: count actual API fetch (cache miss)
    ws = _with_retry(get_worksheet, tab_name, month)
    if ws is None:
        return []
    rows = _with_retry(ws.get_all_values)
    _sheet_values_cache[key] = (now, rows)
    return rows


def get_sheet_records(tab_name, month=None):
    """Records version of get_sheet_values — cached + retry."""
    rows = get_sheet_values(tab_name, month)
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]


def invalidate_cache(tab_name, month=None):
    """Drop cached values for a tab. Call after writes."""
    key = (tab_name, month)
    _sheet_values_cache.pop(key, None)


def _track_write_quota():
    """Record a successful Sheets write for quota_health monitoring.

    AUDIT.2 fix (2026-05-24): This helper was missing — quota_health.record_write()
    existed but no one called it, so the counter stayed at 0 and check_quota_health
    always reported ALLOW. This restores the connection.

    Graceful — never raises. If quota_health unavailable, write succeeds anyway.
    Counter is in-process (resets each orchestrator run), giving partial
    observability of burst-writes within a single run. Cross-run quota tracking
    would require persistent state (deferred).
    """
    try:
        from agent.sentinel.checks.quota_health import record_write
        record_write()
    except Exception:
        pass  # observability is best-effort — never block a successful write


def safe_update(ws, *args, **kwargs):
    """Range-based write with 429 retry. Idempotent — same cells each attempt."""
    result = _with_retry(ws.update, *args, **kwargs)
    _track_write_quota()
    return result


def safe_batch_update(ws, *args, **kwargs):
    """batch_update with 429 retry. Idempotent — explicit ranges."""
    result = _with_retry(ws.batch_update, *args, **kwargs)
    _track_write_quota()
    return result


def safe_append_row(ws, row, dedup_col=None, dedup_val=None, **kwargs):
    """append_row with 429 retry + optional idempotency.

    append_row is NOT idempotent: a 429 that arrives after Google added
    the row but before the response would cause a duplicate on retry.

    If dedup_col (0-based index) and dedup_val are given, then before each
    retry we read that column and skip the write if dedup_val already
    appears — making the retry safe. Without dedup args, retry is blind
    (acceptable only for low-risk, rare writes).
    """
    kwargs.setdefault("value_input_option", "USER_ENTERED")
    last_error = None
    for attempt in range(_APPEND_RETRY_MAX):
        try:
            result = ws.append_row(row, **kwargs)
            _track_write_quota()
            return result
        except Exception as e:
            last_error = e
            if not _is_quota_error(e):
                raise
            if attempt < _APPEND_RETRY_MAX - 1:
                wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                print(f"[sheets_manager] append 429 — retry {attempt+1}/{_APPEND_RETRY_MAX} "
                      f"after {wait}s: {e}")
                _time.sleep(wait)
                if dedup_col is not None and dedup_val is not None:
                    try:
                        col = ws.col_values(dedup_col + 1)
                        if str(dedup_val) in [str(v) for v in col]:
                            print(f"[sheets_manager] dedup hit — row already written "
                                  f"({dedup_val}); skipping retry")
                            return None
                    except Exception as de:
                        print(f"[sheets_manager] dedup check failed (will retry blind): {de}")
    print(f"[sheets_manager] append: all {_APPEND_RETRY_MAX} retries exhausted: {last_error}")
    raise last_error


def safe_append_rows(ws, rows, dedup_col=None, dedup_vals=None, **kwargs):
    """append_rows with 429 retry + optional idempotency.

    Like safe_append_row but for multiple rows in one API call. Used for
    bulk writes (e.g. auto_scanner writes ~20-30 rows to timeline_live
    every minute).

    append_rows is NOT idempotent: a 429 after Google added the rows but
    before responding would cause duplicates on retry.

    If dedup_col (0-based) and dedup_vals (set of values that uniquely
    identify these rows) are given, before each retry we read that column
    and skip the write if ALL dedup_vals are already present — making the
    retry safe.

    Without dedup args, retry is blind: acceptable for low-rate writes
    but risky for high-rate ones (use dedup_vals for HOT paths).
    """
    kwargs.setdefault("value_input_option", "USER_ENTERED")
    last_error = None
    for attempt in range(_RETRY_MAX):
        try:
            result = ws.append_rows(rows, **kwargs)
            _track_write_quota()
            return result
        except Exception as e:
            last_error = e
            if not _is_quota_error(e):
                raise
            if attempt < _RETRY_MAX - 1:
                wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                print(f"[sheets_manager] append_rows 429 — retry {attempt+1}/{_RETRY_MAX} "
                      f"after {wait}s: {e}")
                _time.sleep(wait)
                if dedup_col is not None and dedup_vals:
                    try:
                        col = ws.col_values(dedup_col + 1)
                        col_set = {str(v) for v in col}
                        dedup_set = {str(v) for v in dedup_vals}
                        if dedup_set.issubset(col_set):
                            print(f"[sheets_manager] dedup hit — all {len(dedup_set)} rows "
                                  f"already written; skipping retry")
                            return None
                    except Exception as dedup_err:
                        print(f"[sheets_manager] dedup check failed: {dedup_err} — "
                              f"proceeding with blind retry")
    raise last_error


def get_worksheet(tab_name: str, month: str = None, gc=None):
    """
    Return the gspread Worksheet for tab_name in the given month.
    If the spreadsheet contains a tab whose title matches tab_name, that tab is
    returned (allows multiple logical sheets to share one Spreadsheet file,
    avoiding Drive quota exhaustion). Otherwise falls back to sheet1.
    Pass gc to reuse an existing authenticated client. Auto-creates if needed.
    """
    if month is None:
        month = datetime.now(PERU_TZ).strftime("%Y-%m")

    sheet_id = get_sheet_id(tab_name, month)

    if gc is None:
        gc = _get_gc()
    if gc is None:
        return None

    import gspread
    spreadsheet = gc.open_by_key(sheet_id)
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.sheet1


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
        month = datetime.now(PERU_TZ).strftime("%Y-%m")
    print(f"[SheetsManager] Bootstrapping sheets for {month}...")
    cfg = _ensure_month(month)
    print(f"[SheetsManager] sheets_config.json written to {CONFIG_PATH}")
    for name, sid in cfg.items():
        print(f"  {name}: {sid}")
    return cfg


def trading_days_after(date_str: str, n: int = 3) -> list:
    """Return the next n NASDAQ trading days after date_str (YYYY-MM-DD).

    TASK-130: holiday-aware via utils.is_trading_day (single holiday source,
    §10). Degrades to weekday-only when mcal is unavailable (utils fallback).
    """
    from datetime import timedelta
    from utils import is_trading_day  # local import — mirrors utils→sheets_manager pattern, no module-level cycle
    d = datetime.strptime(date_str, "%Y-%m-%d")
    days = []
    while len(days) < n:
        d += timedelta(days=1)
        if is_trading_day(d.date()):
            days.append(d.strftime("%Y-%m-%d"))
    return days


def archive_live_trades(gc, closed_df) -> int:
    """
    Archive closed live_trades rows (Status TP10/SL) into the 'live_trades_archive'
    tab within the same spreadsheet as live_trades. Creates the tab if needed.

    Safety contract: RAISES on any failure — caller must NOT delete from live_trades
    unless this returns successfully.  Never silently drops data.

    Returns: number of rows archived.
    """
    import pandas as pd
    import pytz

    peru = pytz.timezone("America/Lima")
    archived_at = datetime.now(peru).strftime("%Y-%m-%d %H:%M")

    # Resolve the live_trades spreadsheet
    sheet_id   = get_sheet_id("live_trades")
    spreadsheet = gc.open_by_key(sheet_id)

    # Get or create the archive tab (adding a tab costs no Drive storage quota)
    try:
        ws_arch = spreadsheet.worksheet("live_trades_archive")
    except Exception:
        ws_arch = spreadsheet.add_worksheet(
            title="live_trades_archive", rows=5000, cols=20
        )
        print("[SheetsManager] Created tab 'live_trades_archive'")

    # Stamp each row with archive timestamp
    df = closed_df.copy()
    df["ArchivedAt"] = archived_at

    existing = ws_arch.get_all_values()
    if len(existing) <= 1:
        # Empty or header-only — write header + data
        ws_arch.update("A1", [df.columns.tolist()] + df.astype(str).values.tolist())
    else:
        # Header already present — append data rows only
        ws_arch.append_rows(df.astype(str).values.tolist())

    print(f"[SheetsManager] Archived {len(df)} rows to live_trades_archive (ArchivedAt={archived_at})")
    return len(df)
