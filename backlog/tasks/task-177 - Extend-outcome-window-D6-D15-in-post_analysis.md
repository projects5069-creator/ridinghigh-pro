---
id: TASK-177
title: Extend outcome window D6-D15 in post_analysis
status: To Do
assignee: []
created_date: '2026-06-13 01:26'
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
- [ ] #3 LIVE-VERIFY — confirm D6-D25 columns appear on a real post_analysis_collector run (RULE #6; not run today)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Code + TDD complete (commits 5a252a9 config+collector+frozen-guard · 03d4cb9 grid-resize · a7bbbee §15/§D anti-drift). 9 TDD tests green incl. a regression-guard proving D6-D25 @ -90% does NOT move the frozen D1-D5 classification; suite 347 / formulas 107 / utils 38. **status stays To Do — LIVE-VERIFY (AC#3) pending: the new columns appear only after a real collector run (RULE #6).** Implemented as D6-D25 (the superset containing the D6-D15 hold window); the window definition/anchor is TASK-178, not 177.
<!-- SECTION:NOTES:END -->
