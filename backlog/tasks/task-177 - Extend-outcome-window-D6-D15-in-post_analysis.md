---
id: TASK-177
title: Extend outcome window D6-D15 in post_analysis
status: Done
assignee: []
created_date: '2026-06-13 01:26'
updated_date: '2026-06-23 00:36'
labels:
  - TASK-171
dependencies: []
priority: high
ordinal: 180000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
171-B1 / PT-3. The real collapse arrives AFTER our 5d window: 66% (123/185) of RH pumps drop into DropsLab within 10 days, then continue -17.75% in the following 5d. Add D6-D15 OHLC tracking to post_analysis so future analyses can see the harvest window. Synergy with TASK-83 (DropsLab d6-d15). Infrastructure for crossover-short.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 post_analysis rows gain D6-D15 OHLC (implemented as scan-anchored D6-D25 superset, Close+Low data-only; forward-only from 2026-06-13)
- [x] #2 Schema change coordinated: grid-resize via gsheets_sync.ensure_grid_width (TASK-123); columns documented in PK §15, SCHEMA.json (TASK-167) to adopt
- [x] #3 LIVE-VERIFY — confirm D6-D25 columns appear on a real post_analysis_collector run (RULE #6; not run today)
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
auto-grow gap: D6-D25 cols absent from live post_analysis header (109 cols, 0 D6+, forward-only from 6/13, not yet settled). Before relying on hold-window data — verify sheets_manager grows columns on unknown keys OR pre-define in create_agent_sheets, else values fall silently. Part of AC#3 live-verify.

2026-06-22 live-verify (post-EOD): D6_Close/D6_Low confirmed in prod 2026-06 post_analysis (active month). D7-D25 = time-dependent forward-only growth (~mid-July), not code-dependent. Forward-collection mechanism proven. AC#3 satisfied.
<!-- SECTION:NOTES:END -->
