---
id: TASK-142
title: '[DECISION GATE] Rebase official WR on D1_Open entry; demote Table A'
status: Done
assignee: []
created_date: '2026-06-11 04:01'
updated_date: '2026-06-12 15:08'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 145000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-6.2 + RH-2.6: run_eod books portfolio entries at hindsight peak-Score price -> WR .689 vs .553 at D1_Open on same 103 rows (+13.6pp inflation). Executable WR is ~.53-.55. Decide: rebase official research WR on D1_Open and demote scan-entry table to diagnostic. DECISION = Amihay
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
APPROVED 2026-06-11; IMPLEMENTED 2026-06-12 on branch task-142-147-wr-d1open (9 commits, NOT merged to main — awaiting approval). Official WR rebased to D1_Open via classify_trade(entry_price)/classify_trade_row(entry_basis) — core WIN/LOSS/WHIPSAW mapping untouched. 2 headline surfaces (Post Analysis+Home) on D1_Open + WHIPSAW-as-loss pessimistic bound (metrics_bounds.wr_bounds, TASK-147 WR-half). Table A demoted to diagnostic, Table B official. Score-research TP10_Hit 'Win Rate'→'TP10 Hit-Rate'. calculate_net_pnl scale-invariant (no entry param; locked). PK v3.07 §20. VERIFIED LOCALLY: 56 new+regression pass, formulas 107/107, utils 38/38, pytest tests/ 311 passed (only 2 live-Sheets integration env-failures, unrelated). No test-CI exists in repo (new task opened). 147 expectancy-half → TASK-162.
<!-- SECTION:NOTES:END -->
