---
id: TASK-240
title: Audit data reliability 2026-07-05 to 2026-07-28
status: To Do
assignee: []
created_date: '2026-07-28 12:40'
labels:
  - analysis
dependencies: []
ordinal: 244000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Assess coverage and trustworthiness of the unsupervised three-week period. Questions: daily coverage vs actual trading days; missing or zero rates per metric; whether MxV (the only active gate signal) was collected complete each day; how many rows carry a doubled-letter Ticker and their scan_date distribution (tests the two-regime hypothesis: clean before 22/7, suspect after); whether the cancelled collector runs left post_analysis gaps on 23/7, 24/7, 27/7; whether SCORE_WRITE_FROZEN left Score columns empty as intended. Quota-heavy: run outside market hours. Blocked on the ticker corruption scope.
<!-- SECTION:DESCRIPTION:END -->
