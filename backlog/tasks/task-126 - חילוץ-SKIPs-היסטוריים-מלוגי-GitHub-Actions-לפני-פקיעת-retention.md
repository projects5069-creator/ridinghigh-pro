---
id: TASK-126
title: חילוץ SKIPs היסטוריים מלוגי GitHub Actions לפני פקיעת retention
status: To Do
assignee: []
created_date: '2026-06-10 01:03'
labels: []
dependencies: []
priority: medium
ordinal: 129000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Route B prints [SKIP] lines to Actions stdout. Logs retained ~90 days: May-12 runs expire ~Aug-10. One-off scraper (gh run list + gh run view --log, grep [SKIP]) to rebuild counterfactual dataset May-12..today into local CSV. Read-only, no Sheets writes.
<!-- SECTION:DESCRIPTION:END -->
