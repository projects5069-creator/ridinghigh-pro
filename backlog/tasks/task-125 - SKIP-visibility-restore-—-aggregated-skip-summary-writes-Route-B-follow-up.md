---
id: TASK-125
title: SKIP visibility restore — aggregated skip-summary writes (Route B follow-up)
status: Done
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-11 00:14'
labels: []
dependencies: []
priority: high
ordinal: 128000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Route B (commit b1a4e4f 2026-05-11, decision_logger.py:156-169) sends all non-ENTER decisions to stdout only — counterfactual analysis dead since. Fix approach: aggregate per run (one row per skip-reason, ~5-15 writes/run vs 80-100) or EOD rollup to dedicated tab. Must NOT reintroduce the 429 quota storm that Route B solved.
<!-- SECTION:DESCRIPTION:END -->
