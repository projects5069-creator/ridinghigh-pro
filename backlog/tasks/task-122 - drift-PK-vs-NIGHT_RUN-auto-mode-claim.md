---
id: TASK-122
title: >-
  סנכרון drift: PK v2.90 + plan §5 טוענים TASK-117=auto-mode אבל NIGHT_RUN Run
  Log אומר supervised/Stop-hook (attended). classifier auto-mode עדיין n=1 (לא n
  הוכח). לתקן את הטענה בשני המקומות + להעריך אם צריך עוד ריצת-auto אמיתית בפיקוח
  לפני 2c
status: To Do
assignee: []
created_date: '2026-06-09 22:35'
updated_date: '2026-06-12 01:34'
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
[recon 2026-06-11, Wave A] Skipped — scope unclear / likely already-resolved. (1) The claimed 'plan §5' assertion that TASK-117=auto-mode-proven was NOT found: grep for TASK-117/auto-mode in docs/RIDINGHIGH_FIX_PLAN_2026-06-09.md returns no such §5 claim. (2) PK already self-caveats: v2.90 changelog explicitly states 'classifier נצפה n=1 בלבד — שווה לשקול עוד ריצת-auto בפיקוח'. (3) The remaining 'evaluate whether another supervised auto-run is needed before 2c' is a judgment call (HUMAN), not a doc edit. RECOMMENDATION: close-as-resolved (PK drift already addressed) OR reclassify the residual evaluation as a HUMAN decision task. Needs Amihay to point to the exact stale sentence if a doc fix is still wanted.
<!-- SECTION:NOTES:END -->
