---
id: TASK-130
title: >-
  trading_days_after holiday-aware — weekday-only calc strands holiday-slot rows
  (Good Friday, Memorial Day; Independence Day 2026-07-04 next)
status: To Do
assignee: []
created_date: '2026-06-10 01:57'
labels: []
dependencies: []
priority: high
ordinal: 133000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
sheets_manager.trading_days_after (line ~646) counts weekdays only, no exchange-holiday calendar. Rows scanned before a holiday get a D-day pointing at a closed session that never has data -> stranded PENDING forever. 13 such rows from Apr 3 / May 25 already stuck (+SBLX delisted separate). Deadline: fix before 2026-07-04 to avoid a third batch. Likely fix: use pandas_market_calendars (already a dep, used by utils.is_trading_day) or align with the holiday-aware helper; also needs one-time realignment/backfill of the 13 stranded rows after the fix.
<!-- SECTION:DESCRIPTION:END -->
