---
id: TASK-166
title: Daily lineage sentinel — recompute one random row/day as a health check
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
labels:
  - vision
dependencies: []
priority: medium
ordinal: 169000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Vision via TASK-156. Daily health check: recompute one random settled post_analysis row end-to-end and flag if stored values drift from a fresh recompute — catches silent pipeline/data corruption.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sentinel picks 1 random settled row/day, recomputes, compares to stored; WARNING on mismatch
<!-- AC:END -->
