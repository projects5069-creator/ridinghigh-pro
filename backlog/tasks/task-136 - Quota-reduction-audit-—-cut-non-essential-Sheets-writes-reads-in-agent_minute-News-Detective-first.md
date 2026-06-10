---
id: TASK-136
title: >-
  Quota reduction audit — cut non-essential Sheets writes/reads in agent_minute
  (News Detective first)
status: To Do
assignee: []
created_date: '2026-06-10 18:56'
labels:
  - agent
  - infra
  - quota
dependencies: []
priority: high
ordinal: 139000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Live agent_minute runs hit 429 every minute (verified 10/6 in run logs, blocks B+D). Root sources confirmed from live run logs: (1) news_detective writes per-ticker news findings ~24 writes/run — and per memory/PK it is logging-only (TASK-67: does not separate WIN from LOSS) → prime cut candidate; (2) check_emergency_stop reads Sheets every run start; (3) sentinel event logging writes per WARN. NOT the cause: score_tracker (lives in auto_scanner, dashboard-only consumer per recon block C) and timeline_live (life-line — orchestrator.read_latest_signals + dashboard both read it, MUST NOT touch). Scope: measure writes/reads per agent component per run, verify which are logging-only vs decision-affecting (esp. news_detective — confirm against code, not memory), then cut/aggregate by impact order. Each cut = its own PING-PONG commit (touches live orchestrator/agent). Goal: agent_minute 429 rate ~0. Sibling of TASK-125 (skip aggregation, same quota-budget discipline). Investigate-before-touch — this task is the audit; cuts may spawn sub-tasks.
<!-- SECTION:DESCRIPTION:END -->
