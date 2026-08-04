---
id: TASK-11
title: P2.4 — Cross-month aggregation
status: Done
assignee: []
created_date: '2026-05-23 19:33'
updated_date: '2026-08-04 00:32'
labels: []
dependencies: []
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Dashboard and analytics need to aggregate across months (Phase 1 spans multiple months). Currently each month is siloed in its own sheets_config entry.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-202, 2026-08-04

Closed as a merge. Same root: every sheet operation resolves to the current month, so nothing can aggregate across months.

TASK-202 holds the concrete version of this, five read and write points in post_analysis_collector that all default to the current month, with acceptance criteria and a TDD requirement. This task is the same problem stated at the dashboard level.

Scope note carried to 202: the same month scoping also breaks ticker_follow_up on the first trading day of every month, recorded in the audit note on TASK-124.
