---
id: TASK-105
title: Harden paper_portfolio entry-write — stop swallowing failures (XOS anomaly)
status: To Do
assignee: []
created_date: '2026-06-03 18:13'
labels:
  - order-manager
  - robustness
  - data-integrity
dependencies: []
priority: high
ordinal: 105000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Today's only ENTER (XOS @ 08:48) was logged in decision_log but produced ZERO rows in paper_portfolio. Root cause (from 2026-06-03 diagnosis): the paper_portfolio write in order_manager.py ~line 270 (_write_to_portfolio / _default_sheet_write) is best-effort and swallows exceptions (logger.error, no re-raise) — likely a 429 quota error in the morning. This creates a STRUCTURAL ASYMMETRY: the decision_log ENTER is durable, but the paper_portfolio write is not. Result: a failed write is lost silently and can produce FALSE position-drift (POSITION_SYNC) even without the column-alignment bug fixed in PK v2.64. Scope: the entry-write path in agent/execution/order_manager.py. Related: PK v2.64/v2.65 changelog; position_sync immunization (PR #3, merged 517e701).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A failed paper_portfolio entry-write is no longer swallowed silently — it either retries robustly (idempotent, dedup by PositionID) or surfaces a clear alert/log that makes the failure visible (e.g. sentinel_events / system_events / counted as error in run summary).
- [ ] #2 decision_log ENTER and paper_portfolio write no longer diverge silently: a write failure is observable, not lost.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Entry-write path surfaces failures instead of swallowing them (retry or explicit alert/log).
- [ ] #2 Unit test proves a SIMULATED paper_portfolio write failure is surfaced (raised/alerted/counted), not silently swallowed.
- [ ] #3 py_compile clean + test_formulas 107/107 + sentinel_selftest_v1 green.
- [ ] #4 PK updated (bump + changelog) per Anti-Drift; branch + PR, no push to main.
<!-- DOD:END -->
