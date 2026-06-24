---
id: TASK-149
title: 'Classify 19 NO_DATA rows: delisting = lost short wins (survivorship)'
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-24 18:33'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 152000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV phase0/4: audit_flag=NO_DATA appears on 19 post_analysis rows (+2 with REL_VOL_CAPPED suffix). Classify each: delisted = max short win never counted (survivorship bias, but also un-coverable in practice). Ties TASK-132 (SBLX). Evidence: phase0_evidence.md audit_flag table
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-132 folded in 2026-06-21: SBLX 2026-04-28 (delisted, all-NaN since April) is part of this task's delisting/NO_DATA scope. Handle SBLX when 149 is worked.

CLOSED 2026-06-24 — PREMISE DISPROVEN (read-only analysis, docs/research/SURVIVORSHIP_NO_DATA_2026-06-24.md, gitignored). All 21 NO_DATA rows (16 tickers) have valid ScanPrice>0 AND full D1-D5 OHLC -> classify normally (NOT pending), inside the WR denominator; every ticker traded in April (CLEAN rows, rising prices). 0 delistings among the 19. Survivorship correction = 0 from these; system-wide <=1 (SBLX, phase4 'one candidate', separate PENDING row). audit_flag=NO_DATA fired despite valid price+OHLC (validate_stock_data returns NO_DATA only for price None/0, utils.py:729-730) -> separate flag-semantics data-quality question -> carry to TASK-168. No WR band built (N=0 would mislead).
<!-- SECTION:NOTES:END -->
