---
id: TASK-204
title: add night_return + MxV_at_entry columns to post_analysis
status: To Do
assignee: []
created_date: '2026-06-29 04:15'
labels: []
dependencies: []
ordinal: 210000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The overnight edge (ScanPrice->D1_Open) is the core of the proven MxV method but is NOT recorded in any table; classify_trade measures only 10pct TP/SL touch over 5 days. Add explicit columns so the edge itself is tracked. MxV_at_entry pins the scan-time MxV as the entry anchor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 night_return = (ScanPrice - D1_Open)/ScanPrice*100 written per row
- [ ] #2 MxV_at_entry explicit column (scan-time MxV as entry anchor)
- [ ] #3 schema-union write (collector already unions cols + ensure_grid_width) — zero reader breakage
- [ ] #4 TDD RED->GREEN; name-based readers unaffected
<!-- AC:END -->
