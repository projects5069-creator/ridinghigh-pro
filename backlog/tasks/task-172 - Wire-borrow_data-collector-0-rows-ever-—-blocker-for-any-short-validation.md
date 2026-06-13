---
id: TASK-172
title: Wire borrow_data collector (0 rows ever — blocker for any short validation)
status: To Do
assignee: []
created_date: '2026-06-13 01:26'
labels:
  - TASK-171
dependencies: []
priority: high
ordinal: 175000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
171-A1 / PT-4. borrow_data sheet has been header-only (0 rows) since creation, both months verified. Without HTB fees the pessimistic expectancy bound understates costs for this micro-cap universe. Dashboard says collector is 'ready, unused' — wire it. Blocker for crossover-short validation (171-B3).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 borrow_data receives rows daily for scanned tickers (IsShortable/IsETB/IsHTB/BorrowFeePct)
- [ ] #2 Coverage report: % of signals with borrow data
<!-- AC:END -->
