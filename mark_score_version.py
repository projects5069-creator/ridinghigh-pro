"""
mark_score_version.py — Mark Score v1 vs v2 in post_analysis and daily_snapshots.

Issue #N10: 104 of 156 records (April) were computed with Score v1 (before commit f3d96ca).
Decision: Tag instead of recompute (Option C).

Cutoff: ScanDate < '2026-04-11' → 'v1', else → 'v2'

Safe properties:
- BACKUP every sheet before write (CSV with timestamp)
- IDEMPOTENT: re-running won't change correct values
- AUDIT log per sheet
- Read-once, write-once (no concurrent edits)
- Fails loud on missing columns
"""
import json
import os
import sys
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

CUTOFF_DATE = '2026-04-11'
TARGET_MONTH = '2026-04'
TARGET_SHEETS = {
    'post_analysis': 'ScanDate',
    'daily_snapshots': 'Date',
}
COLUMN_NAME = 'score_version'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
BACKUP_DIR = os.path.expanduser('~/RidingHighPro/backups')
SCRIPT_DIR = os.path.expanduser('~/RidingHighPro')

os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

print(f"╔════════════════════════════════════════════════════════════╗")
print(f"║  Score Version Marker — {timestamp}            ║")
print(f"║  Cutoff: ScanDate < {CUTOFF_DATE} → 'v1', else → 'v2'    ║")
print(f"╚════════════════════════════════════════════════════════════╝\n")

creds_path = os.path.join(SCRIPT_DIR, 'google_credentials.json')
if not os.path.exists(creds_path):
    print(f"❌ Credentials not found: {creds_path}")
    sys.exit(1)

creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
gc = gspread.authorize(creds)

config_path = os.path.join(SCRIPT_DIR, 'sheets_config.json')
with open(config_path) as f:
    config = json.load(f)

if TARGET_MONTH not in config:
    print(f"❌ Month {TARGET_MONTH} not in sheets_config.json")
    sys.exit(1)

summary = []

for sheet_name, date_column in TARGET_SHEETS.items():
    print(f"\n┌─ Processing: {sheet_name} ─────────────────────────────")

    if sheet_name not in config[TARGET_MONTH]:
        print(f"│ ⚠️  Sheet '{sheet_name}' not in config for {TARGET_MONTH} — skipping")
        continue

    sheet_id = config[TARGET_MONTH][sheet_name]
    ws = gc.open_by_key(sheet_id).sheet1

    rows = ws.get_all_values()
    if len(rows) < 2:
        print(f"│ ⚠️  Sheet is empty — skipping")
        continue

    headers = rows[0]
    df = pd.DataFrame(rows[1:], columns=headers)
    print(f"│ 📥 Loaded: {len(df)} rows, {len(headers)} columns")

    if date_column not in df.columns:
        print(f"│ ❌ FATAL: '{date_column}' column missing in {sheet_name}")
        print(f"│    Available columns: {list(df.columns)[:10]}...")
        sys.exit(1)

    backup_path = os.path.join(
        BACKUP_DIR, f'{sheet_name}_{TARGET_MONTH}_pre_mark_{timestamp}.csv'
    )
    df.to_csv(backup_path, index=False)
    print(f"│ 💾 Backup: {backup_path}")

    scan_dates = df[date_column].astype(str).str[:10]
    v1_mask = scan_dates < CUTOFF_DATE
    v2_mask = scan_dates >= CUTOFF_DATE

    v1_count = int(v1_mask.sum())
    v2_count = int(v2_mask.sum())
    other = len(df) - v1_count - v2_count

    print(f"│ 🔍 Classification:")
    print(f"│    v1 (< {CUTOFF_DATE}): {v1_count}")
    print(f"│    v2 (>= {CUTOFF_DATE}): {v2_count}")
    if other > 0:
        print(f"│    ⚠️  Other (empty/malformed): {other}")

    column_exists = COLUMN_NAME in df.columns
    if column_exists:
        existing_v1 = int((df[COLUMN_NAME] == 'v1').sum())
        existing_v2 = int((df[COLUMN_NAME] == 'v2').sum())
        existing_empty = int(df[COLUMN_NAME].isin(['', 'nan', 'None']).sum())
        print(f"│ 🔁 Column '{COLUMN_NAME}' already exists:")
        print(f"│    Existing v1={existing_v1}, v2={existing_v2}, empty={existing_empty}")

        if existing_v1 == v1_count and existing_v2 == v2_count and existing_empty == 0:
            print(f"│ ✅ Already correctly marked — skipping write (idempotent)")
            summary.append({
                'sheet': sheet_name, 'status': 'skipped_idempotent',
                'v1': v1_count, 'v2': v2_count, 'backup': backup_path
            })
            continue

    df[COLUMN_NAME] = ''
    df.loc[v1_mask, COLUMN_NAME] = 'v1'
    df.loc[v2_mask, COLUMN_NAME] = 'v2'

    new_data = [df.columns.tolist()] + df.fillna('').astype(str).values.tolist()

    print(f"│ ⏳ Writing {len(new_data)} rows × {len(df.columns)} cols...")
    ws.clear()
    ws.update(values=new_data, range_name='A1')

    print(f"│ ✅ Saved to Sheets")

    summary.append({
        'sheet': sheet_name, 'status': 'updated',
        'v1': v1_count, 'v2': v2_count, 'backup': backup_path
    })

print(f"\n╔════════════════════════════════════════════════════════════╗")
print(f"║  SUMMARY                                                   ║")
print(f"╚════════════════════════════════════════════════════════════╝")

audit_path = os.path.join(BACKUP_DIR, f'mark_score_version_audit_{timestamp}.csv')
pd.DataFrame(summary).to_csv(audit_path, index=False)

for s in summary:
    icon = '✅' if s['status'] == 'updated' else '⏭️ '
    print(f"{icon} {s['sheet']:<20} v1={s['v1']:>3}  v2={s['v2']:>3}  [{s['status']}]")

print(f"\n📝 Audit log: {audit_path}")
print(f"💾 Backups in: {BACKUP_DIR}/")
print(f"\n✅ Done.\n")
