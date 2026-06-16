---
id: TASK-137
title: >-
  ticker_follow_up RSI/ATR computed manually (SMA not Wilder) — D1-D3 values not
  comparable to D0; route through ta/formulas
status: To Do
assignee: []
created_date: '2026-06-10 19:17'
updated_date: '2026-06-16 16:59'
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
pt1 DONE (1cfe31a, 2026-06-16, CI-verified green): RSI/ATR in update_ticker_follow_up routed through new ta_helpers.py (canonical Wilder, formulas.py stays scalar-only) over hist_full — D1-D3 now comparable to D0. tests/test_ta_helpers_v1.py (7 cases, CI-collected, source-level no-SMA guard). hist_full ~252d so <14 fallback unreachable for real ticker; comparability holds. Zero D0/Score-of-D0/ENTER/sizing change (follow-up Score for D1-D3 intentionally shifts to correct Wilder values). pt2 PENDING (separate, touches Score input): typical_price_dist inline in follow-up -> route through formulas.calculate_vwap_dist (AC#1 RH-2.3). Task stays To Do until pt2.
<!-- SECTION:NOTES:END -->
