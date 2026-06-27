---
id: TASK-190
title: Isolate OHLC backfill from post_analysis collector to fix 15min job-timeout
status: Done
assignee: []
created_date: '2026-06-24 02:00'
updated_date: '2026-06-27 15:27'
labels: []
dependencies: []
priority: high
ordinal: 196000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Root-cause (docs/DIAGNOSIS_post_analysis_2026-06-23.md): the collect job in post_analysis.yml has timeout-minutes:15. Steps 1-7 (checkout/setup/EOD-snapshot/collector/enrich) take ~7-8min, leaving too little for the final "Backfill missing OHLC" step (backfill_ohlc_v2.py --recent 2 --apply). As the month accumulates post_analysis rows (per-row fetch_ohlc network call + time.sleep(0.4)), backfill runtime grows and the whole job hits the 15min ceiling -> GitHub kills it -> backfill step = cancelled. Evidence: every cancelled run ends at exactly 15m17-19s; logs show "##[error]The operation was canceled" mid-backfill (runs 28060995599, 27724742617). Failing most trading days since ~2026-06-16; collector/enrich themselves succeed, only backfill is cut. Solution (Option B - decouple): move OHLC backfill into its own GitHub Actions workflow (e.g. backfill_ohlc.yml) with its own generous timeout (20-25m), scheduled by cron AFTER the collector finishes (collector cron 5 21 * * 1-5 = 16:05 Peru -> backfill a later UTC slot, Mon-Fri); collector workflow drops its final backfill step. No change to backfill logic itself, only where/when it runs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 post_analysis collector workflow completes under its timeout on trading days (backfill step removed from the collector job; no more cancelled runs)
- [ ] #2 OHLC backfill runs independently in its own workflow on a later cron, with its own timeout (20-25m), Mon-Fri after the collector
- [ ] #3 A backfill failure/timeout does NOT cancel or fail the collector run (decoupled separate workflows)
- [ ] #4 PK updated per Anti-Drift Contract (collector loses backfill step + new backfill workflow documented in the workflows section) + version bump + changelog
- [ ] #5 Rows that previously lacked OHLC get backfilled within a few days of the new workflow running (verify the ~87% TP10_Hit/MaxDrop% fill-rate gap closes - outcome, not just mechanism)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC#5 verified 2026-06-27 (Sat) via dry-run re-check: REAL-GAP fillable=0. CLWT 2026-06-17 D5 (open as of 6/26) was filled by the Fri 6/26 16:45 Peru backfill run — end-to-end outcome confirmed (fillable 1->0 across scheduled run). May=0 stable. Only remainder: HSPT 2026-06-11 = known-unfillable (yfinance/Alpaca return empty, delisted/no-data) — documented, not a backfill failure. Gap closed for all fillable rows.
<!-- SECTION:NOTES:END -->
