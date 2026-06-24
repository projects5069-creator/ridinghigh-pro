---
id: TASK-141
title: >-
  [DECISION GATE] Replace Filter1 with explicit volume+price+float gate (Option
  B)
status: Done
assignee: []
created_date: '2026-06-11 04:01'
updated_date: '2026-06-24 16:05'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 144000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-6.1: kill-criterion MET — random-in-filter WR .659 vs top-Score .629 (p=.56), r=-0.02 p=.82, n=123. Pass-all-14-filters WR .846 vs .608 blocked — value lives in the gates, not the continuous Score. Ties to TASK-127 (decision) + TASK-128 (shadow gate). DECISION = Amihay only; report recommends Option B. REPORT.md ch.6
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-171 input (2026-06-12): Score confirmed dead as ranking (AUC 0.531, all 7 components dead, 0 survive BH k=21, n=140). Filter1 replacement decision should fold into TASK-174 (Score decision gate).
<!-- SECTION:NOTES:END -->
