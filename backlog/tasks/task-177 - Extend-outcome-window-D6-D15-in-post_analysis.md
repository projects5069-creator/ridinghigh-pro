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
- [ ] #1 post_analysis rows gain D6-D15 OHLC (collector + backfill plan for settled rows)
- [ ] #2 Schema change coordinated with SCHEMA.json contract (TASK-167) and grid-resize lesson (TASK-123)
<!-- AC:END -->
