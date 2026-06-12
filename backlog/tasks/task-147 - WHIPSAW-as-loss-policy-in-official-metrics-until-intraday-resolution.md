---
id: TASK-147
title: WHIPSAW-as-loss policy in official metrics until intraday resolution
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-12 18:27'
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
DONE 2026-06-12. Permanent dual reporting complete: WR dual-bound (optimistic + WHIPSAW-as-SL) on D1_Open shipped via TASK-142; expectancy dual-bound on D1_Open shipped via TASK-162. Per AC #1, dual (headline + pessimistic WHIPSAW-as-SL) closes 147 — the resolved third-bound (from TASK-155 intraday verdicts) is a NEW enhancement beyond 147's scope -> TASK-164. Finding surfaced: executable D1_Open expectancy is negative under realistic borrow (RH-6.3 confirmed).
<!-- SECTION:NOTES:END -->
