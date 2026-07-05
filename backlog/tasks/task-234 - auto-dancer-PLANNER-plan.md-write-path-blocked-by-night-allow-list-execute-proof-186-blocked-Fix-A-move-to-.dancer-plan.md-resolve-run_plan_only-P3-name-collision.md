---
id: TASK-234
title: >-
  auto-dancer: PLANNER plan.md write-path blocked by night allow-list ->
  execute-proof (186) blocked; Fix A move to .dancer/plan.md + resolve
  run_plan_only P3 name-collision
status: To Do
assignee: []
created_date: '2026-07-05 18:03'
labels: []
dependencies: []
ordinal: 238000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Root-caused this session. plan_task.md:46,107 writes plan.md at worktree root; settings.night allow=Write(.dancer)+Write(tests) only -> silent block. EXECUTOR+CRITIC read plan.md never created. run_plan_only:289 out_json=.dancer/plan.md (name collision). Blocks TASK-186. Fix A: plan_task->.dancer/plan.md; execute+critique read .dancer/plan.md; run_plan_only out_json rename; TDD hermetic write-path-in-allow test.
<!-- SECTION:DESCRIPTION:END -->
