---
id: TASK-219
title: 'TASK-217 Task4 wiring: provisioning fail-loud on header drift (+16-tab audit)'
status: To Do
assignee: []
created_date: '2026-07-02 04:42'
updated_date: '2026-07-03 02:06'
labels: []
dependencies: []
ordinal: 225000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Guard functions header_matches_canonical + assert_header_canonical are committed (ad95806, pure, 5/5). WIRING deferred: add to create_agent_sheets._already_done a per-tab check vs AGENT_SHEET_HEADERS. DECISION NEEDED: raise (halt rotation) vs warn+log; scope (paper_portfolio only vs all 16). PREREQ: audit all 16 agent tabs x3 months (05/06/07) to find other drifts before enabling raise (avoid halting 1/8 rotation). Follow-up of TASK-217.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Wiring implemented+committed (66c984c, PK v4.01): CORE_TABS raise (paper_portfolio/decision_log/postmortems), observability warn, _set_headers hardened. Guard sits in create_agent_sheets idempotency (not-dry-run). Live audit confirmed CORE 9/9 MATCH across 05-07 pre-commit. CI green. NOT Done: raise fires only at rotation 1/8 — pending live behavior verification (or controlled dry-run). Kept To Do.
<!-- SECTION:NOTES:END -->
