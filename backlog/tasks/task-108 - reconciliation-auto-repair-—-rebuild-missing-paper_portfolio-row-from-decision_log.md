---
id: TASK-108
title: >-
  reconciliation auto-repair — rebuild missing paper_portfolio row from
  decision_log
status: To Do
assignee: []
created_date: '2026-06-03 22:34'
labels:
  - reconciler
  - robustness
  - data-integrity
dependencies: []
priority: medium
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Phase-2 of TASK-106. TASK-106 flags a decision_log ENTER with no matching paper_portfolio row (flag-only). Phase-2: auto-repair — reconstruct and write the missing row from decision_log. GATE: enable ONLY after the flag-only reconciler (TASK-106) has proven accurate over time with no false positives — auto-repair WRITES to the sheet, and a false positive would create a wrong/duplicate row. Idempotency is structural via re-detection (a row already present is never flagged), NOT via the blind first-append dedup.

SPEC CORRECTION (verified in code 2026-06-03): all THREE order-ids (Entry/TP/SL OrderID) are blank in a reconstructed row — DecisionLogger.log() runs BEFORE OrderManager.execute(), so order_id/execution_price are still None at log time; "derive from EntryOrderID" is impossible. EntryPrice falls back to Price (signal price), not ExecutionPrice. So "near-lossless" is weakened but still a valid audit row. Status from AgentMode (DRY_RUN→DRY_RUN_CLOSED, LIVE_PAPER→CLOSED); ExitReason=RECONCILER_BACKFILL; ExitDate/ExitTime=EntryDate/EntryTime; empty only in ExitPrice/RealizedPnL/RealizedPnLPct; DataQuality=BACKFILL.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 On a confirmed gap (decision_log ENTER w/o paper_portfolio row), the missing row is reconstructed from decision_log and written idempotently.
- [ ] #2 A false positive does NOT write (no duplicate/wrong row); gated behind a proven-accurate flag period.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Method rebuilds the row from decision_log + writes idempotently (PositionID dedup); unit test proves correct reconstruction AND that a false-positive does not write; py_compile + test_formulas 107/107 + sentinel_selftest green; branch + PR, manual merge.
<!-- DOD:END -->
