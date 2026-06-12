---
id: TASK-122
title: >-
  סנכרון drift: PK v2.90 + plan §5 טוענים TASK-117=auto-mode אבל NIGHT_RUN Run
  Log אומר supervised/Stop-hook (attended). classifier auto-mode עדיין n=1 (לא n
  הוכח). לתקן את הטענה בשני המקומות + להעריך אם צריך עוד ריצת-auto אמיתית בפיקוח
  לפני 2c
status: Done
assignee: []
created_date: '2026-06-09 22:35'
updated_date: '2026-06-12 23:37'
labels:
  - infra
  - agent8
  - drift
dependencies: []
priority: medium
ordinal: 125000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-12 — resolved as NO-OP after verification: the claimed drift does NOT exist. (1) PK v2.90 already self-caveats — 'classifier auto-mode נצפה n=1 בלבד, שווה לשקול עוד ריצת-auto בפיקוח' — no overclaim. (2) The 'plan §5' stale assertion was NOT found (grep of docs returns nothing; NIGHT_RUN docs explicitly say attended/NOT auto-mode). (3) Remaining item = a HUMAN judgment call (another supervised auto-run before 2c), not a doc edit. No PK edit needed. Verify-before-fix: the small 'docs drift' was confirmed already-accurate.
<!-- SECTION:NOTES:END -->
