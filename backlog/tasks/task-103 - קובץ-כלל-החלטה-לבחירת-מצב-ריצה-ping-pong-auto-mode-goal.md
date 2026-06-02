---
id: TASK-103
title: קובץ כלל-החלטה לבחירת מצב ריצה (ping-pong / auto-mode / goal)
status: To Do
assignee: []
created_date: '2026-06-02 17:50'
labels:
  - infra
  - auto-mode
  - goal
  - protocol
  - batch
dependencies: []
priority: high
ordinal: 103000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מטרה: עמיחי לא צריך לזכור איזה מצב ריצה מתאים לכל משימה — הסוכן יחליט לפי כלל כתוב חי (לא זיכרון, שמתיישן). ליצור docs/RUN_MODE_DECISION.md עם עץ-החלטה: לכל משימה — (1) דורשת שיפוט/החלטות עמיחי באמצע? כן->PING-PONG (attended, כמו היום). (2) לא->auto-safe? (repo-scoped, לא קוראת FINVIZ/news/Sheets — חשיפת injection)? לא->ATTENDED עם אישורים (לא auto עיוור). (3) כן auto-safe->יש תנאי-סיום אובייקטיבי (טסטים/grep נקי/קובץ נוצר)? כן->/goal + auto mode (לולאה עד השגה). לא->auto mode רגיל (ביצוע חד-פעמי). אינטגרציה (עוגן מתוקן — אומת מול הקובץ 2/6/2026): SESSION_PROTOCOL.md בנוי בסעיפים, לא ב-'RULE #N'; 'פתיחת יום' היא §2, וההמלצה למשימה הבאה היא §2 שלב 5 ('שאלה אחרונה לפני שמתחילים'). שם להוסיף: 'לכל משימה מועמדת לריצה, החל את עץ-ההחלטה מ-RUN_MODE_DECISION.md והצהר מצב מתאים + נימוק; אם עמיחי לא ציין מצב, הצע את המתאים.' תיקון: הטקסט המקורי אמר 'RULE #13' — שגוי, אין ספרור כזה ב-SESSION_PROTOCOL.md; ה-'RULE #N' שייך למערכת ה-hooks/CLAUDE.md (RULE #11 = skill-gate), מערכת נפרדת. ככה הסוכן הוא התזכורת: גם אם עמיחי שכח, הסוכן יזהה 'משימה זו מתאימה ל-goal כי יש תנאי-סיום ברור' ויציע. כללי בטיחות שמורים: auto רק auto-safe, /goal דורש תנאי-סיום מדיד, branch+PR תמיד. תלוי TASK-102 (אימוץ goal+auto) ובסיווג auto-safe מפתיחת היום. משלים TASK-94 (Agent #8 — Routine Checker).
<!-- SECTION:DESCRIPTION:END -->
