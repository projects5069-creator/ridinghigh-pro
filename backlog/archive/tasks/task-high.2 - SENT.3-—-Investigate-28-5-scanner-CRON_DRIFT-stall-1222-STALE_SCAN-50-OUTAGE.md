---
id: TASK-HIGH.2
title: >-
  SENT.3 — Investigate 28/5 scanner CRON_DRIFT stall (1222 STALE_SCAN + 50
  OUTAGE)
status: To Do
assignee: []
created_date: '2026-05-29 17:09'
labels: []
dependencies: []
parent_task_id: TASK-HIGH
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate 28/5 scanner stall. From 09:53 Peru the scanner lagged 10-24min (scan_age median 12), producing 1222 STALE_SCAN BLOCKs + 50 CRON_DRIFT_OUTAGE events, escalating through the afternoon. Root is NOT the 429 fix (commit 8e3c9ad landed 20:48, ~11h after spike start). Suspects: cron timing of auto_scan/agent_minute on 28/5, and kernel hooks deployed that morning (eb4ac15 13:34 integrity guard; 24708f5 14:41 UserPromptSubmit skill enforcement) possibly slowing orchestrator startup past the per-minute window. 28/5 events cached at /tmp/sentinel_events_full.csv. 29/5 is clean (0 BLOCKs) so not currently active.
<!-- SECTION:DESCRIPTION:END -->
