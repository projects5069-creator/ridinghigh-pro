---
id: TASK-96
title: >-
  check_06 robustness — clustered/recovering Actions failures = WARNING not
  CRITICAL
status: To Do
assignee: []
created_date: '2026-06-02 04:52'
updated_date: '2026-06-04 19:51'
labels:
  - health-audit
dependencies: []
priority: medium
ordinal: 96000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
check_06 robustness — WARNING במקום CRITICAL כשכשלי-Actions מקובצים ובהתאוששות (sample-size/clustering gate), כדי שנפילת-checkout זמנית לא תיצור exit-1 שווא — בלי להחליק להשתקת כשל מתמשך. נגזר מ-TASK-84.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Design note 2026-06-04 (decision-ready for a dedicated session — NOT started, code untouched). Current check_06 (health_audit.py:556): success_rate >=95 PASSED / >=80 WARNING / <80 CRITICAL+exit-1. Gate to add — 3 design decisions: (1) RECOVERING: latest run (or latest N) per-workflow succeeded => recovered; (2) CLUSTERED: failures concentrated in short time window / same workflow / contiguous burst; (3) SAMPLE-SIZE: if completed < ~10, a single failure swings the rate => downgrade. Required test cases: persistent failures => CRITICAL preserved (NO masking); clustered+recovered => WARNING; tiny-sample => WARNING. RISK: a bad gate masks a persistent failure (explicit task constraint). Implement with TDD. Derived from TASK-84.
<!-- SECTION:NOTES:END -->
