---
id: TASK-227
title: 'market_cap_cache not persistent in CI + silent swallows (auto_scanner:108-122)'
status: To Do
assignee: []
created_date: '2026-07-04 01:49'
labels: []
dependencies: []
priority: low
ordinal: 233000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S3 (3/7): load_mc_cache/save_mc_cache use expanduser('~/RidingHighPro/data/market_cap_cache.json') (auto_scanner.py:108/:117). On GitHub Actions HOME=/home/runner != workspace + ephemeral runner => the JSON cache loads empty and saves to a discarded path EVERY Run — silently (bare except :113/:122). In-run memory caches (_mc_cache/_shares_cache) still work; dashboard uses a different cache_dir path (dashboard.py:152). Decide: workspace-relative path (persist via actions/cache?) OR document as local-dev-only + replace bare excepts with logged warnings.
<!-- SECTION:DESCRIPTION:END -->
