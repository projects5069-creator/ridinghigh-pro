---
id: TASK-153
title: Review and adopt DROPSLAB_PK_DRAFT as docs/DropsLab_PK.md
status: To Do
assignee: []
created_date: '2026-06-11 04:03'
updated_date: '2026-08-05 18:16'
labels:
  - TASK-139-INV
dependencies: []
priority: low
ordinal: 156000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV phase7 deliverable: docs/research/INVESTIGATION_2026-06-10/DROPSLAB_PK_DRAFT.md (v0.1) — full schema (38+25 cols), workflows, IDs, data status, research verdicts, open issues. Review with Amihay, then adopt as living docs/DropsLab_PK.md under the Anti-Drift contract
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-156 merge: absorbs TASK-27 (DropsLab integration #N25 — integrate DropsLab signals as Trader input; unblocked 3/6). Adopt DropsLab_PK draft AND wire the integration here.

RULING 2026-08-05 (עמיחי)

הכרעה: לאמץ את DROPSLAB_PK_DRAFT כ-docs/DropsLab_PK.md תחת חוזה ה-Anti-Drift. אימוץ בלבד.

היקף שיוצא מ-153: החיווט של סיגנלי DropsLab כקלט ל-Trader (שנספג לכאן דרך מיזוג TASK-156
שבלע את TASK-27) מוצא מהתיק הזה ועובר לתיק נפרד.

נימוק ראשון — הסוכן החי לא מסוגל לבצע את HYP-001:
HYPOTHESES.md:128 נועל את היציאה של crossover-short על "Cover at D5_Close — exactly 5
trading days after the d1_close entry; time-only, zero-discretion, NO TP/SL".
לסוכן החי אין שום יציאה מבוססת-זמן: AGENT_FORCE_EOD_CLOSE=False (config.py:315) גורם
ל-is_eod_window להחזיר False תמיד (agent/orchestrator.py:117-124), ו-MAX_HOLDING_DAYS
הוא display-only (config.py:146). היציאה היחידה היא TP/SL (position_manager.py:244-251).
חיווט DropsLab ל-Trader לא ייצר את HYP-001 אלא אסטרטגיה שלישית: סיגנל DropsLab -> שער
MxV -> יציאת TP10/SL10. זו לא ההשערה הרשומה ולא זו שנמדדת.

נימוק שני — זיהום המדגם של HYP-002:
HYPOTHESES.md:193-194 מגדיר את היקום כ-"FINVIZ screener (Price>$2 AND Today+15%) ->
tickers passing the LIVE ENTRY_GATE_MINIMAL gate". הזנת יקום שני ל-Trader הופכת את המדגם
שנאסף מ-3/8 לתערובת של שני יקומים. הערה למען הדיוק: סעיף ה-config freeze (:210-215) מונה
ארבעה פרמטרים בלבד (TP/SL/HOLD/reentry) ו-Universe אינו ביניהם, ולכן לפי האות שינוי-יקום
אינו פוסל אוטומטית. לפי המהות כן: ההרצה כבר לא מודדת את מה שנרשם.

מצב לא מאומת: האם DropsLab עצמו עדיין חי. TASK-144 (Revive DropsLab collector) סטטוס Done
מ-2026-06-15, אך לא נבדק מאז.
<!-- SECTION:NOTES:END -->

## ממצא 2026-08-10 — המערכת האחות חיה. התיק אינו נסגר מעצמו.
נמדד מהיסטוריית ההרצות (GitHub Actions, לא Sheets): 42 ריצות ב-30 הימים האחרונים,
האחרונה **היום** 22:06Z ו-21:55Z, שתיהן success; שני ה-workflows במצב active.
הדחיפה האחרונה לקוד היא 21/6 ⇒ היא רצה על תזמון, יציבה, לא נטושה.
⇒ ההנחה שעמדה מאחורי "אולי מתה ולכן התיק מתייתר" **הופרכה**.
מה שהיא מייצרת ואין לנו: היסטוריית אירועי-**נפילה** לטיקר על חלון 30 יום.
⚠️ **לא נמדד:** כמה שורות נכתבו בשבוע האחרון (שאלת-Sheets). ריצה ירוקה אינה הוכחה
לשורות — זו בדיוק חתימת 27/5.
⏳ **ממתין להכרעת עמיחי:** האם "הפרדה מוחלטת" (PK v4.21) חלה גם על **נתונים**,
או רק על תיעוד ואינטגרציית-קוד. בלי התשובה אי-אפשר להכריע כאן ולא ב-258.
