---
id: TASK-194
title: >-
  Stage 2 flip (ADR-009): remove live Score gate + ranking after shadow proves
  benign
status: To Do
assignee: []
created_date: '2026-06-24 16:10'
updated_date: '2026-06-29 23:30'
labels:
  - agent
  - score
dependencies: []
priority: medium
ordinal: 200000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ADR-009 Stage 2 driver-removal — the LIVE flip deferred by the 141+174 ruling (Option B, shadow-first). BLOCKED until >=2 weeks of multi-regime shadow_gate_events data (TASK-128) show the SCORE_TOO_LOW->would-ALLOW divergence is benign. Then either flip EXPLICIT_GATE_MODE to active, OR remove Filter 1 Score gate (decision_logic.py:277 d.score<AGENT_MIN_SCORE) + Score ranking (auto_scanner.py:578/1338 idxmax / TRADE_ENTRY_MIN_SCORE>=70) + retire calculate_score. Two-shape tolerant history reads (ADR-009 over-principle). Linked: TASK-128 (shadow owner) + ADR-009. Decision-gates 141/174/127 already Done (decision recorded). TDD + ping-pong when unblocked.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 decision_logic live path (evaluate_signal) honors EXPLICIT_GATE_MODE: shadow=Score gates byte-identical, active=Filter 1 skipped + filters 2-11 decide (TDD)
- [x] #2 flip AND revert = single EXPLICIT_GATE_MODE config value; zero code change to toggle
- [x] #3 stage-1 lands flag=shadow -> zero live-behavior change verified (shadow test byte-identical)
- [ ] #4 flip executed 2026-06-29 ahead of shadow-accumulation (owner decision, DRY_RUN/reversible); monitoring now POST-flip: track active-mode entries + outcomes vs prior Score-gated; revert=EXPLICIT_GATE_MODE shadow
- [x] #5 zero touch to scanner-ranking (S2) and calculate_score retire (S3) - separate tasks (208/209)
- [x] #6 PK + ADR-009 updated with decision + reversible-flag mechanism
<!-- AC:END -->
