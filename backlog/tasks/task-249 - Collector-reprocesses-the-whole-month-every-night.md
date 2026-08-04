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

## MEASURED 2026-08-03, VERDICT ROOT_CONFIRMED

THE PREDICTION, written before the run and not adjusted afterwards: August opened with an empty post_analysis tab, so the first collector run of the month was the one free measurement. Under eight minutes confirms that runtime scales with the accumulated month to date candidate count. Around twenty seven minutes refutes it and sends the investigation back to step one.

THE RESULT, run 30857866152, created 2026-08-03T22:14Z:
  total run              101 seconds, 1.7 minutes
  Run Post Analysis Collector step   22:14:44 to 22:15:32, 48 seconds
  Enrich with Intraday Data          22:15:32 to 22:15:42, 10 seconds

THE MECHANISM, and this is the part that matters more than the duration:
  daily_snapshots read      85 rows      against 913 on 07-31
  candidates MxV <= -100     4           against 89 on 07-31
  Processing                 4           equal to the candidate count, as on every prior night
  Complete skip              0           the skip path still never fires
  already exists             0
  attempt errors             0
  429 lines                  0
  rows written               4

The five nights now line up on one straight line. 07-15: 43 candidates, 8 minutes. 07-21: 56, 11. 07-28: 77, 23. 07-31: 89, 27. 08-03: 4, 1.7. Cost per candidate is roughly constant, about 12 seconds tonight against about 15 on 07-31, and the total is that cost multiplied by the number of candidates the month has accumulated so far. daily_snapshots resets on the first of the month, so the candidate set resets with it, and the runtime resets with that.

WHAT THIS RULES OUT: the alternative reading was that phantom tickers were burning time in fetch_ohlc_for_days, five retries with two second sleeps each and no printed error. Tonight had zero attempt errors and zero 429 lines, and the run was still fast, so that path is not needed to explain anything. It may still contribute on a contaminated day but it is not the driver.

WHAT THIS DOES NOT PROVE: this is one measurement at the extreme low end of the range. The model would be fully confirmed by watching August climb back through the same slope. At the July accumulation rate, about 4.2 candidates per trading day, August should end near 88 candidates and roughly 19 minutes, still under the 45 minute ceiling. If the scan volume rises, the ceiling comes closer.

NO FIX CHOSEN. The three options in the description above stand as written: bound select_candidates by date, make is_complete horizon aware so a row can settle at D5 for classification purposes, or cache the settled rows. Each changes what the research dataset collects, so each needs TDD and a before and after run comparison. Status unchanged.

## ABSORBS TASK-239, 2026-08-04

TASK-239 closed as a merge into this task. Same code, and this task holds the measurement that 239 was missing.

Three gaps 239 raised that this task does NOT cover, recorded so they are not lost: no timeout on the provider call, no skip cache for dead symbols, no dedup, and post_analysis_collector.py line 638 saves a single batch after the loop so a cancelled run loses the whole day. None of them is the runtime driver, which is why they stayed out of the fix options above, but they are real.
