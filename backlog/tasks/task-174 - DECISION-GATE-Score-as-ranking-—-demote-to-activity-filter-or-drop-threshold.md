---
id: TASK-174
title: '[DECISION GATE] Score-as-ranking — demote to activity-filter or drop threshold'
status: Done
assignee: []
created_date: '2026-06-13 01:26'
updated_date: '2026-06-24 16:05'
labels:
  - TASK-171
dependencies: []
priority: high
ordinal: 177000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
171-A3 / PT-2. Verified across two investigations: Score AUC 0.531 [0.43,0.63] n=140, ALL 7 components dead (max MxV 0.552), nothing survives BH (k=21), no hidden component. Decide: keep Score>=70 as a mere activity filter, or drop the threshold. Do NOT retune weights on n=140 (overfit machine). Ties TASK-127/TASK-141. DECISION=Amihay.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Decision recorded: activity-filter vs no-threshold
- [ ] #2 No weight retuning until n>=300 decided
<!-- AC:END -->
