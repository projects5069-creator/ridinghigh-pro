---
id: TASK-231
title: >-
  DST fix: enrich_post_analysis MinToClose + dashboard check_snapshot_time (SSoT
  dup)
status: To Do
assignee: []
created_date: '2026-07-04 14:58'
labels:
  - dst
  - ssot
dependencies: []
ordinal: 237000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AC#2 sweep of TASK-223 found two live DST bugs mis-labeled cosmetic. (1) enrich_post_analysis.py:167 hardcoded 15:00 close -> MinToClose off by 60min in winter (active via post_analysis.yml). (2) dashboard.py:1202 check_snapshot_time hardcoded 14:59-15:00 = SSoT sec.10 near-dup of is_snapshot_time. Fix: derive close from America/New_York (ref a0d63fe), TDD summer+winter each. Also update stale diagnostic string morning_health_check.py:133.
<!-- SECTION:DESCRIPTION:END -->
