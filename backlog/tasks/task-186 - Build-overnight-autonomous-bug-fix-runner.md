---
id: TASK-186
title: Build overnight autonomous bug-fix runner
status: In Progress
assignee: []
created_date: '2026-06-19 02:09'
updated_date: '2026-06-19 23:28'
labels: []
dependencies: []
priority: high
ordinal: 192000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
launchd + claude -p (Max subscription) overnight runner on feature/overnight-runner. Strict auto-safe filter, worktree-isolated draft PRs, secret+CORE_UNSAFE PreToolUse hooks, token/time circuit breaker. Code+tests DONE & GREEN; schedule-enable gated behind §11 supervised gates.
<!-- SECTION:DESCRIPTION:END -->
