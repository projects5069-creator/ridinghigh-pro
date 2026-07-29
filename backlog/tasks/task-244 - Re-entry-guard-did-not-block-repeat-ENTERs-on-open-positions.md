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
