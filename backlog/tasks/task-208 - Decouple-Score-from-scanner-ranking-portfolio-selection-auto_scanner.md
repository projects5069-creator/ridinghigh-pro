---
id: TASK-208
title: Decouple Score from scanner ranking + portfolio selection (auto_scanner)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
labels: []
dependencies: []
priority: low
ordinal: 214000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
auto_scanner selects/ranks by Score (TRADE_ENTRY_MIN_SCORE>=70, idxmax/sort) at :490/578/1335/1338. After 194/S1 decoupled Score from entry gate, decide MxV-ranking vs lower threshold. Display/portfolio layer, separate from entry decision.
<!-- SECTION:DESCRIPTION:END -->
