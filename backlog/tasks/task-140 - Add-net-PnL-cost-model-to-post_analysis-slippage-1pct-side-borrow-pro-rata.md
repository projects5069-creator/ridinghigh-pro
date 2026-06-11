---
id: TASK-140
title: Add net-PnL cost model to post_analysis (slippage 1pct/side + borrow pro-rata)
status: To Do
assignee: []
created_date: '2026-06-11 04:01'
updated_date: '2026-06-11 18:43'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 143000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-6.3: slippage-only +1.21pct/trade; borrow 50/200/500pct -> +1.06/+0.59/-0.34pct; WHIPSAW-as-SL flips negative in ALL scenarios. Make net-PnL a standing post_analysis metric instead of gross TP/SL. Repro: docs/research/INVESTIGATION_2026-06-10/phase6_analysis.py (seed=42)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Pure fn formulas.calculate_net_pnl(scan_price, classification, resolution_day, borrow_annual_rate, slip=SLIP) -> fraction. Logic per phase6: fill=scan*(1-SLIP); exit=scan*(1-TP_FRAC) WIN / scan*(1+SL_FRAC) LOSS; cover=exit*(1+SLIP); gross=(fill-cover)/fill; bcost=rate*days/365; net=gross-bcost
- [ ] #2 win/loss + resolution_day sourced from classify_trade (SSoT, utils.py) — do NOT duplicate classification logic
- [ ] #3 Only WIN/LOSS computed. WHIPSAW/NO_TOUCH/PENDING -> NULL (empty cell). WHIPSAW-as-loss reporting = separate column after TASK-147
- [ ] #4 borrow: 3 fixed scenarios in config BORROW_SCENARIOS=[0.50,2.00,5.00] per yr (fee=NULL from 139 — assumptions flagged)
- [ ] #5 slippage: config SLIP=0.01 (1pct/side adverse)
- [ ] #6 4 new post_analysis columns: NetPnL_SlipOnly + NetPnL_Borrow50/200/500
- [ ] #7 Basis = Table-A (ScanPrice + TP/SL sim). TDD reproduces phase6 seed=42: slip-only +1.21pct, borrow 50/200/500 -> +1.06/+0.59/-0.34pct (aggregate, integration)
<!-- AC:END -->
