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

## FROZEN UNTIL OCTOBER, 2026-08-04

Staying open on purpose. This is a decision with a return date, not an oversight.

The bug is real and unchanged. _calculate_position in decision_logic.py computes qty as int(AGENT_POSITION_SIZE_USD / price), so any price above 1000 dollars yields zero, and a grep across the whole execution path, decision_logic, order_manager and alpaca_broker, finds no qty greater than or equal to one guard anywhere. An ENTER carrying quantity zero would reach the broker.

Why it is not being fixed now. HYP-002 was voided on 2026-08-03 and re-registered the same day with 45 trading days of forward capture, reaching early October. The registration states that any change to the frozen configuration voids the run. This task argues it is a guard rather than a threshold and therefore outside the freeze, and that argument is reasonable, but the thing that voided the previous run was precisely a change in behaviour on the entry path during a registered run. Being right about the category is not worth a second voiding.

Why waiting costs nothing measurable. The universe this scanner produces is micro caps. The live scan of 2026-08-03 returned 55 tickers with prices between 0.33 and 48.62 dollars. A price above 1000 dollars does not occur in that universe, so the failing branch is not reachable in practice today.

RETURN DATE: early October 2026, when HYP-002 concludes. At that point implement as ruled on 2026-07-03: qty below one returns SKIP with a dedicated skip_reason, not a one share fallback, so notional uniformity is preserved. TDD, RED before GREEN, and an explicit go because it is the live entry path.

WHAT WOULD BRING IT FORWARD: a scanned universe that starts producing prices near or above 1000 dollars. That would make the branch reachable and the freeze would no longer be the cheaper risk.
