---
id: TASK-242
title: August provisioning - canonical root + 16 agent tabs before 1/8 rotation
status: Done
assignee: []
created_date: '2026-07-29 08:00'
updated_date: '2026-07-29 09:07'
labels:
  - bug
  - infra
  - deadline
dependencies: []
priority: high
ordinal: 240000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
DEADLINE: monthly_rotation 2026-08-01 05:01 UTC. Verified read-only 2026-07-29.

STATE (verified via Drive API, OAuth projects5069@gmail.com):
(a) sheets_config[2026-08] has 9/25 tabs. Missing exactly the 16 AGENT_SHEET_NAMES: agent_scorecard, borrow_coverage, borrow_data, config_history, decision_log, market_context, news_findings, paper_portfolio, pending_suggestions, postmortems, score_analytics, sentinel_events, shadow_gate_events, skip_summary, system_events, weekly_summary. Config sha 003b108e identical across HEAD/origin-main/main/all active branches.
(b) All 9 core August sheets live in 1S5bAu4ppxscJE8X-FbtT2BGxs7-_nyR8 = 2026-08 under RidingHigh-Data (KNOWN_BAD_ROOT 1u330dPM). Canonical/2026-08 = 1k-N29HSIX13KHAgyg4qXZ6H6V_KcS0RQ exists, trashed=false, 0 children.
(c) NEW AND WORSE: permissions.list shows the 9 August sheets carry only 2 permissions (owner + ridinghigh-sheets-v2). No _AS, no _AM, no _HA. July sheets carry 5. From 1/8 auto_scan (runs as _AS) gets 403 on timeline_live, daily_snapshots, portfolio, portfolio_live, score_tracker, live_trades. Loud failure, not a silent data hole.

ROOT CAUSE (corrects the 7/29 handoff): the canonical root 1mHSdsT has permissions owner + _AS writer + _AM writer + _HA reader and does NOT include ridinghigh-sheets-v2. So sheets_manager._get_root_folder_id:254 files().get under the shared SA genuinely 404s and the RidingHigh-Data fallback is formally correct. monthly_rotation runs SA-only so it always creates in the wrong root, while prepare_next_month.py and create_agent_sheets.py hardcode ROOT_FOLDER_ID and run OAuth so they hit the canonical one. Monthly loop, not an event. Tail: prepare_next_month.py:212 creates the canonical folder first, then find_duplicate_month_folders sees 2 and raises, so the next workflow step (create_agent_sheets --next-month) never runs. assert_correct_root(ROOT_FOLDER_ID) at :210 compares a constant to itself and catches nothing.

STEPS (each needs separate explicit approval):
1. re-share the 9 August sheets with _AS writer, _AM writer, _HA reader (27 permission calls). BLOCKING. Chosen over relying on move-propagation: Drive propagation-on-move is documented by Google but NOT verified live in this repo.
2. create_agent_sheets --month 2026-08, then commit AND push sheets_config.json (GH Actions read it from the repo). BLOCKING.
3. share canonical root with ridinghigh-sheets-v2 as writer, breaking the monthly loop. Blast-radius: grants the shared SA write access to the whole tree. Alternative is fixing _get_root_folder_id to resolve via OAuth (code change + TDD).
4. move the 9 sheets into canonical/2026-08. Structural cleanup, not blocking. Safe: grep addParents/removeParents returns NONE_FOUND, sheets_config is fully ID-based.
5. PK bump (Anti-Drift; PK is 4.07/2026-07-05 while 223/231/239 shipped).
6. Hardening, separate task: tautological assert_correct_root, guard ordering, check_28 only inspects the ACTIVE month so it alerts a month late.
<!-- SECTION:DESCRIPTION:END -->
