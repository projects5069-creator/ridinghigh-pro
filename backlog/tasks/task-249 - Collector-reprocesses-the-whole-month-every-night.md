---
id: TASK-249
title: Collector reprocesses the whole month every night
status: To Do
assignee: []
created_date: '2026-08-03 16:52'
labels:
  - bug
  - perf
dependencies: []
priority: high
ordinal: 247000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-03 from four run logs. This is the cause behind TASK-239, which two ceiling raises only masked.

Evidence, four nights: 15/7 had 43 candidates and ran 8 minutes. 21/7 had 56 and ran 11. 28/7 had 77 and ran 23. 31/7 had 89 and ran 27. Every one of those runs reported Processing equal to the candidate count and CompleteSkip zero. Nothing is ever skipped, so the work is the running total of the month, not the new rows of the day.

Two mechanisms combine. select_candidates at post_analysis_collector.py:78 filters daily_snapshots on MxV alone with no date bound, so it returns every candidate the month has ever produced. And is_complete cannot return true inside the same month, because COLLECT_DAYS_FORWARD is 25 from the cutoff of 2026-06-13 while a month holds about 21 trading days, so no row reaches its full horizon before the month ends.

Consequence: runtime grows with the month and resets on the first. The 3/8 run is the first on an empty August sheet and is the free measurement. If it drops back to 8 to 11 minutes, the growth is confirmed as month size rather than candidate count.

Not verified: the real per symbol cost on the alpaca path, and whether fetch_ohlc_for_days at :216 with five retries and two second sleeps dominates or whether the sheet reads at :415 and :469 do.

Options to weigh, none chosen: bound select_candidates by date, make is_complete horizon aware so a row settles at D5 for classification purposes, or cache the settled rows. Any change alters what the research dataset collects and needs TDD plus a before and after run comparison.
<!-- SECTION:DESCRIPTION:END -->
