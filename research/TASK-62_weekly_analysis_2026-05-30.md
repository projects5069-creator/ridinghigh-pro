# TASK-62 — ניתוח שבוע מסחר RidingHigh Pro

**תאריך הפקה:** 2026-05-30 (Peru) · **PK:** v2.49 · **מקור:** snapshot מקומי `/tmp/rh62_data.json` (נמשך פעם אחת מ-Sheets, חודש פעיל 2026-05)
**מדגם:** 104 פוזיציות סגורות (DRY_RUN_CLOSED) · טווח כניסות 2026-05-06 → 2026-05-29
**מתודולוגיה:** קריאה בלבד, ניתוח offline. כל קורלציה/פילוח מתויג ב-n ו-confidence.

> ⚠️ **הסתייגות-על:** זהו **שבוע מסחר יחיד / רגיים יחיד** (~104 עסקאות, dry-run). כל הממצאים מטה הם snapshot נקודתי — **אסור להכליל מהם לאסטרטגיה** ללא אישוש רב-שבועי וריבוי רגיימים. רוב הקורלציות **לא-מובהקות (ns)** והפילוחים **EXPLORATORY**.
>
> דרגות confidence: `STRONG ≥100 · RELIABLE 30–99 · EXPLORATORY 10–29 · INSUFFICIENT <10`.

---

## 📊 סיכום ממצאים

**השבוע לא הראה edge.** המערכת התנהגה כהימור מטבע נוטה קלות לרעה:

| KPI | ערך |
|---|---|
| Win Rate | **49.0%** (51W / 53L) |
| Profit Factor ($) | **0.99** |
| Expectancy | **−0.49% / −$0.75** לעסקה |
| Net | **−$77.80** (net% −50.76) |

ולא פחות חשוב: **הציון הכולל (Score) חסר כוח ניבוי** (r=−0.029), **אף מדד אינו מובהק**, ו-**SENTINEL בכיוון הפוך** — אילו היה פעיל היה חוסם דווקא את העסקאות המנצחות.

---

## 🔍 KPI ליבה (ריצה 2ב)

| מדד | ערך |
|---|---|
| n (סגורות עם PnL%) | 104 |
| Win Rate | 49.0% (51W / 53L) |
| Avg Win | +15.12% |
| Avg Loss | −15.51% |
| R:R | 0.98 |
| Profit Factor ($) | 0.99 |
| Expectancy | −0.49% / −$0.75 |
| net% | −50.76 |
| median% | 0.00 |
| net USD | −$77.80 |
| Max Drawdown (cum $) | −$2,087.23 |

**קריאה מבנית:** AvgWin (+15.12%) ≈ |AvgLoss| (−15.51%) ותואם ל-ExitReason: **TP_HIT 51 / SL_HIT 50** (+3 MANUAL_CLEANUP). ברקטים סימטריים של ~±15% עם WR≈50% → **תוחלת אפס מבנית** עוד לפני עלויות. כדי להרוויח צריך WR מעל 50% משמעותית **או** R:R א-סימטרי — כרגע אין אף אחד מהם.

---

## 🔍 קורלציית מדדי-כניסה ל-PnL% (ריצה 2ב)

מקור: 104 שורות `ENTER` מ-`decision_log` (95 ייחודיות), join ל-`RealizedPnLPct` לפי `DecisionID==PositionID` → **93 זוגות**. Pearson r. סף מובהקות crit≈0.203 (p<.05, n=93).

| # | מדד | r | \|r\| | n | conf | in_Score | מובהק? |
|---|---|---|---|---|---|---|---|
| 1 | ScanChange | +0.190 | 0.190 | 93 | RELIABLE | YES | ns |
| 2 | REL_VOL | +0.181 | 0.181 | 93 | RELIABLE | YES | ns |
| 3 | MxV | **−0.139** | 0.139 | 93 | RELIABLE | YES | ns |
| 4 | FloatPct | +0.128 | 0.128 | 93 | RELIABLE | no | ns |
| 5 | ConfidenceScore | −0.124 | 0.124 | 93 | RELIABLE | no | ns |
| 6 | ATRX | +0.098 | 0.098 | 93 | RELIABLE | YES | ns |
| 7 | TypicalPriceDist | +0.079 | 0.079 | 93 | RELIABLE | YES (=משקל VWAP) | ns |
| 8 | RunUp | +0.064 | 0.064 | 93 | RELIABLE | YES | ns |
| 9 | Score | **−0.029** | 0.029 | 93 | RELIABLE | composite | ns |
| 10 | RSI | −0.021 | 0.021 | 93 | RELIABLE | YES | ns |
| — | PriceVsSMA20 | (−0.375) | — | 17 | **INSUFFICIENT** | YES | מוחרג (מילוי 17/93) |

- **STRONGEST:** ScanChange (\|r\|=0.190) · **WEAKEST:** RSI (\|r\|=0.021).
- **⚠️ כל 10 המדדים לא-מובהקים** — אף אחד לא עובר crit≈0.203. אין מנבא מוכח השבוע.
- **Score עצמו r=−0.029** → הציון הכולל לא מפריד מנצחות ממפסידות.
- **MxV — המשקל הגבוה ביותר (25) — קורלציה שלילית** (−0.139).
- **FloatPct (לא ב-Score) עוקף 4 מ-7 רכיבי ה-Score**, כולל את החלש RSI (0.021) — רמז שהקצאת המשקלים אולי לא אופטימלית. **השערה לבדיקה רב-שבועית, לא מסקנה.**

> משקלי Score v2 (PK v2.49): MxV 25 · RunUp 25 · ATRX 20 · RSI 10 · VWAP 10 · ScanChange 5 · REL_VOL 5.

---

## 🔍 ביקורת 5 הסוכנים (ריצה 2ג)

### TRADER → עובד-ומנוצל
מבצע בפועל: 104 ENTER מול 16,145 SKIP ב-`decision_log`. מחווט להחלטה ומתעד מדדי כניסה מלאים (10/10).

### SENTINEL (shadow) → **לשיפור — דגל אדום להפעלה** 🔴 (RELIABLE)
counterfactual לפי ticker+יום (ticker מ-`Details` JSON):

| קבוצה | n | WR | avg PnL | conf |
|---|---|---|---|---|
| would-BLOCK | 36 | **64%** | **+2.76%** | RELIABLE |
| not-blocked | 68 | **41%** | **−2.21%** | RELIABLE |

**הכיוון הפוך מהרצוי:** העסקאות ש-SENTINEL היה חוסם הן דווקא המנצחות. אילו היה פעיל (לא shadow) — היה **מסיר עסקאות מנצחות** = ערך שלילי. פילוח ה-BLOCKs: `scan_freshness` 6,188 · `price_freshness` 557 · `scan_freshness,price_freshness` 337 · `price_sanity,price_freshness` 64 · `system_check` 320 (סה"כ 7,466). **83% scan_freshness** — שערי טריות-דאטה, לא איכות-סיגנל. הפרשנות: עסקאות בימים עם סריקה "לא טריה" דווקא הצליחו יותר (RELIABLE n=36/68, אך רגיים יחיד). → **TASK-66, חוסם מעבר ל-active.**

### NEWS DETECTIVE → **לא-תורם** (כמנבא), EXPLORATORY
| דלי | n | WR | avg PnL | conf |
|---|---|---|---|---|
| WITH material news | 20 | 60% | +0.13% | EXPLORATORY |
| WITHOUT news | 24 | 62% | +2.11% | EXPLORATORY |

נוכחות חדשות לא מפרידה תוצאה (WR 60 מול 62; בלי-חדשות אף הניב יותר). `EDGAR_Filing_Count`↔PnL: r=−0.156 (n=44, לא מובהק). כיסוי חלקי 05-17→05-29 (44/104). → **TASK-67.**

### MARKET CONTEXT → עובד-ולא-מנוצל (רמז כיווני), EXPLORATORY
VIX_Close terciles (44 עסקאות תואמות):

| tercile | n | WR | avg PnL | conf |
|---|---|---|---|---|
| VIX low (≤15.74) | 19 | 58% | +1.75% | EXPLORATORY |
| VIX mid | 7 | 43% | −4.99% | INSUFFICIENT |
| VIX high (≥17.44) | 18 | 72% | +3.05% | EXPLORATORY |

רמז: ימי VIX גבוה ביצעו טוב יותר (72%/+3.05%) — אך EXPLORATORY בלבד, לא actionable. `SPY_Direction=FLAT` כל השבוע = **הגדרה תקינה** (סף 0.2%, תקופה שטוחה), **לא באג**. ה-VIX אינו משמש כיום בהחלטה.

### CRITIC → עובד (השפעה לא נמדדה)
68 שורות `agent_scorecard` (17 ימים × 4 סוכנים: Trader/Sentinel/Market Context/News Detective). 14 anomalies (5 ב-high). מייצר פלט עקבי; האם תורגם לפעולה — לא נמדד.

---

## ⚠️ דגלים

1. **רגיים יחיד / n קטן** — News ו-Market Context EXPLORATORY; רק SENTINEL ב-RELIABLE. שום ערך אינו edge ודאי.
2. **כל הקורלציות ns** — אף מדד-כניסה לא מובהק; Score r≈0.
3. **11 שורות כפולות** ב-`paper_portfolio` (115 שורות → 104 פוזיציות ייחודיות) — לתקן מקור הכפילות לפני KPI עתידי.
4. **`MetricsAtEntry` ריק** (`{}` ב-82+/95 postmortems) — מדדי הכניסה שוחזרו מ-`decision_log` ENTERs. (ראה TASK-65 לפער ה-9.)
5. **MARKET CONTEXT FLAT = הגדרה תקינה**, לא באג (סף 0.2%, שבוע שטוח).
6. **SENTINEL counterfactual** הוא ticker+יום (לא רגע מדויק), shadow, ובלוקי טריות-דאטה — הכיוון השלילי מאומת אך טעון אישוש רב-שבועי.

---

## 💡 המלצה הבאה

1. **לא לשנות משקלים עכשיו.** הממצאים (Score r≈0, MxV שלילי, FloatPct עוקף) הם רמזים מ-93 עסקאות לא-מובהקות. **להמשיך לאסוף עד מדגם רב-שבועי / ריבוי רגיימים** לפני כל כיול משקלים — plateaus, לא peaks.
2. **לא להפעיל את SENTINEL ל-active** עד שייחקר ה-counterfactual ההפוך (**TASK-66, P1**) — בכיוון הנוכחי הפעלה הייתה פוגעת.
3. **מועמד #1 ל-deep-dive עתידי:** משקל MxV=25 מול הקורלציה השלילית — רק כ-hypothesis לבקטסט, לא שינוי מיידי.

---

## קישור למשימות backlog (TASK-62)

| Task | נושא | priority |
|---|---|---|
| TASK-63 | post_analysis_snapshot.json עם 2 רשומות בלבד | P2 |
| TASK-64 | מפת מקורות דאטה מתועדת | P2 |
| TASK-65 | פער postmortems (9 פוזיציות, 104 vs 95) | P2 |
| TASK-66 | SENTINEL counterfactual הפוך — חוסם active | **P1** |
| TASK-67 | NEWS DETECTIVE לא מבחין WIN מ-LOSS | P2 |
| TASK-27 | DropsLab ריק (note נוסף) | LOW |

---
*הופק ב-TASK-62 (ריצות 1/1.5/2/2ב/2ג). כל המספרים נמדדו על snapshot מקומי מאומת; אפס שליפה חוזרת מ-Sheets, אפס חישוב מחדש.*
