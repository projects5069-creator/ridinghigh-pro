---
id: TASK-58
title: >-
  SENT/INFRA — Separate service account for health_audit to end 429 quota
  contention
status: To Do
assignee: []
created_date: '2026-05-29 17:48'
updated_date: '2026-06-26 15:50'
labels: []
dependencies: []
priority: medium
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Root-cause fix for the Sheets 429 read-quota contention (follows TASK-55 phase-2 mitigation). health_audit, agent_minute, and auto_scan all share ONE service account and collectively cross Google's 60 reads/min/user cap during market hours. Phase-2 added backoff patience but the structural problem remains. Solution: provision a SECOND service account dedicated to health_audit (and possibly market_context), share the 9+9 monthly sheets with it, add a new GH secret (e.g. GOOGLE_CREDENTIALS_JSON_HA), and point health_audit's gc at it. Removes health_audit from the trading SA's quota budget entirely. Effort: new SA + share sheets + secret + 1 config switch.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
MEASURE-FIRST resolved 2026-06-26: peak DOES hit 60. Direct evidence — live 429s fired in production run 26964724118 (2026-06-04 16:22 market hours; agent_orchestrator + sentinel + news_detective). Per-tab read-counter under-counts (reported 4 reads in the same run that threw 429), so no clean peak number, but the 429 firing is stronger proof than any counter. Verdict: TASK-58 JUSTIFIED, not redundant. Build (2nd SA + share 18 sheets + GOOGLE_CREDENTIALS_JSON_HA secret + config switch) remains a separate scheduled step — infra change, not a quick fix.
<!-- SECTION:NOTES:END -->
