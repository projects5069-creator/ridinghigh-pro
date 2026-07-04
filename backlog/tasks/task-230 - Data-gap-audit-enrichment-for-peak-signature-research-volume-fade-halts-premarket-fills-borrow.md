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
אילוצים: כל תוספת-שדה דרך union-writer (append-only, אפס שבירת-סכמות קיימות, TASK-182 hardening) · אפס עומס-429 חדש בשעות-שוק (עדיף לצרף לכתיבות-קיימות) · Anti-Drift: עדכון PK+SCHEMA על כל שדה.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 שלב-1: מסמך-recon של הסכמות בפועל (per-tab, per-column, %-מילוי) — קריאה-בלבד
- [ ] #2 שלב-4 enrichment: כל שדה-חדש נכתב union-writer-safe + PK/SCHEMA מעודכנים + אפס תוספת-קריאות בשעות-שוק
- [ ] #3 שלבי-נרות (2-3): verdict מגובה-raw+CI — יש/אין חתימת-פתילים+נפח לפני-ירידה; מעקב-חי רק ב-task נפרד
<!-- AC:END -->
