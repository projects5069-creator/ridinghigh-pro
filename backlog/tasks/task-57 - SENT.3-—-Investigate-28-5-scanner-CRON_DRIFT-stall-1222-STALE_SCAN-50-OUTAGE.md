---
id: TASK-57
title: >-
  SENT.3 — Investigate 28/5 scanner CRON_DRIFT stall (1222 STALE_SCAN + 50
  OUTAGE)
status: Done
assignee: []
created_date: '2026-05-29 17:16'
updated_date: '2026-05-29 20:24'
labels: []
dependencies: []
priority: high
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate 28/5 scanner stall. From 09:53 Peru the scanner lagged 10-24min (scan_age median 12), producing 1222 STALE_SCAN BLOCKs + 50 CRON_DRIFT_OUTAGE events, escalating through the afternoon. Root is NOT the 429 fix (commit 8e3c9ad landed 20:48, ~11h after spike start). Suspects: cron timing of auto_scan/agent_minute on 28/5, and kernel hooks deployed that morning (eb4ac15 13:34 integrity guard; 24708f5 14:41 UserPromptSubmit skill enforcement) possibly slowing orchestrator startup past the per-minute window. 28/5 events cached at /tmp/sentinel_events_full.csv. 29/5 is clean (0 BLOCKs) so not currently active.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done 2026-05-29 (investigated via systematic-debugging, closed as documented one-off). FINDINGS: 28/5 was a clear OUTLIER — 50 CRON_DRIFT_OUTAGE + 1222 STALE_SCAN vs 2/2/5 on 26-27-29 May (~25x neighbors); max gap 20min, 14 distinct stall windows vs 1-2 normal. NOT the 429 fix (8e3c9ad landed 20:48, ~11h after the 09:53 spike). NOT a catch-up regression (TASK-16 catch-up is observability-only; Phase 2 deferred by design). Concentrated in peak hours (12-14h = 41/50), pointing to load/contention — likely correlated with the same-day 429 read-quota peak. TRIGGER UNVERIFIABLE: 28/5 workflow logs aged out of GH Actions; evening-27/5 commits touch logging/agents, not orchestrator startup. NOT RECURRING: 29/5 already clean (OUTAGE 50->5, STALE_SCAN ->0). TASK-58 (separate SA) will cut the load that likely contributed. Decision: do not chase an unverifiable non-recurring one-off.
<!-- SECTION:NOTES:END -->
