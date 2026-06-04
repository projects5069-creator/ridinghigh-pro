---
id: TASK-58
title: >-
  SENT/INFRA — Separate service account for health_audit to end 429 quota
  contention
status: To Do
assignee: []
created_date: '2026-05-29 17:48'
updated_date: '2026-06-04 16:28'
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
4/6: Phase 1+2 (read reduction) VERIFIED live — run 26964724118 total=4 reads; per-tab 4 tabs x1 each = consolidation verified (per-tab counter, NOT per-function — no build_account_state attribution; timeline_live 4->2 is scanner target, needs scanner log). S2 deferred (no quota pressure). NOT closing: AC is separate SA for health_audit (GOOGLE_CREDENTIALS_JSON_HA) — not done. Open Q: does combined peak (agent+scanner+health_audit same minute) still hit 60? If not, separate SA may be unnecessary — measure peak before building.
<!-- SECTION:NOTES:END -->
