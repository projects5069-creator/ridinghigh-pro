---
id: TASK-176
title: News Detective demotion — EOD-only or disable pending value proof
status: To Do
assignee: []
created_date: '2026-06-13 01:26'
updated_date: '2026-07-02 04:43'
labels:
  - TASK-171
dependencies: []
priority: medium
ordinal: 179000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
171-A5 / PT-5. Scorecard 1/5: no WIN/LOSS discrimination (WITH news WR 60% vs WITHOUT 62%, EDGAR r=-0.156, TASK-67), heavy quota in agent_minute (TASK-136 marks it first to cut). Net-negative at present. Demote to EOD-only or disable until value is proven.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 News Detective no longer runs per-minute (EOD-only or disabled)
- [ ] #2 Quota savings measured
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC#1 DONE (news_detective off per-minute, NEWS_DETECTIVE_ENABLED=False, pushed 5f0b288). AC#2 (quota savings) = measure via scripts/measure_429_by_workflow_v1.py over 1-3/7.
<!-- SECTION:NOTES:END -->

## RESTATED 2026-08-04

The scope is narrower than the title suggests. AC#1 is done and verified: config.py line 364 sets NEWS_DETECTIVE_ENABLED to False, and the news_findings tab holds 3,012 rows for 2026-07 and zero for 2026-08, which is the demotion working.

What remains is AC#2 alone, measuring the quota saving, and the tool for it already exists at scripts/measure_429_by_workflow_v1.py. It was never run.

Consider whether that measurement is still worth a separate task. The 429 picture is now owned by TASK-215, whose own verification step is exactly a before and after 429 comparison over trading days. If 215 runs that measurement, this task closes with it.
