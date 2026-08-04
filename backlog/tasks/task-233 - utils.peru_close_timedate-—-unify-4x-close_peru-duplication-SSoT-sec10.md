---
id: TASK-233
title: utils.peru_close_time(date) — unify 4x close_peru duplication (SSoT sec10)
status: Done
assignee: []
created_date: '2026-07-05 17:17'
updated_date: '2026-08-04 00:32'
labels: []
dependencies: []
ordinal: 239000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
close_peru derived from 16:00 ET in 4 places: is_day_complete, is_market_hours, is_snapshot_time, enrich._min_to_close. Extract single utils helper.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-222, 2026-08-04

Closed as a merge. Same DST and time root as TASK-222 and TASK-232.

The four close_peru derivations this task lists are the same duplication TASK-222 records for _is_day_complete and MARKET_CLOSE_HOUR_PERU. One utils helper closes all of it.
