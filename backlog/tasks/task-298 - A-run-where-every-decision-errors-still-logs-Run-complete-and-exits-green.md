---
id: TASK-298
title: A run where every decision errors still logs Run complete and exits green
status: To Do
assignee: []
created_date: '2026-08-10 02:05'
labels: []
dependencies: []
priority: high
ordinal: 296000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמצא 9/8 בחקירת 27/5. ריצה עם errors=65 מתוך 65 החלטות הדפיסה Run complete ויצאה בקוד 0. GitHub Actions הציג את כל היום כירוק.
זו אותה מחלקת-כשל של תקלת FINVIZ מ-8/8: 397 ריצות דיווחו errors=0 ביום שהמערכת הייתה עיוורת. כאן errors היה גדול מאפס - ואיש עדיין לא ידע.
שער-קבלה: ריצה שבה errors גדול מאחוז מסוים מ-decisions נכשלת בקול או מעלה התראה, ולא מסתיימת כירוקה. נבדק דו-כיוונית: ריצה נקייה עוברת, ריצה חנוקה נכשלת.
<!-- SECTION:DESCRIPTION:END -->
