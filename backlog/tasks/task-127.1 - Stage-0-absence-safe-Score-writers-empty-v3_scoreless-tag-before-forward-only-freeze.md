---
id: TASK-127.1
title: >-
  Stage 0: absence-safe Score writers (empty + v3_scoreless tag) before
  forward-only freeze
status: To Do
assignee: []
created_date: '2026-06-18 17:40'
labels:
  - data-integrity
dependencies: []
parent_task_id: TASK-127
priority: high
ordinal: 189000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Forward-only Score removal, Stage 0 = writer-integrity guarantee BEFORE freeze. Make the warehouse writers absence-safe so no masquerading 0-as-Score row is ever written. No-op while Score is still computed; auto-correct at freeze. New score_version tag 'v3_scoreless' is the queryable anchor separating the Score era from the scoreless era.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 post_analysis_collector writes Score='' + score_version='v3_scoreless' when score absent; numeric + 'v2' when present (no-regression)
- [ ] #2 postmortem: _get_decision_context returns Score=None on absence; ScoreAtEntry='' ; forensic prose omits the Score line (guards lines 402-407 AND 444)
- [ ] #3 decision_logger skip_summary ScoreMin/Max written '' when no score seen (freeze)
- [ ] #4 no-op verified on the score-present path; py_compile clean; only the 3 writer files + new test touched
<!-- AC:END -->
