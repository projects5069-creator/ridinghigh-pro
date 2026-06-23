---
id: TASK-167
title: SCHEMA.json contract for all sheets + drift check
status: Done
assignee: []
created_date: '2026-06-12 22:55'
updated_date: '2026-06-23 00:36'
labels:
  - vision
dependencies: []
priority: medium
ordinal: 170000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Vision via TASK-156. Single SCHEMA.json declaring canonical columns of every sheet; a check that fails when a live sheet header drifts from contract (cf. TASK-150 cross-month column-order drift).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SCHEMA.json with per-sheet column contracts
- [x] #2 Drift check (CI or sentinel) flags live-header mismatch vs contract
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-06-22 Layer-2 live-verify (post-EOD): check_08(gc) ran live = PASSED, 'All contracted columns present (16 sheets)' against SCHEMA.json. AC#1 (SCHEMA.json) + AC#2 (drift-check) both done — Layer-1 landed 83b2952, Layer-2 verified now.
<!-- SECTION:NOTES:END -->
