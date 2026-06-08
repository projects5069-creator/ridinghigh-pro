---
id: TASK-121
title: 'חיבור דור-שני: ריצת-לילה אוטונומית ↔ Agent #8'
status: To Do
assignee: []
created_date: '2026-06-08 18:52'
updated_date: '2026-06-08 18:54'
labels:
  - agent8
  - night-run
  - gen2
  - wiring
dependencies: []
priority: high
ordinal: 124000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
איחוד TASK-102/103 (ריצת-לילה אוטונומית — RUN_MODE_DECISION + NIGHT_RUN_TEMPLATE) עם TASK-94 (Agent #8 Routine Checker) לזרימה אחת: לילה עובד → night/* branch (PR בלי merge) → בוקר Agent #8 בודק → §3.3 verdict → עמיחי מכריע merge. מקור-אמת: docs/plan (plan-optimized-bird.md, מקומי ב-~/.claude/plans/). שלב 1 (מבחן בפיקוח, קלט TASK-120) Done — night/TASK-120 → §3.3 Ready → merged 81313d1. שלב 2: 2a ריצת-לילה בפיקוח (auto-mode + /goal, קלט TASK-114, + מנגנון run-log שסוגר כלל-5); 2b/2c לא-מפוקח (routine update + cron-בוקר + ירי) = החלטה נפרדת מפורשת מאחורי gates (RULE #6, כלל-בטיחות #7). פערים G1-G5: G1 מרחב-שמות night/*, G2 push ל-origin, G3 no-merge, G4 טריגר-בוקר, G5 metadata/run-log.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 שלב 1 (מבחן בפיקוח, night/TASK-120 → Agent #8 §3.3 Ready → merge): ✅ Done (81313d1)
- [ ] #2 שלב 2a: ריצת-לילה auto-mode בפיקוח (TASK-114) מייצרת night/* + Run Log; Agent #8 מאמת כלל-5=✅ (לא 'לא-ודאי'); עמיחי מכריע merge
- [ ] #3 מנגנון run-log: section '## Run Log' נוסף ל-NIGHT_RUN_TEMPLATE.md (Anti-Drift) ו-Agent #8 קורא stop-counters
- [ ] #4 שלב 2b/2c (לא-מפוקח): routine update + cron-בוקר + ריצת-לילה לא-מפוקחת end-to-end — מאחורי gates מפורשים (RULE #6)
- [ ] #5 כל G1-G5 סגורים + מתועד ב-PK (bump)
<!-- AC:END -->
