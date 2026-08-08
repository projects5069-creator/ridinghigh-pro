---
id: TASK-279
title: Recompute Quantity and PositionSizeUSD at the live-price override
status: To Do
assignee: []
created_date: '2026-08-08 19:48'
labels: []
dependencies: []
priority: high
ordinal: 277000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-301 from S7_TASKS_v1.md, gate 3, marked critical there. OPENED 2026-08-08 - it was dropped by mistake when the other six T-tasks became tickets (272-277); the omission surfaced only when the work plan mapped milestone M5 and found gate 3 had no owner. Without this ticket gate 3 can never go green.

THE PROBLEM, verified against live code today: order_manager.py:150-158 overrides the scan price with the live bar - it sets decision.execution_price, and recalculates tp_price and sl_price from the live price - but leaves quantity and position_size_usd at their scan-time values. The row is then written with a price from one moment and a quantity from another, so E x Q no longer equals PS. Measured: 205 of 291 rows violate the identity, worst case 25,975 dollars on TTC (scan 3.46, live 93.34). Separately CR-05: nothing anywhere checks qty >= 1, so a 1,200-dollar price silently yields quantity 0.

SCOPE:
(1) order_manager.py:155-158 - recompute quantity and position_size_usd from live_price using the same formula the decision path already uses at decision_logic.py:145-146 (qty = int(AGENT_POSITION_SIZE_USD / price); actual_size = qty * price). Reuse it, do not write a second calculator - section 10.
(2) Before build_portfolio_row (order_manager.py:267) enforce three invariants: Q >= 1; |E*Q - PS| <= eps_identity; |Q*(SL-E) - 0.10*E*Q| <= eps_risk. A violation must block the write and mark an error, not warn and continue.
(3) Same validation on the second row-builder: reconciler._build_portfolio_row_from_decision (reconciler.py:169-207) and scripts/repair_paper_portfolio_misalign_v1.py. The backfill row happens to be self-consistent today because all three values come from the same scan-era record; the invariant pins that rather than trusting it.

NOT IN SCOPE: do not repair historical rows - that is D4 and the purity package. Do not touch TP/SL - they are already consistent with the live price.

EPSILONS ARE ALREADY DECIDED - do not re-open: docs/DECISIONS_2026-08-08.md D3 fixes eps_identity 0.02 and eps_risk 0.05.

ACCEPTANCE: gate 3 (audit_gate/gate3_risk.py, already rescoped to EntryDate >= 2026-08-10 by T-303) returns zero violating rows in scope. RED-first: test_qty_recomputed_on_override_v1.py - scan 3.46 with live 93.34 must yield a recomputed qty where E*Q approximately equals PS; fails today. Second case: a 1,200-dollar price yielding qty 0 must be rejected, not written.

EXPECT COLLATERAL DAMAGE: this changes the meaning of Quantity and PositionSizeUSD on new rows, so existing tests that assert row shape may go red. Run the full suite before and after, record which reds were predicted, and fix our code rather than the tests.

TIMING - HARD CONSTRAINT: after 2026-09-04 only. This changes what gets written to paper_portfolio, and the measurement window 2026-08-10 to 2026-09-04 must not have its write semantics changed mid-flight. That is exactly what voided HYP-002 in July.

RELATED: TASK-217 touched the same 25-element row for a different defect (column alignment) - cross-reference only. TASK-276 (heat cap) reads E*Q for its sum, so it inherits correctness from this task.
<!-- SECTION:DESCRIPTION:END -->
