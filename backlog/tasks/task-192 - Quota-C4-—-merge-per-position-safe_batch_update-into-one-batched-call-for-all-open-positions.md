---
id: TASK-192
title: >-
  Quota C4 — merge per-position safe_batch_update into one batched call for all
  open positions
status: To Do
assignee: []
created_date: '2026-06-24 14:11'
labels:
  - agent
  - infra
  - quota
dependencies: []
priority: medium
ordinal: 198000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Spawned by TASK-136 audit. _portfolio_sheet_writer (orchestrator.py:622) issues one safe_batch_update per monitored position; with N open positions that is N API writes/run. Accumulate all positions' cell updates and flush a single batch_update. Preserve the positional _row_number targeting (Bug #2 fix) and USER_ENTERED. TDD + PING-PONG.
<!-- SECTION:DESCRIPTION:END -->
