---
id: TASK-205
title: >-
  extend documentation horizon to 25 days (classify-25 added alongside
  classify-5, not replacing)
status: To Do
assignee: []
created_date: '2026-06-29 04:15'
labels: []
dependencies: []
ordinal: 211000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
MAX_HOLDING_DAYS=5 (classify window) vs COLLECT_DAYS_FORWARD=25 (OHLC). Extend the documentation/classification horizon to 25 days for richer outcome study, WITHOUT changing existing 5-day semantics.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 25-day documentation/classification computed and stored ALONGSIDE the existing 5-day classify (not replacing it)
- [ ] #2 recon classify_trade callers (dashboard/analytics/orchestrator) BEFORE any change — verify none break
- [ ] #3 final WIN/LOSS classification thresholds deferred until data is seen (B1)
- [ ] #4 zero regression to existing classify_trade / 5-day outcome columns
<!-- AC:END -->
