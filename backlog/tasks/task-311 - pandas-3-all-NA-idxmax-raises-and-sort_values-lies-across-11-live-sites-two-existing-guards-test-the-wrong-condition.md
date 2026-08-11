---
id: TASK-311
title: >-
  pandas 3 all-NA: idxmax raises and sort_values lies across 11 live sites; two
  existing guards test the wrong condition
status: To Do
assignee: []
created_date: '2026-08-11 03:49'
labels: []
dependencies: []
priority: high
ordinal: 309000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמדד 10/8 בהרצה (pandas 3.0.5): עמודה ריקה-לחלוטין מפילה או משקרת ב-11 מקומות בקוד החי. השורש: pandas 3.0.0 (21/1/2026) אכפה deprecation מ-2.1.0 — idxmax/idxmin/argmax זורקים ValueError במקום להחזיר NaN. requirements.txt:2 הוא pandas>=2.2.0 (פין פתוח), ולכן ההתנהגות השתנתה בלי שאיש נגע בשורה — אותה מחלקת-כשל של TASK-248.
<!-- SECTION:DESCRIPTION:END -->

## המיפוי האמפירי (הורץ, pandas 3.0.5 — לא מהזיכרון)
```
idxmax / idxmin / argmax / idxmax(axis=1)  → ⛔ ValueError: Encountered all NA values
Series ריק לגמרי                           → ⛔ ValueError: attempt to get argmax of an empty sequence
max / min / mean                           → מחזירים NaN בשקט
mode().iloc[0]                             → ⛔ IndexError
nsmallest / sort_values                    → **אינם זורקים** ומחזירים שורות שרירותיות
בקרה חיובית: ערך תקין אחד מתוך שלושה       → הכל עובד כרגיל
```

## 11 המופעים, מדורגים לפי סכנה
| מקום | התנהגות | עטוף? | סכנה |
|---|---|---|---|
| `enrich_post_analysis.py:163` | זורק | ❌ | קריסה גלויה — צינור-המחקר הלילי מת |
| `auto_scanner.py:591` | זורק | ✅ | ⚠️ שקט — daily_summary מפסיק להיכתב, בכל דקה |
| `post_analysis_collector.py:356` | זורק | ✅ | ⚠️ שקט |
| `dashboard.py:2835` | זורק | ✅ | ⚠️ שקט + **שומר שגוי** |
| `dashboard.py:3252` | זורק | ✅ | ⚠️ שקט |
| `dashboard.py:1221` `.argmax()` | זורק | ❌ | קריסה בדשבורד |
| `dashboard.py:3557` | זורק | ❌ | קריסה בדשבורד |
| `dashboard.py:3751` `idxmax(axis=1)` | זורק | ❌ | קריסה בדשבורד |
| `trade_history_page.py:489` `.mode().iloc[0]` | IndexError | ❌ | **שומר שגוי** |
| `drop_analysis.py:227` `nsmallest` | **אינו זורק** | ❌ | ⚠️⚠️ תשובה שגויה בשקט |
| `post_analysis_collector.py:437` `sort_values` | **אינו זורק** | ❌ | ⚠️⚠️ בוחר שורה שרירותית במקום שורת-השיא |

## ⚠️ שני "שומרים" קיימים אינם שומרים
`dashboard.py:2835` (`if not valid_rows.empty`) ו-`trade_history_page.py:489`
(`if not durations.empty`) בודקים **ריקנות**. האימות מוכיח שריקנות ≠ ריק-לחלוטין:
שני המצבים זורקים, בהודעות שונות. השומר מכסה אחד מהשניים.

## הדפוס המוצע — אחד, חל על כל המופעים
```python
# utils.py — טהור, בלי I/O
def safe_idxmax(series, default=None):
    s = pd.to_numeric(series, errors="coerce")
    return default if s.notna().sum() == 0 else s.idxmax()
```
`notna().sum() == 0` ולא `.empty` — זה בדיוק ההבדל שהשומרים הקיימים מפספסים.
⚠️ הדפוס **אינו** מכסה את `sort_values`/`nsmallest` (הם לעולם אינם זורקים) — שם נדרשת
בדיקה מפורשת לפני הקריאה.
⚠️ ארבעה מהמופעים עטופים ב-`try` ⇒ הדפוס לבדו יחליף כשל-שקט בערך-ברירת-מחדל-שקט.
**חייב ללוות ב-`logger.warning`.**

## תלויות
חוסם את **TASK-260** ואת **TASK-208** — שתיהן החלטה אחת, ושתיהן דורשות שהפונקציה
הבטוחה תנחת קודם. אף אחד מ-11 המופעים אינו בחמשת קבצי-המסחר הקפואים.

ייסגר כאשר: כל 11 המופעים עוברים דרך הדפוס הבטוח או דרך בדיקה מפורשת;
`pandas` מוצמד לגרסה מדויקת ב-`requirements.txt`; ובדיקה דו-כיוונית עוברת —
עמודה ריקה-לחלוטין מחזירה ברירת-מחדל ומדפיסה אזהרה, ועמודה עם ערך תקין אחד
מחזירה את אותה תוצאה כמו היום.
