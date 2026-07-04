---
id: TASK-224
title: >-
  qty guard: quantity<1 => SKIP with dedicated skip_reason (notional-uniformity
  ruling)
status: To Do
assignee: []
created_date: '2026-07-04 01:48'
labels: []
dependencies: []
priority: medium
ordinal: 230000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S2 (3/7): _calculate_position (decision_logic.py:139-151) does qty=int(AGENT_POSITION_SIZE_USD/price) — price>$1000 => qty=0, and NO qty>=1 guard exists anywhere in the execution path (order_manager/alpaca_broker/decision_logic — grep empty). An ENTER with quantity=0 would reach the broker. RULING (עמיחי 3/7): direction 'up to $1000' — qty<1 => SKIP with a dedicated skip_reason (NOT a 1-share fallback; preserves notional uniformity). LIVE ENTRY PATH — implement only on a separate explicit go. Not a HYP-002 frozen param (guard, not threshold). Evidence: plans/stateless-seeking-sifakis.md S2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 qty<1 returns SKIP with dedicated skip_reason (e.g. PRICE_ABOVE_NOTIONAL), TDD RED->GREEN
- [ ] #2 no behavior change for any price where qty>=1 (regression suite green)
<!-- AC:END -->
