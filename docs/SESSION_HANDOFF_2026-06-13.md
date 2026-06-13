# SESSION_HANDOFF — 2026-06-13

*מצב: DRY_RUN · Sentinel=shadow · PK v3.15 · main נקי ומסונכרן (0/0).*

## מה היה בסשן
פתיחת-יום מלאה → המיקוד עבר לכיוון החדש מ-investigation II: **crossover-short**.
2 commits נקיים, אפס שינוי לוגיקת מסחר.

## הושלם היום
| Task | מה | תוצאה |
|---|---|---|
| **TASK-172** | refocus — borrow_collector | מומקד-מחדש: ה-collector **אומת אוסף חי מ-11/6** (ADIL Shortable/ETB; EDHL NOT-shortable) דרך לוגי EOD + קריאת הטאב; פרמיסת "0 rows ever / wire it" הופרכה; II-0.2 stale; PK §1 drift 3.06→3.14 תוקן. `2e0519c`. **נשאר To Do:** coverage→universe + coverage report |
| **TASK-165** | HYPOTHESES.md (ממשל-מחקר) | **Done** (framework + DRAFT, לא נעילה) — §A policy נעול + §B template + §C journal + §D HYP-001 crossover-short DRAFT; PK v3.15; references מ-close-ritual (SESSION_PROTOCOL §3) + PK. `0792795` |

## תובנות-המפתח של היום
- ה-edge הישן (long/D1_Open) **מת ב-HIGH power** (n=2,103) — לא נרדף יותר.
- **fee לא חוסם 178/179** — worst-case borrow כבר פרמטרי ב-`calculate_net_pnl` (50/200/500%/שנה, TASK-140). אין צורך במקור-fee חיצוני בשלב EXPLORATORY; fee אמיתי per-ticker = שכבה-2 LOW אופציונלי.
- ה-collector **חי מ-11/6** — לא "לבנות", אלא להרחיב coverage.
- *(שמור בזיכרון: `project_borrow_collector_verified`.)*

## מסלול ה-crossover-short (נעול בכתב ב-HYPOTHESES.md §D)
```
TASK-165 ✅ (framework + HYP-001 DRAFT)
   ├─ TASK-172  coverage→universe  ← פתוח (shortability לכל crossover-candidate)
   └─ TASK-177  hold window D6-D15 ← ⭐ השאלה המרכזית (§D דורש לפתור לפני נעילה)
        └─→ TASK-178 (נעילה רשמית) ─→ TASK-179 (ולידציה, ≥150 אירועים חדשים, ~4-5 ח')
```
**⚠️ החולשה המרכזית (גלויה במכוון ב-§D):** discovery window (5d, ה-−17.75% n=62) **≠** validation hold window (D6-D15). ה-−17.75% **לא** מתגלגל ל-D6-D15. TASK-177 חייב להכריע אם D6-D15 מרחיב או מחליף את חלון-הגילוי — ו-TASK-178 לא נועל עד אז.

## קריאת-חובה לסשן הבא
1. `docs/HYPOTHESES.md` §A (policy נעול) + §D (HYP-001 DRAFT) — מקור-האמת לכיוון.
2. ה-PK החי (v3.15) — changelog v3.14/v3.15.

## משימות פתוחות
**OPEN: 65** (חי). שרשרת crossover (כולן HIGH): 172 · 177 · 178 · 179.

## תעדוף למחר
1. **חובה — TASK-177** (חלון D6-D15): השאלה החוסמת את כל השרשרת. שינוי schema ב-post_analysis → תיאום עם TASK-167 (SCHEMA.json) + לקח grid-resize (TASK-123). ping-pong + ask-before-building.
2. **חשוב — TASK-172 coverage**: הרחבת מקור-הטיקרים ל-universe + coverage report.
3. **רצוי**: TASK-175 (סגירת כיוון LONG ב-PK §4 מהראיות) — קצר.

## לטיפול ניהולי
- **תיקון לוקלי לא-מסונכרן:** `REPORT.md` II-0.2 תויג STALE לוקלית בלבד (`docs/research` gitignored). התיעוד הבר-קיימא ב-PK v3.14/v3.15. לא דורש פעולה — רק מודעות.
- **slip baseline:** §D נועל slip=2%/side (2× config.SLIP); phase-5 בדו"ח השתמש ב-0.5%/side. מתועד ב-§D כמכוון ("punish"). לאישור-סופי ב-TASK-178.
- **fee layer-2:** מקור-fee אמיתי per-ticker לא נפתח כ-TASK (אופציונלי LOW; מתועד ב-172/PK). לפתוח רק אם יידרש אחרי 179.

## חתימה
DRY_RUN · Sentinel=shadow · PK v3.15 · main@`0792795` נקי ומסונכרן. 2 commits, אפס שינוי לוגיקת מסחר.

*— END —*
