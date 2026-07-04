---
id: TASK-222
title: >-
  dashboard.py:1928 _is_day_complete duplicates utils.is_day_complete —
  consolidate to single SSoT (§10)
status: To Do
assignee: []
created_date: '2026-07-02 19:52'
updated_date: '2026-07-04 01:50'
labels:
  - tech-debt
  - dst
dependencies: []
priority: medium
ordinal: 228000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
utils.is_day_complete fixed in TASK-211 to derive close from 16:00 ET. dashboard._is_day_complete (:1928) is a real §10 duplicate — consolidate to utils. CORRECTION (E2E-audit S5, 3/7): the duplicate does NOT carry the pre-fix 15:00-Peru DST bug — its semantics are 'day < today (Peru) AND weekday<5', i.e. conservative-safe (today never counts as complete → lags up to a day after close, never uses mid-session data). Still wrong to keep two implementations. Also MARKET_CLOSE_HOUR_PERU defined twice (config.py:185 + utils.py:58) — consolidate.
<!-- SECTION:DESCRIPTION:END -->
