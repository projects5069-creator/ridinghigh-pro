---
id: TASK-124
title: >-
  Collector cross-month leak — fix permanent: rows scanned at month-end never
  get D4/D5 after rotation
status: Done
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-11 00:14'
labels: []
dependencies: []
priority: high
ordinal: 127000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post_analysis_collector candidates come from active-month daily_snapshots/timeline_live only, so prior-month incomplete rows are never re-processed. Recurs every month-end. Options: collector also loads prior-month post_analysis incompletes, or monthly scheduled backfill step in post_analysis.yml. Depends on backfill_v2 learnings.
<!-- SECTION:DESCRIPTION:END -->
