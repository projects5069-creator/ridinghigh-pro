---
id: TASK-121
title: 'חיבור דור-שני: ריצת-לילה אוטונומית ↔ Agent #8'
status: Done
assignee: []
created_date: '2026-06-08 18:52'
updated_date: '2026-06-12 03:24'
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
- [x] #2 שלב 2a: ריצת-לילה auto-mode בפיקוח (TASK-114) מייצרת night/* + Run Log; Agent #8 מאמת כלל-5=✅ (לא 'לא-ודאי'); עמיחי מכריע merge
- [x] #3 מנגנון run-log: section '## Run Log' נוסף ל-NIGHT_RUN_TEMPLATE.md (Anti-Drift) ו-Agent #8 קורא stop-counters
- [ ] #4 שלב 2b/2c (לא-מפוקח): routine update + cron-בוקר + ריצת-לילה לא-מפוקחת end-to-end — מאחורי gates מפורשים (RULE #6)
- [ ] #5 כל G1-G5 סגורים + מתועד ב-PK (bump)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-06-08 (שמירת-ביניים): AC#2 (2a/TASK-114 attended auto-mode → §3.3 כלל-5=✅ → merged) ו-AC#3 (Run Log mechanism ב-NIGHT_RUN_TEMPLATE + Agent #8 קורא stop-counters) סומנו ✅. בנוסף 2b-prep (TASK-117 — auto-mode אמיתי בפיקוח) הושלם: classifier של --permission-mode auto נצפה עובד (n=1), night/TASK-117 → Agent #8 verdict Ready → PR #15 squash-merged ff9b1c9. הזרימה night/*→#8→§3.3→verdict→merge הוכחה 3× (120/114/117). נשאר פתוח: AC#4 (2c לא-מפוקח: routine תפעולי + cron-בוקר + ריצה עיוורת) ו-AC#5 (G1-G5 + PK), מאחורי gates RULE #6 / כלל-בטיחות #7. TASK-121 נשאר In Progress.

[DECISION 2026-06-11] AC4-5 DESCOPED (parked). Core AC1-3 delivered & proven: supervised test (TASK-120), supervised auto-mode (TASK-114), Run Log + stop-counters — validated across Wave A and the 2c-1 run (skip-valve fired correctly twice, n=2). AC4-5 (unattended operational routine + morning cron + blind night run; G4 cron-trigger) NOT pursued, by explicit decision. Rationale (LIVE backlog counts of the 25 AUTO-triaged): 5 Done (133/138/150/160/118); 13 fence-excluded [Sheets-write 42/74/152 · non-Group-A read 61/126 · scanner 113 · behavior/creds 39/58/109 · environment 101 · skill-gate 54 · semantic-HUMAN 46/151]; 7 unassessed (143/38/87/88/89/122 + 96=parallel) most of which will also hit Sheets/data/judgment on recon. The genuinely clean-auto pool is small, and attended batches already clear it with the human at the merge gate — so a cloud-unattended build's complexity + failure-surface on a LIVE trading system outweigh autonomously clearing a handful of mostly-doc tasks. Operating model going forward: attended batches for the clean-auto slice; human-at-the-gate (CC-assisted) for anything touching Sheets / scanner / judgment. Status -> Done (decision = terminal resolution; AC4-5 descoped, not built). Pointer in docs/RUN_MODE_DECISION.md.
<!-- SECTION:NOTES:END -->
