---
id: TASK-287
title: >-
  Extractor _SUMMARY_RE demands sentinel_blocks, leaving 189 May-era runs
  unverified
status: To Do
assignee: []
created_date: '2026-08-09 14:24'
labels: []
dependencies: []
priority: medium
ordinal: 285000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמצא 9/8. _SUMMARY_RE שורות 60-64 דורש sentinel_blocks שלא היה בלוגי מאי. 189 ריצות, 16348 שורות, סומנו no_summary_found. ground-truth ריצה 25683522241: SKIP=70, שבעים חולצו. לא-מאומת, לא שגוי. יוני תקין, ריצה 27297182915 נושאת sentinel_blocks=0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 רגקס סלחני מאמת גם סיכומים ללא sentinel_blocks
- [ ] #2 189 הריצות מאומתות מהדאטה הקיים בלי משיכת לוגים
<!-- AC:END -->
