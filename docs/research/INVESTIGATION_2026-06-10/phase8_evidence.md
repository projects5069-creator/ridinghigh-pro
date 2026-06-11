# שלב 8 — ראיות גולמיות (drift תיעודי: PK חי מול קוד)

הוראה: לתעד בלבד, לא לסנכרן. כל הפערים נבדקו מול PK v2.99 (נקרא חי בתחילת הריצה).

## טבלת פערים

| # | תחום | PK חי אומר | הקוד/המציאות | ראיה |
|---|---|---|---|---|
| D1 | §1 Metadata | "Active workflows: 7" | **15** קובצי workflow פעילים | PK:19 מול `ls .github/workflows` (15 yml + 1 .bak) |
| D2 | §18 Caps | `RSI_LOW: 50 # bell curve center low` | config.py:57 = **60**; ושניהם מתים — calculate_score משתמש במדרגות 80/85/90 קשיחות | PK:1604, config.py:56-57, formulas.py:408-417 (שלב 1 §1) |
| D3 | §18 + docstring | "RSI: bell curve, peak 50-70" | אין bell curve מאז 22/4 — extreme-overbought steps בלבד | formulas.py:388 מול :408-417 |
| D4 | §19 | validate_atrx "Returns bool"; normalize_* "0-1" | float; 0-100 | formulas.py:120-131, 352-371 (ידוע — TASK-138 פתוח) |
| D5 | §Decision flow :3060 | ROCKET_GUARD "blocks 16 losses, 0 winners" | OOS ≥16/5: 8 חסומות = 5 LOSS + 3 WIN; ועל כלל המוכרעות: 19 = 7 LOSS + 12 WIN | שלב 6ה |
| D6 | changelog v2.99 | "n מוכרע 93→123... (150 כולל WHIPSAW)" | 123 ✓ אך כולל-WHIPSAW = **149** (150 רק אם סופרים NO_TOUCH) | שלב 0ב |
| D7 | עותק PK ב-Sheets | (לא מוזכר ב-PK) | mirror "RidingHigh-Pro-System-Reference" (1SuHj0jo...) — sync אחרון **2026-05-16**, Metadata Version="v2.0", 2,875 שורות מקור מול 3,588 היום — 25 ימים מאחור | קריאת Metadata חיה (פלט לעיל); הערה: הפרומפט ציין "תקוע על v2.12" — שדה ה-Version במirror מציג "v2.0" (כנראה פורס כותרת-מסמך, לא גרסת-changelog); ה-staleness אומת כך או כך |
| D8 | TASK-122 (ידוע) | PK v2.90/plan טוענים TASK-117=auto-mode מוכח | NIGHT_RUN Run-Log אומר supervised; classifier n=1 | קובץ backlog task-122 (פתוח — לא טופל כאן) |
| D9 | §1 Metadata | "Codebase ~13,000 lines / 60+ files" | agent בלבד = 11,012; ספירה כוללת לא אומתה — השערה, לא וידאתי | wc -l חלקי |
| D10 | v2.98 "פער ידוע: 2026-07 עם 13 טאבים" | **נסגר** — skip_summary ל-2026-07 נוצר (4d30a7a; Drive: 13jMGlhp... created 10/6 23:20Z; sheets_config:84 כולל אותו) | שלב 4ה פלט Drive |

## הקשר לפילטרים ולסכימות

- מספר הפילטרים: PK אומר 14 (שורה 3045) — תואם קוד ✓. (הפרומפט של ריצה זו אמר "12" — הפער הוא בפרומפט, לא ב-PK.)
- סכימת post_analysis: PK לא מתעד את פער 122/105 העמודות אפריל-מול-מאי/יוני ולא את שינוי הסדר (שלב 4א).
- borrow_data: PK v2.63 "ללא writer פעיל" — אומת ✓ (0 שורות בשני החודשים).

## סקילים שבוצעו בשלב זה
data-quality-checker, rhpro-live (השוואה מול PK חי).
