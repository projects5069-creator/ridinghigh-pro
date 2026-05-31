---
id: TASK-80
title: >-
  ניתוח החוזרים הסדרתיים בDropsLab — האם מניה שנפלה N פעמים נופלת שוב (edge
  בר-בדיקה ללא survivorship bias)
status: Done
assignee: []
created_date: '2026-05-31 05:39'
updated_date: '2026-05-31 16:46'
labels:
  - dropslab
  - serial-fallers
  - edge
  - priority
  - from-task-62
dependencies: []
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עלה ב-TASK-62 portrait 31/5. 41.4% מהנופלים (520/1257) נפלו יותר מפעם; חלקם 9-13 פעמים (BIYA x13, ADTX x11, IPST x11, SMX x10, AEHL x9, HCAI x9). הזווית היחידה שעוקפת survivorship bias. AEHL כבר ב-CHRONIC_DROPPER_BLACKLIST; BIYA/ADTX/IPST/SMX לא. צעד ראשון: הגדר תחזית + משוך תוצאת-יום-אחרי לחוזרים. P1 משימת המשך ראשונה.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 שלב -1 feasibility gate: SA קורא את DropsLab החי (1XM-qId7); אם 403 — עוצרים ורושמים כחוסם, לא ממציאים נתונים
- [ ] #2 שלב 0: משיכה טרייה מ-drops_raw (snapshot ישן התנדף) + ספירת הופעות לכל טיקר; RidingHigh paper_portfolio+decision_log read-only; snapshot מקומי לשחזור
- [ ] #3 שלב 1 overlap gate (מכריע): כמה מהחוזרים RidingHigh בכלל סחר; אם ריק/זניח — edge לא ישים, מתעדים ועוצרים (תוצאה לגיטימית)
- [ ] #4 שלב 2 counterfactual PnL (רק אם overlap): WR/PnL עם מול בלי, לכל סף N; המלצת חסימה רק לטיקר ש-(א) נסחר (ב) הפסיד (ג) חסימתו משפרת אגרגט
- [ ] #5 תוספת 1 base-rate: הצהרת מגבלה מפורשת ב-findings — בלי TASK-79 הטענה מוגבלת ל-conditional-on-trading, לא 'נופל יותר מהממוצע'
- [ ] #6 תוספת 2 multiple-testing: סף N נסרק 2/3/4/5+ — לדווח את כל הספים, לא לבחור הטוב בדיעבד; מובהקות עם תיקון Bonferroni/BH
- [ ] #7 תוספת 3 כיוון: לבדוק אם החוזרים עושים reversal (עולים) או continuation (יורדים) ביום-אחרי — קובע אם שורט הגיוני (ספרות: reversal חזק ל-liquid, לא ל-micro)
- [ ] #8 תוספת 4 עלויות שורט: כל PnL כולל borrow cost/spread — בלעדיהם מסקנת 'שורט רווחי' על micro-caps מנופחת
- [ ] #9 עקרונות: read-only מוחלט, אפס מוטציות קוד; אימות צולב data:statistical-analysis מול קוד ידני; תוצר research/TASK-80_serial_fallers_<date>/findings.md
<!-- AC:END -->
