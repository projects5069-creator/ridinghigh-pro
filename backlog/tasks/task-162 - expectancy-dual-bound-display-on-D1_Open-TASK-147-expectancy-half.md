---
id: TASK-162
title: expectancy dual-bound display on D1_Open (TASK-147 expectancy half)
status: Done
assignee: []
created_date: '2026-06-12 14:21'
updated_date: '2026-06-12 18:27'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 165000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Split from TASK-147. The WR half shipped via the 142-merged branch (headline WR on D1_Open + WHIPSAW-as-loss pessimistic bound). This is the EXPECTANCY half. calculate_net_pnl already accepts entry_price (plumbing laid in 142-merge, formulas.py). Remaining: build the live expectancy surface on D1_Open basis and demote ScanPrice NetPnL to diagnostic.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Live dashboard expectancy surface with DUAL reporting: optimistic (WHIPSAW excluded) vs pessimistic (WHIPSAW-as-SL), shown for borrow 50/200/500
- [ ] #2 Expectancy basis = D1_Open (consumes calculate_net_pnl entry_price param); NOT ScanPrice
- [ ] #3 New D1_Open NetPnL official columns + backfill of the settled rows
- [ ] #4 Existing ScanPrice NetPnL_* columns relabeled diagnostic (no silent removal)
- [ ] #5 No drift: official WR (D1_Open) and official expectancy (D1_Open) share the same entry basis
- [ ] #6 INPUT from TASK-155 (2026-06-12): intraday resolution of the 26 WHIPSAW = 8 WIN / 17 LOSS / 1 UNRESOLVED; executable WR D1_Open RESOLVED=49.2% (vs optimistic 53.5% / pessimistic 42.4%). Use the resolved verdicts (not the pessimistic-all-SL bound) for the expectancy surface where available; XNDU stays UNRESOLVED.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-12 on branch task-162-expectancy (not merged — review first). On-the-fly executable D1_Open expectancy dual-bound surface in Post Analysis (metrics_bounds.expectancy_bounds + classify_trade_row_full + calculate_net_pnl). ANCHOR CORRECTION: the AC's +1.06/-1.28 @ borrow50 was ScanPrice/investigation-era (inflated, the look-ahead 142 fixed) — NOT reproducible on D1_Open. Correct executable D1_Open expectancy = -1.47pct optimistic / -3.74pct pessimistic @ borrow50 (negative even optimistically; breakeven WR ~60.8% with slip vs actual ~53.5%). AC #2/#3 superseded (no net_pnl param — scale-invariant; on-the-fly, no backfill). AC #4 done (NetPnL_* labeled ScanPrice diagnostic). AC #6 (resolved third-bound) deferred to TASK-164. No persisted-column/schema change.
<!-- SECTION:NOTES:END -->
