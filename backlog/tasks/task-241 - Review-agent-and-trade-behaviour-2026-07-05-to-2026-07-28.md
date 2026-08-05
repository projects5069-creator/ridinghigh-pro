---
id: TASK-241
title: Review agent and trade behaviour 2026-07-05 to 2026-07-28
status: To Do
assignee: []
created_date: '2026-07-28 12:40'
labels:
  - analysis
dependencies: []
ordinal: 245000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Review what the system actually decided during the unsupervised period. Context verified live this session: AGENT_DRY_RUN=True, SENTINEL_MODE=shadow, EXPLICIT_GATE_MODE=active, ENTRY_GATE_MINIMAL=True, NEWS_DETECTIVE_ENABLED=False - so trades are paper and MxV was the only active gate. Questions: ENTER vs SKIP counts; exit reason distribution; whether TP10/SL10/HOLD5 behaved as expected; whipsaw count; whether any ENTER fired on a doubled-letter phantom symbol and how that distorts win-rate; whether n reached the HYP-002 validation threshold whose checkpoint fell on 27/7. Quota-heavy: run outside market hours.
<!-- SECTION:DESCRIPTION:END -->

## PARTIALLY ANSWERED (2026-07-29, read only)

decision_log 2026-07 holds 137 rows, all ENTER, zero SKIP for the entire month. The ENTER versus SKIP ratio cannot be computed from this tab. Where rejections are recorded is filed as TASK-247 and must be settled before this task proceeds.

64 of 137 ENTERs, 46.7 percent, fired on a confirmed phantom symbol.

Win rate is not computable for July. paper_portfolio holds 83 DRY_RUN_OPEN and 46 DRY_RUN_CLOSED. Every open row is on a suspect symbol and none on a clean ticker, and all four exit columns are blank on all 83, so the closed set and the open set are two different populations. 29 of 83 already exceed MAX_HOLDING_DAYS.

Repeat entries on the same open symbol were found, 43 ENTERs on 4 tickers on 07-22. Filed as TASK-244.

BLOCKED ON: TASK-246 (stuck positions) — that is the only blocker left. Updated 2026-08-05: TASK-238 (ticker fix) and TASK-247 (SKIP source) are both Done; TASK-246 is still To Do. The HYP-002 checkpoint that fell on 27/7 cannot be evaluated on this data.
