---
id: TASK-149
title: 'Classify 19 NO_DATA rows: delisting = lost short wins (survivorship)'
status: To Do
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-22 01:05'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 152000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV phase0/4: audit_flag=NO_DATA appears on 19 post_analysis rows (+2 with REL_VOL_CAPPED suffix). Classify each: delisted = max short win never counted (survivorship bias, but also un-coverable in practice). Ties TASK-132 (SBLX). Evidence: phase0_evidence.md audit_flag table
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-132 folded in 2026-06-21: SBLX 2026-04-28 (delisted, all-NaN since April) is part of this task's delisting/NO_DATA scope. Handle SBLX when 149 is worked.
<!-- SECTION:NOTES:END -->
