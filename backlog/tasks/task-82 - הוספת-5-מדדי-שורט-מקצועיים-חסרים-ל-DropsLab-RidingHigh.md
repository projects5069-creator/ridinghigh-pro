---
id: TASK-82
title: הוספת 5 מדדי-שורט מקצועיים חסרים ל-DropsLab/RidingHigh
status: To Do
assignee: []
created_date: '2026-05-31 15:40'
updated_date: '2026-06-11 04:01'
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
