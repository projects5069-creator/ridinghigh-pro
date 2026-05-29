---
id: TASK-28
title: SENT.2 — Verify scan_freshness on 26-5 first market day
status: Done
assignee: []
created_date: '2026-05-24 19:25'
updated_date: '2026-05-29 17:04'
labels: []
dependencies: []
priority: high
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
First market day after the lex-compare bug fix (commits 5cc658b + 2ef7ceb). Verify scan_freshness BLOCK rate is below 5% on 2026-05-26 (Tuesday, post-Memorial Day).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
VERIFIED 2026-05-29: lex-compare fix (5cc658b/2ef7ceb) confirmed — scan_freshness BLOCKs fell 2125 (21/5) -> 42 (26/5) -> 0 (29/5). The 5% threshold is unmeasurable (sentinel_events stores no ALLOW denominator). The 28/5 spike (1222 STALE_SCAN) is a SEPARATE mechanism: CRON_DRIFT scanner stall (scan_age median 12min, OUTAGE shows scan_time frozen), NOT a lex-compare regression. Sentinel responded correctly. Stall tracked in TASK-57.
<!-- SECTION:NOTES:END -->
