---
id: TASK-182
title: Backfill InterdayArtifact on legacy post_analysis rows
status: To Do
assignee: []
created_date: '2026-06-15 13:17'
updated_date: '2026-06-16 15:23'
labels:
  - data-integrity
dependencies: []
ordinal: 185000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
§0 closed in a2bd740 (2026-06-16): _coerce_bool now reads numeric-truthy ('1.0'->True). Remaining = backfill of 128-NaN/51-blank InterdayArtifact column (live-write, post-market). Stays To Do.
<!-- SECTION:NOTES:END -->
