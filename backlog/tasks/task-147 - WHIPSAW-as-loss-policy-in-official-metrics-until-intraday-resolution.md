---
id: TASK-147
title: WHIPSAW-as-loss policy in official metrics until intraday resolution
status: To Do
assignee: []
created_date: '2026-06-11 04:02'
labels:
  - TASK-139
dependencies: []
priority: medium
ordinal: 150000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139 RH-6.3 sensitivity: 26 WHIPSAW rows excluded from n=123; if resolved at SL the edge turns negative in ALL borrow scenarios (-1.28 to -2.66 pct/trade). Until intraday data resolves them (ties TASK-26), official metrics should report a WHIPSAW-as-loss pessimistic bound alongside the optimistic one
<!-- SECTION:DESCRIPTION:END -->
