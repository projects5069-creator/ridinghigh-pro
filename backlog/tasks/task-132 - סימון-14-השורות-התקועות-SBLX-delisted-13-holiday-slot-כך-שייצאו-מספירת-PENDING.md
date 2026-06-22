---
id: TASK-132
title: >-
  סימון 14 השורות התקועות (SBLX delisted + 13 holiday-slot) כך שייצאו מספירת
  PENDING
status: Done
assignee: []
created_date: '2026-06-10 02:04'
updated_date: '2026-06-22 01:05'
labels: []
dependencies: []
priority: medium
ordinal: 135000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After TASK-123 backfill, 14 rows remain permanently PENDING: SBLX 2026-04-28 (delisted, no bars) + 13 holiday-slot rows (Apr-3 Good Friday / May-25 Memorial Day diagonals; full list in /tmp verification output + PK v2.94 changelog). Mark them (e.g. audit_flag DELISTED / HOLIDAY_SLOT) so research queries and dashboards stop counting them as live PENDING. The 13 holiday rows may become fillable after TASK-130 realignment — marking should be reversible (flag, not delete). Writes to post_analysis -> ping-pong, off-hours, fill-only-style targeted cell writes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RESOLVED 2026-06-21: recount proved 13/14 already freed (TASK-130 + 6/10 backfill). Only SBLX 2026-04-28 (delisted) remained. Folded into TASK-149 (delisting handling) rather than a single-cell live write — SBLX overlaps TASK-149's NO_DATA set. No live write. Closed as subsumed.
<!-- SECTION:NOTES:END -->
