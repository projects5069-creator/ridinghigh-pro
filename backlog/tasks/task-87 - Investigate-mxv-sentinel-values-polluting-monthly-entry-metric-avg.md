---
id: TASK-87
title: Investigate mxv sentinel values polluting monthly entry-metric avg
status: To Do
assignee: []
created_date: '2026-05-31 21:45'
labels:
  - bug
  - data-quality
  - critic
dependencies: []
priority: medium
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
build_monthly_detail (TASK-48) avg mxv for May = -1053 (win) / -1107 (loss), but a single sampled trade showed mxv=92.67. Average of -1000+ implies sentinel/garbage values (e.g. -9999 for missing) polluting the mean. mxv was DROPPED from the monthly email Section C until resolved. Find where mxv sentinels come from (review_completed_trades source / postmortems / timeline), decide handling (filter sentinels or fix at source), then re-add mxv to Section C.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sentinel source identified
- [ ] #2 mxv avg sane after filtering
- [ ] #3 mxv re-added to monthly Section C
<!-- AC:END -->
