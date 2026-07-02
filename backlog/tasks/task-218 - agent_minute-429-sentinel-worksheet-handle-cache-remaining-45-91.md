---
id: TASK-218
title: 'agent_minute 429: sentinel worksheet-handle cache (remaining 45/91)'
status: To Do
assignee: []
created_date: '2026-07-02 04:42'
labels: []
dependencies: []
ordinal: 224000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After TASK-176 removed news_detective (46/91), agent.sentinel still calls get_worksheet('sentinel_events') per BLOCK/WARN event (~45/91 429 on the dedicated _AM SA). Cache the worksheet handle once/run. Connects to TASK-213 (429 measurement) + TASK-217 (paper_portfolio). MARKET-SAFE code.
<!-- SECTION:DESCRIPTION:END -->
