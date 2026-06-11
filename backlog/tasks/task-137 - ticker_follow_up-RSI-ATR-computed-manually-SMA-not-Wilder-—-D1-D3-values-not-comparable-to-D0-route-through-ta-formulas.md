---
id: TASK-137
title: >-
  ticker_follow_up RSI/ATR computed manually (SMA not Wilder) — D1-D3 values not
  comparable to D0; route through ta/formulas
status: To Do
assignee: []
created_date: '2026-06-10 19:17'
updated_date: '2026-06-11 04:01'
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
- [ ] #1 TASK-139 RH-2.2 confirms: follow_up RSI = SMA-rolling vs Wilder EWM in analyze_ticker; plus typical_price_dist inline duplicate (RH-2.3) — route both through formulas
<!-- AC:END -->
