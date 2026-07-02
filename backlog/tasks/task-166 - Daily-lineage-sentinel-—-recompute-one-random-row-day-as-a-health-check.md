---
id: TASK-166
title: Daily lineage sentinel — recompute one random row/day as a health check
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
updated_date: '2026-07-02 19:22'
labels:
  - vision
dependencies: []
priority: medium
ordinal: 169000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Vision via TASK-156. Daily health check: recompute one random settled post_analysis row end-to-end and flag if stored values drift from a fresh recompute — catches silent pipeline/data corruption.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sentinel picks 1 random settled row/day, recomputes, compares to stored; WARNING on mismatch
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Design locked 2026-07-02: new post-settlement check on existing DataSentinel infra (no new calc logic, §10). Compares 5 metrics (MxV/REL_VOL/RunUp/Gap/ATRX)+Score via formulas.calculate_* on stored raw. Depth: stored-raw formula-layer only, NOT OHLC re-fetch (avoids I/O+429; re-fetch = future scope). Tolerance abs(diff)>0.01 not ==. MUST exclude TypicalPrice (collector:573 intentionally differs from formulas -> naive recompute = built-in FP). WARN-only via _log_sentinel_event->sentinel_events, not BLOCK. Runs from orchestrator_eod, random.choice on settled rows (D1..CLASSIFY_DAYS full). Impl is Sheets-read -> post-market. Stated limit: formula-layer not full end-to-end lineage.
<!-- SECTION:NOTES:END -->
