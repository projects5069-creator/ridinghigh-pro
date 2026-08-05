---
id: TASK-244
title: Re-entry guard did not block repeat ENTERs on open positions
status: To Do
assignee: []
created_date: '2026-07-29 09:27'
updated_date: '2026-08-05 20:33'
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

DEPENDS ON TASK-215 (Dedicated SA for auto_scan, To Do). Corrected 2026-08-05: this line previously named TASK-55, which has status Done — TASK-55 covered the health_audit contribution and closed on it, and TASK-213 verified that reduction. What remains open is the agent_minute and auto_scan read burst, owned by TASK-215. This filter stops the damage, it does not stop the 429. While the quota is exhausted the agent will now SKIP instead of entering blind, which is correct but is still lost trading time. The quota pressure is live: 29/7 had 175 cancelled agent_minute runs against 2 on 22/7.

STILL OPEN: the 22/7 day produced 43 ENTERs against a daily cap of 10, which the decision_log read alone should have enforced. That implies both reads failed in the entering runs, not only paper_portfolio. Confirming it needs a decision_log read, which is quota heavy and must wait for market close.

## CORRECTION 2026-08-03, same evening

The DEPENDS ON line above names TASK-55. That is wrong. TASK-55 has status Done.

The open owner of the 429 root is TASK-215, Dedicated SA for auto_scan, mirror TASK-58, real fix for market hours 429, status To Do. TASK-55 covered the health_audit contribution and closed on it; TASK-213 verified that specific reduction. What remains is the agent_minute and auto_scan read burst, which is TASK-215.

Quota state measured 2026-08-03, and it moved: cancelled agent_minute runs were 118 on 07-31 and 25 on 08-03, cancelled auto_scan runs were 79 on 07-31 and zero on 08-03. Sampled agent_minute runs from today still carry 5 to 9 lines mentioning 429, so the pressure is lower but not gone. Why today was better is not established. It may be lower scan volume rather than any fix.

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
MEASURED 2026-08-05 — the SCOPE OF INVESTIGATION question is answered.

Source: reports/2026-08-05_1455_measurement.md Q-244.

decision_log 2026-07, every row dated 2026-07-22:
  rows on 2026-07-22                 = 43
  Action counts                      = {'ENTER': 43}
  ExistingPosition value counts      = {'FALSE': 43}
  tickers = {'LLABT': 11, 'IINLF': 11, 'AADVB': 11, 'ZZCMD': 10}

THE ANSWER: not absent, not bypassed — WRONG INPUT. All 43 rows carry the literal string
FALSE. The field is not blank and not missing, so the guard ran on every one of them and
applied a value that was false. build_account_state returned a state in which no position
existed, and filters 7 through 10 each honoured it. F6b (decision_logic.py:428) is the
correct fix for exactly this: it refuses to evaluate the exposure filters at all when the
account state could not be read.

ACCOUNT_STATE_UNAVAILABLE rows in decision_log 2026-08 = 0. In skip_summary 2026-08 there
are 2, both on 2026-08-04 on AMIX. The discrepancy is Route B: SKIPs are counted in
skip_summary and never written to decision_log (decision_logger.py:322-346).

IMPORTANT — F6b DOES NOT COVER THE OTHER ROOT. The investigation of 2026-08-05
(reports/2026-08-05_1515_reentry_breach.md) found the re-entry cap breached twice on
2026-08-05, on DFNS and SHPH, with NO 429 and NO ACCOUNT_STATE_UNAVAILABLE anywhere that
day, while REENTRY_LIMIT fired 269 times and EXISTING_POSITION 48 times. That breach has
a different cause: agent_minute runs overlap (median run duration 292s against a 60s
cron, 92.5% of consecutive pairs overlapping), so build_account_state snapshots a world
that predates the earlier run's decision. F6b closes the 429 path only. The overlap path
is filed separately.

Stays To Do: the live verification of F6b under a real 429 has not happened — August
produced no 429 on the agent path to test it against.
<!-- SECTION:NOTES:END -->
