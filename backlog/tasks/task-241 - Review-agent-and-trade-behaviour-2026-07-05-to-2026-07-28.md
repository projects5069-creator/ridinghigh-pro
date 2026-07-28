---
id: TASK-241
title: Review agent and trade behaviour 2026-07-05 to 2026-07-28
status: To Do
assignee: []
created_date: '2026-07-28 12:40'
labels:
  - analysis
dependencies: []
ordinal: 245000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Review what the system actually decided during the unsupervised period. Context verified live this session: AGENT_DRY_RUN=True, SENTINEL_MODE=shadow, EXPLICIT_GATE_MODE=active, ENTRY_GATE_MINIMAL=True, NEWS_DETECTIVE_ENABLED=False - so trades are paper and MxV was the only active gate. Questions: ENTER vs SKIP counts; exit reason distribution; whether TP10/SL10/HOLD5 behaved as expected; whipsaw count; whether any ENTER fired on a doubled-letter phantom symbol and how that distorts win-rate; whether n reached the HYP-002 validation threshold whose checkpoint fell on 27/7. Quota-heavy: run outside market hours.
<!-- SECTION:DESCRIPTION:END -->
