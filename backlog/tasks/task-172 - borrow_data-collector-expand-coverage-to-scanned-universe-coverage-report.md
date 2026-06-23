---
id: TASK-172
title: >-
  borrow_data collector — expand coverage to scanned universe + coverage report
  (collecting verified 6/11)
status: Done
assignee: []
created_date: '2026-06-13 01:26'
updated_date: '2026-06-23 01:14'
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
- [x] #1 borrow_data receives rows daily for existing_positions (verified live 6/11: ADIL/EDHL) — EXPAND ticker source to the full scanned universe so every crossover candidate gets a shortability verdict
- [x] #2 Coverage report: % of signals / crossover-candidates with borrow data
- [x] #3 #3 LIVE-VERIFY (RULE #6, deferred — needs real collector run + OAuth tab creation): create borrow_coverage tab via create_agent_sheets and confirm one real coverage row writes with both pcts. Blocked on market-day EOD run (like TASK-177 AC#3).
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-06-14: code+TDD complete (6 commits 76d39b2..137f658). AC#1+#2 satisfied in code: get_scanned_universe + union wiring (scanned Score>=60 union existing_positions) + borrow_coverage tab schema + collect_borrow_coverage writer (two separate pcts over universe denom). 12 new tests, suite 361 passed. AC#3 live-verify pending (deferred RULE #6). Status stays To Do until live row confirmed — mirrors TASK-177.

2026-06-22 AC#3 live-verified (post-EOD): ROOT FIX — borrow_coverage was in AGENT_SHEET_HEADERS but missing from AGENT_SHEET_NAMES → create_agent_sheets never created/registered it → collect_borrow_coverage always returned None. Added to NAMES (+test test_task172_names_gap_v1) + regenerated SCHEMA.json. Ran create_agent_sheets(2026-06) → created RH-2026-06-borrow_coverage (id 1w8sx-...), sheets_config +1 key (merge, 23 existing untouched). collect_borrow_coverage wrote one real row: ScannedUniverse=1 WithBorrowData=1 PctWithBorrowData=100 ShortableCount=0 PctShortable=0 (n=1: existing position, no Score>=60 scans today). Both pcts real/non-null. Mechanism verified end-to-end.
<!-- SECTION:NOTES:END -->
