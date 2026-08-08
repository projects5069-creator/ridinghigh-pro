---
id: TASK-274
title: Qualify the REALIZED P&L dollars in the daily email
status: To Do
assignee: []
created_date: '2026-08-08 17:52'
labels: []
dependencies: []
priority: medium
ordinal: 272000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-104 (S7_TASKS_v1.md, gate 1 extension T1d). PROBLEM: templates/daily_brief.py:129 (subject line) and :169 (the headline number) print a REALIZED P&L dollar figure that is a sum of RealizedPnL - dollars derived from the Quantity that finding CR-02 showed is wrong at the write site - with no qualification at all. GOOD NEWS ALREADY VERIFIED: WIN RATE on the same page IS already qualified via fmt_rate_ci at daily_brief.py:127, so only the dollars are exposed. SCOPE: add a caption - PnL dollars derive from Quantity, see the quantity-recompute task - until package 3 lands, and add item T1d to audit_gate/gate1_truth.py (edit is outside the repo). GATE: extended gate 1 green. BLOCKED BY: soft dependency on the quantity-recompute work (T-301, not yet a ticket); the caption is the interim. CROSS-REF: TASK-39 (email consolidation) covers the same mail from a volume angle - if 39 runs first the caption lands in the new template. Side note from the same read: gather_daily_stats calls ws.get_all_records() raw at :63/:83/:161 instead of the get_sheet_records cache - three unoptimised reads a day, not blocking.
<!-- SECTION:DESCRIPTION:END -->
