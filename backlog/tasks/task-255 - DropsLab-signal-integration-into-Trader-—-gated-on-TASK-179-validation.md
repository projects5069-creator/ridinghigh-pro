---
id: TASK-255
title: DropsLab signal integration into Trader — gated on TASK-179 validation
status: To Do
assignee: []
created_date: '2026-08-05 18:17'
labels:
  - dropslab
  - integration
  - blocked
dependencies: []
ordinal: 253000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
חיווט סיגנלי DropsLab כקלט ל-Trader. הופרד מ-TASK-153 בהכרעת 2026-08-05: 153 נשאר אימוץ-PK בלבד. חסום עד ולידציית TASK-179, ושלוש חלופות נתיב-הדאטה טרם הוכרעו. פירוט מלא ב-Implementation Notes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
מקור: RULING 2026-08-05 (עמיחי). ההיקף הזה יצא מ-TASK-153, שנשאר אימוץ-PK בלבד.

מה נדרש: חיווט סיגנלי DropsLab כקלט ל-Trader. הרעיון נספג ל-153 דרך מיזוג TASK-156
שבלע את TASK-27 (DropsLab integration #N25).

חסום עד: ולידציית TASK-179 (crossover-short על hold-out, n>=150). שתי סיבות נפרדות.

סיבה 1 — הסוכן החי לא מסוגל לבצע את HYP-001:
HYPOTHESES.md:128 נועל את היציאה על D5_Close, time-only, NO TP/SL. לסוכן אין יציאה
מבוססת-זמן: AGENT_FORCE_EOD_CLOSE=False (config.py:315), is_eod_window תמיד False
(orchestrator.py:117-124), MAX_HOLDING_DAYS display-only (config.py:146). היציאה היחידה
היא TP/SL (position_manager.py:244-251). חיווט ייצר אסטרטגיה שלישית שאינה HYP-001
ואינה HYP-002.

סיבה 2 — זיהום המדגם של HYP-002:
היקום הרשום הוא FINVIZ בלבד (HYPOTHESES.md:193-194). יקום שני הופך את המדגם שנאסף
מ-3/8 לתערובת. סעיף ה-freeze מונה ארבעה פרמטרים ו-Universe אינו ביניהם, כך שלפי האות
אין פסילה אוטומטית; לפי המהות ההרצה כבר לא מודדת את הרשום.

שלוש חלופות נתיב-הדאטה, אף אחת לא הוכרעה:
(א) קריאה חוצת-ריפו מול Ambroseius/DropsLab.
(ב) גיליון Google משותף שאליו DropsLab כותב ו-RH קורא.
(ג) קובץ ביניים מקומי שנכתב off-hours ונקרא בריצה.

מצב היום, מאומת 2026-08-05: אין שום reader. grep על dropslab/drops_raw/drops_post בכל
הקוד החי מחזיר שלוש תוצאות והן כולן הערות בלבד (formulas.py:353, config.py:301,
decision_logic.py:396). sheets_config.json לא מכיל אף מפתח DropsLab. זו בניית נתיב-דאטה
מאפס, לא שינוי קטן.

לא אומת: האם DropsLab עצמו עדיין חי (TASK-144 Done מ-2026-06-15, לא נבדק מאז).
<!-- SECTION:NOTES:END -->
