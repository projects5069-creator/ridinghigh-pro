---
id: TASK-170
title: Market-regime cluster — unify TASK-15 + TASK-42 + TASK-70
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
updated_date: '2026-07-02 21:11'
labels:
  - vision
  - market-regime
dependencies: []
priority: medium
ordinal: 173000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per TASK-156 agenda: unify the three market-regime items. (15) wire Market Context (SPY/IWM/VIX regime) into decision_logic as filter/score-modifier; (42) add SPY/IWM benchmark price per paper_portfolio row at entry+exit for return-vs-market — 42 is NOT standalone, it is part of this regime cluster; (70) simulate VIX-above-threshold as an entry filter. Market Context agent already collects SPY/IWM/VIX (market_context_v1.py).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Wire Market Context regime into decision_logic (was TASK-15)
- [ ] #2 SPY/IWM benchmark per paper_portfolio row, entry+exit (was TASK-42 — part of regime, not standalone)
- [ ] #3 VIX entry-filter simulation (was TASK-70)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
VIX-sim measured 2026-07-02 (n=219 dated entries): VIX<20 n=205 WR53.7%, VIX 20-30 n=14 WR57.1%, VIX>30 n=0. Entire 05-07 period was low-vol -> zero high-VIX entries, no regime variance. Original TASK-70 finding (72% vs 58%) NOT reproducible — insufficient VIX spread. NOT ready for HYP-004 (no significant edge, no regime coverage, n=14 in mid-bucket is noise). Re-examine only when VIX variance appears or n grows. Inconclusive-not-actioned.
<!-- SECTION:NOTES:END -->
