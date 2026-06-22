---
id: TASK-38
title: AUDIT.3 — Health checks for support agents
status: Done
assignee: []
created_date: '2026-05-24 20:59'
updated_date: '2026-06-22 01:50'
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

VERIFIED DONE 2026-06-21: the 3 support-agent freshness checks already exist + wired in health_audit.py — check_25_critic_agent (agent_scorecard, L1856), check_26_market_context_agent (market_context, L1857), check_27_news_detective_agent (news_findings, L1858), all WARNING via _check_agent_freshness (ran-in-last-trading-day + sheet freshness). No code needed.

Done 2026-06-21: verify-and-close. 3 agent freshness checks already wired — check_25/26/27 (critic/market_context/news_detective) via _check_agent_freshness, WARNING. Zero code needed.
<!-- SECTION:NOTES:END -->
