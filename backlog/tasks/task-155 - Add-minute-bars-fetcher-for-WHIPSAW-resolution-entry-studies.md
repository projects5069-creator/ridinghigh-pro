---
id: TASK-155
title: Add minute-bars fetcher for WHIPSAW resolution + entry studies
status: Done
assignee: []
created_date: '2026-06-11 04:26'
updated_date: '2026-06-12 17:51'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-12 on branch task-155-minute-bars (not merged — branch review first). Phases: 0 spike GATE (IEX 96% RESOLVABLE on the official 26), 1 intraday_cache (settled-day disk cache, 4 tests), 2 utils.resolve_whipsaw (BOTH-sides-or-UNRESOLVED, 9 tests; classify_trade frozen), 3 offline study docs/research/WHIPSAW_RESOLUTION_2026-06-12/ (gitignored). FINDING: 26 WHIPSAW -> 8 WIN / 17 LOSS / 1 UNRESOLVED (XNDU); WR D1_Open optimistic 53.5% / RESOLVED 49.2% / pessimistic 42.4% — WHIPSAW skew negative (68% LOSS). No official WR/dashboard change. PK v3.09.
<!-- SECTION:NOTES:END -->
