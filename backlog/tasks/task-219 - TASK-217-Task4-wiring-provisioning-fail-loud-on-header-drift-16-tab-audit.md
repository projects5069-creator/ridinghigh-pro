---
id: TASK-219
title: 'TASK-217 Task4 wiring: provisioning fail-loud on header drift (+16-tab audit)'
status: To Do
assignee: []
created_date: '2026-07-02 04:42'
labels: []
dependencies: []
ordinal: 225000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Guard functions header_matches_canonical + assert_header_canonical are committed (ad95806, pure, 5/5). WIRING deferred: add to create_agent_sheets._already_done a per-tab check vs AGENT_SHEET_HEADERS. DECISION NEEDED: raise (halt rotation) vs warn+log; scope (paper_portfolio only vs all 16). PREREQ: audit all 16 agent tabs x3 months (05/06/07) to find other drifts before enabling raise (avoid halting 1/8 rotation). Follow-up of TASK-217.
<!-- SECTION:DESCRIPTION:END -->
