---
id: TASK-256
title: CI signature guard validates finvizfinance 0.14.6 while production runs 1.3.0
status: To Do
assignee: []
created_date: '2026-08-05 18:22'
labels:
  - ci
  - tests
  - finviz
  - task-248-followup
dependencies: []
priority: high
ordinal: 254000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ה-CI מתקין -r requirements.txt (0.14.6) והפרודקשן מתקין ללא pin (1.3.0). שומר החתימה של TASK-238 מאמת את הגרסה שאינה בפרודקשן, ולכן מעולם לא הגן על הגרסה שהוא נבנה בשבילה. פירוט מלא ב-Implementation Notes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
מקור: ביקורת ההחלטות 2026-08-05 (RULING עמיחי). התגלה תוך כדי בחינת TASK-248.

הפער, מאומת בקוד:
  tests.yml:31   ->  uv run --with-requirements requirements.txt --with pytest pytest ...
  requirements.txt:4  ->  finvizfinance==0.14.6
  auto_scan.yml:24    ->  pip install finvizfinance ... (ללא pin)  =>  1.3.0

כלומר ה-CI מתקין 0.14.6 והפרודקשן מריץ 1.3.0.

מה זה שובר:
tests/test_ticker_sanitizer_v1.py:155-167 הוא שומר החתימה שנבנה ב-TASK-238 כדי למנוע
חזרה שקטה של שיבוש הטיקרים:

    LIBRARY_GET_TABLE_SIGNATURE = "(self, rows, df, num_col_index, table_header, limit=-1)"

    def test_library_get_table_signature_is_what_the_override_expects():
        pytest.importorskip("finvizfinance")
        from finvizfinance.screener.overview import Overview
        actual = str(inspect.signature(Overview._get_table))
        assert actual == LIBRARY_GET_TABLE_SIGNATURE

הטסט הזה רץ ב-CI על 0.14.6 בלבד. הוא מעולם לא ראה את 1.3.0 — הגרסה שהוא אמור להגן עליה.
אם finvizfinance תשנה את החתימה ב-1.3.x, ה-override של utils.SanitizedOverview._get_table
(utils.py:884) יפסיק לחול, הטיקרים יחזרו להיקרא מ-col.text, והשיבוש שגרם ל-83 פוזיציות
תקועות ביולי (TASK-246) יחזור בלי שאף בדיקה תיפול.

הקביעה שהחתימה זהה בשתי הגרסאות מופיעה פעמיים כהערת קוד — utils.py:824 ו-
tests/test_ticker_sanitizer_v1.py:7-9 — שתיהן מצטטות "0.14.6 overview.py:199,
1.3.0 base.py:127". זו קביעה עם file:line בשתי הגרסאות, אבל היא אינה נאכפת אוטומטית
על 1.3.0 ולא אומתה בביקורת (דורש התקנה).

פער שני, נלווה:
bs4 אינו ב-requirements.txt. הוא מגיע כתלות טרנזיטיבית של finvizfinance.
tests/test_ticker_sanitizer_v1.py:35 פותח ב-pytest.importorskip("bs4"), ולכן שינוי בתלות
שמשמיט את bs4 יגרום לכל קובץ הטסט לדלג בשקט במקום להיכשל. אותו דפוס חל על
pytest.importorskip("finvizfinance") ב-:109, :145, :159, :172.

קשר ל-TASK-248: איחוד ההתקנה דרך -r requirements.txt הוא מה שיסגור את הפער הזה — אבל רק
אחרי שהפין ישתנה ל-1.3.0. סדר הפוך מוריד את auto_scan.yml ל-0.14.6 והסורק מת.
<!-- SECTION:NOTES:END -->
