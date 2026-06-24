---
id: TASK-193
title: >-
  Quota C5 (AC#1) — jitter agent_market_context read off top-of-minute to avoid
  429 collisions
status: To Do
assignee: []
created_date: '2026-06-24 14:11'
labels:
  - agent
  - infra
  - quota
dependencies: []
priority: medium
ordinal: 199000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Spawned by TASK-136 audit, satisfies TASK-136 AC#1. agent_market_context 14.8%/30d fail rate from top-of-hour 429 collisions (run 27293631392): many workflows contend on the exact minute boundary. Offset/jitter the market_context Sheets read a few seconds, or wrap in the existing 429 retry. Note: the 'scanner reads 5-13/run vs counter=1' is NOT a bug — record_read counts only cache misses; cache hits are free (sheets_manager:432). TDD + PING-PONG.
<!-- SECTION:DESCRIPTION:END -->
