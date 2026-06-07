---
id: TASK-79
title: תובנת survivorship bias ב-drops_raw — צריך dataset של לא-נופלים
status: Done
assignee: []
created_date: '2026-05-31 05:11'
updated_date: '2026-06-07 21:41'
labels:
  - insight
  - strategy
  - dropslab
  - from-task-62
dependencies: []
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
[כותרת מלאה] תובנת survivorship bias — drops_raw מכיל רק מי שכבר ירד 10%+, לכן מודד 'עומק ירידה בתוך נופלים' לא 'מי ייפול'. edge לסלקציה דורש השוואת נופלים מול לא-נופלים. גם על n=2378 כל המדדים WEAK (volume rho=-0.294 הכי חזק). כיוון מחקר חדש: dataset של לא-נופלים להשוואה.

עלה ב-TASK-62 30/5, מאומת בשתי שיטות (scipy+ידני, פער 0.000). התובנה המרכזית של היום. משנה גישת המחקר. קושר ל-TASK-71 (הצד השני). P2.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
CLOSED-AS-DOCUMENTED (2026-06-07): התובנה (survivorship bias ב-drops_raw, מאומת scipy+ידני פער 0.000) רשומה במלואה. ה-actionable (dataset לא-נופלים) נותב ל-TASK-71. נסגר — תובנה נלכדה, פעולה נמשכת ב-71. ללא שינוי קוד.
<!-- SECTION:NOTES:END -->
