---
id: TASK-236
title: >-
  auto-dancer VERIFY produces empty verify.json -> task_result=stage_error
  (execute-proof final stage)
status: To Do
assignee: []
created_date: '2026-07-05 23:17'
labels: []
dependencies: []
ordinal: 240000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
First full --manual run 2026-07-05: P->C->E->C all passed (plan.md 145 lines; execution status=executed; both critics pass) but VERIFY returned empty verify.json -> stage_error. Investigate verify_task.md invocation + verify.json write path. Blocks TASK-186 final.
<!-- SECTION:DESCRIPTION:END -->
