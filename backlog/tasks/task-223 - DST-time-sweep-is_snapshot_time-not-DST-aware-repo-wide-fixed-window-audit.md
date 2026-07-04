---
id: TASK-223
title: 'DST time-sweep: is_snapshot_time not DST-aware + repo-wide fixed-window audit'
status: Done
assignee: []
created_date: '2026-07-04 01:48'
updated_date: '2026-07-04 15:07'
labels: []
dependencies: []
priority: high
ordinal: 229000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S3 (3/7): auto_scanner:76-78 is_snapshot_time = hardcoded 14:55-15:05 Peru — NOT DST-aware. In winter (EST, close=16:00 Peru) the 14:59 daily_snapshot fires an HOUR BEFORE close → mid-session data in end-of-day columns. Fix: derive window from America/New_York close like a0d63fe (is_market_hours/is_day_complete). This is the SECOND instance of this bug class → include a repo-wide sweep of fixed time-windows (known cosmetic leftovers: dashboard.py:1309/:1603 captions, morning_health_check.py:57/:133 prints, enrich_post_analysis.py:167 legacy default; MARKET_OPEN_HOUR_PERU config:180 print-only). DEADLINE: before 2026-11-01 (EST switch). Evidence: plans/stateless-seeking-sifakis.md S3.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 is_snapshot_time derives its window from the ET close (DST-aware), TDD with summer+winter anchors
- [x] #2 repo-wide sweep of hardcoded Peru-time windows documented: each site fixed or explicitly marked display-only
<!-- AC:END -->
