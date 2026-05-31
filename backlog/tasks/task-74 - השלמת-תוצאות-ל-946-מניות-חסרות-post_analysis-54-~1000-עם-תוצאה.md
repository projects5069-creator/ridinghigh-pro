---
id: TASK-74
title: השלמת תוצאות ל-946 מניות חסרות (post_analysis 54/~1000 עם תוצאה)
status: To Do
assignee: []
created_date: '2026-05-31 02:51'
labels:
  - data-quality
  - backfill
  - exploration
  - from-task-62
dependencies: []
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
[כותרת מלאה] השלמת תוצאות ל-946 מניות חסרות — post_analysis מכסה רק 54 מתוך ~1000 מניות שנסרקו. למשוך 5-day OHLC (כמו post_analysis_collector) ל-946 הנותרות מ-daily_snapshots, לחשב MaxDrop/TP10/תוצאה, כדי שאפשר יהיה לנתח מדדים מול תוצאה על כל המדגם ולא רק על מי שנכנס.

עלה ב-TASK-62 (source map 30/5): timeline_live 1006 מניות / daily_snapshots 948 / post_analysis רק 54 עם תוצאה. 94% מהמניות שנסרקו אין להן תוצאה ידועה = עיוורון. חוסם ניתוח 'הצד השני' המלא (TASK-71) ברמת n משמעותי. עבודה כבדה (משיכת Alpaca ל-946). P2.
<!-- SECTION:DESCRIPTION:END -->
