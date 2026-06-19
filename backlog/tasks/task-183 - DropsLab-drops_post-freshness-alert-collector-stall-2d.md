---
id: TASK-183
title: DropsLab drops_post freshness alert (collector stall >2d)
status: Done
assignee: []
created_date: '2026-06-15 20:51'
updated_date: '2026-06-18 22:36'
labels:
  - monitoring
dependencies: []
ordinal: 186000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
FALSE ALARM verified (deep falsification). collector healthy since TASK-144 (6/15): drops_post newest=6/9 is CORRECT — structural D5-ripeness lag, 100% coverage 5/20-6/9 (positive evidence, zero gap/partial). 6/10 ripe only as of 6/18 (D5=6/17), first eligible run is tonight. 698-spike on 6/5 = real broad down-day (698 unique tickers all >=10% drops, zero dupes), not corruption; penny-artifacts handled by Option B exclude. Pending: verify 6/10 enters tonight's run (closes the loop). 698 sampling-weight -> robustness check in TASK-179.
<!-- SECTION:NOTES:END -->
