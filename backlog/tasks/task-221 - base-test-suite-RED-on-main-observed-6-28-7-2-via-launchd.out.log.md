---
id: TASK-221
title: base test suite RED on main (observed 6/28 + 7/2 via launchd.out.log)
status: Done
assignee: []
created_date: '2026-07-02 16:21'
updated_date: '2026-07-02 17:58'
labels:
  - quality
  - tests
dependencies: []
priority: high
ordinal: 227000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
overnight runner aborted 2 nights on base-RED. Independent quality flag: main has failing tests. Needs recon: which tests, since when, is it the 2 pre-existing eod_borrow fails from 217 handoff or new. read-only pytest first.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
base-RED root-cause: stale test test_noargs_default_200_flags_grandfathered — assertion tied to tree content (>=3 files 204-219B), invalidated when dcd218a shortened last grandfathered file (204B->83B). Guard itself correct (6/7 green). Fixed: converted to synthetic tmp_path repo (bf7f7ad), 7/7 green, pushed to origin. NOT a code regression, NOT the eod_borrow fails from 217 handoff (those are green), NOT related to 211/is_day_complete.
<!-- SECTION:NOTES:END -->
