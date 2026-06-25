---
id: TASK-192
title: >-
  Quota C4 — merge per-position safe_batch_update into one batched call for all
  open positions
status: Done
assignee: []
created_date: '2026-06-24 14:11'
updated_date: '2026-06-25 12:52'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-24 (TDD). make_portfolio_batch_writer (orchestrator.py) buffers per-position paper_portfolio cells and flushes ONE safe_batch_update per step (after monitor_all + eod_close_all), replacing the old write-per-position closure. N open positions -> 1 API write/step instead of N (cap AGENT_COLD_START_MAX_CONCURRENT=5 -> savings N-1, up to 4/run; 0 when N=1). _row_number targeting locked: tests/agent/unit/test_portfolio_batch_writer_v1.py 5/5 (rows 2/5/9 no cross-row + USER_ENTERED + N=0/1 + buffer-clear + unknown-col dropped). Preserves PositionID fallback. Zero change to ENTER/SKIP/Score/decision; no live flush (RULE #6). Full suite 540 passed, 0 regression. PK v3.60.
<!-- SECTION:NOTES:END -->
