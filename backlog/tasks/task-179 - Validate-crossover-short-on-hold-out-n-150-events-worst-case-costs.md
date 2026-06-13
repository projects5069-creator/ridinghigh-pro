---
id: TASK-179
title: 'Validate crossover-short on hold-out (n>=150 events, worst-case costs)'
status: To Do
assignee: []
created_date: '2026-06-13 01:27'
labels:
  - TASK-171
  - crossover-short
dependencies: []
priority: high
ordinal: 182000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
171-B3. Validation of the pre-registered crossover-short: hold-out on NEW data only (post pre-registration), worst-case HTB borrow model (from TASK-172 data), slippage 2x, fitness locked = net expectancy. Power: needs >=150 crossover events (~450 RH rows, ~4-5 months at current capture rate — see power_analysis.md). BLOCKED ON: TASK-172 + TASK-177 + pre-registration task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Validation runs ONLY on data collected after pre-registration (no reuse of the n=62 discovery sample)
- [ ] #2 Verdict at n>=150 events: edge survives worst-case costs or hypothesis rejected — either outcome documented
<!-- AC:END -->
