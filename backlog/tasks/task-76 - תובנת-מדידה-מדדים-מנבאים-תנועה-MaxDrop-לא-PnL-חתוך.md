---
id: TASK-76
title: 'תובנת מדידה: מדדים מנבאים תנועה (MaxDrop) לא PnL חתוך'
status: Done
assignee: []
created_date: '2026-05-31 03:03'
updated_date: '2026-06-07 21:41'
labels:
  - score
  - calibration
  - insight
  - from-task-62
dependencies: []
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
[כותרת מלאה] תובנת מדידה: מדדים מנבאים תנועה (MaxDrop) אך לא PnL חתוך ב-TP/SL — RunUp r=-0.064 מול PnL אך r=-0.377 מול MaxDrop. ייתכן שצריך לכייל מדדים מול פוטנציאל התנועה ולא מול PnL חתוך. השלכה על כל גישת הקליברציה.

TASK-62: הסתירה בין ניתוח PnL (Score r≈0 על 104 שנכנסו) לסריקה רחבה (RunUp/ScanChange/Score מובהקים מול MaxDrop על 73). RunUp מנבא מי תרד (סלקציה) לא כמה נרוויח (תזמון, חתוך TP/SL — דליפת ביצוע). מתחבר ל-TASK-69 (קליברציה). רגיים יחיד, RELIABLE. P2.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
CLOSED-AS-DOCUMENTED (2026-06-07): התובנה (RunUp מנבא MaxDrop לא PnL; דליפת ביצוע TP/SL) מאומתת ורשומה במלואה בגוף. ה-actionable (קליברציה) נותב ל-TASK-69. נסגר — תובנה נלכדה, פעולה נמשכת ב-69. ללא שינוי קוד.
<!-- SECTION:NOTES:END -->
