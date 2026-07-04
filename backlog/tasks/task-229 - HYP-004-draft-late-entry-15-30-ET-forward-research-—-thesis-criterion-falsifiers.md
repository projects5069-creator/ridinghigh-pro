---
id: TASK-229
title: >-
  HYP-004-draft: late-entry (>=15:30 ET) forward research — thesis, criterion,
  falsifiers
status: To Do
assignee: []
created_date: '2026-07-04 04:44'
labels: []
dependencies: []
priority: medium
ordinal: 235000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
תזת-עמיחי (3/7): כניסה >=15:30 ET עדיפה על כניסה-בטריגר-הראשון, תחת TP10/SL10 הקפואים. READ-ONLY research; אפס שינוי-קוד/gate.
תמיכה-מקדימה (raw, timing-research 3/7, plans/stateless-seeking-sifakis.md): sim R1 מול R0 על 176 ticker-days (04-07): WR 57.1% [49-65] מול 46.9% [40-54], sumPnL −287 מול −702 (1%/side; שניהם שליליים — השוואה-יחסית בלבד); אנטומיית-שיא n=4,425: 78.2% דועכים >=3% מהשיא באותו-יום, שיא→−3% median 6 דק', אין חתימת-שיא מדדית (RSI בהופעה≈בשיא); SL-vindication 71.7% [62-80] n=99 (median 1 יום-מסחר); R2/R3 (אישור-מחיר) לא עזרו — ה-edge בזמן-מוחלט; מתלכד עם overnight-edge של מחקר-199.
קריטריון-הצלחה מוצע: forward-only אחרי-רישום — bootstrap CI של Δ(net-PnL, R1−R0) > 0 ∧ Δ-WR מובהק ∧ עלות-ה-missed (19% מהטריגרים ב-R1) לא הופכת את סך-התוחלת.
מה-יפריך: Δ-CI חוצה-0 על forward; missed מרוכזים בעסקאות-רווחיות; אי-שחזור מחוץ-לעונת-המדגם.
הסתייגויות-חובה: survivorship (יקום-sim 176/4,425 pa-joined בלבד) · CIs חופפים · מילוי=מחיר-סריקת-דקה proxy · SL-first פסימי · 5-חוקים ללא תיקון-רב-השוואות.
חסמים: הכרעה/רישום-פורמלי ל-HYPOTHESES.md רק בהחלטת-עמיחי נפרדת ואחרי סיום HYP-002 (~27/7 / n>=150 / 45 ימים); HYP-003 §G תפוס (4-dim) — לכן HYP-004.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 מסמך-מחקר forward-only עם Δ-CI מבוקר + ניתוח-missed — ללא נגיעה בקוד
- [ ] #2 המלצת register/reject ל-HYP-004 מוגשת לעמיחי רק אחרי verdict של HYP-002
<!-- AC:END -->
