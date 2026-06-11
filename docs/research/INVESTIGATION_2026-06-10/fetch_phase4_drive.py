#!/usr/bin/env python3
"""INVESTIGATION — Phase 4(e): list Drive files named like RH-2026-07-post_analysis.
READ-ONLY Drive query via service account. Throttled."""
import os, sys, time
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

gc = sheets_manager._get_gc()
drive = sheets_manager._get_drive_service(gc)
q = "name contains 'RH-2026-07' and trashed = false"
res = drive.files().list(q=q, fields="files(id,name,createdTime,modifiedTime,owners(emailAddress))", pageSize=100).execute()
for f in res.get("files", []):
    print(f"{f['name']} | {f['id']} | created={f.get('createdTime')} | modified={f.get('modifiedTime')}")
time.sleep(3)
q2 = "name contains 'post_analysis' and name contains '2026-07' and trashed = false"
res2 = drive.files().list(q=q2, fields="files(id,name,createdTime)", pageSize=100).execute()
print("--- query2:")
for f in res2.get("files", []):
    print(f"{f['name']} | {f['id']} | created={f.get('createdTime')}")
