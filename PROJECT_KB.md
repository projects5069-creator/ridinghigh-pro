# 🎯 RidingHigh Pro — Project Knowledge Base
*עודכן: 2026-04-16 — אחרי סקירה מערכתית מלאה של 9 הדפים וכל 12 הציונים*

> **⚠️ הוראה קריטית ל-Claude:** לפני כל פעולה במערכת, **קרא את המסמך הזה במלואו**. אם אתה מזהה פער בין המסמך לקוד — **תעדכן את המסמך**, אל תנחש. המערכת התפתחה מהר, ותיעוד ישן גרם לכישלונות משמעותיים בעבר.

---

## 📋 תוכן עניינים

1. [מטרת המערכת](#1-מטרת-המערכת)
2. [סטטוס נוכחי](#2-סטטוס-נוכחי)
3. [ארכיטקטורה וטכנולוגיה](#3-ארכיטקטורה-וטכנולוגיה)
4. [מערכת הציונים (12 ציונים!)](#4-מערכת-הציונים)
5. [Google Sheets — 7 קבצים חודשיים](#5-google-sheets)
6. [9 דפי Dashboard](#6-9-דפי-dashboard)
7. [פייפליין הדאטה](#7-פייפליין-הדאטה)
8. [קבצי קוד מרכזיים](#8-קבצי-קוד-מרכזיים)
9. [Known Issues & Bugs](#9-known-issues)
10. [כללי עבודה עם המערכת](#10-כללי-עבודה)
11. [היסטוריית תיקונים](#11-היסטוריית-תיקונים)

---

## 1. מטרת המערכת

**RidingHigh Pro** היא מערכת סריקה וסימולציה אוטומטית של עסקאות **שורט** (short-selling) על מניות פאמפ.

**הרעיון:** לזהות מניות שעוברות "פאמפ" חריג (עלייה מהירה עם נפח גבוה) ולסמלץ שורט בציפייה לירידה.

**משתמש:** עמיחי (adilevy, Ambroseius ב-GitHub), לימה פרו, UTC-5 קבוע בלי שעון קיץ.

**סטטוס:** Phase 1 — איסוף דאטה וולידציה. **אין מסחר בכסף אמיתי.**

---

## 2. סטטוס נוכחי

### ✅ מה עובד
- GitHub Actions מריץ סריקה כל דקה בשעות מסחר (13:30–20:00 UTC = 08:30–15:00 פרו)
- 7 קבצי Google Sheets חודשיים נפרדים (לא קובץ אחד עם טאבים!)
- Streamlit Dashboard ב-`ridinghigh-pro.streamlit.app` עם 9 דפים
- ATRX validation (מוגן מפני yfinance שגוי — commit 884088c, 16/4/2026)
- MxV *100 fix (commit 97a7b86, 16/4/2026)
- REL_VOL cap 100 (commit 97a7b86, 16/4/2026)

### 🔢 מספרים מרכזיים (נכון ל-16/4/2026)
- **124 רשומות** ב-post_analysis (חודש אפריל)
- **91 CLEAN, 9 SUSPICIOUS, 3 BROKEN, 21 NO_DATA** (לפי audit_flag)
- **TP10 hit rate:** ~74-81%
- **MaxDrop ממוצע:** -23.14% (חציון -19.12%)
- **Score ממוצע אחרי recalc:** 58.5 (ירד מ-74 אחרי תיקון ATRX)

### 🚨 בעיות פתוחות (14)
ראה סעיף [Known Issues](#9-known-issues). הקריטיות ביותר:
1. **3 הגדרות SL שונות** ב-3 דפים
2. **KB לא תאם לקוד** (תוקן במסמך הזה!)
3. **Gap הוסר מה-Score** למרות קורלציה חזקה
4. **live_trades sheet עם Scores ישנים שבורים**

---

## 3. ארכיטקטורה וטכנולוגיה

### Runtime
| רכיב | טכנולוגיה | הערה |
|------|-----------|------|
| Scanner | GitHub Actions + Python | cron-job.org מפעיל כל דקה |
| Trigger | cron-job.org | שולח POST ל-GitHub dispatch API |
| Dashboard | Streamlit Cloud | `ridinghigh-pro.streamlit.app` |
| Storage | Google Sheets | 7 קבצים חודשיים נפרדים |
| Post-analysis | GitHub Actions cron | `0 21 * * 1-5` = 16:00 פרו |

### מקורות דאטה
- **FINVIZ** — מקור ראשי לסריקה (Price, Volume, Change%, MarketCap)
  - ⚠️ FINVIZ Change% מגיע כ-decimal (0.3726) — צריך `*100`
- **Yahoo Finance (yfinance)** — לחישוב ATR14, RSI14, historical OHLC
  - ⚠️ **yfinance לא אמין ב-10% מהסריקות** — מחזיר pre-split או intraday חלקי
  - ATRX validation הוסף כדי להגן מפני זה

### Timezone — קריטי!
- **Peru = UTC-5 קבוע, בלי DST**
- שעות מסחר: **08:30–15:00 Peru** = **13:30–20:00 UTC**
- Post-analysis רץ: **16:00 Peru** = **21:00 UTC**
- GitHub Actions cron `0 21 * * 1-5` = 16:00 Peru ✅

### מיקומים
- **Repo:** `Ambroseius/-ridinghigh-pro`
- **Local path:** `~/RidingHighPro/`
- **Credentials:** `~/RidingHighPro/google_credentials.json` (gitignored!)
- **Service account:** `ridinghigh-sheets@ridinghigh-pro.iam.gserviceaccount.com`

---

## 4. מערכת הציונים

### ⚠️ במערכת יש **12 ציונים שונים**, לא 9!

| קבוצה | כמות | הציונים |
|-------|------|---------|
| Short Quality | 9 | Score, Score_B, Score_C, Score_D, Score_E, Score_F, Score_G, Score_H, Score_I |
| Entry Timing | 1 | EntryScore |
| Experimental | 2 | DynamicScore, Score_v2 (on-the-fly בדשבורד) |

### 4.1 Score (הציון הראשי — Score v2, מ-11 אפריל 2026)
**חשוב:** במערכת רץ **Score v2**, לא v1 (שמתועד ב-PROJECT_DOCUMENTATION.md הישן).

**הנוסחה (auto_scanner.py, שורות 151-189):**

```python
def calculate_score(metrics):
    score = 0
    # MxV — 25% — cap 200
    if metrics['mxv'] < 0:
        score += min(abs(metrics['mxv']) / 200, 1) * 25
    # RunUp — 25% — cap 30%
    if metrics['run_up'] > 0:
        score += min(metrics['run_up'] / 30, 1) * 25
    # ATRX — 20% — cap 5x
    score += min(metrics['atrx'] / 5, 1) * 20
    # RSI — 10% — bell curve, sweet spot 60-70
    if rsi < 50:    score += (rsi / 50) * 5
    elif rsi <= 70: score += 5 + ((rsi - 50) / 20) * 5
    else:           score += max(0, 10 - ((rsi - 70) / 30) * 5)
    # VWAP — 10% — cap 8%
    if metrics['vwap_dist'] > 0:
        score += min(metrics['vwap_dist'] / 8, 1) * 10
    # ScanChange% — 5% — cap 60%
    if metrics['change'] > 0:
        score += min(metrics['change'] / 60, 1) * 5
    # REL_VOL — 5% — cap 15x
    score += min(metrics['rel_vol'] / 15, 1) * 5
    # Gap הוסר לחלוטין!
    return round(score, 2)
```

**סיכום משקלים:**

| מטריקה | משקל | Cap | הערה |
|---------|------|-----|------|
| MxV | 25% | 200 | רק ערכים שליליים תורמים |
| RunUp | 25% | 30% | רק חיובי |
| ATRX | 20% | 5x | תמיד תורם |
| RSI | 10% | Bell 60-70 | לא ליניארי! |
| VWAP | 10% | 8% | רק אם מעל VWAP |
| ScanChange% | 5% | 60% | רק חיובי |
| REL_VOL | 5% | 15x | תמיד תורם |
| **Gap** | **0%** | **הוסר** | **⚠️ תועד במסמכים ישנים כ-5%** |

**סיפים לציון:**
- **85+ = Critical 🔴** (בורדו)
- **60-84 = High 🟠**
- **40-59 = Medium 🟡**
- **0-39 = Low ⚪**

### 4.2 Score_B עד Score_I (וריאציות ניסיוניות)

כל variant הוא ניסוי של משקלים שונים. כולם מחושבים בכל סריקה ונשמרים ב-timeline_live.

**פונקציות ב-auto_scanner.py (שורות 192-395):**

| Score | דומיננטי | משקלים |
|-------|----------|--------|
| Score_I | MxV | MxV=50, RunUp=20, ATRX=20, Change=10 |
| Score_B | MxV+RunUp | MxV=30, RunUp=30, ATRX=25, VWAP=10, Change=5 |
| Score_C | ATRX | ATRX=35, Change=25, RunUp=20, VWAP=15, MxV=5 |
| Score_D | MxV | MxV=40, RunUp=25, Change=20, ATRX=10, VWAP=5 |
| Score_E | Change | Change=35, RunUp=30, MxV=20, ATRX=15 |
| Score_F | VWAP | VWAP=40, RunUp=25, ATRX=20, MxV=10, Change=5 |
| Score_G | Balanced + RelVol | MxV=25, RunUp=25, ATRX=20, **RelVol sweet 10-100x=20**, Change=10 |
| Score_H | Balanced + ATRX | MxV=25, RunUp=25, ATRX=25, VWAP=15, Change=10 |

**חשוב:** Score_G הוא מיוחד — הוא נותן 20 נק' רק ל-RelVol בטווח 10-100x, ומעניש ערכים גבוהים יותר (dilution detector).

### 4.3 EntryScore (תזמון כניסה)

**מטרה שונה מהציונים האחרים!** לא "כמה המניה ראויה לשורט", אלא "**האם הרגע הזה נכון להיכנס?**"

רץ רק על מניות עם Score ≥ 60.

**4 רכיבים (auto_scanner.py, שורות 398-447):**

| רכיב | נקודות | מה מודד |
|------|--------|---------|
| PeakConfirm | 40 | ירדה ≥1% מה-intraday high |
| ReversalDepth | 30 | אחוז הפאמפ שכבר התהפך |
| TimeToClose | 20 | 14:00-15:00 = max, 13:00-14:00 = חצי |
| VWAPCross | 10 | מחיר מתחת ל-VWAP |

### 4.4 DynamicScore (ניסיוני, דשבורד בלבד)

מחושב **on-the-fly בדף Post Analysis** (dashboard.py, שורות 2426-2459). לא נשמר!

```
DynamicScore = MxV_norm × 0.6 + ATRX_norm × 0.4
MxV_norm: clip(-5000, 0) → scale 0-100
ATRX_norm: clip(0, 50) → scale 0-100
```

### 4.5 חישוב המטריקות הגולמיות

**MxV** (Market Cap vs Volume):
```python
MxV = ((MarketCap - Price × Volume) / MarketCap) × 100
```
יותר שלילי = פאמפ חזק יותר. טווח טיפוסי -30 עד -1500.
⚠️ **ראינו קורלציה r=+0.179 (הפוכה!)** — צריך מחקר נוסף.

**RunUp:**
```python
RunUp = (Price - Open) / Open × 100
```

**REL_VOL:**
```python
REL_VOL = Volume / AvgVolume(20d)
if REL_VOL > 100: REL_VOL = 100  # cap (נוסף 16/4/2026)
```

**RSI:** RSI(14) מספריית `ta`, על hist של 60 ימים.

**ATRX:**
```python
ATR14 = AverageTrueRange(hist, window=14)
ATRX = (current_High - current_Low) / ATR14
# Validation (נוסף 16/4/2026):
if ATR < 0.005 * price and ATRX > 5:
    ATRX = 0  # yfinance bad data
```

**Gap:**
```python
Gap = (Open - PrevClose) / PrevClose × 100
```
**⚠️ מחושב ונשמר, אבל לא תורם ל-Score (הוסר ב-v2)!**

**VWAP** (בפועל Typical Price!):
```python
VWAP = (High + Low + Price) / 3  # זה Typical Price, לא VWAP אמיתי
VWAP_dist = ((Price / VWAP) - 1) × 100
```
**⚠️ שם מטעה** — זה לא VWAP, זה Typical Price Distance.

---

## 5. Google Sheets

**7 קבצי Google Sheets נפרדים לכל חודש** (לא קובץ אחד עם טאבים!).

Config: `~/RidingHighPro/sheets_config.json`

### מבנה ל-2026-04:
```json
{
  "2026-04": {
    "timeline_live":   "1N54o4fBLBN2bB_hWGTlOY6yGFTIUJDDOQVW5F_C9Fg4",
    "daily_snapshots": "1aPU8-5vEEMMCM5KHRTs8VqrZ7T8wl3uaYbmW37NOsJY",
    "daily_summary":   "1-QMMljd2qp0hpiL190EFZdF7ruuMBOOvTQrm5-0sgQI",
    "post_analysis":   "1ELD5VcvAdN8oM63ZAjSRoyH_kZS8G8cuC8Nj_yNFkqk",
    "portfolio":       "1rAU8VSXuwBads_LsnTfPbgXJw3bnKY95RvoYplKhVqY",
    "portfolio_live":  "1XtsG2vBmOgjvxjJOovFlvR-9fIGB4EnhfqClG9sxcrQ",
    "score_tracker":   "1rCRF7Dj8cGkb9chLO1lb6FlODr4AkaUlcEcezDc72z0",
    "live_trades":     "1rCRF7Dj8cGkb9chLO1lb6FlODr4AkaUlcEcezDc72z0"
  }
}
```

**הערה:** score_tracker ו-live_trades באותו קובץ, בטאבים שונים.

**Legacy spreadsheet (לפני אפריל):** `1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k` — לא בשימוש.

### תפקיד כל גיליון

| גיליון | תפקיד | עמודות מרכזיות |
|--------|-------|----------------|
| `timeline_live` | כל סריקה, כל דקה (slim) | Date, ScanTime, Ticker, Price, Score, Score_B-I, EntryScore, MxV, RunUp, REL_VOL |
| `daily_snapshots` | Snapshot מלא ב-14:59 | כל המטריקות + raw fields |
| `daily_summary` | שורת סיכום יומית | Date, total stocks, avg score |
| `post_analysis` | **מקור האמת** — 5 ימי מעקב פר מניה | Ticker, ScanDate, D0-D5 OHLC, TP10/15/20_Hit, MaxDrop%, audit_flag |
| `portfolio` | סימולציית shorts — רשימה | Ticker, ScanDate, EntryPrice, Status |
| `portfolio_live` | realtime intraday | RunningHigh, RunningLow, Status (מעודכן כל דקה) |
| `score_tracker` | Score כל 5 דקות | Ticker, ScanDate, Score over time |
| `live_trades` | סימולציית real-time trades | EntryTime, Status, ScoreType, PnL |

### עמודות חשובות ב-post_analysis (119 עמודות!)

המרכזיות:
- **Identity:** Ticker, ScanDate, Score (+ 8 variants), EntryScore
- **Metrics:** MxV, RunUp, ATRX, RSI, REL_VOL, Gap, VWAP
- **Raw fields:** Volume_raw, MarketCap_raw, ATR14_raw, Open_price_raw, High_today_raw, Low_today_raw, AvgVolume_raw, VWAP_price_raw
- **_calc fields:** MxV_calc, ATRX_calc, RunUp_calc, VWAP_calc, REL_VOL_calc, Gap_calc (חושבו ב-post_analysis_collector — זה ה-"ground truth")
- **5-day tracking:** D1_Open/High/Low/Close עד D5, D0_* (יום הסריקה)
- **Results:** MaxDrop%, TP10_Hit, TP15_Hit, TP20_Hit, SL7_Hit_D1, SL_Hit_D0
- **Context:** IntraDay_TP10, IntraDay_SL, MinToClose, PeakScoreTime, PeakScorePrice
- **Catalysts:** cat_fda_approval, cat_merger_acquisition, cat_lawsuit וכו' (10 קטגוריות)
- **Meta (נוסף 16/4/2026):** audit_flag (CLEAN/SUSPICIOUS/BROKEN/NO_DATA), Score_recalc_date

---

## 6. 9 דפי Dashboard

`dashboard.py` = 3,778 שורות, 161KB. **רגיש לשינויים — קל לשבור.**

### 6.1 🏠 Home (dashboard_home_page, שורה 3565)
- **מטרה:** תמונת מצב מהירה + ניווט
- **KPIs:** שעה, שוק פתוח/סגור, Last Scan, Total scanned, Win Rate, Top stock
- **מקורות:** timeline_live, live_trades, post_analysis
- **חישובים:** רק aggregations (mean, max, count) — אין חישוב Score

### 6.2 📊 Live Tracker (main_page, שורה 1344)
- **מטרה:** סריקה בזמן אמת + Timeline Grid
- **שתי טבלאות:**
  - **Table 1 — Live Scanner:** מניות עכשיו, ממוינות לפי EntryScore
  - **Table 2 — Timeline Grid:** Ticker × ScanTime (איך Score השתנה לאורך היום)
- **Auto-refresh:** כל 60 שניות בזמן מסחר
- **Cloud mode:** קורא מ-Sheets
- **Local mode:** מריץ dashboard.scan() (FINVIZ + yfinance)

### 6.3 💼 Portfolio Tracker (portfolio_tracker_page, שורה 2202)
- **מטרה:** סימולציית $1,000 shorts
- **פרמטרים:** TP=10%, **SL=7%**, Min Score=60
- **שני טאבים:**
  - Table A: Entry at ScanPrice (EOD)
  - Table B: Entry at D1_Open
- **6 KPIs:** Closed, Wins, Losses, Alive, Win Rate, Total PnL
- **לוגיקה:** SL תמיד מנצח אם שניהם באותו יום (pessimistic)

### 6.4 ⚡ Live Trades (live_trades_page, שורה 3077)
- **מטרה:** trades אמיתיים בזמן אמת
- **פרמטרים:** TP=10%, **SL=10%**, Min Score=70 **⚠️ שונה מ-Portfolio Tracker!**
- **ScoreType logic:** מניה נכנסת פעם אחת עם Score המקסימלי שלה מבין 9
- **9 Expanders** — אחד לכל ScoreType
- **Auto-refresh:** כל 60 שניות

### 6.5 🎯 Portfolio Score Tracker (score_tracker_page, שורה 2790)
- **מטרה:** גרפים ויזואליים של Score+Price לאורך D0-D3
- **2 גרפים Plotly לכל מניה** (Score Trajectory + Price vs TP/SL)
- **SL=7% ב-TP/SL lines (כמו דף 3!)**
- **⚠️ Hardcoded cutoff:** `if sd < "2026-04-10": continue` — מניות לפני 10/4 לא מופיעות!

### 6.6 📅 Daily Summary (daily_summary_page, שורה 1654)
- **מטרה:** צפייה היסטורית יומית
- **בורר תאריך + טבלת כל המניות**
- **Read-only, אין חישובים**

### 6.7 📦 Timeline Archive (timeline_archive_page, שורה 1736)
- **מטרה:** ארכיון Timeline Grid היסטורי
- **זהה ל-Table 2 בדף Live Tracker, אבל עם בורר תאריך**

### 6.8 🔬 Post Analysis (post_analysis_page, שורה 2270)
- **הדף האנליטי המרכזי!**
- **9 סקציות:** KPIs, Win/Loss, טבלה מפולטרת, BestDay chart, DynamicScore, Score Tier Analysis, Metric Correlation, Catalyst Analysis, Export
- **שתי גרסאות Score מוצגות:**
  - `Score` — מהגיליון (תוקן 16/4)
  - `Score_v2` — on-the-fly מ-_calc fields (calc_score_v2, שורה 1079)

### 6.9 📊 Score Comparison (score_comparison_page, שורה 3246)
- **הדף שבגללו גילינו את ה-9 ציונים!**
- **סקציה 1:** נתונים חיים (היום) — מטריצה של 9 ציונים
- **סקציה 2:** טבלת ביצועים היסטורית — Win Rate לכל Score type
- **סקציה 3:** Win Rate by Score Bucket (גרף קווים)
- **סקציה 5:** "מי הכי צודק" — איזה Score type נתן ציון גבוה ביותר לכל מניה
- **⚠️ SL logic שונה:** SL7_Hit_D1 (רק D1!) — הגדרה שלישית של SL במערכת!

---

## 7. פייפליין הדאטה

```
┌──────────────────────────────────────────────────────────────┐
│  FINVIZ (realtime)                yfinance (historical)      │
└─────────┬────────────────────────────────┬───────────────────┘
          │                                │
          ▼                                ▼
    ┌──────────────────────────────────────────────┐
    │  auto_scanner.py                             │
    │  • כל דקה 13:30-20:00 UTC (Mon-Fri)          │
    │  • GitHub Actions trigger                    │
    │  • מחשב 9 ציונים + EntryScore                │
    │  • Validation: ATRX, REL_VOL                 │
    └──────────────┬───────────────────────────────┘
                   │
          ┌────────┼───────────┬──────────────┐
          ▼        ▼           ▼              ▼
    timeline_live  daily_      score_         portfolio_
                   snapshots   tracker        live
                                              (update_live_trades)
                   ▲
                   │ ב-14:59 פרו
                   │
    ┌──────────────┴───────────────────────────────┐
    │  post_analysis_collector.py                  │
    │  • 16:00 פרו יומי (cron: 0 21 * * 1-5)       │
    │  • שולף D1-D5 OHLC מ-Yahoo                   │
    │  • מחשב _calc fields (ground truth)          │
    │  • מחשב TP10/15/20_Hit, MaxDrop%             │
    └──────────────┬───────────────────────────────┘
                   ▼
              post_analysis
                   │
                   │ ← backfill_ohlc.py (אם חסר D1-D5)
                   │ ← enrich_post_analysis.py (אינטראדיי)
                   ▼
               Dashboard (9 pages)
```

### GitHub Actions Workflows
| Workflow | Cron | מה עושה |
|----------|------|---------|
| `auto_scan.yml` | כל דקה, 13:30-20:00 UTC, Mon-Fri | Main scanner |
| `post_analysis.yml` | `0 21 * * 1-5` = 16:00 פרו | EOD: EOD snapshot → collector → enrich → backfill |

---

## 8. קבצי קוד מרכזיים

| קובץ | שורות | תפקיד |
|------|-------|-------|
| `auto_scanner.py` | 1,395 | Scanner ראשי: FINVIZ scrape, 9 Score calc, Sheets write |
| `dashboard.py` | 3,778 | Streamlit app, 9 דפים, 161KB — **רגיש!** |
| `post_analysis_collector.py` | 539 | EOD collector: D1-D5 OHLC, TP/SL check |
| `sheets_manager.py` | 354 | Multi-sheet architecture, monthly rotation |
| `gsheets_sync.py` | - | Load/save post_analysis ל/מ-Sheets |
| `enrich_post_analysis.py` | - | אינטראדיי enrichment |
| `backfill_ohlc.py` | - | ממלא D1-D5 חסרים |
| `config.py` | 32 | **⚠️ משקלים ישנים (v1)!** לא בשימוש בפועל, calculate_score ב-auto_scanner hardcoded |
| `score_tracker_sync.py` | - | Score every 5 min |
| `health_check.py` | - | System health button |

### Scripts מה-16/4/2026
- `fix_atrx.py` — one-time fix שהעתיק ATRX_calc → ATRX ב-80 שורות
- `recalculate_scores_v2.py` — recalc של 9 ציונים על 100 שורות (CLEAN+SUSPICIOUS)
- `quick_audit.py` — audit של post_analysis → audit_flag
- `OPEN_ISSUES.md` — מעקב אחר באגים פתוחים (מקומי)

---

## 9. Known Issues

### 🔴 עדיפות גבוהה מאוד

**#1: 3 הגדרות SL שונות**
- Portfolio Tracker (דף 3): SL=7%, תוך 5 ימים
- Live Trades (דף 4): SL=10%, תוך 5 ימים
- Score Comparison (דף 9): SL=7%, **רק D1!** (SL7_Hit_D1)
- **השפעה:** אותה מניה יכולה להיות Win/Loss/Pending בדפים שונים

**#2: Min Score Threshold שונה**
- דף 3: ≥60 | דף 4: ≥70 | דף 9: ≥60
- **השפעה:** אי עקביות בניתוח

### 🟠 עדיפות גבוהה

**#3: Gap הוסר מ-Score v2 למרות r=-0.256 (חזק!)**
- הוסר ב-11/4 (commit f3d96ca) בלי תיעוד סיבה
- **השפעה:** Score חלש ממה שאפשר

**#4: live_trades מכיל Scores ישנים שבורים**
- Score_D עד 19,000 (לפני תיקון ATRX)
- לא נעשה recalc
- **השפעה:** ציונים היסטוריים של trades שגויים

**#5: DynamicScore — לא ברור אם נשמר**
- מחושב on-the-fly בדף 8
- **אם נשמר** איפה שהוא עם ATRX ישן — צריך recalc

### 🟡 עדיפות בינונית

**#6: yfinance raw data שגוי (דפוס מערכתי)**
- 3 BROKEN rows (RDGT, AHMA, UCAR) — pre-split prices
- 21 NO_DATA (9-10/4) — post_analysis_collector נכשל
- **שקול:** Polygon.io ($29/חודש) או FMP ($14/חודש)

**#7: REL_VOL max היה 26,794** — תוקן עם cap=100 (16/4/2026)

**#8: Hardcoded cutoff 2026-04-10 בדף 7** — מניות ישנות נעלמות בלי הודעה

**#9: VWAP בעצם Typical Price** — השם מטעה, לא VWAP אמיתי

**#10: Score vs Score_v2 כפילות בדף 8** — אחרי recalc הם זהים, Score_v2 מיותר

**#11: סקציה 5 בדף 9 מוטה** — Score שנוטה לציונים גבוהים "מנצח" בלי לנרמל

### 🟢 עדיפות נמוכה

**#12-14:** שם VWAP, hardcoded cutoff, Score_v2 כפילות

---

## 10. כללי עבודה

### 🛑 לפני כל שינוי

1. **אל תמחק כלום** — לא שורות, לא עמודות, לא קבצים
2. **Backup לפני כל שינוי** של דאטה — CSV עם timestamp
3. **Dry-run קודם, apply אחרי** — תמיד
4. **לא `git push` ללא אישור מפורש** — גם אם בטוח
5. **אל תיגע ב-`dashboard.py` (161KB) אלא במקרה הכרחי** — קל לשבור

### 📐 קונבנציות קוד

1. **קובץ מלא** — לא partial edits, לא line-by-line
2. **`sed -i ''`** למק (לא להוריד קבצי החלפה)
3. **שמות קבצים מגורסים:** `fix_atrx.py`, `recalculate_scores_v2.py`
4. **Scores: 2 decimals** (77.63, לא 77.6 או 77.633)
5. **Percentages: include % symbol**
6. **Environment:** `is_cloud()` ל-Streamlit Cloud, local אחרת
7. **pandas 2.x:** `.map()` לא `.applymap()`, `errors='coerce'` לא `'ignore'`
8. **FINVIZ Change%:** תמיד `* 100` (decimal → percentage)

### 🇮🇱 תקשורת עם עמיחי

1. **עברית** תמיד
2. **תיעוד באנגלית** (קוד + commit messages)
3. **אמוג'י** שימושיים 🎯
4. **אופטימי ומעודד** אבל **ישר**
5. **לא לפחד לומר "לא יודע"** או "תבדוק בקוד" — זה מעדיף מההמצאה
6. **Ground truth = הקוד**, לא הזיכרון שלי, לא התיעוד הישן
7. **אם יש אי-ודאות — לעצור ולבקש הבהרה** במקום לרוץ

### 🚨 Red flags שאסור להתעלם מהן

- "המערכת איטית" → בדוק cache ו-lazy loading
- "התוצאה לא נראית הגיונית" → עצור, לא להמשיך עם שינויים
- "ATRX גדול מ-10" → דגל אדום (cap הוא 3-5, בפועל גבוה יותר = yfinance bug)
- "Score > 100" → שגיאה בבטוח — פונקציות לא מחזירות 100+
- "REL_VOL > 100" → yfinance bug (עכשיו מכוסה ב-cap, אבל ציינו ב-logging)

### 💾 Backups שחייבים להישמר
- `post_analysis_backup_2026-04-16_1855.csv` (לפני fix_atrx)
- `post_analysis_backup_recalc_2026-04-16_2005.csv` (לפני recalc)
- `OPEN_ISSUES.md` (תיעוד באגים)

---

## 11. היסטוריית תיקונים

### 16 אפריל 2026 — "The Big Cleanup Day"

**Commit 884088c (12:03 פרו):**
```
fix: add ATRX validation to prevent yfinance bad data
- Sanity check after ATRX calculation in analyze_ticker() and update_score_tracker()
- Block ATRX when ATR < 0.5% of price AND ATRX > 5 (bug signature)
```

**Scripts שרצו (לא ב-GitHub):**
- `fix_atrx.py` → 80 שורות ATRX תוקנו ב-post_analysis (ATRX_calc → ATRX)
- `recalculate_scores_v2.py` → 100 שורות recalc של 9 ציונים
- `quick_audit.py` → audit_flag נוסף ל-124 שורות

**Commit 97a7b86 (19:xx פרו):**
```
fix: MxV percentage bug in score_tracker + REL_VOL cap
- Fix MxV missing *100 multiplier in update_score_tracker() (line 1269)
- Remove now-double *100 in MxV write to sheet (line 1282)
- Add REL_VOL cap=100 in analyze_ticker (line 508-510)
- Add REL_VOL cap=100 in update_score_tracker (line 1250-1252)
- Logging when cap triggered (yfinance bad data indicator)
```

### 11 אפריל 2026 — Score v2 launched
Commit f3d96ca — השוני ממגרסה v1:
- משקלים חדשים (ראה סעיף 4.1)
- **Gap הוסר** (בלי תיעוד סיבה!)
- ScanChange% נוסף

### 4 אפריל 2026 — "Final score weights" (v1 = LAST VERSION BEFORE v2)
Commits a8535da, 77e3964 — התיעוד ב-PROJECT_DOCUMENTATION.md מתייחס לזה.

### 17 מרץ 2026 — v12.0
התחלה של הפרויקט, עם 10 מטריקות ו-Google Sheets יחיד. **רוב התיעוד הישן מתייחס לזה — לא רלוונטי היום.**

---

## 🎓 טיפים אחרונים ל-Claude שקורא את זה

### לפני שאתה עונה:
1. ✅ קראת את כל המסמך?
2. ✅ אתה יודע איזה Score version רץ? (v2)
3. ✅ אתה יודע כמה ציונים יש? (12, לא 9)
4. ✅ אתה יודע ש-Gap הוסר? (v2 removed it)
5. ✅ אתה יודע שיש 3 הגדרות SL שונות? (7%/10%/D1)
6. ✅ אתה יודע ש-yfinance לא אמין? (יש validation)
7. ✅ אתה יודע שהתיעוד הישן ב-PROJECT_DOCUMENTATION.md **לא נכון**?

### כשאתה מציע שינוי:
1. **תסתכל בקוד קודם** — אל תסמוך רק על המסמך הזה
2. **אם יש פער בין קוד למסמך** — הקוד הוא האמת
3. **אל תמציא פונקציות שלא קיימות** — תחפש ב-grep
4. **תתחיל מהבדיקה הכי פשוטה** — אל תיכנס לפתרונות מורכבים לפני שהבנת את הבעיה

### כשעמיחי אומר "יש בעיה":
1. **תאמין לו** — הוא יודע את המערכת
2. **תבקש reproduce** — מה בדיוק קרה?
3. **תעצור לפני שאתה מתקן** — קודם תבין, אז תתקן
4. **תתעד ב-OPEN_ISSUES.md** אם זה לא מיידי

---

**תאריך עדכון אחרון:** 2026-04-16, 20:30 פרו  
**עדכון הבא נדרש:** אחרי כל שינוי מרכזי במערכת  
**אחראי עדכון:** Claude + עמיחי ביחד
