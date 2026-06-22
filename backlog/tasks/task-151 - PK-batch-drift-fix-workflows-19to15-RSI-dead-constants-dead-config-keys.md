---
id: TASK-151
title: 'PK batch drift fix: workflows 19to15, RSI dead constants, dead config keys'
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-22 01:50'
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
PARTIAL 2026-06-16: workflow-count drift was already fixed (PK line 19 = 17 = ground-truth, via TASK-138 7->16 + TASK-163 16->17) — task premise ('says 7') was stale. Fixed the real remaining doc-drift: SCORE_CAPS_V2 RSI_LOW 50->60 to match config.py:57 + removed false '(alias)' (PK v3.30). STILL OPEN: RSI-semantics claims ('bell curve 50-70 false', SCORE_RSI_PARAMS dead — config HAS it at :64 with CENTER_LOW=50) need code-investigation of the actual score-RSI path (out of docs-only scope); 9 dead config constants (MIN_PRICE etc) = separate code cleanup. Extends 129+138.

PARTIAL-2 2026-06-21: removed only AGENT_NO_TIME_LIMIT (truly 0-ref dead). VERIFICATION corrected the premise: RSI_LOW/RSI_HIGH are NOT dead (live dict keys, config:56-57, RSI scoring); MARKET_CLOSE_HOUR_PERU in use (2 refs); MIN_PRICE/MAX_HOLDING_DAYS/MEDIUM_SCORE are intentional DISPLAY-ONLY (config:153). RSI-semantics PK claim = separate code-investigation, out of scope. Remaining 'dead config' scope is effectively closed.

RESOLVED 2026-06-21: dead-const scope done (removed AGENT_NO_TIME_LIMIT; RSI_LOW/HIGH are live dict keys, MARKET_CLOSE in use, MIN_PRICE/MAX_HOLDING_DAYS/MEDIUM_SCORE intentionally display-only per config:153 — premise '9 dead' was wrong). RSI-semantics PK-vs-code claim spun off to TASK-188.
<!-- SECTION:NOTES:END -->
