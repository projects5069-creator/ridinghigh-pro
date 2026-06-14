---
id: TASK-181
title: Cleanup stale .bak backup files
status: To Do
assignee: []
created_date: '2026-06-14 23:29'
labels:
  - hygiene
  - cleanup
dependencies: []
priority: low
ordinal: 184000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
10+ *.bak_* files accumulate in the working dir from RULE #4 backups (gitignored, do NOT pollute git, but clutter the tree). Task: safely delete OLD .bak files (verify no active restore is needed before deleting — never delete blind). Optional: ensure .gitignore has the *.bak_* glob; add a periodic cleanup helper.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Working dir is clear of stale .bak files; zero dangerous files deleted; restore-needed backups preserved
<!-- AC:END -->
