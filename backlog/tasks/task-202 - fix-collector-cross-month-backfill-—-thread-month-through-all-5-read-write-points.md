---
id: TASK-202
title: >-
  fix: collector cross-month backfill — thread month through all 5 read/write
  points
status: To Do
assignee: []
created_date: '2026-06-28 23:47'
labels: []
dependencies: []
ordinal: 208000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post_analysis_collector.run() resolves every sheet op to the CURRENT month, so a historical cross-month --date backfill reads/writes the wrong monthly tab. Discovered during TASK-200 June backfill; June only worked because current month was June (all 5 points agreed by coincidence). A read-only fix is dangerous: it would build past-month rows and save them into the current-month tab = misplaced data.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 run() derives month from target_date and passes it to all sheet reads (daily_snapshots:396 + timeline_live fallback:411 + timeline_live stats:454)
- [ ] #2 load_post_analysis_from_sheets(month=None) + save_post_analysis_to_sheets(df, month=None) + _get_post_analysis_ws(gc, month=None): signature change, month targets the correct monthly tab
- [ ] #3 historical cross-month --date reads AND writes the target-month tab (candidates>0 and rows land in the target month, not current)
- [ ] #4 month=None preserves current-month default; live EOD collector + dashboard unaffected (regression focus)
- [ ] #5 TDD: RED documents that today save/load resolve to current-month regardless of target_date
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Context: surfaced by TASK-200 backfill (commit 96de9f0). 5 broken points all default to current month: collector:396/411/454 (reads), :461 load, :617 save; load/save route via _get_post_analysis_ws (gsheets_sync:52) -> get_worksheet(no month). May/April backfill returned 0 candidates (read June tab). Documented debt; not started.
<!-- SECTION:NOTES:END -->

## ABSORBS TASK-11, 2026-08-04

TASK-11 closed as a merge into this task. Same root stated at two levels.

11 said the dashboard and analytics cannot aggregate across months because each month is siloed in its own sheets_config entry. This task is the concrete version: five read and write points in post_analysis_collector.run that all resolve to the current month, with acceptance criteria and a TDD requirement already written.

Scope note: the same month scoping breaks ticker_follow_up on the first trading day of every month, because it filters timeline_live of the active month for days earlier than today and finds none. Recorded in the audit note on TASK-124.
