---
id: TASK-161
title: Stop post-commit hook committing PROJECT_STATE.md (branch merge-conflict)
status: In Progress
assignee: []
created_date: '2026-06-12 01:40'
updated_date: '2026-06-12 01:51'
labels: []
dependencies: []
priority: high
ordinal: 164000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post-commit hook regenerates+commits PROJECT_STATE.md on every branch -> branches from same base conflict on it once main moves; stalled Wave A merges. Untrack or regenerate-on-main only. Repo-scoped infra; no trading logic.
<!-- SECTION:DESCRIPTION:END -->
