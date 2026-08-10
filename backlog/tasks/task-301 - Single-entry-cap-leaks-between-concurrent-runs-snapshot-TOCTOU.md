---
id: TASK-301
title: Single-entry cap leaks between concurrent runs - snapshot TOCTOU
status: To Do
assignee: []
created_date: '2026-08-10 19:56'
labels: []
dependencies: []
priority: high
ordinal: 299000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמדד 10/8, יום 1 של חלון-המדידה: JWEL ו-DKI נכנסו פעמיים כל אחד, בהפרש 1-2 שניות, משתי ריצות שהתחילו job באותה שנייה (31392859358 נוצרה 13:26:02Z והמתינה 311ש בתור; 31393286602 נוצרה 13:31:02Z; שתיהן התחילו 13:31:13Z). Score זהה לספרה (70.76 / 66.33) = אותה שורת-סיגנל = כפילות-אכיפה, לא החלטה חדשה.

השורש (הוכח מהקוד): build_account_state בונה snapshot פעם אחת בתחילת ריצה (orchestrator.py:212-299), מתעדכן in-process בלבד (:772-779); Filter 9 (decision_logic.py:443-446) קורא רק ממנו. אין lock. AGENT_MAX_REENTRIES_PER_TICKER=1 עצמו תקין - הוכח בהרצה: 0 כניסות→ENTER, 1→SKIP. הצבת 0 היתה חוסמת הכל.

קריאה-מחדש לפני הכתיבה לא תעבוד: Sheets eventual-consistency נמדד בדקות (orchestrator.py:200-203, PIII×14 HCWB×5) מול מרוץ של שנייה; והקריאה מקושטת 60ש (sheets_manager.py:390). ההזמנה נשלחת לפני הכתיבה (order_manager.py:115 מול :164).

התיקון היחיד שמונע: concurrency ב-yml (סריאליזציה). מחיר נמדד 10/8: 137/365 ריצות נזרקות (37.5%, חסם עליון), כיסוי-דקות 359→228; אף אחת מ-5 ריצות-ה-ENTER לא נזרקת, והסימולציה מראה שהכפילות נמנעת (A מסיים 13:27:01, B מתחיל 13:31:03). הכרעת עמיחי 10/8: ממתין 3-4 ימים לנתוני הגלאי (scripts/detect_duplicate_entries_v1.py רץ יומית, שורה 8 בבדיקת-הפתיחה).

קפוא עד 4/9: כל תיקון-קוד נוגע ב-orchestrator/decision_logic. פריסת concurrency = שינוי משטר-ריצות.

שער-קבלה: 5+ ימי-מסחר רצופים עם STATUS=CLEAN בדוח הגלאי אחרי התיקון הנבחר, ואפס ריצת-ENTER שנזרקה באותם ימים.
<!-- SECTION:DESCRIPTION:END -->
