---
id: TASK-302
title: ROCKET_GUARD calibration comment contradicts measurement
status: To Do
assignee: []
created_date: '2026-08-10 19:56'
labels: []
dependencies: []
priority: medium
ordinal: 300000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
config.py:334 טוען: "blocks 16 historical losses, 0 winners" (כויל על 196 שורות post_analysis).

נמדד 10/8 על 292 עסקאות מקומיות (audit/hist/full_cache.json, יוני-אוגוסט, PositionID↔DecisionID): הגארד (RunUp>=50 AND PriceToHigh>=-10, נגזר Price/High לפי formulas.py:220) היה חוסם 18 כניסות ראשונות שמהן רק 8 מפסידות = 10 מנצחות נחסמות, ורק 1 כניסה מאוחרת. כלומר פוגע בעיקר בכניסה הראשונה - ההפוכה מהמפסידה (כניסות מאוחרות: חציון -10.4% מול +10.5% בראשונות, לא מובהק, n=64-74).

כרגע ENTRY_GATE_MINIMAL=True מנטרל אותו ממילא (_minimal ב-decision_logic). זו סתירת-תיעוד, לא באג חי.

שער-קבלה: ההערה ב-config.py מתוקנת לשקף את שתי המדידות עם תאריכיהן, או שנפתח תיק כיול-מחדש עם דאטה עדכני. config.py קפוא עד 4/9 - התיקון אחרי.
<!-- SECTION:DESCRIPTION:END -->
