---
id: TASK-65
title: >-
  פער postmortems: 9 פוזיציות סגורות ללא postmortem (104 vs 95). לזהות אילו
  ולהחליט אם לשחזר retroactively מ-decision_log
status: To Do
assignee: []
created_date: '2026-05-31 00:48'
updated_date: '2026-06-28 00:13'
labels:
  - data-quality
  - postmortems
  - from-task-62
dependencies: []
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עלה ב-TASK-62 ריצה 1.5. רשימה שמית ידועה (DEC-2026-05-14-00003 וכו'). P2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 read-only עד שלב-ההחלטה; כל backfill בפועל = צעד מאושר נפרד
- [ ] #2 scope multi-month GLOBAL set-diff (לא per-month isolated): לאחד ENTER DecisionIDs מכל החודשים (2026-05/06/07), לאחד PositionIDs מכל ה-postmortems, missing = enters_global − pm_global. הכרחי כי postmortem נכתב בחודש-הסגירה ועלול לשבת ב-spreadsheet שונה מה-ENTER — per-month isolated מנפח false-missing
- [ ] #3 FINAL scope 2026-06-27: gap אמיתי = 36 פוזיציות CLOSED-בלי-postmortem (ב-paper_portfolio עם ExitDate+ExitReason: TP_HIT/SL_HIT + 3 MANUAL_CLEANUP). 0 pending. ה-20 ENTERs ללא שורת-paper_portfolio הופרדו ל-task נפרד (לא postmortem-gap). backfill של ה-36 = החלטת-עיצוב נפרדת (שחזור-מלא מול חלקי מול תיעוד) טרם בוצעה — read-only עד אישור backfill
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
צ'אט-recon 2026-06-27 (READ-ONLY, נפרד+נוסף ל-scope=36 שכבר תועד): מעבר על 182 ה-postmortems הקיימים מצא MetricsAtEntry ריק (={}) ב-55% (101/182) — בעיה מובחנת מ-36 ה-חסרים (כאן ה-postmortem קיים אך חסר-מדדים). היפותזה-לשורש (לא מאומת): postmortem_engine._get_decision_context קורא ל-_read_decision(position_id) שעושה linear-scan ב-decision_log ומחזיר {} ב-miss — לחקור quota-drop של כתיבת decision_log מול PositionID!=DecisionID מול eventual-consistency. רלוונטי גם ל-TASK-198. הערה: אין כאן מסקנת-edge — ה-edge-verdict השלילי הופרך בדוח IB (PK v3.63).
<!-- SECTION:NOTES:END -->
