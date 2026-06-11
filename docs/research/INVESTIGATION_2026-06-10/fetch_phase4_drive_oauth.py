#!/usr/bin/env python3
"""Phase 4(e) — OAuth-side Drive listing for RH-2026-07-post_analysis duplicates. READ-ONLY."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

drive = sheets_manager._get_drive_service_oauth()
if drive is None:
    print("NO OAUTH DRIVE")
    sys.exit(0)
q = "name = 'RH-2026-07-post_analysis' and trashed = false"
res = drive.files().list(q=q, fields="files(id,name,createdTime,modifiedTime,owners(emailAddress),parents)", pageSize=50).execute()
files = res.get("files", [])
print(f"exact-name matches: {len(files)}")
for f in files:
    print(f"{f['name']} | {f['id']} | created={f.get('createdTime')} | owner={[o.get('emailAddress') for o in f.get('owners',[])]} | parents={f.get('parents')}")
