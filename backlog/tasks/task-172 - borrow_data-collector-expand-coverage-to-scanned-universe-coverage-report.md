---
id: TASK-172
title: borrow_data collector — expand coverage to scanned universe + coverage report (collecting verified 6/11)
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
171-A1 / PT-4. **CORRECTION (verified live 2026-06-13):** the collector was WIRED by TASK-139 (commits 2448cf6 + c3cf125, 6/11) and IS collecting — borrow_data 2026-06 has real rows (ADIL 6/11 Shortable/ETB; EDHL 6/12 NOT-shortable), verified live. The EOD 21:00 run writes 1 row/day; the 22:16 run returns 0 (dedup, not failure). II-0.2 "0 rows ever" was stale (backup CSV predated the 6/11 21:00 EOD run). AC#1 is met for `existing_positions` (~1 ticker/day = open positions ∪ today's ENTERs). REMAINING: (a) expand the ticker source from `existing_positions` to the scanned universe so every crossover candidate gets a shortability verdict (EDHL showed non-shortable RH pumps exist); (b) coverage report. NOTE: BorrowFeePct stays NULL — Alpaca exposes shortability flags only, no fee; worst-case borrow COST is already parametric in `calculate_net_pnl` (50/200/500%/yr, TASK-140), so 178/179 fitness is NOT blocked on a fee source. Real per-ticker fee = optional layer-2 (LOW), already noted in PK v3.02.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 borrow_data receives rows daily for existing_positions (verified live 6/11: ADIL/EDHL) — EXPAND ticker source to the full scanned universe so every crossover candidate gets a shortability verdict
- [ ] #2 Coverage report: % of signals / crossover-candidates with borrow data
<!-- AC:END -->
