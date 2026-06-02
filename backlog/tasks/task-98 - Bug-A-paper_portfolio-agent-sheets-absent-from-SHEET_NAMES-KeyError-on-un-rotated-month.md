---
id: TASK-98
title: >-
  Bug A: paper_portfolio + agent sheets absent from SHEET_NAMES (KeyError on
  un-rotated month)
status: Done
assignee: []
created_date: '2026-06-02 17:15'
updated_date: '2026-06-02 17:51'
labels: []
dependencies: []
priority: high
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
_ensure_month only auto-provisions the 9 core SHEET_NAMES; paper_portfolio (and other agent sheets) are created only by create_agent_sheets.py at rotation. If the monthly cron runs before rotation completes, get_sheet_id('paper_portfolio') raises KeyError. This is what crashed the 1/6 monthly run. Root cause overlaps TASK-91 (atomic rotation with guard). Link to TASK-91. Discovered 2026-06-02.
<!-- SECTION:DESCRIPTION:END -->
