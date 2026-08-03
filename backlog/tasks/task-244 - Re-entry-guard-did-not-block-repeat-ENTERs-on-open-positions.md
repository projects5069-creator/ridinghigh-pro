---
id: TASK-244
title: Re-entry guard did not block repeat ENTERs on open positions
status: To Do
assignee: []
created_date: '2026-07-29 09:27'
labels:
  - bug
  - agent
dependencies: []
priority: high
ordinal: 242000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29, read only, from decision_log 2026-07 and paper_portfolio 2026-07.

OBSERVED: 137 ENTER decisions in July. On 2026-07-22 there were 43 ENTERs across only 4 distinct tickers: IINLF 11, LLABT 11, AADVB 11, ZZCMD 10. On 2026-07-16 there were 17 ENTERs of which VVEEE accounts for 9. Every one of those repeat entries has a matching row in paper_portfolio with Status DRY_RUN_OPEN and all four exit columns blank.

WHY THIS MATTERS: HYP-002 locks reentry at most 1, and the entry path is supposed to check for an existing position before entering. It did not block here. Position sizing was roughly 1000 USD per entry, so 11 stacked entries on one symbol is roughly 11k of notional exposure on a single ticker that does not exist.

HYPOTHESIS, NOT VERIFIED: the existing position check reads state that never advanced because the position was never closed, so each new scan looked like a fresh opportunity. decision_log carries an ExistingPosition column at index 35 which was not inspected in this measurement.

SCOPE OF INVESTIGATION: read the ExistingPosition values for the 22/7 rows, find the code path that enforces reentry, and determine whether the guard is absent, misreading state, or correctly bypassed under DRY_RUN. This is a separate bug from the finviz ticker corruption, though it only became visible because of it.

Do not fix without live verification. Quota heavy, run outside market hours.
<!-- SECTION:DESCRIPTION:END -->

## ROOT CORRECTED 2026-08-03

The hypothesis recorded above is wrong. The guard does not misread stale state. It fails OPEN under a Google Sheets 429.

Evidence, agent_minute run 29940103210 (2026-07-22 16:56Z):
  [WARNING] build_account_state: paper_portfolio fetch failed (APIError: [429]: Quota exceeded
  for quota metric 'Read requests' and limit 'Read requests per minute per user'), setting
  paper_portfolio_fetch_failed=True
  [INFO] Account state: 0 open positions, 36 ENTER today, $200000 buying_power
Sixty nine positions were open at that moment. The state reported zero because the read failed, not because the sheet was empty.

Counter evidence from the same day, run 29943602007 (17:44Z), no 429:
  [INFO] Account state: 69 open positions, 40 ENTER today
  [SKIP] ZZCMD Score=30.33 to EXISTING_POSITION: already short ZZCMD
  [SKIP] AADVB, LLABT, IINLF, same reason
So the filter logic is correct. The defect is that a failed read produces defaults that look like a free account: existing_positions empty, open_position_count zero, entries_today_by_ticker empty. Filters 7, 8 and 9 all read that same failed fetch, so they passed together.

The signal already existed and nobody consumed it. build_account_state sets paper_portfolio_fetch_failed at all three failure points (agent/orchestrator.py:228 for paper_portfolio, :274 for decision_log, :302 for the outer handler). The only reader was agent/sentinel/checks/position_sync.py:43, which downgrades a drift BLOCK to a WARN. No entry filter looked at it.

FIX APPLIED 2026-08-03, not yet verified live: Filter 6b in decision_logic._check_filters returns ACCOUNT_STATE_UNAVAILABLE when the flag is set. Placed after the signal only filters 1 to 6 so a signal that fails on its own merits still reports its own reason, and before 7 to 10 because those four are the blind ones. Decision gains the field account_state_unavailable. Four tests added, including backward compatibility for callers that predate the flag and for the None default.

DEPENDS ON TASK-55. This filter stops the damage, it does not stop the 429. While the quota is exhausted the agent will now SKIP instead of entering blind, which is correct but is still lost trading time. The quota pressure is live: 29/7 had 175 cancelled agent_minute runs against 2 on 22/7.

STILL OPEN: the 22/7 day produced 43 ENTERs against a daily cap of 10, which the decision_log read alone should have enforced. That implies both reads failed in the entering runs, not only paper_portfolio. Confirming it needs a decision_log read, which is quota heavy and must wait for market close.
