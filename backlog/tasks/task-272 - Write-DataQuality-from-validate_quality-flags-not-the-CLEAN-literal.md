---
id: TASK-272
title: 'Write DataQuality from validate_quality flags, not the CLEAN literal'
status: To Do
assignee: []
created_date: '2026-08-08 17:52'
labels: []
dependencies: []
priority: medium
ordinal: 270000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-101 (S7_TASKS_v1.md, gate 1 T1a). PROBLEM: order_manager.py:283 writes "DataQuality": "CLEAN" as a literal - a trustworthiness label nothing checked. And data_quality.py:32-132 validates 5 single-field ranges with zero cross-field consistency, so a TTC row with Price 3.46 and High 93.59 passed with score 1. SCOPE: (1) data_quality.py - add check 6: price within [low, high] when both present, flag PRICE_BAR_MISMATCH; (2) decision_logic.py:273-278 - preserve quality[flags] on the Decision as a new quality_flags field; (3) order_manager.py:283 - write CLEAN only when flags are empty, else join them. NOT IN SCOPE: do not touch is_trustworthy (the decision threshold) - that is gate behaviour and a separate decision. GATE: audit_gate/gate1_truth.py item T1a green + unit: a TTC-shaped signal yields DataQuality != CLEAN + regression: a new row with the CLEAN literal while flags are non-empty. RED-first: test_dataquality_reflects_flags_v1.py fails today (always CLEAN). BLOCKED BY: nothing. CROSS-REF: TASK-217 touches the same 25-element paper_portfolio row (different defect - column alignment).
<!-- SECTION:DESCRIPTION:END -->
