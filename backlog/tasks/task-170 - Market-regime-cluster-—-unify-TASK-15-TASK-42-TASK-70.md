---
id: TASK-170
title: Market-regime cluster — unify TASK-15 + TASK-42 + TASK-70
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
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
