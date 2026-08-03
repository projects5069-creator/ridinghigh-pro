---
id: TASK-213
title: 'Verify TASK-58 429-reduction (DEADLINE 2026-07-06, do NOT defer)'
status: Done
assignee: []
created_date: '2026-06-30 16:48'
updated_date: '2026-07-03 02:52'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified 2026-07-02 (measure_429_by_workflow_v1, market-hours window 14-15Z, gh-logs): agent_minute 24.7->1.3 mean-429 (~95% drop), news_detective+sentinel 402+192->0 (TASK-176 effective 2/7). AC#1: health_audit 0.0 across 30/6-2/7 (10 runs). AC#2: SA=_HA verified (YAML inject health_audit.yml:38 + code-pref health_audit.py:137 + TDD test_task58_ha_credential_pref). Artifact research/measure_429_20260702.csv. Residual 1.3/run = sheets_manager+orch, not news/sentinel flood.
<!-- SECTION:NOTES:END -->

## AUDIT 2026-08-03: GOAL NOT HELD

The scope of this task was health_audit's own contribution to 429, and that part stands. The stated goal, 429 reduction during market hours, does not.

Cancelled agent_minute runs: 2 on 2026-07-22, 175 out of 488 on 2026-07-29. On 22/7 a 429 on the paper_portfolio read blinded the entry guards, see TASK-244.

The remaining source is agent_minute and auto_scan, not health_audit, so the open successor is TASK-215, a dedicated SA for auto_scan, plus TASK-218. Status left unchanged.
