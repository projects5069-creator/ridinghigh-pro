---
id: TASK-87
title: Investigate mxv sentinel values polluting monthly entry-metric avg
status: Done
assignee: []
created_date: '2026-05-31 21:45'
updated_date: '2026-06-24 19:23'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-24 (TDD). Root cause: NOT sentinels (0 values == -9999 / == 0.0 in MxV). MxV=((mcap-price*vol)/mcap)*100 is a heavy-tailed signed ratio (median APR/MAY -216/-396 vs mean -1914/-1425, min -21950/-12598); the arithmetic mean is genuine but unrepresentative, and the +92.67 sample is a legitimately-positive row. Fix: build_monthly_detail Section C switched mean->statistics.median for ALL metrics (critic_v1.py:_avgs); mxv re-added to _METRICS+_LABELS; monthly_brief.py wording average->median (label). AC#1 source=heavy-tail (no sentinels). AC#2 median sane (~-200/-400). AC#3 mxv re-added (as median). Section C is descriptive email-only -> zero live ENTER/SKIP/WR/Score impact; render-time, no Sheet write, no historical recompute. TDD test_monthly_section_c_median_v1.py 4/4; suite 535 passed.
<!-- SECTION:NOTES:END -->
