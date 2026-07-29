---
id: TASK-240
title: Audit data reliability 2026-07-05 to 2026-07-28
status: To Do
assignee: []
created_date: '2026-07-28 12:40'
labels:
  - analysis
dependencies: []
ordinal: 244000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Assess coverage and trustworthiness of the unsupervised three-week period. Questions: daily coverage vs actual trading days; missing or zero rates per metric; whether MxV (the only active gate signal) was collected complete each day; how many rows carry a doubled-letter Ticker and their scan_date distribution (tests the two-regime hypothesis: clean before 22/7, suspect after); whether the cancelled collector runs left post_analysis gaps on 23/7, 24/7, 27/7; whether SCORE_WRITE_FROZEN left Score columns empty as intended. Quota-heavy: run outside market hours. Blocked on the ticker corruption scope.
<!-- SECTION:DESCRIPTION:END -->

## ANSWERED (2026-07-29, read only)

Day coverage is complete. 17 of 17 trading days present in both post_analysis and daily_snapshots, zero missing days. The cancelled collector runs on 23/7, 24/7 and 27/7 left no gaps, those days hold 18, 14 and 22 rows.

MxV is complete at 77 of 77 with zero blanks, zero zeros and zero non numeric values. The only active gate signal had full data every day.

SCORE_WRITE_FROZEN behaved as intended, zero of 77 rows carry a Score.

The two regime hypothesis is confirmed but the cutover is 2026-07-15, not 2026-07-22. Scope detail in TASK-238.

One thin day, 2026-07-17 at 12 rows against a median of 25.

REMAINING: per metric missing rates beyond MxV were not measured. The scan volume drop is filed as TASK-245.
