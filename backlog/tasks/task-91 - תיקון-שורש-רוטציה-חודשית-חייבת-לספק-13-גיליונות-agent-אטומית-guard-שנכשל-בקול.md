---
id: TASK-91
title: >-
  תיקון שורש: רוטציה חודשית חייבת לספק 13 גיליונות agent אטומית + guard שנכשל
  בקול
status: Done
assignee: []
created_date: '2026-06-01 16:16'
updated_date: '2026-06-02 19:39'
labels: []
dependencies: []
priority: high
ordinal: 91000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
1/5 rotation left June with only 9 scanner sheets — agent step failed silently (prepare_next_month failed 14:17 + 14:32, 14:44 succeeded partial). _ensure_month covers only the 9 SHEET_NAMES (scanner), never agent sheets, so get_sheet_id auto-create does NOT self-heal the agent KeyError — it surfaced only 1/6 via the monthly Critic. SCOPE: (1) rotation/prepare_next_month must run create_agent_sheets AND verify all 13 landed in config before reporting success; (2) post-rotation guard that fails LOUDLY (email) if any active month has scanner-but-no-agent sheets; (3) consider extending _ensure_month to agent sheets as last-resort self-heal; (4) fix cosmetic '11 agent sheets' strings in create_agent_sheets.py (really 13). GOAL: 1/7 rotation cannot repeat this silently.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
MERGED TASK-98 (2026-06-02): Bug A — paper_portfolio (and 12 other agent sheets) live in AGENT_SHEET_NAMES (create_agent_sheets.py), NOT in SHEET_NAMES (9 core). _ensure_month self-heal covers only the 9 core, so get_sheet_id('paper_portfolio') raises KeyError if the agent-sheets provisioning step failed silently. This is what crashed the 1/6 monthly Critic (surfaced via TASK-60). Root is identical to TASK-91's non-atomic rotation. Scope for the full fix: (1) prepare_next_month must VERIFY all agent sheets landed in config before reporting success; (2) loud guard (email) if an active month has scanner-but-no-agent sheets; (3) consider extending _ensure_month to agent sheets (needs AGENT_SHEET_HEADERS); (4) fix stale '11 agent sheets' strings (actually 13). June+July already fully provisioned (22 sheets each) — next risk is 1/8 provisioning.    || SCOPE-2 DONE 2026-06-02: health_audit check_28 (AS1) added as the loud guard — active month verified to have all 13 agent sheets, CRITICAL+email if missing. Remaining open: atomic rotation, _ensure_month agent-sheet coverage, stale '11 agent sheets' strings.
<!-- SECTION:NOTES:END -->
