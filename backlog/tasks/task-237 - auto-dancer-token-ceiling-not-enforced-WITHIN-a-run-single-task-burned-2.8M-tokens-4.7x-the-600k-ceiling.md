---
id: TASK-237
title: >-
  auto-dancer token ceiling not enforced WITHIN a run -> single task burned 2.8M
  tokens (4.7x the 600k ceiling)
status: To Do
assignee: []
created_date: '2026-07-05 23:17'
labels: []
dependencies: []
ordinal: 241000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
over_ceiling checked BETWEEN tasks not WITHIN a run: TASK-232 --manual spent 2,808,459 tokens vs 600k ceiling. Need in-run guard aborting stage/task when cumulative exceeds ceiling. HIGH cost-risk; blocks safe re-runs.
<!-- SECTION:DESCRIPTION:END -->
