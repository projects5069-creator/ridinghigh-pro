# שלב 1 — ראיות גולמיות (config / formulas / utils + lineage)

## 1. הכרעת RSI_LOW (config=60 מול PK §18=50)

ראיה — `formulas.py:408-417` (calculate_score, גוף ה-RSI):
```python
# RSI — extreme overbought only (research 22/4/2026: RSI 90+=100% TP20, bell curve 50-70 was weakest zone)
try:
    rsi = metrics['rsi']
    if rsi >= 90:
        score += W["RSI"]       # full 10 points
    elif rsi >= 85:
        score += W["RSI"] * 0.7  # 7 points
    elif rsi >= 80:
        score += W["RSI"] * 0.4  # 4 points
except: pass
```

grep מלא על הקודבייס (ללא .bak/__pycache__):
```
RSI_LOW / RSI_HIGH: מופיעים רק ב-config.py (הגדרה) — אפס שימוש בחישוב כלשהו.
SCORE_RSI_PARAMS: מיובא ב-formulas.py:69, מוקצה ל-R ב-formulas.py:392 — R לא מופיע שוב בגוף הפונקציה. קוד מת.
```

**הכרעה: אף אחד לא "צודק" — הקוד משתמש במדרגות קשיחות 80/85/90 ומתעלם משני הקבועים.**
- config RSI_LOW=60, RSI_HIGH=70 → קוד מת (caps שאינם בשימוש).
- PK §18 RSI_LOW=50 + "bell curve, peak 50-70" → תיאור שגוי של ההתנהגות בפועל פעמיים (גם הערך וגם הצורה).
- docstring של calculate_score עצמו (formulas.py:388 — "RSI: bell curve centered at 50-70 sweet spot") סותר את גוף הפונקציה 20 שורות מתחתיו.
- תואם ממצא v2.93 (SCORE_RSI_PARAMS dead) — אבל ה-drift ב-PK §18 (50 + bell curve) לא תוקן שם.

## 2. קבועי config מתים (אפס שימוש מחוץ ל-config.py)

grep usage לכל ~47 הקבועים. מוגדרים-בלבד (self-test בלבד):

| קבוע | ערך | הטענה בקוד | בפועל |
|---|---|---|---|
| MIN_PRICE | 2.00 | "Minimum stock price to include in scans" | אף סורק לא קורא אותו |
| MIN_VOLUME | 100,000 | "include in scans" | לא בשימוש |
| MIN_MARKET_CAP | 1M | "include in scans" | לא בשימוש |
| MAX_HOLDING_DAYS | 5 | "max days to hold" | classify_trade/calculate_stats מקודדים 5 ידנית (range(1,6)) |
| SCAN_FREQUENCY_SECONDS | 60 | קצב סריקה | הקצב נקבע ב-cron של workflow |
| MARKET_OPEN_HOUR_PERU/MINUTE, POST_ANALYSIS_HOUR_PERU | 8:30/16 | תזמון | utils.is_market_hours מקודד 8:30-15:00 ידנית; cron ב-workflows |
| MEDIUM_SCORE | 40 | tier תצוגה | לא בשימוש |
| AGENT_NO_TIME_LIMIT | True | אין מגבלת זמן | אף קורא — ההתנהגות ממומשת בהיעדר exit ולא דרך הדגל |
| RSI_LOW/RSI_HIGH (ב-SCORE_CAPS_V2), SCORE_RSI_PARAMS | — | פרמטרי RSI | ראו §1 |
| normalize_mxv/normalize_atrx (formulas) | — | "scoring helper" (PK §19) | מיובאים ב-dashboard.py:59-60 ולא נקראים בשום מקום בו |

הערה: MARKET_CLOSE_HOUR_PERU של config הוא כן בשימוש (3 קבצים) אבל utils.py מגדיר עותק עצמאי משלו (utils.py:58) — שני מקורות-אמת לאותו ערך (הפרת §10 רכה; הערכים זהים כיום).

## 3. פערי PK §19 (אינוונטר הנוסחאות)

- `validate_atrx` — PK: "Returns bool"; קוד: מחזיר float (0.0 או atrx).
- `normalize_mxv/atrx` — PK: "normalized 0-1"; קוד: 0-100.
- PK §18 "score = sum(contributions) capped at 100" — אין cap מפורש בקוד (המשקלים מסתכמים ל-100 אז התקרה טבעית; נכון רק במקרה).

## 4. בדיקת lineage — 5 שורות אקראיות seed=42 (post_analysis יוני, artifact 23:09Z)

SDOT 3/6, DSY 10/6, CPOP 10/6, ANY 3/6, CCTG 9/6. חושבו מחדש מהעמודות הגולמיות
(MarketCap_raw, Volume_raw, AvgVolume_raw, Open/PrevClose/High/Low_raw, ATR14_raw,
Week52High_raw, Float/SharesOutstanding_raw) דרך formulas.py:

- **9/10 מטריקות תואמות בכל 5 השורות** בסטייה ≤0.005 (עיגול ל-2 ספרות): MxV, RunUp, ATRX, REL_VOL, Gap, TypicalPriceDist, PriceToHigh, PriceTo52WHigh, Float%.
- **ScanChange% סוטה בכל 5 השורות**: סטיות 1.63 / 12.47 / 15.70 / 49.99 / 109.36 נק' אחוז.
  - הסבר (מאומת בכיוון, לא במקור): הערך המאוחסן נכתב בזמן הסריקה (מקור FINVIZ), בעוד PrevClose_raw מועשר אחר-כך מ-yfinance — שני מקורות שונים לאותה הגדרה. אין עמודת ScanChange_calc (בניגוד ל-MxV_calc וכו') ואין PrevClose של FINVIZ נשמר → **ScanChange% המאוחסן אינו ניתן לשחזור/ביקורת מהדאטה השמורה**. זה המדד שמתועד ב-formulas.py:252 כ"מנבא היחיד החזק ביותר".
- **Score lineage נקי**: calculate_score על המטריקות המאוחסנות מול Score המאוחסן — סטייה ≤0.01 בכל 5 (SDOT 0.01 עיגול; השאר 0.0000).

## 5. הערות utils.py

- `is_day_complete` (utils.py:160-198): בודק weekend בלבד — חג-עבר נחשב "complete". בפועל לא מזיק כיום (משמש gating לאיסוף; ביום חג אין נתונים והשורה נשארת PENDING עד שה-backfill holiday-aware של TASK-130 משלים), אבל לא עקבי עם is_trading_day.
- `parse_market_cap` לא מטפל בסיומת K (FINVIZ כנראה לא פולט K ל-MC; שולי).
- classify_trade: סדר הכרעה בתוך יום — WHIPSAW לפני LOSS לפני WIN; ברמת חלון BUG-free (אומת מול 107 הטסטים).

## סקילים שבוצעו בשלב זה
data-quality-checker (lineage), systematic-debugging (RSI dead-code tracing).
