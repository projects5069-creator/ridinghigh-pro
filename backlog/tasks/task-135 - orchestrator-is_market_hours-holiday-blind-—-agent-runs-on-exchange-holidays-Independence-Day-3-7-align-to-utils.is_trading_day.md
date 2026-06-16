---
id: TASK-135
title: >-
  orchestrator is_market_hours holiday-blind — agent runs on exchange holidays
  (Independence Day 3/7); align to utils.is_trading_day
status: Done
assignee: []
created_date: '2026-06-10 18:13'
updated_date: '2026-06-16 18:03'
labels:
  - bug
  - agent
dependencies: []
priority: high
ordinal: 138000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found in SYSTEM_REVIEW B.4 + TASK-130 recon (10/6). agent/orchestrator.py:104 is_market_hours uses weekday-only (now.weekday()>=5) with NO holiday calendar, while utils.is_market_hours/is_trading_day include NASDAQ holidays via mcal. Consequence: on exchange holidays that are weekdays (Independence Day observed Fri 3/7/2026, etc) the agent attempts to run while the scanner correctly does not. DRY_RUN so no money risk, but wrong run condition on live agent. Fix: replace orchestrator weekday-only check with a call to utils.is_trading_day (mirrors the TASK-130 pattern). Separate from TASK-130 deliberately: touches live orchestrator run-condition, needs its own diff-review + PING-PONG commit. Deadline: before Fri 3/7/2026.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TASK-139-INV RH-1.4: utils.is_day_complete is also weekday-only (past holiday counted complete) — align together with is_market_hours fix
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE (c508879, 2026-06-16, CI green): bug1 orchestrator.is_market_hours + bug2 utils.is_day_complete both routed through utils.is_trading_day (SSoT reuse of TASK-130, zero dup). bug1 reachable (agent ran on weekday holidays e.g. Independence Day Fri 7/3); bug2 defensive (callers feed holiday-free trading_days from get_trading_days_after). +2 hermetic holiday tests in test_trading_days_holiday_v1.py (CI-collected). suite 369 passed; zero ENTER/sizing/Score/D0 change. AC#1 (is_market_hours + is_day_complete) satisfied. Deadline 3-4/7 cleared early.
<!-- SECTION:NOTES:END -->
