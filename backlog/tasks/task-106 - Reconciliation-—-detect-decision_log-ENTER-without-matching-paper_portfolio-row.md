---
id: TASK-106
title: >-
  Reconciliation — detect decision_log ENTER without matching paper_portfolio
  row
status: Done
assignee: []
created_date: '2026-06-03 18:36'
updated_date: '2026-06-03 19:06'
labels:
  - order-manager
  - reconciliation
  - data-integrity
dependencies: []
priority: medium
ordinal: 106000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Defense-in-depth follow-up to TASK-105 (Option 3). TASK-105 surfaces a failed paper_portfolio write at write-time; this task adds after-the-fact reconciliation: detect a decision_log ENTER (today) that has NO matching paper_portfolio row (by PositionID/Ticker+EntryDate) and repair or flag it. Existing scaffold: agent/execution/reconciler.py. Catches cases where the write failed AND the surfaced error was missed, or older gaps (e.g. XOS 2026-06-03).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision_log ENTER without a matching paper_portfolio row is detected and either repaired (row re-written, idempotent by PositionID) or flagged (alert/log).
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Resolved by PR #5 (commit c210f9a, 2026-06-03): Reconciler.reconcile_decision_log_vs_portfolio() flags decision_log ENTER w/o matching paper_portfolio row (PositionID==DecisionID, all statuses), wired into EOD. flag-only. Repair is phase-2 (NO task yet). Verified green on main (3c631d9). PK v2.67.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Reconciliation routine detects ENTER/portfolio mismatches; unit test proves a seeded mismatch is detected; py_compile + test_formulas 107/107 + sentinel_selftest green; PK bump + changelog; branch + PR.
<!-- DOD:END -->
