---
id: TASK-233
title: utils.peru_close_time(date) — unify 4x close_peru duplication (SSoT sec10)
status: To Do
assignee: []
created_date: '2026-07-05 17:17'
labels: []
dependencies: []
ordinal: 239000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
close_peru derived from 16:00 ET in 4 places: is_day_complete, is_market_hours, is_snapshot_time, enrich._min_to_close. Extract single utils helper.
<!-- SECTION:DESCRIPTION:END -->
