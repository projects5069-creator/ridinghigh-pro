---
id: TASK-166
title: Daily lineage sentinel — recompute one random row/day as a health check
status: Done
assignee: []
created_date: '2026-06-12 22:55'
updated_date: '2026-08-04 00:51'
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

## DONE 2026-08-04

The check exists, runs, and does what the acceptance criterion asks.

health_audit.py line 1339, check_30_lineage_sentinel. Its own docstring names this task. It picks one random settled post_analysis row, recomputes it end to end through the calculate_stats single source of truth, and returns WARNING when any stored field has drifted from the fresh recompute. Load, skip and row prep failures return INFO rather than a false alarm. That is AC#1 in full: one random settled row per day, recomputed, compared to stored, WARNING on mismatch.

Verified live: it ran and returned PASSED in the health_audit run of 2026-08-03.

The one difference from the design note of 2026-07-02, recorded so nobody reopens this on it later: that note placed the check in orchestrator_eod, and it lives in health_audit instead. health_audit runs three times a day and orchestrator_eod runs once in the evening, so the check fires more often than designed, not less. The purpose was a daily recompute as a health check, and the location was never the purpose.

The stated limit from the design note still stands and is not a defect: this is a formula layer comparison on stored raw values, not an OHLC re-fetch, which is what keeps it free of extra IO and 429 pressure. A full end to end lineage check would be a different and much more expensive piece of work, and it is not what this task asked for.
