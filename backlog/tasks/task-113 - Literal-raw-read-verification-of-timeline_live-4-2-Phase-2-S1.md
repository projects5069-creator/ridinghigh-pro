---
id: TASK-113
title: Literal raw-read verification of timeline_live 4->2 (Phase 2 S1)
status: To Do
assignee: []
created_date: '2026-06-04 17:52'
labels: []
dependencies: []
priority: low
ordinal: 113000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-112 cache-miss counter shows timeline_live=1 miss/run (total=1) — confirms caching effective but does NOT literally observe the v2.70 4->2 RAW-reads claim (different metric: misses vs raw reads). If literal raw-read accounting is ever needed: instrument auto_scanner to count raw get_worksheet/get_all_values calls for timeline_live (not just cache misses) and verify exactly 2 raw reads/run (pre-write + post-write-after-invalidate). LOW — caching already effective (<=1 miss/run); only needed if raw-read accounting becomes important.
<!-- SECTION:DESCRIPTION:END -->
