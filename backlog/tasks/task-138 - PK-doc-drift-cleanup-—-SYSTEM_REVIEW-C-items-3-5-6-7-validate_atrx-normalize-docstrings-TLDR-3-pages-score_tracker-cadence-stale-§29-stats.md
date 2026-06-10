---
id: TASK-138
title: >-
  PK doc drift cleanup — SYSTEM_REVIEW C items 3/5/6/7 (validate_atrx/normalize
  docstrings, TL;DR 3-pages, score_tracker cadence, stale §29 stats)
status: To Do
assignee: []
created_date: '2026-06-10 19:18'
labels:
  - docs
  - drift
dependencies: []
priority: low
ordinal: 141000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
SYSTEM_REVIEW C (10/6) — docs-only drift, no code/trading change. (3) PK §19: validate_atrx says returns bool (returns float); normalize_mxv/atrx say 0-1 (return 0-100, and are DEAD/unused). (5) PK §2 TL;DR says Dashboard 3 pages — actually 10. (6) PK §20: score_tracker cadence (every 5 min, auto_scanner:524) undocumented. (7) PK §29 stats from 2026-05-02 mislabeled current — now 276 post_analysis rows / 172 v2 (not 156/52). Align all to reality + bump PK. Pure documentation — group into one PK pass. Separate from TASK-129 (which covers RSI drift items 1/2) and TASK-119 (metadata item 4).
<!-- SECTION:DESCRIPTION:END -->
