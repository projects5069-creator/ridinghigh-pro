---
id: TASK-38
title: AUDIT.3 — Health checks for support agents
status: To Do
assignee: []
created_date: '2026-05-24 20:59'
labels: []
dependencies: []
priority: medium
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add health_audit.py checks for Critic, Market Context, and News Detective agents. Verify each ran in last 24h + their output sheets are being updated.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified bug 24/5: 5 days of silence. Add 3 checks for agent_scorecard, market_context, news_findings freshness. WARNING level.
<!-- SECTION:NOTES:END -->
