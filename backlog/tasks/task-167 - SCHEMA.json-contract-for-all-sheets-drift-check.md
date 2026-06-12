---
id: TASK-167
title: SCHEMA.json contract for all sheets + drift check
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
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
- [ ] #1 SCHEMA.json with per-sheet column contracts
- [ ] #2 Drift check (CI or sentinel) flags live-header mismatch vs contract
<!-- AC:END -->
