---
id: TASK-127
title: הכרעת ניתוק Score מההחלטה — Filter 1 review
status: To Do
assignee: []
created_date: '2026-06-10 01:03'
labels: []
dependencies: []
priority: medium
ordinal: 130000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verified: Score gates entry (decision_logic.py:276-278, AGENT_MIN_SCORE=50) while 70% of its weight (MxV25+RunUp25+ATRX20, config.py:41-43) shows ~0 correlation to outcome and Price (the only significant predictor, r=+0.25/+0.33) has 0 weight. Decision gated on freed data (after backfill task) — recompute on ~115 settled rows first. Policy decision = ping-pong, locked like TASK-69.
<!-- SECTION:DESCRIPTION:END -->
