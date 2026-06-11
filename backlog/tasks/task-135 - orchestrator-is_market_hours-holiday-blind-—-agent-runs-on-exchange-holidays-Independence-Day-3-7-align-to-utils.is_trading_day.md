---
id: TASK-135
title: >-
  orchestrator is_market_hours holiday-blind — agent runs on exchange holidays
  (Independence Day 3/7); align to utils.is_trading_day
status: To Do
assignee: []
created_date: '2026-06-10 18:13'
updated_date: '2026-06-11 04:01'
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
- [ ] #1 TASK-139 RH-1.4: utils.is_day_complete is also weekday-only (past holiday counted complete) — align together with is_market_hours fix
<!-- AC:END -->
