---
id: TASK-58
title: >-
  SENT/INFRA — Separate service account for health_audit to end 429 quota
  contention
status: To Do
assignee: []
created_date: '2026-05-29 17:48'
labels: []
dependencies: []
priority: medium
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Root-cause fix for the Sheets 429 read-quota contention (follows TASK-55 phase-2 mitigation). health_audit, agent_minute, and auto_scan all share ONE service account and collectively cross Google's 60 reads/min/user cap during market hours. Phase-2 added backoff patience but the structural problem remains. Solution: provision a SECOND service account dedicated to health_audit (and possibly market_context), share the 9+9 monthly sheets with it, add a new GH secret (e.g. GOOGLE_CREDENTIALS_JSON_HA), and point health_audit's gc at it. Removes health_audit from the trading SA's quota budget entirely. Effort: new SA + share sheets + secret + 1 config switch.
<!-- SECTION:DESCRIPTION:END -->
