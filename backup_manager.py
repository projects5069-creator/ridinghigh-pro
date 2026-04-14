#!/usr/bin/env python3
"""
RidingHigh Pro — Daily Backup Manager

Backups are stored as Google Sheets (no service-account quota cost).
Each backup is a spreadsheet named "Backup_post_analysis_YYYY-MM-DD"
inside the "RidingHigh-Backups" Drive folder.

daily_backup()
    1. Load post_analysis from Sheets
    2. Save CSV to backups/post_analysis_YYYY-MM-DD.csv  (local)
    3. Upload to Drive as a Google Sheet  (no quota)
    4. Prune local + Drive files older than KEEP_DAYS
    5. Print summary

restore_from_backup(date_str)
    1. Find the backup spreadsheet in Drive for the given date
    2. Export it as CSV → DataFrame
    3. Write back to Sheets via gsheets_sync
    4. Print row count restored

list_backups()
    Return list of backup names available in Drive.
"""

import os
import sys
import io
from datetime import datetime, timedelta

import pandas as pd
import pytz

sys.path.insert(0, os.path.dirname(__file__))

PERU_TZ     = pytz.timezone("America/Lima")
BACKUP_DIR  = os.path.join(os.path.dirname(__file__), "backups")
FOLDER_NAME = "RidingHigh-Backups"
FILE_PREFIX = "Backup_post_analysis_"
KEEP_DAYS   = 30


# ── Drive helpers ──────────────────────────────────────────────────────────────

def _get_clients():
    """Return (gc, drive_svc) using sheets_manager helpers."""
    import sheets_manager
    gc = sheets_manager._get_gc()
    if gc is None:
        raise RuntimeError("Cannot connect to Google — GOOGLE_CREDENTIALS_JSON missing or invalid")
    drive_svc = sheets_manager._get_drive_service(gc)
    return gc, drive_svc


def _get_or_create_backup_folder(drive_svc) -> str:
    """Return Drive folder ID for RidingHigh-Backups, creating it if needed."""
    import sheets_manager
    root_id = sheets_manager._get_root_folder_id(drive_svc)

    q = (
        f"name='{FOLDER_NAME}' and '{root_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    res   = drive_svc.files().list(q=q, fields="files(id, name)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]

    meta = {
        "name": FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [root_id],
    }
    folder    = drive_svc.files().create(body=meta, fields="id").execute()
    folder_id = folder["id"]
    print(f"[Backup] Created Drive folder '{FOLDER_NAME}' → {folder_id}")
    return folder_id


def _list_backup_files(drive_svc, folder_id: str) -> list:
    """Return [{id, name, createdTime}] for all backup spreadsheets, newest first."""
    q = (
        f"'{folder_id}' in parents "
        f"and mimeType='application/vnd.google-apps.spreadsheet' "
        f"and name contains '{FILE_PREFIX}' "
        f"and trashed=false"
    )
    res = drive_svc.files().list(
        q=q, fields="files(id, name, createdTime)", orderBy="createdTime desc"
    ).execute()
    return res.get("files", [])


def _upload_as_sheet(gc, drive_svc, folder_id: str, sheet_name: str, df: pd.DataFrame) -> str:
    """
    Create an empty Google Sheet (no media upload = no quota cost),
    then write df rows via gspread. Returns the new file ID.
    """
    import gspread

    # 1. Create empty spreadsheet in the backup folder
    meta   = {
        "name":     sheet_name,
        "parents":  [folder_id],
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }
    result  = drive_svc.files().create(body=meta, fields="id").execute()
    file_id = result["id"]

    # 2. Open with gspread and write data
    sh = gc.open_by_key(file_id)
    ws = sh.sheet1
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    ws.clear()
    ws.update("A1", data)
    return file_id


def _export_sheet_as_csv(drive_svc, file_id: str) -> bytes:
    """Download a Google Sheet as CSV bytes."""
    from googleapiclient.http import MediaIoBaseDownload

    buf  = io.BytesIO()
    req  = drive_svc.files().export_media(fileId=file_id, mimeType="text/csv")
    dl   = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


# ── Main functions ─────────────────────────────────────────────────────────────

def daily_backup(date_str: str = None) -> bool:
    """
    Export post_analysis → local CSV + Drive Sheet.
    Returns True on success.
    """
    from gsheets_sync import load_post_analysis_from_sheets

    today      = date_str or datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    sheet_name = f"{FILE_PREFIX}{today}"
    local_path = os.path.join(BACKUP_DIR, f"post_analysis_{today}.csv")

    print(f"[Backup] Starting daily backup for {today}...")

    # ── 1. Load from Sheets ───────────────────────────────────────────────────
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("[Backup] ⚠️ post_analysis is empty — nothing to back up.")
        return False
    print(f"[Backup] Loaded {len(df)} rows from post_analysis")

    # ── 2. Save CSV locally ───────────────────────────────────────────────────
    os.makedirs(BACKUP_DIR, exist_ok=True)
    df.to_csv(local_path, index=False)
    size_kb = os.path.getsize(local_path) / 1024
    print(f"[Backup] Saved local: {local_path} ({size_kb:.1f} KB)")

    # ── 3. Write to Drive as Google Sheet (best-effort — SA quota may be full) ─
    drive_ok = False
    try:
        gc, drive_svc = _get_clients()
        folder_id     = _get_or_create_backup_folder(drive_svc)

        # Remove existing backup for same date (avoid duplicates)
        existing = _list_backup_files(drive_svc, folder_id)
        for f in existing:
            if f["name"] == sheet_name:
                drive_svc.files().delete(fileId=f["id"]).execute()
                print(f"[Backup] Replaced existing: {sheet_name}")

        file_id  = _upload_as_sheet(gc, drive_svc, folder_id, sheet_name, df)
        drive_ok = True
        print(f"[Backup] ✅ Saved to Drive as Sheet → {sheet_name} (id={file_id})")
    except Exception as e:
        if "storageQuotaExceeded" in str(e) or "quota" in str(e).lower():
            print(f"[Backup] ⚠️ Drive quota full — local CSV is your backup.")
            print(f"[Backup]    Free up SA Drive space or use a Shared Drive to re-enable.")
        else:
            print(f"[Backup] ⚠️ Drive upload failed: {e}")
        print(f"[Backup]    Local backup saved at: {local_path}")

    # ── 4. Prune old backups ──────────────────────────────────────────────────
    cutoff = datetime.now(PERU_TZ) - timedelta(days=KEEP_DAYS)

    # Local prune
    local_deleted = 0
    if os.path.isdir(BACKUP_DIR):
        for fname in os.listdir(BACKUP_DIR):
            if not fname.startswith("post_analysis_") or not fname.endswith(".csv"):
                continue
            fpath = os.path.join(BACKUP_DIR, fname)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath), tz=PERU_TZ)
            if mtime < cutoff:
                os.remove(fpath)
                local_deleted += 1

    # Drive prune (only if Drive is accessible)
    drive_deleted = 0
    remaining     = 0
    if drive_ok:
        try:
            for f in _list_backup_files(drive_svc, folder_id):
                created = datetime.fromisoformat(f["createdTime"].replace("Z", "+00:00"))
                if created.astimezone(PERU_TZ) < cutoff:
                    drive_svc.files().delete(fileId=f["id"]).execute()
                    drive_deleted += 1
                    print(f"[Backup] Pruned old: {f['name']}")
            remaining = len(_list_backup_files(drive_svc, folder_id))
        except Exception:
            pass

    # ── 5. Summary ────────────────────────────────────────────────────────────
    local_files = len([f for f in os.listdir(BACKUP_DIR)
                       if f.startswith("post_analysis_") and f.endswith(".csv")])
    drive_info  = f"Drive backups: {remaining}" if drive_ok else "Drive: unavailable (quota)"
    print(
        f"[Backup] Done — {len(df)} rows backed up | "
        f"Local CSVs: {local_files} | {drive_info} | "
        f"Pruned: {local_deleted} local, {drive_deleted} Drive"
    )
    return True


def restore_from_backup(date_str: str) -> bool:
    """
    Restore post_analysis from backup for date_str (YYYY-MM-DD).
    Tries Drive first; falls back to local CSV in backups/.
    Returns True on success.
    """
    from gsheets_sync import save_post_analysis_to_sheets

    sheet_name = f"{FILE_PREFIX}{date_str}"
    local_path = os.path.join(BACKUP_DIR, f"post_analysis_{date_str}.csv")
    print(f"[Restore] Looking for backup: {date_str} ...")

    df = None

    # ── Try Drive first ───────────────────────────────────────────────────────
    try:
        _, drive_svc = _get_clients()
        folder_id    = _get_or_create_backup_folder(drive_svc)
        all_files    = _list_backup_files(drive_svc, folder_id)
        match        = next((f for f in all_files if f["name"] == sheet_name), None)
        if match:
            csv_bytes = _export_sheet_as_csv(drive_svc, match["id"])
            df        = pd.read_csv(io.BytesIO(csv_bytes))
            print(f"[Restore] Found on Drive — {len(df)} rows")
        else:
            available = [f["name"] for f in all_files]
            print(f"[Restore] Not on Drive. Available: {', '.join(available) or 'none'}")
    except Exception as e:
        print(f"[Restore] Drive unavailable: {e}")

    # ── Fallback: local CSV ───────────────────────────────────────────────────
    if df is None:
        if os.path.isfile(local_path):
            df = pd.read_csv(local_path)
            print(f"[Restore] Using local CSV: {local_path} — {len(df)} rows")
        else:
            print(f"[Restore] ❌ No backup found for {date_str} (Drive or local).")
            return False

    # ── Write back to Sheets ──────────────────────────────────────────────────
    try:
        ok = save_post_analysis_to_sheets(df)
        if ok:
            print(f"[Restore] ✅ Restored {len(df)} rows to post_analysis sheet")
        else:
            print("[Restore] ⚠️ save returned False — check gsheets_sync logs")
        return ok
    except Exception as e:
        print(f"[Restore] ❌ Sheet write failed: {e}")
        return False


def list_backups() -> list:
    """Return list of backup names available in Drive, newest first."""
    try:
        _, drive_svc = _get_clients()
        folder_id    = _get_or_create_backup_folder(drive_svc)
        return [f["name"] for f in _list_backup_files(drive_svc, folder_id)]
    except Exception as e:
        print(f"[Backup] ⚠️ list_backups error: {e}")
        return []


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="RidingHigh Backup Manager")
    p.add_argument("--restore", metavar="DATE", help="Restore from backup (YYYY-MM-DD)")
    p.add_argument("--list",    action="store_true", help="List available Drive backups")
    p.add_argument("--date",    metavar="DATE",      help="Run backup for specific date")
    args = p.parse_args()

    if args.list:
        backups = list_backups()
        print(f"Available backups ({len(backups)}):")
        for b in backups:
            print(f"  {b}")
    elif args.restore:
        restore_from_backup(args.restore)
    else:
        daily_backup(args.date)
