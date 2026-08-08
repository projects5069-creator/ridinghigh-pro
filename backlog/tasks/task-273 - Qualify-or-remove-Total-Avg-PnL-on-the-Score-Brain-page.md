---
id: TASK-273
title: Qualify or remove Total/Avg PnL on the Score Brain page
status: To Do
assignee: []
created_date: '2026-08-08 17:52'
labels: []
dependencies: []
priority: low
ordinal: 271000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-102 (S7_TASKS_v1.md, gate 1 T1c). PROBLEM: agent/dashboard/score_brain_page.py:92-93 shows Total PnL and Avg PnL as percentages with no qualification, while finding E-09 measured CI95 [-0.362, +4.995] - the interval contains zero. The page presents noise as a result. SCOPE: add a caption carrying n= and the CI (reuse the existing fmt_rate_ci helper already used at templates/daily_brief.py:127), or remove both metrics. GATE: audit_gate/gate1_truth.py item T1c green - the grep detects a qualification token near the display. NOTE STATED HONESTLY: there is no render unit test for Streamlit pages; the gate is the only automated check, no AC is invented beyond it. BLOCKED BY: the fate of the page itself sits with TASK-209 (Score cluster, parked until the HYP-002 verdict in early October). If 209 retires the page, this task evaporates - sequence after 209.
<!-- SECTION:DESCRIPTION:END -->
