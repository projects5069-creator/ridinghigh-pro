---
id: TASK-308
title: Prompt classifier maps to a single skill - should return a list
status: To Do
assignee: []
created_date: '2026-08-10 19:57'
labels: []
dependencies: []
priority: low
ordinal: 306000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
skill_enforcement_hook.sh:53-68 - שרשרת if/elif, ההתאמה הראשונה זוכה, משתנה יחיד. פרומפט שהוא גם ניתוח וגם באג מקבל סקיל אחד.

נמדד 10/8: נדרש שינוי במקום אחד בלבד - אם המסווג יכתוב declared:a,b,c:offset, ענף ה-declared בשער (pretooluse_skill_gate.sh:134+) כבר מטפל ברשימה. השער אינו דורש שינוי. claudework-filing חסר במיפוי לגמרי (נטען 7 פעמים, כולן ביוזמה); הדפוס risk רחב מדי (position-sizer על כל אזכור risk).

שער-קבלה: המסווג מחזיר רשימה; מקרה חדש ב-skill_gate_selftest.sh מוכיח פרומפט מרובה-תחומים שנחסם עד טעינת שני הסקילים; claudework-filing ממופה; selftest נשאר ירוק.
<!-- SECTION:DESCRIPTION:END -->
