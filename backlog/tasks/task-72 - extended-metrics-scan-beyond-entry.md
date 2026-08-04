---
id: TASK-72
title: >-
  סריקת מדדים מורחבת — כל מדד שנאסף מעבר לכניסה
  (timeline_live/post_analysis/daily_snapshots): Price_vs_SMA20, Gap,
  PriceToHigh, Consecutive_Up, DaysSinceIPO, ScoreMax/Min/Std. לחפש מדד שעוקף את
  מדדי הכניסה
status: Done
assignee: []
created_date: '2026-05-31 02:32'
updated_date: '2026-08-04 00:32'
labels:
  - metric
  - exploration
  - from-task-62
dependencies: []
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-62 סעיף 1. P2.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-71, 2026-08-04

Closed as a merge. Same research question on the same sample, and blocked on the same thing.

TASK-71 asks which metrics should have led, this task asks which collected metrics beat the entry metrics, and TASK-75 is a specific candidate out of the same scan. All three need outcomes for the stocks that were scanned and not entered, which is TASK-74, and TASK-74 has not moved in 65 days.

Value note recorded 2026-08-04: the July sample is contaminated. 84 positions from the 15/7 to 29/7 window will never close because the symbol does not resolve, so any metric to outcome analysis over that window is unusable.
