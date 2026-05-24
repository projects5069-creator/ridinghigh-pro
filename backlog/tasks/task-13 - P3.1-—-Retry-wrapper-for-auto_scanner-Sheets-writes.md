---
id: TASK-13
title: P3.1 — Retry wrapper for auto_scanner Sheets writes
status: Done
assignee: []
created_date: '2026-05-23 19:33'
updated_date: '2026-05-24 02:21'
labels: []
dependencies: []
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
auto_scanner.py lines 921, 1219, 1223 — wrap Sheets writes in retry logic. Currently 429 errors are silently swallowed.
<!-- SECTION:DESCRIPTION:END -->
