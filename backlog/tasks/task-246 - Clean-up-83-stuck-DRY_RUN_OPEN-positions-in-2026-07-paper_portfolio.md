---
id: TASK-246
title: Clean up 83 stuck DRY_RUN_OPEN positions in 2026-07 paper_portfolio
status: To Do
assignee: []
created_date: '2026-07-29 09:28'
labels:
  - data-integrity
  - cleanup
dependencies: []
priority: medium
ordinal: 244000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29, read only.

STATE: paper_portfolio 2026-07 holds 137 rows. Status distribution is DRY_RUN_OPEN 83, DRY_RUN_CLOSED 46, MANUAL_CLEANUP 8. All 83 open rows have ExitPrice, ExitDate, ExitTime and ExitReason blank. Age in trading days runs 1 to 10 with a median of 5, and 29 of 83 already exceed MAX_HOLDING_DAYS of 5.

EVERY ONE OF THE 83 IS ON A SUSPECT SYMBOL. 64 are on confirmed phantom tickers, 19 are on doubled letter candidates that were not independently confirmed, and zero are on a clean ticker. The reason they never closed is almost certainly that the symbol does not resolve at the data provider, so no current price is available, so no TP or SL can be evaluated and the monitor never exits the position.

CONSEQUENCE FOR MEASUREMENT: any win rate or exit distribution computed over July 2026 mixes two different populations, the 46 that closed and predate the corruption, and everything opened after 2026-07-15 which is stuck. Performance for this month should not be computed before this is resolved.

BLOCKED ON: the finviz ticker fix, so that the cleanup rule can distinguish a phantom from a real symbol. Any correction is a write to Sheets and needs explicit approval and a dated backup first. Never delete rows, mark them.

OPEN QUESTION: whether these rows should be marked with a distinct status rather than reusing MANUAL_CLEANUP, so that research queries can exclude them by rule.
<!-- SECTION:DESCRIPTION:END -->
