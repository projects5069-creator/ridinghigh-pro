---
id: TASK-199
title: מחקר כוח-חיזוי per-מדד מול עסקאות רווח/הפסד אמיתיות (IB ground-truth)
status: To Do
assignee: []
created_date: '2026-06-28 00:11'
labels: []
dependencies: []
ordinal: 205000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מחקר READ-ONLY. לכל מדד בנפרד (MxV, RunUp, ATRX, RSI, REL_VOL, TypicalPriceDist, ScanChange) — לבדוק כיוון + עוצמת הקשר לתוצאות העסקאות האמיתיות (ground-truth: תיקייה חודשית + דוח IB), ולא מול post_analysis/Score>=60. בנוסף לזהות באילו עסקאות-רווח/הפסד אמיתיות כל מדד בא לידי ביטוי. ממשיך TASK-171 (per-metric AUC) אך מתקן את פער-אוכלוסייה #1 שזוהה ב-PK v3.63: TASK-171 רץ על post_analysis (Score>=60), כאן על אוכלוסיית עסקאות-אמת (MxV<=-100%, הקריטריון שעמיחי סוחר בו). מוטיבציה: ה-edge-verdict השלילי (edge_audit v3.61 + Batch 1-8) הופרך ע"י דוח IB אמיתי 2025 (NAV +32.71%, borrow ~161 שנתי) בגלל אוכלוסייה/borrow/holding/exit שגויים.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 טבלת per-מדד: כיוון + עוצמת-קשר + n לכל אחד מ-7 המדדים מול תוצאות עסקאות אמיתיות (IB + תיקייה חודשית), לא מול post_analysis/Score>=60
- [ ] #2 מיפוי: באילו עסקאות-רווח/הפסד אמיתיות כל מדד בא לידי ביטוי
- [ ] #3 READ-ONLY; אסור לגעת בטכניקת הכניסה (MxV<=-100%) או ביציאה הדינמית
- [ ] #4 תלות: שם התיקייה החודשית יסופק ע"י עמיחי לפני התחלה
<!-- AC:END -->
