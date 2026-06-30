---
id: TASK-213
title: 'Verify TASK-58 429-reduction (DEADLINE 2026-07-06, do NOT defer)'
status: To Do
assignee: []
created_date: '2026-06-30 16:48'
labels:
  - infra
  - quota
  - deadline
  - task-58-followup
dependencies: []
priority: high
ordinal: 219000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
HARD DEADLINE 2026-07-06 (Mon, first market-day after +5d). MUST execute, not defer (avoid May-backlog rot). TASK-58 closed Done 30/6 functionally (code+infra+live health_audit run=success), but the GOAL — 429 reduction in market hours — was NOT yet measured over time. AC#1: compare 429-error count in agent_minute/auto_scan/health_audit logs across 3-4 market days (30/6 baseline -> 1-3/7) — confirm health_audit no longer contributes 429 (now on dedicated HA SA). AC#2: confirm health_audit CI runs use the HA SA (add client_email log-line if needed). AC#3: if 429 NOT reduced -> reopen TASK-58 root-cause. baseline: 429 fired 3x on 30/6 on shared SA.
<!-- SECTION:DESCRIPTION:END -->
