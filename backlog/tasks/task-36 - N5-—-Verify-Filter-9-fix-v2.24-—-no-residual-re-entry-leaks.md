---
id: TASK-36
title: N5 — Verify Filter 9 fix (v2.24) — no residual re-entry leaks
status: Done
assignee: []
created_date: '2026-05-23 22:32'
updated_date: '2026-05-23 22:58'
labels: []
dependencies: []
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
PK v2.24 (19/5) fixed Filter 9 re-entry leak (counted from decision_log instead of paper_portfolio). But the fix happened AFTER both leaks already manifested: PIII×14 on 15/5 and HCAI×4 on 18/5. Verify no ticker has >3 ENTERs/day after 2026-05-19. If clean = close as verified. If not clean = real bug, escalate.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Query decision_log: count ENTERs per (date, ticker) for dates >= 2026-05-20
- [ ] #2 Confirm no ticker exceeds 3 ENTERs on any day
- [ ] #3 If any exceed: investigate which other path leaks
<!-- AC:END -->

## AUDIT 2026-08-03: THE CONDITION RETURNED

This task closed on the rule "no ticker has more than 3 ENTERs per day after 2026-05-19, if clean close as verified". It is no longer clean.

Measured from decision_log on 2026-08-03: 2026-07-22 LLABT 11, IINLF 11, AADVB 11, ZZCMD 10. 2026-07-16 AATPC 9, VVEEE 8. Eleven ticker day pairs exceed two ENTERs, with 54 entries beyond the cap.

The threshold in the closing rule is also stale. AGENT_MAX_REENTRIES_PER_TICKER became 1 on 2026-06-29, so "more than 3" no longer describes the contract.

Root cause is not Filter 9 itself. Under a Sheets 429 build_account_state returns defaults and Filters 7, 8 and 9 all read the same failed fetch, so they pass together. See TASK-244 for the evidence and the fix, and TASK-55 for the quota cause. Status left unchanged, reopening is a judgement call for the owner.
