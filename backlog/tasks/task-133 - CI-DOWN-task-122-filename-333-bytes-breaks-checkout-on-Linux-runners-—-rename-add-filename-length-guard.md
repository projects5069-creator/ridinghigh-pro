---
id: TASK-133
title: >-
  CI DOWN: task-122 filename 333 bytes breaks checkout on Linux runners — rename
  + add filename-length guard
status: To Do
assignee: []
created_date: '2026-06-10 15:55'
updated_date: '2026-06-11 04:01'
labels: []
dependencies: []
priority: high
ordinal: 136000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
rename done (307c0e5, 10/6); REMAINING: filename-length guard (pre-commit/CI check ש-basename<200B).
<!-- SECTION:NOTES:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TASK-139-INV phase0/5: all 4 night-of-9/6 failures + warm_oauth 10/6 15:42Z = 'File name too long' on task-122 at checkout; rename landed (307c0e5), length-guard still pending
<!-- AC:END -->
