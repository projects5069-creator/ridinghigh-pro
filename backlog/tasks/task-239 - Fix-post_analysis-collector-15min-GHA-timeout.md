---
id: TASK-239
title: Fix post_analysis collector 15min GHA timeout
status: Done
assignee: []
created_date: '2026-07-28 12:40'
updated_date: '2026-08-04 00:32'
labels:
  - bug
  - perf
dependencies: []
ordinal: 243000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post_analysis.yml timeout-minutes:15. Runs cancelled 23/7, 24/7, 27/7 at 15m1Xs; also 23/6. Time burned in the collector step: yfinance_provider.py:316 yf.Ticker(ticker).info blocks ~18s per dead symbol, no timeout, no skip-cache, no dedup; called once per row plus sleep 0.3 at :632. Same failure class as TASK-190. Independent of the finvizfinance root: fixing perf alone returns the job under 15 minutes. Consider raising timeout-minutes as an interim palliative before month end. Verify against the next scheduled run.
<!-- SECTION:DESCRIPTION:END -->

## MEASURED 2026-07-30

The palliative from 28/7 held but the trend is against it. Collector duration went 23m25s on 28/7 to 26m23s on 29/7, roughly 3 minutes per day, against a 30 minute ceiling. Straight-line projection put the next run at 29.4m and the one after at 32.3m, so the second-next run would have been cancelled. Raised to 45 today.

backfill_ohlc raised from 25 to 40 as headroom, NOT because the data demanded it. Its duration was measured today for the first time: last ten runs span 8m53s to 18m22s, and the last two went 18m22s down to 15m28s, so it had about 38 percent headroom under the old ceiling. The raise is insurance in case the collector trend reaches it, since it reads the same July rows through recent_months 2.

The TASK-238 ticker fix did NOT reduce the runtime. It stops new phantom rows but the 35 existing ones in July are still read every run, and each unresolvable symbol blocks yf.Ticker().info for about 18 seconds, so roughly 10 minutes per run is pure waste. Marking those rows under TASK-246 is the actual fix for the runtime, not a cleanup task.

Still not addressed and still the real risk: no timeout on the provider call, no skip cache for dead symbols, no dedup, and post_analysis_collector.py:638 saves a single batch after the loop so a cancelled run loses the whole day. Exposure is limited to two runs, since from 1/8 the active month becomes 2026-08 and post_analysis starts empty, but backfill keeps touching July via recent_months 2.

Note on scope: the 30 minute ceiling covered three steps, not just the collector. EOD Snapshot, Run Post Analysis Collector and Enrich with Intraday Data all share the one job budget, so the 26m23s figure is the whole job.

DECISION: this task stays open. The ceiling is a second palliative, not a fix.

## AUDIT 2026-08-03: PREMISE STALE, SUPERSEDED

The title says 15min timeout. The ceiling has been 45 since 2026-07-30 and 30 since 28/7, so a timeout is no longer the problem being solved. Both raises were palliatives on a symptom.

The measured cause is that the collector reprocesses the whole month every night: select_candidates at post_analysis_collector.py:78 filters on MxV with no date bound, and COLLECT_DAYS_FORWARD of 25 from the 2026-06-13 cutoff means no row can complete inside a month. Four runs, zero skips in all of them.

Moved to TASK-249 with the correct framing. This task should be closed or merged rather than worked as written.

## MERGED INTO TASK-249, 2026-08-04

Closed as a merge, not as completed work. The remaining scope moved to TASK-249.

Same code, verified: post_analysis_collector.py line 78 select_candidates and COLLECT_DAYS_FORWARD at line 55. TASK-249 measured the mechanism on 2026-08-03 and the verdict was ROOT_CONFIRMED: 4 candidates ran in 48 seconds against 89 candidates in 22.9 minutes. This task describes a 15 minute ceiling that has been 45 since 30/7.

CARRIED TO 249: nothing new, 249 already holds the mechanism and the measurement.

NOT CARRIED, recorded here so it is not lost: three gaps this task raised that 249 does not cover. There is no timeout on the provider call, no skip cache for dead symbols, and no dedup, and post_analysis_collector.py line 638 saves a single batch after the loop so a cancelled run loses the whole day. If any of those matters later, open a task for it rather than reopening this one.
