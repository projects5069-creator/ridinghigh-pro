---
id: TASK-183
title: DropsLab drops_post freshness alert (collector stall >2d)
status: To Do
assignee: []
created_date: '2026-06-15 20:51'
updated_date: '2026-06-16 16:20'
labels:
  - monitoring
dependencies: []
ordinal: 186000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
FINDING 2026-06-16 (read-only health check, market-open): DropsLab drops_post is STALE — newest scan_date=2026-06-05, ~7 trading days behind today (16/6). Collector workflow itself RAN success on 15/6 (post TASK-144 fix), but no scan_dates after 6/5 landed. Also: anomalous 698-row spike on 6/5 (vs ~80-200/day norm). Hypotheses NOT investigated (deferred): (1) ripeness lag — but 6/9 should be ripe by 16/6, doesn't fully explain; (2) TASK-144 drain mis-stamped 698 rows as 6/5; (3) scanner found no drops 6/6-6/15 (drops_raw empty). NEXT: dedicated session — compare drops_raw vs drops_post for 6/6-6/16 + trace origin of the 698 rows. This is the freshness gap 183 exists to catch.
<!-- SECTION:NOTES:END -->
