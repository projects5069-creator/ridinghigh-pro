---
id: TASK-232
title: 'morning_health_check:55-56 market-open 08:30 hardcoded (DST) — diagnostic'
status: Done
assignee: []
created_date: '2026-07-05 17:17'
updated_date: '2026-08-04 00:32'
labels: []
dependencies: []
ordinal: 238000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Same DST class as TASK-231. Market-open threshold hardcoded 08:30 Peru; wrong in winter (09:30). Diagnostic-only print. Derive from ET.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-222, 2026-08-04

Closed as a merge. Same DST root as TASK-222 and TASK-233, and the three are one commit.

Verified live 2026-08-04: MARKET_CLOSE_HOUR_PERU is defined twice, config.py line 185 and utils.py line 58, dashboard._is_day_complete sits at dashboard.py line 1922, and close_peru is derived in four places. Fixing them separately means touching the same idea three times.

Deadline note carried to 222: the next DST transition is November, so the winter case starts failing then.
