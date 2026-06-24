---
id: TASK-194
title: >-
  Stage 2 flip (ADR-009): remove live Score gate + ranking after shadow proves
  benign
status: To Do
assignee: []
created_date: '2026-06-24 16:10'
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
