---
id: TASK-227
title: 'market_cap_cache not persistent in CI + silent swallows (auto_scanner:108-122)'
status: Done
assignee: []
created_date: '2026-07-04 01:49'
updated_date: '2026-08-04 00:32'
labels: []
dependencies: []
priority: low
ordinal: 233000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S3 (3/7): load_mc_cache/save_mc_cache use expanduser('~/RidingHighPro/data/market_cap_cache.json') (auto_scanner.py:108/:117). On GitHub Actions HOME=/home/runner != workspace + ephemeral runner => the JSON cache loads empty and saves to a discarded path EVERY Run — silently (bare except :113/:122). In-run memory caches (_mc_cache/_shares_cache) still work; dashboard uses a different cache_dir path (dashboard.py:152). Decide: workspace-relative path (persist via actions/cache?) OR document as local-dev-only + replace bare excepts with logged warnings.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-245, 2026-08-04

Closed as a merge. Same pattern: a bare except that swallows in silence.

Verified live 2026-08-04: auto_scanner.py carries five bare except clauses, and the two this task names, lines 113 and 122, are two of them. The audit note added to TASK-245 on 2026-08-03 records the same pattern around the scan loop at lines 413 to 416 and proposes the same fix, replacing bare handlers with logged warnings.

The cache path question, whether to make it workspace relative or document it as local only, travels with it.
