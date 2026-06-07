---
id: TASK-116
title: 'תיקון post-commit hook: python3 -> uv run python3 ל-generate_project_state'
status: Done
assignee: []
created_date: '2026-06-05 23:39'
updated_date: '2026-06-07 21:13'
labels:
  - infra
  - hooks
  - bug
dependencies: []
priority: medium
ordinal: 116000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ה-post-commit hook נכשל ב-commit 9f0d527 (2026-06-05): 'Use uv run python3 ... instead of python3 ...'. הסביבה עברה ל-uv; ה-hook עדיין קורא python3 ישיר. תוצאה: PROJECT_STATE.md לא מתעדכן אוטומטית (stale). תיקון: עדכן .git/hooks/post-commit לקרוא 'uv run python3 generate_project_state.py'. אומת: הכשל לפני amend -> אין שכתוב היסטוריה (push נקי). repo-scoped, auto-safe.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
FIXED (2026-06-07, local): .git/hooks/post-commit שורה 41 python3→uv run python3. אומת חי — empty commit הריץ uv run python3 נקי, אין "generator failed". ⚠️ מקומי-בלבד: ה-hook לא tracked ואין installer (setup_project_state.sh מת). לא שורד clone. עמידוּת → follow-up TASK.
<!-- SECTION:NOTES:END -->
