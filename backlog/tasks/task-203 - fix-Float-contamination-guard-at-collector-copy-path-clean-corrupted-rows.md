---
id: TASK-203
title: 'fix Float% contamination: guard at collector copy-path + clean corrupted rows'
status: Done
assignee: []
created_date: '2026-06-29 04:14'
updated_date: '2026-06-29 04:38'
labels: []
dependencies: []
ordinal: 209000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post_analysis_collector copies Float% as-is from daily_snapshots (metric_fields). TASK-201 guard is forward-only in auto_scanner; pre-fix scanned rows stay corrupted and the collector propagates them (8 June rows >100, max 93448). Establishes the guard pattern reused by TASK-206 (yfinance .info fields are all unreliable for nano-caps).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 guard at the collector copy-path: a Float% outside 0<x<=100 (or where float>shares) is written NULL/blank, not the raw value
- [ ] #2 clean/flag the corrupted June rows (>100)
- [ ] #3 TDD RED documents the bug (corrupted row -> guarded), GREEN passes
- [ ] #4 zero regression: valid Float% rows unchanged; collector suite + formulas green
- [ ] #5 establishes the reusable guard+NaN pattern for TASK-206 fundamental fields
<!-- AC:END -->
