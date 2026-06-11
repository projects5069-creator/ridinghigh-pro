# שלב 3 — ראיות גולמיות (הסוכן: decision_logic / sentinel / execution / analytics)

## 1. הפילטרים ב-decision_logic — בפועל 14, לא 12

`agent/trader/decision_logic.py:_check_filters` (סדר אמיתי): F1 Score, F2 MxV, F3 RunUp,
F4 Volume, F4b PRICE_TOO_LOW, F4c BLACKLIST, F4d TOXIC_PROFILE, F5 MarketCap (שני גבולות),
F6 Quality, F7 ExistingPosition, F8 ColdStart (כפול: concurrent+daily), F9 Reentry,
F10 BuyingPower, F11 ROCKET_GUARD. (תואם PK v2.39 "14 filters total"; הפרומפט אמר 12 — מתועד ב-OPEN_QUESTIONS.)

### סף + מקור + תוקף על הדאטה העדכני

בדיקה אמפירית על n=123 מוכרעות v2 (שלושת החודשים; base WR=65.9%).
**caveat מתודולוגי**: post_analysis מכיל רק שורות שכבר עברו סף 70 ב-peak —
מדגם מסונן; F1/F4 לא נבדקים עליו באמת (חוסמים 0).

| פילטר | סף | מקור הכיול | pass n/WR | blocked n/WR | הצדקה כיום |
|---|---|---|---|---|---|
| F1 Score≥50 | 50 | "lowered from 60" (config) | 123/.659 | 0/— | לא בדיק על דאטה מסונן-70 |
| F2 MxV≤-100 | -100 | config Phase-1, ללא n מתועד | 74/.662 | 49/.653 | **אפס הפרדה** |
| F3 RunUp≥0 | 0 | config Phase-1 | 115/.652 | 8/.750 | החסומות מנצחות יותר (n=8 קטן) |
| F4 Vol≥100k | 100k | config Phase-1 | 123/.659 | 0/— | לא בדיק (אין שורות מתחת) |
| F4b Price≥$3 | 3.0 | L6 25/5, "+129pp" | 99/.697 | 24/.500 | **מוצדק** (פער 19.7pp) |
| F4c Blacklist | AEHL,TDIC | DropsLab x-ref אפריל | 119/.664 | 4/.500 | שולי, n=4 |
| F4d TOXIC | RSI>88∧SMA20>250 | L3 26/5, "+145pp" | 100/.680 | 23/.565 | כיוון נכון, מתון (SMA חסר ב-20/123 → הפילטר מדלג) |
| F5 MC 5M-2B | — | config Phase-1 | 112/.661 | 11/.636 | אפס הפרדה |
| F6 Quality≥0.5 | 0.5 | perception/data_quality | — | — | תלוי-ריצה, לא בדיק על post_analysis |
| F7-F10 | מצב חשבון | מבני | — | — | לא סטטיסטיים |
| F11 ROCKET_GUARD | RunUp≥50∧PTH≥-10 | 196 שורות: "16 הפסדים, 0 מנצחות" | 104/.663 | 19/.632 | **לא משתחזר: 19 חסומות = 12 WIN + 7 LOSS** (OOS מלא בשלב 6ה) |

כל ה-14 יחד: עוברות-הכל n=26, WR=84.6% מול חסומות-ע"י-משהו n=97, WR=60.8% —
הצירוף כן בורר תת-קבוצה טובה, מונע בעיקר ע"י F4b+F4d.

## 2. Tradability ממוקה — נקודות שמשפיעות על ריאליזם

| # | מיקום | ממצא |
|---|---|---|
| T1 | `agent/perception/tradability.py:28-33,63-66` | `AGENT_DRY_RUN=True` ⇒ **תמיד** mock: `is_shortable=True, borrow_fee_pct=12.5, borrow_available=True`. אף ENTER מעולם לא נחסם על זמינות-שורט. במניות nano-cap pump זו הנחת-יתר חמורה — בדיוק המניות הקשות/יקרות ביותר ל-borrow. |
| T2 | decision_logic.py:242 | check_tradability נקרא **רק אחרי** שכל הפילטרים עברו — תוצאתו נרשמת אך לא מסננת (אין פילטר tradability בעץ). |
| T3 | borrow_fee=12.5 קבוע נכתב ל-decision_log | עמודת borrow_fee חסרת שונות — לא שמישה למחקר עלויות. |
| T4 | `auto_scanner.update_live_trades:1036,1040` | יציאת TP/SL נרשמת במחיר הסף המדויק (אפס slippage, אפס gap-through). |
| T5 | `position_manager._process_position:184-190` | הסוכן יוצא ב-current_price (bar close) — ריאלי יותר מ-T4, אבל בדיקת הסף היא על close ולא על High/Low תוך-דקתי. |
| T6 | `auto_scanner.run_eod:1320-1344` | כניסות portfolio נקבעות EOD לפי שורת **peak-Score** בדיעבד (look-ahead מובנה; כימות בשלב 6ד). |
| T7 | delisting | מניות delisted (SBLX) נשארות PENDING ולעולם לא נספרות — שורט על מניה שנמחקה הוא לרוב ניצחון-שורט מקסימלי שלא נספר, אבל גם לא היה ניתן-לכיסוי בפועל. הטיה דו-כיוונית; ספירה בשלב 4. |

## 3. Sentinel — 7 בדיקות + מוכנות shadow→active

`agent/sentinel/data_sentinel.py`: per-signal: completeness, scan_freshness, price_sanity,
price_freshness; system: position_sync, quota_health, provider_heartbeat. סה"כ 7 ✓ (כל הדגלים ב-config דלוקים).
- shadow פעיל (config.py:321): BLOCK→ALLOW עם SHADOW_LOGGED ל-sentinel_events; check-exception→WARN (fail-open סביר).
- מוכנות לחזרה ל-active: על בסיס ה-counterfactual של TASK-62 (would-block WR 64% מול 41% not-blocked — staleness היא סיגנל, לא רעש) — **אין כיום הצדקה כמותית להחזרת active גורף**; הוחזר רק אם סלקטיבי (price_sanity/completeness). הראיה היחידה היא single-regime n=36 — עדיין תקפה כהסתייגות.
- system BLOCK עוצר בראשון (break) — סדר הבדיקות קובע מי מדווח; תיעודי בלבד.

## 4. execution / reconciler / postmortem / score_analytics

- order_manager.execute: DRY_RUN order "filled" מיידית במחיר decision.price (אין סימולציית spread); execution_price=fill או fallback ל-price. כשל כתיבת portfolio מסומן (TASK-105) ✓.
- reconciler: flag-only (RECONCILE_AUTO_REPAIR=False) — תואם GATE המתועד ✓.
- postmortem_engine: מחשב MFE/MAE מדאטה אמיתי; ScoreVersion v2.6 מתויג ✓.
- score_analytics: observational, רמות confidence לפי n (10/30/100); כותב SUG ל-pending_suggestions — אין מוטציה אוטומטית של משקלים ✓ (תואם §Phase-1).

## סקילים שבוצעו בשלב זה
backtest-expert (מתודולוגיית בדיקת פילטרים על דאטה מסונן — selection-bias caveat), data-quality-checker, systematic-debugging.
