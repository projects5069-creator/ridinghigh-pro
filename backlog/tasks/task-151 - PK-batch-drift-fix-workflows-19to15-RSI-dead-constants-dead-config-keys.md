---
id: TASK-151
title: 'PK batch drift fix: workflows 19to15, RSI dead constants, dead config keys'
status: To Do
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-12 22:56'
labels:
  - TASK-139-INV
dependencies: []
priority: low
ordinal: 154000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV D1+RH-1.1+RH-1.2: PK line 19 says 'Active workflows: 7' vs 15 actual; RSI_LOW/RSI_HIGH/SCORE_RSI_PARAMS dead (code uses hardcoded 80/85/90 steps, PK sec-18 'bell curve 50-70' false twice); 9 dead config constants (MIN_PRICE, MAX_HOLDING_DAYS, market-hours consts, MEDIUM_SCORE, AGENT_NO_TIME_LIMIT...). Extends TASK-129+TASK-138. Evidence: phase1+phase8
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-156 merge: absorbs TASK-129 (RSI dead-config cleanup: SCORE_RSI_PARAMS unused, hardcoded tiers, PK §18 wrong). Fold into this PK-batch-drift cleanup.
<!-- SECTION:NOTES:END -->
