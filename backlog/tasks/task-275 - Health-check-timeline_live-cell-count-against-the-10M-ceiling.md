---
id: TASK-275
title: 'Health check: timeline_live cell count against the 10M ceiling'
status: To Do
assignee: []
created_date: '2026-08-08 17:52'
labels: []
dependencies: []
priority: medium
ordinal: 273000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-204 (S7_TASKS_v1.md, gate 2 c3). PROBLEM: findings B-09 and R24 - there is zero mention of the Google Sheets 10M-cell ceiling anywhere in the live code. Finding H-01 measured May at 84.4% of the ceiling, a margin of 1.08x. timeline_live is the heaviest writer (~250-300K rows/month) and TASK-253 shows duplicate rows from overlapping runs inflate that same counter. SCOPE: new check in health_audit.py using sheet.properties.gridProperties (one metadata read) to report percent of 10M; proposed thresholds WARNING 60% / CRITICAL 80% - owner may change them, not blocking. INTERNAL PRECONDITION: read monthly_rotation.py (207 lines) before writing - it is the only mechanism standing between timeline_live and the ceiling and has never been read. GATE: audit_gate/gate2_detection.py item c3 green + injected control: a mocked 8.5M cell count yields CRITICAL. PATTERN: follow the injection point and shape used by TASK-252 (health_audit.py ~line 2005, one results.append per check). BLOCKED BY: nothing (T-201 SMTP already deployed, so an alert would now be delivered).
<!-- SECTION:DESCRIPTION:END -->
