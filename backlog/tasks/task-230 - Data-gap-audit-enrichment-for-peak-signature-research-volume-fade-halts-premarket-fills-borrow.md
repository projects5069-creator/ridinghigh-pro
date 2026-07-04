---
id: TASK-230
title: >-
  Data-gap audit + enrichment for peak-signature research (volume-fade, halts,
  premarket, fills, borrow)
status: To Do
assignee: []
created_date: '2026-07-04 04:44'
updated_date: '2026-07-04 04:55'
labels: []
dependencies: []
priority: medium
ordinal: 236000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מטרה (timing-research 3/7): לאפשר חיפוש 'חתימת-שיא' שהדגימה-הנקודתית לא מראה — כולל ממד-הנרות (wicks+volume). המדדים הנוכחיים כמעט-זהים בהופעה ובשיא (RSI 64.6→66.1) וההפרדה כיום זמנית-בלבד.
שלב-1 recon (READ-ONLY, אל תניח): סכמה-מלאה בפועל של timeline_live / decision_log / paper_portfolio פר-סריקה — מה נשמר, מה ריק, מה נגזר.
שלב-2 candles-recon (READ-ONLY): לאמת מול providers/alpaca_provider החי אילו נרות-דקה (OHLCV) זמינים היסטורית לעולם-המניות שלנו — עומק-היסטוריה, limits, עלות-קריאות. ReboundPro/intraday_timeseries.py = תבנית-השראה בלבד — אפס ערבוב-קוד (§2).
שלב-3 peak-signature research (READ-ONLY): משיכת נרות-דקה היסטוריים לימי-השיא הממופים (מדגם מייצג מתוך 4,425 ticker-days של timing-research 3/7) ובדיקה: האם פתילים-עליונים + דעיכת-נפח מקדימים את תחילת-הירידה? פלט: יש/אין חתימה + עוצמתה, raw+CI. רק אם מוכח — מעקב-חי = שלב עתידי ב-task נפרד (לא כאן).
שלב-4 enrichment (רק אחרי אישור השלבים הקודמים): להוסיף את החסר — volume-per-scan + volume-fade (Δnpm) · trading-halts LULD (זמני-halt) · premarket high/volume · real-fill מול scan-price (Alpaca fills כבר קיימים ב-order records — לחבר) · intraday borrow/shortability snapshots.
שלב-4א (מאושר-עמיחי 4/7; מימוש-בקוד = go נפרד): volume-per-scan מ-FINVIZ ל-timeline — נפח-מצטבר-מאוחד (consolidated) פר-סריקה; delta בין-סריקות עוקבות = נפח-פר-דקה. פותר את חצי-הנפח של חתימת-השיא, feed-independent, union-writer-safe.
שלב-4ב (מאושר-עמיחי 4/7; מימוש-בקוד = go נפרד): איסוף-שוטף yfinance 1m — משיכה יומית (off-hours) של נרות-אתמול לכל טיקר-שנסרק, לארכיון-נרות מקומי (data/, gitignored). חלון-עומק yfinance-1m ≈ 30 יום ⇒ forward-only; פותר את חצי-הפתילים לשיאים חדשים.
שלב-4ג — IBKR data-feed evaluation (recon בלבד, בקשת-עמיחי 4/7; מימוש/חיבור = go נפרד):
· מנויי-market-data פעילים בחשבון-ה-IBKR של עמיחי — לאמת בחשבון בפועל, לא להניח.
· בדיקת-כיסוי אמפירית: נרות-דקה היסטוריים מ-IBKR על אותו מדגם-מרובד של 168 ימי-השיא (אותו seed=42) — bars-per-day מול ה-28/390 של IEX, השוואה ישירה.
· זמינות borrow/shortable + fee (סוגר את פער-#5 של שלב-4) וסטטוס-halts (פער-#2).
· תפעול: IBKR API הוא session-based (דורש Gateway/TWS רץ, לא REST) — השלכות על אוטומציה/GHA; מגבלות-pacing של בקשות-היסטוריות בפועל.
· Verdict: כיסוי-נרות טוב ⇒ IBKR מחליף את אופציית-SIP-בתשלום כמסלול-ה-backfill המרכזי; אחרת נשארים ב-4א+4ב.
הערת-אופציה: SIP feed בתשלום (Alpaca) = מסלול-backfill חלופי — **לבחון רק אם IBKR-recon (4ג) נכשל**; החלטת-עלות של עמיחי, לבדוק תמחור עדכני באתר Alpaca לפני.
אילוצים: כל תוספת-שדה דרך union-writer (append-only, אפס שבירת-סכמות קיימות, TASK-182 hardening) · אפס עומס-429 חדש בשעות-שוק (עדיף לצרף לכתיבות-קיימות) · Anti-Drift: עדכון PK+SCHEMA על כל שדה.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 שלב-1: מסמך-recon של הסכמות בפועל (per-tab, per-column, %-מילוי) — קריאה-בלבד
- [ ] #2 שלב-4 enrichment: כל שדה-חדש נכתב union-writer-safe + PK/SCHEMA מעודכנים + אפס תוספת-קריאות בשעות-שוק
- [x] #3 שלבי-נרות (2-3): **verdict 4/7 = blocked-by-data** — feed=IEX-בלבד (paper-plan, alpaca_provider:365), median 28/390 נרות ליום למיקרו-קאפ (n=168 מדגם-מרובד, 33 שמישים-מזווגים); חתימת-פתילים/נפח **לא ניתנת-לבדיקה** על ה-feed הנוכחי. על השבר: אין wick-signature (36.4% [22-53]) ואין volume-fade — אנקדוטת **volume-climax הפוכה** (27.3% fade, n=33 small) = שאלה פתוחה לדאטת-forward. דו"ח מלא: candle-research 4/7 (צ'אט) + PK v4.04
<!-- AC:END -->
