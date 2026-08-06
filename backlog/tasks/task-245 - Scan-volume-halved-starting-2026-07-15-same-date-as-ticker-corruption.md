---
id: TASK-245
title: 'Scan volume halved starting 2026-07-15, same date as ticker corruption'
status: Done
assignee: []
created_date: '2026-07-29 09:28'
updated_date: '2026-08-05 20:32'
labels:
  - bug
  - data-integrity
dependencies: []
priority: medium
ordinal: 243000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29 from daily_snapshots 2026-07, rows per scan day.

OBSERVED: through 2026-07-14 the daily row count runs 80, 46, 68, 34, 25, 59, 42, 36, 55. From 2026-07-15 onward it runs 23, 14, 12, 20, 38, 20, 18, 14, 22, 28. Median falls from roughly 46 to roughly 20. The break lands on exactly the same scan day as the first confirmed doubled letter tickers.

WHY THIS MATTERS: fewer rows per scan means a smaller candidate universe reaching the gate, which changes how many ENTER opportunities exist per day and therefore any per day rate computed over July. 2026-07-17 is the thinnest day at 12 rows, under half the July median.

TWO COMPETING EXPLANATIONS, NEITHER VERIFIED: (a) same root as the finviz parse change, where a corrupted row fails downstream and is dropped, so the loss is an artifact; (b) a genuine change in market breadth or in what the scanner filter admitted. These have opposite implications and the distinction must be measured, not assumed.

SCOPE: compare row counts against the raw finviz result count per scan if it is recorded anywhere, and check whether any drop or exception path silently discards rows. Blocked in practice on the ticker corruption scope.
<!-- SECTION:DESCRIPTION:END -->

## AUDIT NOTE 2026-08-03

Two things from the write audit that bear on this task.

FIRST, the premise may no longer hold. daily_snapshots rows per trading day: 2026-07-29 had 57, 2026-07-30 had 145, 2026-07-31 had 57, and 2026-08-03 had 85. Volume today is above the late July level, not halved. Either the drop reversed or it was never a sustained halving. Re-measure before investigating a cause.

SECOND, a concrete candidate for volume variance that was not in the task. auto_scanner.py wraps the per ticker analysis loop and the loop around it in bare handlers, lines 413 to 416:

                    except:
                        pass
    except:
        pass

A failure part way through the scan therefore produces a short result set with no error, no log line and a successful workflow conclusion. auto_scanner.py carries 5 bare except clauses and 7 handler bodies that are pass, continue or return with no logging. Every other write path module is clean by comparison: orchestrator, orchestrator_eod, post_analysis_collector and order_manager have zero bare handlers and log through except Exception.

NOT VERIFIED: whether those handlers actually swallow anything in practice. Proving it needs instrumentation, a counter or a log line on each swallow, run over a full trading day. That measurement should come before any theory about the volume.

## ABSORBS TASK-227, 2026-08-04

TASK-227 closed as a merge into this task. Same pattern, same file.

227 covers load_mc_cache and save_mc_cache at auto_scanner.py lines 108 and 117, whose bare except at lines 113 and 122 hide the fact that the cache loads empty and saves to a discarded path on every CI run. That is two of the five bare handlers this task already records, and the fix is the same: replace bare handlers with logged warnings so a swallow becomes visible.

The open question from 227 travels with it: make the cache path workspace relative and persist it, or document it as local development only.

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
MEASURED 2026-08-05 — CLOSED. The premise does not hold.

Source: reports/2026-08-05_1455_measurement.md Q-245 (one-pass read after the close,
no writes).

daily_snapshots rows per day:
  2026-07  total 913 rows over 22 days   median 35.0 rows/day
  2026-08  total 269 rows over  3 days   median 85   rows/day

Volume did not merely recover after the finviz DOM fix of 2026-07-29 (TASK-238) — the
August median is 2.4x the July median. Within July itself the series runs 80/68/59 early,
bottoms at 23/14/12 on 07-15..07-17, and returns to 57/145/57 from 07-29 onward.

Both competing hypotheses in this ticket are therefore moot:
  - "same root as the ticker corruption" cannot be tested against a volume that is now
    above the pre-drop level;
  - "a second unidentified cause" has no surviving symptom to attach to.
Nothing measurable remains open here. Reopen only if a fresh drop appears.
<!-- SECTION:NOTES:END -->
