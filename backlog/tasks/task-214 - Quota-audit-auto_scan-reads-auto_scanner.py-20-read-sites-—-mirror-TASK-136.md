---
id: TASK-214
title: Quota audit auto_scan reads (auto_scanner.py 20 read-sites) — mirror TASK-136
status: To Do
assignee: []
created_date: '2026-06-30 17:05'
labels:
  - quota
  - performance
  - market-hours
  - recon-done
dependencies: []
priority: medium
ordinal: 220000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Recon 30/6 (read-only) identified the remaining market-hours 429 driver after TASK-58 closed health_audit out of contention. health_audit is NOW fully off the shared SA (dedicated HA SA) AND moved off-hours (cron 06:00+15:30 Peru). Remaining per-minute consumers on the shared commercial SA (project 591299446687): auto_scanner.py (20 read-sites, every minute via auto_scan) + agent/orchestrator.py (13 sites, agent_minute — already audited+cut in TASK-136 Done). auto_scanner.py was NEVER quota-audited and is now the heaviest un-optimized market-hours reader. AC#1: map all 20 read-sites in auto_scanner.py (file:line + what each reads + frequency). AC#2: identify redundant/cacheable per-minute reads (same pattern TASK-136 used for position_manager). AC#3: propose cuts (cache TTL / consolidate / row_count-instead-of-full-read) — propose only, do NOT implement here. evidence: 429 observed live 30/6 (dashboard Post Analysis/Score Tracker) — shared-SA exhaustion in market hours, NOT health_audit. NOTE: dashboard.py Score pages (14 sites) belong to TASK-209 Score-demotion, not here. distinct from TASK-213 (which measures health_audit's own 429 post-TASK-58). MEDIUM — does NOT break live system (agent works through backoff); only dashboard+CLI reads suffer.
<!-- SECTION:DESCRIPTION:END -->
