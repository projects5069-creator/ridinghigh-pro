---
id: TASK-261
title: borrow_coverage measures a universe of 2-5 tickers per day
status: To Do
assignee: []
created_date: '2026-08-05 20:34'
updated_date: '2026-08-05 20:35'
labels:
  - data-integrity
  - borrow
  - coverage
  - measured
dependencies: []
priority: medium
ordinal: 259000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-05: borrow_coverage 2026-08 reports ScannedUniverse of 5, 4, 2 and 2 per day against 71,397 timeline_live rows in the same month. get_scanned_universe (agent/perception/borrow_collector.py:32-44) selects daily_snapshots rows with MxV <= AGENT_MXV_MAX, so the denominator is gate-passers rather than the scanned universe, and both coverage percentages are computed over it. Coverage is not partial, it is near-absent. Relates to TASK-82 AC#4 and TASK-230.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-08-05. Source: reports/2026-08-05_1455_measurement.md Q-240.

THE MEASUREMENT
borrow_coverage 2026-08, live read after the close: 41 rows. Sampled tail:
  {'CheckDate': '2026-08-03', 'ScannedUniverse': '5', 'WithBorrowData': '4', 'PctWithBorrowData': '80'}
  {'CheckDate': '2026-08-03', 'ScannedUniverse': '5', 'WithBorrowData': '4', 'PctWithBorrowData': '80'}
  {'CheckDate': '2026-08-03', 'ScannedUniverse': '4', 'WithBorrowData': '4', 'PctWithBorrowData': '100'}
  {'CheckDate': '2026-08-04', 'ScannedUniverse': '2', 'WithBorrowData': '2', 'PctWithBorrowData': '100'}
  {'CheckDate': '2026-08-04', 'ScannedUniverse': '2', 'WithBorrowData': '2', 'PctWithBorrowData': '100'}

A universe of 2 to 5 tickers per day, against 71,397 timeline_live rows in the same month.
PctWithBorrowData reads 80 to 100 percent, which is true of the denominator it uses and
says nothing about the scanned universe in the ordinary sense of the phrase.

WHERE THE DENOMINATOR COMES FROM — verified in code 2026-08-05:
  agent/perception/borrow_collector.py:32-44  get_scanned_universe(snapshots_df, mxv_max=AGENT_MXV_MAX)
      selects daily_snapshots rows with MxV <= mxv_max, returns the ticker set
  the docstring records the history: TASK-208-B switched the selector from Score>=min_score
  to MxV, because under SCORE_WRITE_FROZEN the daily_snapshots Score column is blank and
  selected nothing.
  compute_coverage (:53 onward) uses that set as the denominator for BOTH percentages.

So the universe is "tickers that passed the entry gate in the daily snapshot", not
"tickers scanned". daily_snapshots itself held 85, 105 and 79 rows on the three August
days (Q-245), so even that upper bound is far above 2 to 5.

WHY IT MATTERS
  - TASK-82 AC#4 and TASK-230 both treat borrow_coverage as the coverage measure for
    short-side research. At n=2 to 5 per day it cannot support that.
  - TASK-178 and TASK-179 price a worst-case HTB borrow model. The borrow data backing it
    is this thin, and BorrowFeePct is separately known to be always NULL because Alpaca
    exposes flags only.

NOT ESTABLISHED: whether the small universe is the intended definition (gate-passers only)
or a regression from the TASK-208-B switch. The docstring explains the switch but does not
state the expected magnitude. No fix proposed here.
<!-- SECTION:NOTES:END -->

## ממצא 2026-08-10 — הטענה מחזיקה ומחמירה. הזיהום לא יצר אותה.
גזירה מחדש מעותק מקומי (`ClaudeWork/RidingHighPro/audit/raw/sheets_data_cache.json`,
צילום 6/8 19:42, מכסה 01/8-06/8) — **אפס קריאות Sheets**:
    שורות בחלון-הריצה 16:00-17:59 (נקיות): 21 מתוך 75
    ScannedUniverse בנקיות: חציון 5 · טווח **2-7** · ממוצע 4.7
    Σמונים/Σמכנים = 79/98 = **80.6%**  (הכיסוי המשוקלל האמיתי)
⇒ אחרי ניקוי הזיהום המכנה הוא 2-7 ולא 2-5. הטענה המרכזית עומדת על קריאת-קוד ממילא.
⚠️ ההצגה כ-"80-100%" נובעת מ**ממוצע-של-יחסים** (AoR) על מכנים זעירים ומשתנים — אומד
לא-עקבי בספרות; הנוסחה הנכונה היא יחס-הסכומים (RoA).
⚠️ סריקת שאר הקוד: `PctWithBorrowData`/`PctShortable` **נכתבים ואינם מצורפים** בשום קוד
חי ⇒ הקוד אינו מבצע את השגיאה; הפרשנות האנושית כן. `TP10_Hit.mean()*100` הוא ממוצע
מחוון 0/1 ⇒ תקין. **לא נמצא אף מופע נוסף של הפגם המדויק.**
⚠️ ממצא נלווה שאינו מוסבר: **16 שורות נקיות ביום אחד (3/8)** בעוד הקולקטור אמור לכתוב
1-2; המכנה משתנה (4/5/7) בעוד המונה נעוץ ב-4 בכולן. לא בדיקות ולא ריצה תקינה.
