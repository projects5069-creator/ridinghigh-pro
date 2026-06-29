---
id: TASK-209
title: Retire calculate_score or demote to logged diagnostic (~15 consumers)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
labels: []
dependencies: []
priority: low
ordinal: 215000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
calculate_score feeds ~15 display/analysis consumers (dashboard, post_analysis_collector, health_check, health_audit). After 194 decoupled Score from entry, decide full retire vs keep as documented diagnostic. High blast-radius; likely keep as diagnostic.
<!-- SECTION:DESCRIPTION:END -->
