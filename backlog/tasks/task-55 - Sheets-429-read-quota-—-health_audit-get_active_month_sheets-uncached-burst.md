---
id: TASK-55
title: Sheets 429 read-quota — health_audit get_active_month_sheets uncached burst
status: Done
assignee: []
created_date: '2026-05-29 01:42'
updated_date: '2026-05-29 17:48'
labels: []
dependencies: []
ordinal: 55000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ROOT (6-round recon 2026-05-28): health_audit calls get_active_month_sheets 11x/run; each does uncached gc.open_by_key (1-3 API calls) = up to 33 spurious reads vs Google 60/min/user cap. 3 failing checks (16/20/21) share _load_recent_metrics which calls it before the cached read. Amplified by retries=3 backoff + 17:00 UTC 4-workflow collision (agent_minute+auto_scan+market_context+health_audit). Emails 09:36 & 14:34 both CRITICAL on different checks (non-deterministic burst). FIX phase1: memoize get_active_month_sheets (11->1, 300s TTL, mirrors _HA_SHEET_CACHE). Deferred if needed: retries=3->1, move cron 0 17->0 16 UTC (12:00 Peru = market hours).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PHASE 2 (2026-05-29): root was the sentinel_events read in S1 (line 1347) exhausting the 3-retry/15s backoff during market-hours SA contention (3 minute-cadence workflows share one SA). Phase-1 memoize of get_active_month_sheets was correct but covered a different path. Cron move 17->16 UTC REJECTED — collision map shows 16 UTC equally crowded (auto_scan */1 13-19 + agent_minute */1 13-20 cover both). Fix: _ha_cached_read retries 3->5, backoff cap 40s (~115s total patience across >1 minute-window), TTL 300->600. Root-cause separate-SA solution tracked in TASK-58.
<!-- SECTION:NOTES:END -->
