---
id: TASK-259
title: agent_minute runs overlap — account state snapshot is stale by design
status: To Do
assignee: []
created_date: '2026-08-05 20:34'
updated_date: '2026-08-05 20:34'
labels:
  - bug
  - agent
  - concurrency
  - hyp-002
  - measured
dependencies: []
priority: high
ordinal: 257000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-05: agent_minute has a 60s cron but a median run duration of 292s, so 92.5 percent of consecutive run pairs overlap. build_account_state snapshots once per run before the signal loop, so a later run can decide against a world that predates an earlier run's ENTER. Produced two re-entry cap breaches on 2026-08-05 (DFNS, SHPH). Different root from TASK-244. Full evidence in Implementation Notes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-08-05 from 400 agent_minute runs of that day. Full evidence:
reports/2026-08-05_1515_reentry_breach.md.

THE MEASUREMENT
  gh run list --workflow=agent_minute.yml, all 400 runs dated 2026-08-05:
    duration s: min=34  p25=136  median=292  p75=321  max=370
    runs longer than 60s: 366 of 400 (91.5 percent)
    consecutive pairs where run N+1 STARTS before run N ENDS: 369 of 399 (92.5 percent)
The cron is every minute. The median run takes 292 seconds. Overlap is the normal state,
not an exception.

THE MECHANISM
build_account_state is called ONCE at the start of a run (agent/orchestrator.py:608-670),
before the signal loop at :721, and the resulting snapshot serves every signal in that
run. When runs overlap, a later run's snapshot can predate an earlier run's decision.
Filters 7 through 10 in decision_logic._check_filters then evaluate a world that has
already changed. This is a time-of-check to time-of-use gap BETWEEN PROCESSES: there is
no lock and no mechanism preventing two concurrent runs from deciding on the same ticker.

WHAT IT PRODUCED ON 2026-08-05
Two breaches of the re-entry cap (the frozen config allows at most 1 entry per ticker per
day):
  DFNS  ENTER 09:32:29 and 09:32:54   (25 seconds apart)
  SHPH  ENTER 11:40:39 and 11:43:55   (3 min 16 s apart)
In both pairs ColdStartConcurrentLeft and ColdStartDailyLeft are IDENTICAL between the two
entries (DFNS 5/7 and 5/7; SHPH 5/5 and 5/5). Had the first entry been visible they would
have decremented. The snapshot predates the event.

DFNS is conclusive. Three runs were active at the instant of ENTER #1, started at
09:30:08, 09:31:02 and 09:32:03. ALL THREE started before ENTER #1 was decided at
09:32:29. Whichever of them decided ENTER #2, its account snapshot could not contain the
first decision. DFNS position #1 opened 09:32:31 and closed 10:45:06 while position #2
opened 09:32:55 — 72 minutes of genuine simultaneous exposure on one ticker, not the
open-then-reenter case documented in TASK-107.

DIFFERENT ROOT FROM TASK-244. On 2026-07-22 build_account_state failed under a Sheets 429
and returned defaults. On 2026-08-05 there was no 429 and no ACCOUNT_STATE_UNAVAILABLE
anywhere in the day, while REENTRY_LIMIT fired 269 times and EXISTING_POSITION 48 times.
The reads succeeded; the guards ran; the input was simply older than the event. F6b
(decision_logic.py:428) closes the 429 path and does not touch this one.

CONSEQUENCE FOR HYP-002. The run re-registered on 2026-08-03 states that another breach of
the re-entry cap voids it (docs/HYPOTHESES.md section F). Two breaches are already in the
sample at n=17 of 150.

SHPH IS PARTLY A SECOND BUG. The first SHPH ENTER, DecisionID
DEC-2026-08-05-SHPH-114039-09, produced NO paper_portfolio row at all. Only the second
wrote one. Even a fresh snapshot would not have found it in the paper_portfolio source.
That belongs to the TASK-105 / TASK-106 / TASK-198 class.

NOT ESTABLISHED, do not assume:
  - 396 of the 400 runs are workflow_dispatch and only 4 are schedule. What triggers them
    was not investigated.
  - Whether the same overlap explains the timeline_live duplicates in TASK-253 (931
    duplicate (ScanTime, Ticker) pairs over three days). auto_scan.yml was not examined.
  - Which specific run made each decision. Three candidates for DFNS, five for SHPH; run
    logs were not opened.
  - Why only one run appeared in skip_summary during the 11:36-11:48 window while five
    were active.

No fix is proposed here by design.
<!-- SECTION:NOTES:END -->
