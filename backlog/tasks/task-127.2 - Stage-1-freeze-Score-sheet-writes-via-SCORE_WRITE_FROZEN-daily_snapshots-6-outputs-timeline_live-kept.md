---
id: TASK-127.2
title: >-
  Stage 1: freeze Score sheet-writes via SCORE_WRITE_FROZEN (daily_snapshots + 6
  outputs -> ''); timeline_live kept
status: To Do
assignee: []
created_date: '2026-06-18 20:12'
labels:
  - data-integrity
dependencies: []
parent_task_id: TASK-127
priority: high
ordinal: 190000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Stage 1 of forward-only Score removal (ADR-009). config flag SCORE_WRITE_FROZEN (default True): auto_scanner still computes Score in-memory (sort/>=70/idxmax intact) but writes '' to the Score column of daily_snapshots + 6 output sheets (portfolio x2, daily_summary, ticker_follow_up, live_trades, score_tracker). timeline_live Score kept (run_eod:1315 re-reads it for EOD selection). Warehouse goes scoreless -> collector emits ''+v3_scoreless (Stage 0). Decision-role removal = Stage 2+141.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SCORE_WRITE_FROZEN=True -> Score column written '' at all 7 sites; =False -> numeric (no-op)
- [ ] #2 in-memory selection (results_df >=70, idxmax, sort) unchanged when frozen
- [ ] #3 timeline_live + run_eod EOD-selection unaffected; ScoreType column untouched
- [ ] #4 frozen daily_snapshots -> collector post_analysis ''+v3_scoreless (end-to-end)
<!-- AC:END -->
