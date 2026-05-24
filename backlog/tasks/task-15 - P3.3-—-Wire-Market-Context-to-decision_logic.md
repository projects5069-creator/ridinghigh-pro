---
id: TASK-15
title: P3.3 — Wire Market Context to decision_logic
status: To Do
assignee: []
created_date: '2026-05-23 19:33'
updated_date: '2026-05-24 03:25'
labels: []
dependencies: []
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Agent #3 Market Context writes SPY/IWM/VIX regime to sheet but decision_logic.py does not yet consume it. Wire it as a filter or score modifier.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Deferred 2026-05-23 after Phase 0 analysis. Data shows: 100% NEUTRAL+LOW regime (zero variance in 18 samples). Only 18/89 trades joinable to market_context. Median context age at trade time: 19 hours stale. Web research confirms: filter design REQUIRES backtest with regime variance — not yet available. Re-evaluate after 4 weeks (~2026-06-23) when ~100-200 decisions with regime tags accumulated.
<!-- SECTION:NOTES:END -->
