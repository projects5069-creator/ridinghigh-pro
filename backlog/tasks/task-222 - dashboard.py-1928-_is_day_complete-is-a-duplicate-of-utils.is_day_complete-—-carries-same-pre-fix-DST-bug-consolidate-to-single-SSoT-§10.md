---
id: TASK-222
title: >-
  dashboard.py:1928 _is_day_complete is a duplicate of utils.is_day_complete —
  carries same pre-fix DST bug; consolidate to single SSoT (§10)
status: To Do
assignee: []
created_date: '2026-07-02 19:52'
labels:
  - tech-debt
  - dst
dependencies: []
priority: medium
ordinal: 228000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
utils.is_day_complete fixed in TASK-211 to derive close from 16:00 ET. dashboard._is_day_complete still hardcodes 15:00 Peru -> same winter EST bug. Also MARKET_CLOSE_HOUR_PERU defined twice (config.py:185 + utils.py:58). Consolidate.
<!-- SECTION:DESCRIPTION:END -->
