#!/usr/bin/env python3
"""
מכין את תשתית החודש הבא: תיקייה + 7 Sheets + שיתוף עם SA + עדכון config.
רץ גם מקומית (קובץ oauth_token.json) וגם ב-GitHub Actions (env var).
"""
import json
import os
import sys
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import gspread

# הגדרות
ROOT_FOLDER_ID = "1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh"
SHEET_NAMES = [
    "timeline_live",
    "daily_snapshots",
    "daily_summary",
    "post_analysis",
    "portfolio",
    "portfolio_live",
    "score_tracker",  # live_trades יהיה כ-tab נוסף בתוכו
]
CONFIG_PATH = "sheets_config.json"

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]


def load_credentials():
    """טוען OAuth credentials מ-env var (Actions) או מקובץ (מקומי)."""
    token_json = os.environ.get('GOOGLE_OAUTH_TOKEN_JSON')
    if token_json:
        print("🔑 משתמש ב-GOOGLE_OAUTH_TOKEN_JSON מ-env var")
        data = json.loads(token_json)
    elif os.path.exists('oauth_token.json'):
        print("🔑 משתמש ב-oauth_token.json מקומי")
        data = json.load(open('oauth_token.json'))
    else:
        print("❌ לא נמצא OAuth token")
        sys.exit(1)
    
    creds = Credentials(
        token=data['token'],
        refresh_token=data['refresh_token'],
        token_uri=data['token_uri'],
        client_id=data['client_id'],
        client_secret=data['client_secret'],
        scopes=data['scopes'],
    )
    # רענון אוטומטי אם expired
    if not creds.valid:
        creds.refresh(Request())
        print("   🔄 Token רוענן")
    return creds


def get_sa_email():
    """מחזיר את האימייל של ה-Service Account מ-GOOGLE_CREDENTIALS_JSON."""
    sa_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if sa_json:
        return json.loads(sa_json)['client_email']
    elif os.path.exists('google_credentials.json'):
        return json.load(open('google_credentials.json'))['client_email']
    return None


def find_or_create_folder(drive, name, parent_id):
    """מחפש תיקייה בשם name תחת parent_id. אם אין - יוצר."""
    query = (f"name='{name}' and '{parent_id}' in parents "
             f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
    res = drive.files().list(q=query, fields="files(id, name)").execute()
    files = res.get('files', [])
    if files:
        print(f"   📁 תיקייה '{name}' כבר קיימת: {files[0]['id']}")
        return files[0]['id'], False
    
    meta = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id],
    }
    folder = drive.files().create(body=meta, fields='id').execute()
    print(f"   ✅ נוצרה תיקייה '{name}': {folder['id']}")
    return folder['id'], True


def find_or_create_sheet(drive, gc, sa_email, filename, folder_id):
    """מחפש sheet בשם filename בתיקייה. אם אין - יוצר ומשתף עם SA."""
    query = (f"name='{filename}' and '{folder_id}' in parents "
             f"and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false")
    res = drive.files().list(q=query, fields="files(id)").execute()
    files = res.get('files', [])
    if files:
        return files[0]['id'], False
    
    meta = {
        'name': filename,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [folder_id],
    }
    sheet = drive.files().create(body=meta, fields='id').execute()
    sheet_id = sheet['id']
    
    # שתף עם SA
    if sa_email:
        drive.permissions().create(
            fileId=sheet_id,
            body={'type': 'user', 'role': 'writer', 'emailAddress': sa_email},
            sendNotificationEmail=False,
            fields='id',
        ).execute()
    
    return sheet_id, True


def add_live_trades_tab(gc, score_tracker_id):
    """מוסיף tab 'live_trades' ל-score_tracker אם לא קיים."""
    try:
        sh = gc.open_by_key(score_tracker_id)
        try:
            sh.worksheet('live_trades')
            return False  # כבר קיים
        except gspread.WorksheetNotFound:
            sh.add_worksheet('live_trades', rows=1000, cols=30)
            return True
    except Exception as e:
        print(f"   ⚠️  שגיאה ב-live_trades tab: {e}")
        return False


def main():
    # חודש הבא
    now = datetime.now()
    if now.month == 12:
        next_year, next_month = now.year + 1, 1
    else:
        next_year, next_month = now.year, now.month + 1
    month_key = f"{next_year:04d}-{next_month:02d}"
    
    print(f"\n🗓️  מכין חודש: {month_key}")
    print("=" * 60)
    
    creds = load_credentials()
    drive = build('drive', 'v3', credentials=creds)
    gc = gspread.authorize(creds)
    sa_email = get_sa_email()
    
    if sa_email:
        print(f"🤖 SA לשיתוף: {sa_email}")
    else:
        print("⚠️  לא נמצא SA email - לא יתבצע שיתוף אוטומטי!")
    
    # 1. תיקיית החודש
    print(f"\n📁 תיקיית {month_key}")
    month_folder_id, folder_created = find_or_create_folder(drive, month_key, ROOT_FOLDER_ID)
    
    # 2. 7 Sheets
    print(f"\n📄 יצירת 7 Sheets:")
    created_ids = {}
    for logical_name in SHEET_NAMES:
        filename = f"RH-{month_key}-{logical_name}"
        sheet_id, was_created = find_or_create_sheet(
            drive, gc, sa_email, filename, month_folder_id
        )
        created_ids[logical_name] = sheet_id
        symbol = "✅ חדש" if was_created else "🔗 קיים"
        print(f"   {symbol}: {filename} → {sheet_id}")
    
    # 3. live_trades tab בתוך score_tracker
    print(f"\n📋 טיפול ב-live_trades tab:")
    if add_live_trades_tab(gc, created_ids['score_tracker']):
        print(f"   ✅ הוסף tab 'live_trades' ל-score_tracker")
    else:
        print(f"   🔗 tab 'live_trades' כבר קיים")
    created_ids['live_trades'] = created_ids['score_tracker']
    
    # 4. עדכן sheets_config.json
    print(f"\n💾 עדכון {CONFIG_PATH}:")
    if os.path.exists(CONFIG_PATH):
        config = json.load(open(CONFIG_PATH))
    else:
        config = {}
    
    if month_key in config:
        print(f"   🔗 {month_key} כבר ב-config - מעדכן את ה-IDs")
    else:
        print(f"   ✅ מוסיף {month_key} ל-config")
    
    config[month_key] = created_ids
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ הסתיים! חודש {month_key} מוכן.")
    print("=" * 60)
    print("\n📋 IDs:")
    for name, sid in created_ids.items():
        print(f"   {name}: {sid}")


if __name__ == '__main__':
    main()
