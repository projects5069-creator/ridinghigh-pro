---
id: TASK-137
title: >-
  ticker_follow_up RSI/ATR computed manually (SMA not Wilder) — D1-D3 values not
  comparable to D0; route through ta/formulas
status: Done
assignee: []
created_date: '2026-06-10 19:17'
updated_date: '2026-06-16 17:46'
labels:
  - bug
  - data-quality
dependencies: []
priority: medium
ordinal: 140000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
SYSTEM_REVIEW B.4 (10/6). auto_scanner.py:865-870 (ATR14) + 880-886 (RSI) in update_ticker_follow_up compute via manual rolling(14).mean() (SMA-RSI / SMA-ATR), while the canonical source is ta.RSIIndicator/ta.AverageTrueRange (Wilder) at auto_scanner.py:183,190 + formulas.py. Consequence: RSI/ATRX recorded for D1-D3 in ticker_follow_up are methodologically different from D0 — not comparable across the follow window, polluting any multi-day RSI/ATR research. Fix: route ticker_follow_up through the same ta-based path (single source of truth, §10). Touches auto_scanner live path → PING-PONG. Verify no regression in ticker_follow_up schema.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TASK-139-INV RH-2.2 confirms: follow_up RSI = SMA-rolling vs Wilder EWM in analyze_ticker; plus typical_price_dist inline duplicate (RH-2.3) — route both through formulas
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
pt2 DONE (24f9edb, 2026-06-16, CI green): typical_price_dist in update_ticker_follow_up routed through formulas.calculate_typical_price_dist (canonical, same as D0:227) — value-preserving (math identical to old inline; covered by test_vwap_dist) + source-guard in tests/test_ta_helpers_v1.py. TASK-137 COMPLETE: pt1 (1cfe31a Wilder RSI/ATR) + pt2 (24f9edb typical_price_dist dedup). Both AC#1 halves (RH-2.2 + RH-2.3) satisfied. Zero ENTER/sizing change.
<!-- SECTION:NOTES:END -->
