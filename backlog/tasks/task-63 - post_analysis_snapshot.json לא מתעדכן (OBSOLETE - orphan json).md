---
id: TASK-63
title: post_analysis_snapshot.json לא מתעדכן (OBSOLETE - orphan json)
status: Done
assignee: []
created_date: '2026-05-31 00:48'
updated_date: '2026-06-27 18:35'
labels:
  - investigation
  - data-quality
  - from-task-62
dependencies: []
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עלה ב-TASK-62 ריצה 1. ה-snapshot המקומי כמעט ריק, מנע שימוש בו לניתוח. P2.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Recon 2026-06-27: premise stale. post_analysis_snapshot.json is an ORPHAN artifact — no .py writes or reads it (grep confirmed). Live snapshots migrated to Sheets (save_snapshot_to_sheets, gsheets_sync.py) + per-day snapshot_today.csv (dashboard.py). The json froze at ScanDate 2026-05-15 / mtime 5-18 because the writer was refactored away, not a save-process bug. The 2-records premise was also wrong: file actually holds 196 rows. Offline source going forward = monthly post_analysis CSVs (same 232 rows as F2) or Sheets. Closing obsolete/wont-fix. Orphan json left in place (delete is a separate explicit decision).
<!-- SECTION:NOTES:END -->
