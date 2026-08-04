---
id: TASK-225
title: >-
  Hold-window research: D1-D25 optimal holding analysis — decision blocked until
  HYP-002 concludes
status: To Do
assignee: []
created_date: '2026-07-04 01:48'
labels: []
dependencies: []
priority: medium
ordinal: 231000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S2 (3/7) established: there is NO live forced-exit — MAX_HOLDING_DAYS=5 is display-only (config.py:146), positions ride until TP/SL (AGENT_FORCE_EOD_CLOSE=False); 'HOLD<=5' in HYP-002 = classify/fitness window (HYPOTHESES.md:194), explaining OPEN=45 accumulation. RESEARCH: analyze D1-D25 forward data (post_analysis; CLASSIFY_DAYS=5 full-OHLC + D6-D25 Close+Low, COLLECT_DAYS_FORWARD=25) to determine the optimal holding window for the live agent. HARD GATE (עמיחי 3/7): decision/implementation BLOCKED until HYP-002 concludes (~2026-07-27 / n>=150 post-flip / 45 trading days, first-of) — any hold-behavior change before that = void to the hypothesis (re-registration). Research read-only may start earlier.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 read-only analysis of D1-D25 outcomes (night/TP/SL/adverse-tail per horizon) documented with n per cell
- [ ] #2 recommendation (keep TP/SL-only vs add forced-exit at day-K) presented ONLY after HYP-002 verdict
<!-- AC:END -->

## GATE DATE MOVED 2026-08-04

The hard gate in the description estimates HYP-002 concluding around 2026-07-27. That estimate is two months out of date.

HYP-002 was voided on 2026-08-03. Its stopping rule had already fired at n equal to 173 against a threshold of 150, but the sample could not be scored: 86 of the 173 entries sat on phantom tickers, 84 had no outcome at all, and 54 exceeded the frozen reentry cap of one per ticker per day. It was re-registered the same day as a fresh run starting 2026-08-03, with no carry forward, under the identical criterion and the identical frozen configuration.

NEW GATE DATE: early October 2026. Forty five trading days from 2026-08-03, or n greater than or equal to 150 post flip entries, whichever comes first, exactly as before.

Everything else in this task is unchanged and still correct. There is still no live forced exit, MAX_HOLDING_DAYS remains display only at 5, AGENT_FORCE_EOD_CLOSE is still False at config.py line 315, and positions still ride until TP or SL. The read only research permission also stands: analysing the D1 to D25 outcomes may begin at any time. Only the recommendation and any implementation wait for the verdict.
