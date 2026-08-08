---
id: TASK-277
title: Build gate 6 - no aggregate includes a non-CLEAN row
status: To Do
assignee: []
created_date: '2026-08-08 17:53'
labels: []
dependencies: []
priority: medium
ordinal: 275000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-601 (S7_TASKS_v1.md, package 6). PROBLEM: gate 6 does not exist - session S6 built five gates, not six, so the purity claim has never been measured. A gate that does not exist cannot be green. SCOPE: audit_gate/gate6_purity.py (outside the repo, zero production risk) - read paper_portfolio + postmortems, classify rows via formulas.classify_phantom_tier, and check that dashboard/email aggregates filter them: statically, that consumers carry a DataQuality filter; dynamically, by comparing an aggregate computed with and without the contaminated rows. A positive control is mandatory, same discipline as gates 1-5. SEMANTICS ARE ALREADY SETTLED - DO NOT INVENT A SECOND RULE: TASK-246 fixed the two-tier rule on 2026-08-03 (PhantomTicker PHANTOM/PHANTOM_SUSPECT and paper_portfolio.DataQuality PHANTOM_TICKER/PHANTOM_TICKER_SUSPECT), and TASK-246:34 defines what CLEAN means - a statement about shape only. Gate 6 adopts that vocabulary. LIVE TARGETS to check: critic_v1 weekly/monthly builders, templates/daily_brief.py, the dashboard pages, and any future aggregate such as the equity curve discussed in DECISIONS D8. GATE: the script runs and returns a baseline number. BLOCKED BY: nothing to build the gate (measurement); enforcement is the separate marking-and-filtering work, which needs TASK-246 to be executed first.
<!-- SECTION:DESCRIPTION:END -->
