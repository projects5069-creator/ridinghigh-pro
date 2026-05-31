---
id: TASK-85
title: 'Pre-commit guard: reject backlog filenames over 200 bytes'
status: To Do
assignee: []
created_date: '2026-05-31 18:27'
labels:
  - infra
  - backlog
  - guard
dependencies: []
priority: medium
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On 5/31 five backlog task files (66/67/69/71/72) had Hebrew-title filenames 271-326 bytes. macOS allows 255 CHARS but Linux ext4 caps at 255 BYTES (Hebrew=2B/char), so actions/checkout failed on every workflow since c07c848. Add a pre-commit hook rejecting any backlog/tasks/*.md basename >200 bytes (margin under 255). Root cause: backlog CLI embeds the full title into the filename -> keep task titles short.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Pre-commit hook rejects basename >200 bytes
- [ ] #2 Existing files all pass
<!-- AC:END -->
