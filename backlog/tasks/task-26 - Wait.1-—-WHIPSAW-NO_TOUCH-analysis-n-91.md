---
id: TASK-26
title: Wait.1 — WHIPSAW + NO_TOUCH analysis (n>91)
status: To Do
assignee: []
created_date: '2026-05-23 19:35'
updated_date: '2026-06-12 17:51'
labels: []
dependencies: []
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate WHIPSAW and NO_TOUCH trade categories. BLOCKED on data: currently n=62, need n>91 for statistical significance. Expected unblock: end of May 2026.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 RESOLVED by TASK-155 minute-bars (2026-06-12): the 26 WHIPSAW resolve to 8 WIN / 17 LOSS / 1 UNRESOLVED (XNDU, one-side-only on IEX). resolver=utils.resolve_whipsaw, cache=intraday_cache; per-row CSV in docs/research/WHIPSAW_RESOLUTION_2026-06-12/. WHIPSAW skew strongly negative (68% LOSS) — confirms RH-6.3 edge concern.
<!-- AC:END -->
