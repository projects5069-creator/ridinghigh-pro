---
id: TASK-140
title: Add net-PnL cost model to post_analysis (slippage 1pct/side + borrow pro-rata)
status: To Do
assignee: []
created_date: '2026-06-11 04:01'
labels:
  - TASK-139
dependencies: []
priority: high
ordinal: 143000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139 RH-6.3: slippage-only +1.21pct/trade; borrow 50/200/500pct -> +1.06/+0.59/-0.34pct; WHIPSAW-as-SL flips negative in ALL scenarios. Make net-PnL a standing post_analysis metric instead of gross TP/SL. Repro: docs/research/INVESTIGATION_2026-06-10/phase6_analysis.py (seed=42)
<!-- SECTION:DESCRIPTION:END -->
