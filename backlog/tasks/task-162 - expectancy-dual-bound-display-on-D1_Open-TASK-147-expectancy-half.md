---
id: TASK-162
title: expectancy dual-bound display on D1_Open (TASK-147 expectancy half)
status: To Do
assignee: []
created_date: '2026-06-12 14:21'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 165000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Split from TASK-147. The WR half shipped via the 142-merged branch (headline WR on D1_Open + WHIPSAW-as-loss pessimistic bound). This is the EXPECTANCY half. calculate_net_pnl already accepts entry_price (plumbing laid in 142-merge, formulas.py). Remaining: build the live expectancy surface on D1_Open basis and demote ScanPrice NetPnL to diagnostic.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Live dashboard expectancy surface with DUAL reporting: optimistic (WHIPSAW excluded) vs pessimistic (WHIPSAW-as-SL), shown for borrow 50/200/500
- [ ] #2 Expectancy basis = D1_Open (consumes calculate_net_pnl entry_price param); NOT ScanPrice
- [ ] #3 New D1_Open NetPnL official columns + backfill of the settled rows
- [ ] #4 Existing ScanPrice NetPnL_* columns relabeled diagnostic (no silent removal)
- [ ] #5 No drift: official WR (D1_Open) and official expectancy (D1_Open) share the same entry basis
<!-- AC:END -->
