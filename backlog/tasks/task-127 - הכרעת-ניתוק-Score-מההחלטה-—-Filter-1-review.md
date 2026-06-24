---
id: TASK-127
title: הכרעת ניתוק Score מההחלטה — Filter 1 review
status: Done
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-24 16:05'
labels: []
dependencies: []
priority: medium
ordinal: 130000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verified: Score gates entry (decision_logic.py:276-278, AGENT_MIN_SCORE=50) while 70% of its weight (MxV25+RunUp25+ATRX20, config.py:41-43) shows ~0 correlation to outcome and Price (the only significant predictor, r=+0.25/+0.33) has 0 weight. Decision gated on freed data (after backfill task) — recompute on ~115 settled rows first. Policy decision = ping-pong, locked like TASK-69.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TASK-139-INV kill-criterion MET (RH-6.1): random-in-filter WR .659 vs top-Score-half .629 (p=.56); r(Score,WIN)=-0.02 p=.82 on n=123. Report recommends Option B explicit gate — see REPORT.md ch.6 + phase6_evidence.md
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-171 input (2026-06-12): Score confirmed dead as ranking signal (AUC 0.531; no hidden component — all 7 <= 0.552). Score-decoupling decision folds into TASK-174 (decision gate). Do not retune weights on current n.
<!-- SECTION:NOTES:END -->
