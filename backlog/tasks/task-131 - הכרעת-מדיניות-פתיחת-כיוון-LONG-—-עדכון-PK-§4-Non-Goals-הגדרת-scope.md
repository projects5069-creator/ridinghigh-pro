---
id: TASK-131
title: 'הכרעת מדיניות: פתיחת כיוון LONG — עדכון PK §4 Non-Goals + הגדרת scope'
status: Done
assignee: []
created_date: '2026-06-10 02:04'
updated_date: '2026-06-13 01:27'
labels: []
dependencies: []
priority: low
ordinal: 134000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
PK §4 lists Long positions as explicit Non-Goal. Opening LONG requires a formal policy decision by Amihay (ping-pong per RUN_MODE tree branch 1) + PK §4 update + scope definition (universe, sizing, gates). HONEST CONTEXT from 9/6 DropsLab research: bottom-reversal LONG at daily resolution showed NO entry-time-detectable edge (long sim at D1-open LOSES: mean -0.83% at TP10; reversal predictors = volatility not direction); only unexplored path = intraday confirmed-bounce trigger after reversal candle (bd_candle AUC .598 marginal). Decision should weigh that evidence; if approved, start research-only (no live).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TASK-139-INV DL-7.4 (deprioritize): no daily directional signal on n=2,231 — P(D1 up)=.496, all 14 metric AUCs .457-.524; long-at-D1 thesis has no data support at daily resolution
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
READY-TO-CLOSE per TASK-171 (2026-06-12): LONG thesis dead at HIGH power — DropsLab tradeable long d1c->d5c = -1.64% [-2.50,-0.77] n=2,103 (after slip -3.64%); the '75% recovery' was hindsight peak-touch. Closure executes via TASK-175 (PK §4 Non-Goals update). Evidence: docs/research/INVESTIGATION_2026-06-12_II/ phase 7.

CLOSED 2026-06-13 via TASK-175 (PK v3.17): §4 Non-Goal "Long positions" rationale upgraded to evidence-confirmed + #N25 "active longs" contradiction fixed. Decision = LONG stays a closed non-goal (no open).
<!-- SECTION:NOTES:END -->
