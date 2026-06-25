---
id: TASK-193
title: >-
  Quota C5 (AC#1) — jitter agent_market_context read off top-of-minute to avoid
  429 collisions
status: Done
assignee: []
created_date: '2026-06-24 14:11'
updated_date: '2026-06-24 20:16'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-24. Jitter agent_market_context.yml hourly cron '0 14-20' -> '23 14-20' (YAML-only, single line; OPEN run '30 13' market-open untouched). Root: AC#1 documented 14.8%/30d fail from top-of-hour 429 collisions (run 27293631392) — :00 is the GH-Actions hour-boundary batch + the stacked '0 ...' crons. :23 is a free minute across 14-20 UTC (not :00 cluster, not :07 = '7 13-21', not :30 = '30 20'). Removes the :00 spike. The */1 floor (agent_minute + auto_scan, every minute) remains unavoidable but is the steady baseline that safe_append_row's existing 429-retry absorbs; won't reach 0% but removes the documented spike. No code/logic/write change; no live trigger (RULE #6) — effective on the next scheduled run after push. Not committed yet — accumulating with TASK-192 (shared PK bump).
<!-- SECTION:NOTES:END -->
