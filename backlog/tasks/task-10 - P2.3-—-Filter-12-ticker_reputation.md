---
id: TASK-10
title: P2.3 — Filter 12 ticker_reputation
status: Done
assignee: []
created_date: '2026-05-23 19:33'
updated_date: '2026-08-05 18:21'
labels: []
dependencies: []
priority: medium
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Filter 12 to Trader: ticker_reputation score based on historical performance. Skip tickers with bad track record (e.g., HCWB-style chronic whipsaws).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RULING 2026-08-05 (עמיחי)

הכרעה: WON'T-DO. התיק נסגר.

נימוק 1 — המערכת כבר מימשה פילטר מוניטין וכיבתה אותו במכוון.
CHRONIC_DROPPER_BLACKLIST = ["AEHL", "TDIC"] (config.py:301) הוא בדיוק "skip tickers with
bad track record", בגרסה ידנית. ההערה שם: "chronic droppers from DropsLab x-ref
(3+ drops in 30d in Apr 2026), accounted for major DRY_RUN losses". הוא נאכף כפילטר 4c
(decision_logic.py:398) וכבוי היום תחת ENTRY_GATE_MINIMAL=True (config.py:378), שהופעל
ב-29/6 יחד עם כיבוי 5 פילטרים מגנים נוספים. הנימוק לכיבוי מתועד ב-TASK-128 Notes:
"protective filters were NOT part of the 2yr real-money method, all added May-2026...
re-validation deflated them: 129pp became 19.7pp; ROCKET_GUARD blocks 12 wins vs 7 losses".
הוספת Filter 12 היא הוספת פילטר מגן בזמן שהמערכת בכוונה מריצה שער מינימלי — סתירה ישירה
לכיוון שנבחר.

נימוק 2 — הדוגמה בגוף התיק אינה נתמכת.
התיק מצטט "HCWB-style chronic whipsaws". HCWB מופיע בהיסטוריה כבאג ולא כתופעת שוק:
TASK-4 "P1.1 — HCWB×5 Filter 9 regression", סטטוס Done. חמש הכניסות ל-HCWB היו רגרסיה
בפילטר ה-re-entry, לא מוניטין גרוע של הטיקר.

נימוק 3 — סיכון למדידה.
בניגוד לגארד qty<1 (TASK-224) שיכול רק להסיר תצפיות מנוונות, פילטר מוניטין מסיר תצפיות
אמיתיות ומטה את המדגם של HYP-002 באופן שלא ניתן לכמת מראש.

הנמקה שנבדקה ונדחתה — לתיעוד מפורש:
נשקל לנמק את הסגירה בכך ש-MxV אינו מנבא פר-עסקה (HYPOTHESES.md §H(a), n=229, MxV WIN
med -698 מול LOSS med -559, הפוך). ההנמקה הזו נדחתה כהקבלה שגויה: §H(a) מודד מדד רציף
ברמת הסיגנל — האם ערך MxV של עסקה בודדת מנבא את תוצאתה. ticker_reputation הוא אובייקט
אחר, prior קטגורי ברמת הישות — האם היסטוריית הטיקר מנבאת את התוצאה הבאה שלו. אלה שתי
שאלות סטטיסטיות נפרדות, ו-§H אינו מכיל אף מדידה ברמת טיקר.

מה שחסר בריפו ומה שיפתח את התיק מחדש:
אין בריפו שום מדידה של יציבות WR פר-טיקר בין תקופות. agent/dashboard/trade_history_page.py:463
(_render_win_rate_by_ticker, groupby ב-:476) מציג WR פר-טיקר בדשבורד, אבל אף מסמך לא בדק
אם הוא יציב. אם תימדד יציבות כזו בעתיד — ייפתח תיק חדש מול השער שיהיה בתוקף אז, ולא
ייפתח מחדש התיק הזה.
<!-- SECTION:NOTES:END -->
