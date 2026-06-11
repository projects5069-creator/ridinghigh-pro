#!/usr/bin/env python3
"""Phase 8 — read the PK mirror Sheet's Metadata tab (version check). READ-ONLY."""
import os, sys, time
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

gc = sheets_manager._get_gc()
drive = sheets_manager._get_drive_service_oauth() or sheets_manager._get_drive_service(gc)
res = drive.files().list(q="name contains 'PK' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                         fields="files(id,name,modifiedTime)", pageSize=20).execute()
for f in res.get("files", []):
    print(f"{f['name']} | {f['id']} | modified={f['modifiedTime']}")
files = res.get("files", [])
if files:
    time.sleep(3)
    sh = gc.open_by_key(files[0]["id"])
    try:
        ws = sh.worksheet("Metadata")
        vals = ws.get_all_values()
        for row in vals[:8]:
            print("META:", row)
    except Exception as e:
        print("metadata read failed:", e)
