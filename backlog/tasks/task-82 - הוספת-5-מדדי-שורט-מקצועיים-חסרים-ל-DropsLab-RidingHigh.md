---
id: TASK-82
title: הוספת 5 מדדי-שורט מקצועיים חסרים ל-DropsLab/RidingHigh
status: To Do
assignee: []
created_date: '2026-05-31 15:40'
updated_date: '2026-08-05 18:19'
labels:
  - metrics
  - short-signals
  - from-task-80
  - research
dependencies: []
ordinal: 82000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מחקר רשת 31/5 (יועצים/ברוקרים) זיהה 5 מדדים שהשחקנים הגדולים מחפשים ואין לנו: (1) days-to-cover היסטורי + שינוי שורט-אינטרס חודשי [דורש מקור בתשלום], (2) utilization rate מניות-מושאלות/זמינות [securities-lending feed, בתשלום], (3) VWAP תוך-יומי אמיתי [בר-בנייה מנתוני דקה קיימים], (4) Bollinger/sigma-bands extension [בר-בנייה מ-SMA+std], (5) institutional/insider ownership [דורש מקור]. שלב 1: לבדוק זמינות+עלות לכל אחד (חינם מול בתשלום). שלב 2: לממש את בני-המימוש-חינם (VWAP, sigma-bands, days-to-cover גזיר מ-short_float×float/avg_vol). שלב 3: להחליט על מקור בתשלום לשאר. עוקף הנחות — לאמת זמינות לפני מימוש.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 קטליזט מסווג: לא רק earnings_within_7d אלא סוג האירוע (offering/דילול, חקירה, delisting-warning). הספרות: דילולים מנבאים המשך-ירידה. מועמד למבדיל שהמדדים הרציפים פספסו
- [ ] #2 דגל reverse-split בזמן-אמת: TASK-80 מצא 82 אנומליות (+28000% CTNT/CODX). סימון split ימנע זיהום pattern_tag מלכתחילה
- [ ] #3 מילוי חורים: short_float_pct 22% ריק, shares_float 19% ריק — מדדי-מפתח לשורט. לוודא איסוף. pe_ratio 82% ריק = חברות בלי רווח (אינהרנטי, פחות דחוף)
- [ ] #4 TASK-139-INV RH-3.1/RH-6.3: borrow_data tabs empty (verified live), tradability mocked (is_shortable=True, fee=12.5 const); edge breakeven ~388pct/yr borrow — real shortability metrics are the blocking input
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RULING 2026-08-05 (עמיחי)

הכרעה מפוצלת. לא "שני מדדים חינמיים" — אחד.

sigma-bands (רצועות סטיית תקן): מאושר למימוש.
היתכנות מאומתת 2026-08-05: agent/enrichment/sma20_cache.py:78 כבר עושה
closes = bars["close"].dropna().tolist() מתוך get_daily_bars(ticker, days=25) שכבר נקרא.
הרשימה כבר בזיכרון באותה פונקציה. חישוב std ממנה דורש אפס קריאות ספק נוספות.
מה שנדרש: חישוב std ושדה נוסף בקאש. הקאש היום שומר שדה אחד בלבד —
cache[key] = {"sma20": ..., "computed_at": ...} (sma20_cache.py:84). ה-.std() היחיד
בכל הקוד החי הוא score_analytics.py:357.

VWAP אמיתי: נסגר. לא ייושם.
הנימוק אינו מאמץ אלא תקפות. הפיד הוא IEX בלבד (providers/alpaca_provider.py:364,
"paper plan only allows IEX"), ו-TASK-230 AC#3 מדד verdict סגור: חציון 28 נרות מתוך
390 ליום למיקרו-קאפ (n=168 מדגם מרובד, 33 שמישים מזווגים). VWAP הוא
sum(price*volume)/sum(volume); חישוב שלו על 7% מהדקות ומבורסה אחת ייתן מספר גרוע
יותר מ-calculate_typical_price_dist הקיים (formulas.py:147), ויישא שם שמרמז על סמכות
שאין לו. formulas.py:150-153 כבר מתעד את זה: "True VWAP requires intraday tick-by-tick
volume data, which we don't have".
הערה: המוטות התוך-יומיים כן נושאים נפח (intraday_cache.py:25,
_COLS = ["open","high","low","close","volume"]). הבעיה אינה היעדר השדה אלא הכיסוי.

שלושת המדדים בתשלום (days-to-cover היסטורי, utilization rate,
institutional/insider ownership): מוקפאים עד תוצאת ה-recon של IBKR (TASK-230 שלב 4ג).
אם ה-recon לא מחזיר אותם — נסגרים אז.

לתעד לפני מימוש sigma-bands: כל מדד חדש ב-timeline_live הוא שינוי סכמה. SCHEMA.json הוא
חוזה שנאכף ב-check_08_required_columns (health_audit.py:834). נדרש עדכון SCHEMA + PK
לפי חוזה ה-Anti-Drift.

הערה על AC#4 של התיק: הוא אומר "borrow_data tabs empty (verified live)". זה התיישן —
MASTER_TASK_LIST_2026-08-03 מתעד 63 שורות ביולי ו-4 באוגוסט.
<!-- SECTION:NOTES:END -->
