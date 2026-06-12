---
id: TASK-151
title: 'PK batch drift fix: workflows 19to15, RSI dead constants, dead config keys'
status: To Do
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-12 01:34'
labels:
  - TASK-139-INV
dependencies: []
priority: low
ordinal: 154000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV D1+RH-1.1+RH-1.2: PK line 19 says 'Active workflows: 7' vs 15 actual; RSI_LOW/RSI_HIGH/SCORE_RSI_PARAMS dead (code uses hardcoded 80/85/90 steps, PK sec-18 'bell curve 50-70' false twice); 9 dead config constants (MIN_PRICE, MAX_HOLDING_DAYS, market-hours consts, MEDIUM_SCORE, AGENT_NO_TIME_LIMIT...). Extends TASK-129+TASK-138. Evidence: phase1+phase8
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[recon 2026-06-11, Wave A] Skipped — superseded/overlapping/needs-audit. (1) workflow-count '7→16' is now DONE under TASK-138 (PK v3.05, merged #17). (2) The RSI dead-constants + 'bell curve 50-70 false' part OVERLAPS TASK-129 (RSI drift, code side) — unclear ownership of the PK RSI text; left untouched to avoid stepping on 129. (3) The only unique remaining work = a dead-config-constant audit: SCORE_RSI_PARAMS/MIN_PRICE/MAX_HOLDING_DAYS/MEDIUM_SCORE still have 2-3 code refs, so 'dead' is NOT yet verified — writing 'dead' into the PK without per-constant proof would create NEW drift. RECOMMENDATION: split into a focused task = 'per-constant deadness audit + PK doc' (verify each constant's refs are defs-only before documenting), and let TASK-129 own the RSI text.
<!-- SECTION:NOTES:END -->
