---
id: TASK-99
title: build_weekly_row cross-month bug (same root as TASK-60 bug B)
status: Done
assignee: []
created_date: '2026-06-02 17:15'
updated_date: '2026-06-02 18:57'
labels: []
dependencies: []
priority: medium
ordinal: 99000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
build_weekly_row calls review_completed_trades() with no month (defaults to current). A weekly window spanning a month boundary (e.g. last week of May into June) will read the wrong monthly paper_portfolio sheet and miss trades. Same class of bug as TASK-60 bug B but for weekly. Needs month-aware read or cross-month merge. Discovered 2026-06-02.
<!-- SECTION:DESCRIPTION:END -->
