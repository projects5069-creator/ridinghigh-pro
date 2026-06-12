---
id: TASK-155
title: Add minute-bars fetcher for WHIPSAW resolution + entry studies
status: In Progress
assignee: []
created_date: '2026-06-11 04:26'
updated_date: '2026-06-12 17:16'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 158000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Week-1 work-plan item: intraday 1-min bars fetcher (Alpaca) to (a) resolve the 26 WHIPSAW rows that flip the edge sign (TASK-147 dual reporting), (b) enable D1_Open/entry-timing event studies (TASK-142). Scope: fetch+cache only, no trading logic
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Cached intraday fetch: fetch-once per (ticker, settled-day, timeframe) to data/intraday_cache/, never re-fetch a cached settled day
- [ ] #2 Pure resolve_whipsaw(entry_price, minute_bars_df) -> WIN/LOSS/UNRESOLVED by walking bars in time order (same-bar both -> UNRESOLVED); core classify_trade mapping untouched
- [ ] #3 Offline study resolves the 26 WHIPSAW rows -> docs/research/WHIPSAW_RESOLUTION_<date>/ report (CSV+MD) with recomputed WR + per-row coverage
- [ ] #4 Phase 0 spike GATE: prove IEX 1-min coverage before building Phases 1-3; no change to official WR/dashboard/dataset/sizing
<!-- AC:END -->
