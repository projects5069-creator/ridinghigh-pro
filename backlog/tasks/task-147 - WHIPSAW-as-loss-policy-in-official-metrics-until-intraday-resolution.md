---
id: TASK-147
title: WHIPSAW-as-loss policy in official metrics until intraday resolution
status: In Progress
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-12 14:22'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 150000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-6.3 sensitivity: 26 WHIPSAW rows excluded from n=123; if resolved at SL the edge turns negative in ALL borrow scenarios (-1.28 to -2.66 pct/trade). Until intraday data resolves them (ties TASK-26), official metrics should report a WHIPSAW-as-loss pessimistic bound alongside the optimistic one
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 DECISION 2026-06-10 (Amihay, approved): permanent DUAL REPORTING — every official WR/expectancy shows the headline metric PLUS the pessimistic WHIPSAW-as-SL bound next to it (today: +1.06pct vs -1.28pct at borrow 50). The 26 rows themselves stay open until intraday resolution (TASK-26 + minute-bars fetcher)
- [ ] #2 WR half: headline WR dual-bound (optimistic + WHIPSAW-as-SL) on D1_Open — SHIPPED via the 142-merged branch (metrics_bounds.wr_bounds + dashboard headline surfaces)
- [ ] #3 Expectancy half: split to TASK-162 (live expectancy surface, D1_Open basis). 147 stays open until 162 lands
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
APPROVED 2026-06-11. Split 2026-06-12: WR-half shipped via 142-merge (D1_Open headline + WHIPSAW-as-loss pessimistic bound, policy-layer only — core classify_trade mapping untouched). Expectancy-half -> TASK-162 (calculate_net_pnl entry_price plumbing already laid in formulas.py). 26 WHIPSAW rows stay open until minute-bars (TASK-26). 147 = In Progress until TASK-162 done.
<!-- SECTION:NOTES:END -->
