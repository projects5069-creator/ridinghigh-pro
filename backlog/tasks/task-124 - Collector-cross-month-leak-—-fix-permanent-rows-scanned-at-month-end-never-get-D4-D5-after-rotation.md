---
id: TASK-124
title: >-
  Collector cross-month leak — fix permanent: rows scanned at month-end never
  get D4/D5 after rotation
status: Done
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-11 00:14'
labels: []
dependencies: []
priority: high
ordinal: 127000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post_analysis_collector candidates come from active-month daily_snapshots/timeline_live only, so prior-month incomplete rows are never re-processed. Recurs every month-end. Options: collector also loads prior-month post_analysis incompletes, or monthly scheduled backfill step in post_analysis.yml. Depends on backfill_v2 learnings.
<!-- SECTION:DESCRIPTION:END -->

## AUDIT NOTE 2026-08-03: THE PATTERN IS WIDER THAN THIS TASK RECORDS

This task closed on the collector. The same month scoping affects ticker_follow_up, which was not mentioned.

auto_scanner.update_ticker_follow_up reads timeline_live for the active month only, filters to Date earlier than today, and writes a row only when follow_day falls between 1 and 3. On the first trading day of a month the active tab holds no earlier day, so the function returns without writing. Measured: the 2026-08 ticker_follow_up tab holds zero rows while 2026-07 holds 25867.

The blind window is exactly one trading day and it heals on the second. What does not heal is the follow up owed to tickers scanned near the end of the previous month: a ticker first seen on 2026-07-31 should have been followed on the first three trading days of August and never will be, because its history lives in the July tab.

Recorded here rather than filed separately, since it is the same root as this task and the same root as TASK-202. Status unchanged.
