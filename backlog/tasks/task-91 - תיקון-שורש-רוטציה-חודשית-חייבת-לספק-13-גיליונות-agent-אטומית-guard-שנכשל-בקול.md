---
id: TASK-91
title: >-
  תיקון שורש: רוטציה חודשית חייבת לספק 13 גיליונות agent אטומית + guard שנכשל
  בקול
status: To Do
assignee: []
created_date: '2026-06-01 16:16'
labels: []
dependencies: []
priority: high
ordinal: 91000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1/5 rotation left June with only 9 scanner sheets — agent step failed silently (prepare_next_month failed 14:17 + 14:32, 14:44 succeeded partial). _ensure_month covers only the 9 SHEET_NAMES (scanner), never agent sheets, so get_sheet_id auto-create does NOT self-heal the agent KeyError — it surfaced only 1/6 via the monthly Critic. SCOPE: (1) rotation/prepare_next_month must run create_agent_sheets AND verify all 13 landed in config before reporting success; (2) post-rotation guard that fails LOUDLY (email) if any active month has scanner-but-no-agent sheets; (3) consider extending _ensure_month to agent sheets as last-resort self-heal; (4) fix cosmetic '11 agent sheets' strings in create_agent_sheets.py (really 13). GOAL: 1/7 rotation cannot repeat this silently.
<!-- SECTION:DESCRIPTION:END -->
