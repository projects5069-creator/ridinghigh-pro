---
id: TASK-150
title: Enforce header-aware cross-month reads; June column-order drift
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-12 03:15'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 153000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-4.1: April post_analysis has 122 cols vs 105 in May/June (17 legacy Score_B-I etc.); May vs June same set but DIFFERENT ORDER from idx 60 (score_version moved before IntraHigh). Any positional reader breaks across months. Add an audit check + document in PK schema section. Evidence: phase4_evidence.md (a)
<!-- SECTION:DESCRIPTION:END -->
