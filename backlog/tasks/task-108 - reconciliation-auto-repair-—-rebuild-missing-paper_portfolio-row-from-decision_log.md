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
Phase-2 of TASK-106. TASK-106 flags a decision_log ENTER with no matching paper_portfolio row (flag-only). Phase-2: auto-repair — reconstruct and write the missing row from decision_log (near-lossless; only TPOrderID/SLOrderID cosmetic leg-ids are missing, leave blank or derive from EntryOrderID). GATE: enable ONLY after the flag-only reconciler (TASK-106) has proven accurate over time with no false positives — auto-repair WRITES to the sheet, and a false positive would create a wrong/duplicate row. Idempotent via PositionID dedup (safe_append_row dedup_col=0).
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
