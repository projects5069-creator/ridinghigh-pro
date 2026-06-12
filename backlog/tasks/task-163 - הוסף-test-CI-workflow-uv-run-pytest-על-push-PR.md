---
id: TASK-163
title: הוסף test-CI workflow (uv run pytest על push/PR)
status: Done
assignee: []
created_date: '2026-06-12 15:08'
updated_date: '2026-06-12 15:30'
labels: []
dependencies: []
priority: medium
ordinal: 166000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
פער אמת מול הנחה: לאורך TASK-142 הסתמכנו על 'CI ירוק 221/0' לאימות-סגירה, בעוד שבריפו אין שום workflow שמריץ pytest (רק filename_guard רץ על push). ה-221/0 המתועד (PK v3.03) הוא הרצה מקומית בלבד: uv run --with-requirements requirements.txt pytest. נדרש workflow שמריץ את הסוויטה על push/PR. שתי מלכודות לטפל בהן: (1) project_sync_20260418/ (snapshot gitignored) מזהם collection מקומית — לוודא שה-CI לא כולל אותו / להוסיף --ignore; (2) tests/agent/integration/ דורשים Google Sheets creds — לסמן אותם כ-integration ולדלג עליהם ב-CI ללא creds (pytest -m 'not integration' או skip-on-missing-creds).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Workflow .github/workflows שמריץ את הסוויטה (uv run --with-requirements requirements.txt pytest) על push + pull_request
- [ ] #2 מתעלם מ-project_sync_20260418/ ומקבצי הסקריפט הלא-pytest (test_formulas.py/test_utils.py רצים בנפרד)
- [ ] #3 טסטי tests/agent/integration (live Sheets) מסומנים ומדולגים ב-CI ללא creds — לא נספרים ככשל
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-12. Added .github/workflows/tests.yml (pytest on push/PR) + pytest.ini (testpaths=tests) + tests/conftest.py (auto-mark tests/agent/integration as 'integration'). First real test-CI run on branch: 301 passed, 2 skipped, 3 deselected (integration), formulas 107/107, utils 38/38 — conclusion success on clean runner. Closes the 'no pytest CI' gap surfaced in TASK-142.
<!-- SECTION:NOTES:END -->
