---
id: TASK-132
title: >-
  סימון 14 השורות התקועות (SBLX delisted + 13 holiday-slot) כך שייצאו מספירת
  PENDING
status: To Do
assignee: []
created_date: '2026-06-10 02:04'
labels: []
dependencies: []
priority: medium
ordinal: 135000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After TASK-123 backfill, 14 rows remain permanently PENDING: SBLX 2026-04-28 (delisted, no bars) + 13 holiday-slot rows (Apr-3 Good Friday / May-25 Memorial Day diagonals; full list in /tmp verification output + PK v2.94 changelog). Mark them (e.g. audit_flag DELISTED / HOLIDAY_SLOT) so research queries and dashboards stop counting them as live PENDING. The 13 holiday rows may become fillable after TASK-130 realignment — marking should be reversible (flag, not delete). Writes to post_analysis -> ping-pong, off-hours, fill-only-style targeted cell writes.
<!-- SECTION:DESCRIPTION:END -->
