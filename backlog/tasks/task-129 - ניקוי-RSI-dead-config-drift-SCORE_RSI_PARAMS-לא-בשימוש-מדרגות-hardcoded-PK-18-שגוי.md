---
id: TASK-129
title: >-
  ניקוי RSI dead-config + drift: SCORE_RSI_PARAMS לא בשימוש, מדרגות hardcoded,
  PK 18 שגוי
status: Done
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-22 17:08'
labels: []
dependencies: []
priority: medium
ordinal: 132000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verified: formulas.py:392 assigns R=SCORE_RSI_PARAMS but no R[ usage; actual scoring = hardcoded steps 80/85/90 (formulas.py:408-417); docstring line 388 says bell curve (wrong); PK 18 says bell curve + RSI_LOW=50 vs config 60. Fix: delete dead params (config.py:64-70 + RSI_HIGH/LOW caps) or wire them; align docstring + PK. Touches config.py+formulas.py = forbidden auto paths = ping-pong.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
MERGED into TASK-151 (TASK-156 agenda). RSI dead-config cleanup folds into the PK-batch-drift task — not independently completed.

2026-06-22 (TASK-188 reopen): סגירה קודמת הייתה docs-only / merged-into-151; dead-config (SCORE_RSI_PARAMS dict, RSI_HIGH/RSI_LOW caps, R= var) נשאר חי בקוד והוסר בפועל רק ב-TASK-188 (commit c0bc60c). ה-cleanup הושלם שם — אפשר לסגור שוב כ-Done-via-188, מושאר To Do לבחירת עמיחי.

2026-06-22 verify+close: all named scope (formulas.py R=SCORE_RSI_PARAMS, config.py:64-70 dead dict + RSI_HIGH/RSI_LOW caps, docstring, PK 18/36) was removed/fixed in TASK-188 (c0bc60c); code-truth grep = clean. Closed via 188. Separate finding (score_backtest.py bell-curve RSI) spun off to its own LOW task.
<!-- SECTION:NOTES:END -->
