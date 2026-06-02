---
id: TASK-85
title: 'Pre-commit guard: reject backlog filenames over 200 bytes'
status: Done
assignee: []
created_date: '2026-05-31 18:27'
updated_date: '2026-06-02 04:38'
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
- [x] #1 Pre-commit hook rejects basename >200 bytes
- [x] #2 Existing files all pass
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Pre-commit guard added (scripts/git_hooks/pre-commit + install.sh), rejects staged backlog/*.md basenames >200B; PR#2 merged b98ae90; installed locally. 3 files 200-255B grandfathered (staged-only scope).
<!-- SECTION:FINAL_SUMMARY:END -->
