---
id: TASK-188
title: Investigate RSI-semantics PK claim vs code (bell-curve vs overbought-only)
status: Done
assignee: []
created_date: '2026-06-22 01:50'
updated_date: '2026-06-22 13:53'
labels: []
dependencies: []
priority: medium
ordinal: 194000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
PK §18/§36 describes RSI scoring as a bell curve (peak band 50-70), but memory/code point to an overbought-only graded path (rsi>=90->10, >=85->7, >=80->4, <80->0). The drift between PK and the actual formulas.calculate_score RSI path is UNVERIFIED — this task is to determine which is correct, not to assume. Read the live RSI scoring path (formulas.calculate_score + SCORE_RSI_PARAMS/SCORE_CAPS_V2 in config.py) and fix whichever side is wrong (code OR PK §18/§36). Note: SCORE_RSI_PARAMS may be dead code — verify. Spun off from TASK-151 (dead-const part closed 2026-06-21). No deadline.
<!-- SECTION:DESCRIPTION:END -->
