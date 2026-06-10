# 🛠️ RidingHigh — תוכנית תיקון מסודרת — 2026-06-09

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans או subagent-driven-development. תכנון בלבד — שום פריט לא מומש בכתיבת מסמך זה.

**Goal:** לשחרר את שני חסמי-הדאטה, לנתק את ה-Score מההחלטה על בסיס ראיות, ולבנות gate מבוסס-מדדים — בסדר תלות נכון.

**מקור הממצאים:** `docs/SYSTEM_REVIEW_2026-06-09_v1.md` + חקירות 9/6 (כולן read-only). כל ממצא אומת מול קוד חי ב-20:02 פרו (ראיות file:line למטה).

**עוגן רעיוני:** המדדים שנבדקו מנבאים **תנועה**, לא **כיוון** (TASK-76 + מחקר DropsLab 9/6) — לכן שלב 3 חייב לבוא אחרי דאטה משוחררת, לא לפניה.

---

## ממצאים מאומתים (STEP 1 — ראיות)

| # | ממצא | ראיה (אומת 9/6 20:02) |
|---|------|------------------------|
| A | Score הוא Filter 1 וחוסם כניסה; 70% מהמשקל (MxV 25 + RunUp 25 + ATRX 20) על מדדים עם ~0 קורלציה לתוצאה; Price — המנבא המובהק היחיד (r=+0.249 אמיתי / +0.332 מחקרי) — **לא במשקלים בכלל** (grep `"Price"` ב-config = 0) | decision_logic.py:276-278; config.py:40-49 |
| B | SKIP logging מת ב-**11/5**: "Route B" — כל non-ENTER מודפס ל-stdout בלבד ולא נכתב ל-Sheet. סיבה מתועדת: 80-100 SKIPs/דקה ≈ 30K כתיבות/יום מול quota 60/דקה → 429 ששברו את monitor_all. תופעת לוואי: אובדן counterfactual | decision_logger.py:156-169; commit `b1a4e4f` 2026-05-11 |
| C | 70 שורות post_analysis v2 תקועות PENDING (אפריל 34, מאי 36). `backfill_ohlc.py` לא סוגר אותן משתי סיבות בלתי-תלויות: (1) טוען חודש פעיל בלבד; (2) טריגר = D1_Open חסר בלבד → רק 19/70 נראות, 51 בלתי-נראות. דולף מחדש בכל סוף-חודש | backfill_ohlc.py:76-77; gsheets_sync.py:47-49,357; אימות דאטה 19:58 |
| D | ניקוד RSI: `SCORE_RSI_PARAMS` מוקצה (`R=`) ולא נצרך אף פעם; בפועל מדרגות hardcoded ≥80/85/90; docstring + PK §18 מתארים bell-curve שלא קיים; PK RSI_LOW=50 מול config=60 | formulas.py:392 (אין `R[`), 408-417, 388; config.py:64-70 |

---

## קבוצה 1 — שחרור בריאות-הדאטה (תיקונים ודאיים, ראשונים בתלות)

### 1.1 ⬛ TASK-123 — `backfill_ohlc_v2.py`: סגירת 70 ה-PENDING
- **מה ולמה:** סקריפט versioned חדש (§12) עם פרמטר `month` המועבר ל-load/save + טריגר "כל D{i} חסר" — מכפיל את ה-n המחקרי 49→~115.
- **קבצים:** חדש `backfill_ohlc_v2.py` (בסיס: backfill_ohlc.py); אין נגיעה ב-formulas/config/orchestrator.
- **תלות:** אין — ראשון.
- **Run-mode:** **PING-PONG.** כותב ל-Sheets (תוכן חיצוני + side-effects על דאטת המחקר) → לא auto-safe לפי כלל-3; הרצה מחוץ לשעות מסחר, diff על dry-run לפני כתיבה.
- **Done:** stale-PENDING (ScanDate<מחזור נוכחי) יורד מ-70 ל-≤טיקרים-delisted בלבד, מאומת בשליפה חוזרת; py_compile; אפס שינוי בשורות מלאות.

### 1.2 ⬛ TASK-124 — תיקון קבוע לדליפת ה-cross-month ב-collector
- **מה ולמה:** שורות שנסרקות בסוף-חודש מאבדות D4/D5 אחרי הרוטציה — לתקן שה-collector (או step חודשי ב-post_analysis.yml) יסרוק גם חודש-קודם-לא-שלם.
- **קבצים:** post_analysis_collector.py (או workflow step חדש — שינוי workflow = נתיב אסור-אוטומציה).
- **תלות:** אחרי 1.1 (לקחי ההרצה הידנית).
- **Run-mode:** **PING-PONG** (נוגע ב-pipeline ייצור + ייתכן `.github/workflows/*` — נתיב אסור לפי כלל-2).
- **Done:** סימולציית מעבר-חודש (יוני→יולי) לא משאירה שורת יוני פתוחה; טסט יחידה על בחירת מועמדים.

### 1.3 ⬛ TASK-125 — החזרת נראות SKIP (המשך Route B)
- **מה ולמה:** counterfactual הוא לולאת-הלמידה המרכזית (חשף את MXV/RUNUP ב-25/5) ומת מאז 11/5. פתרון: צבירה — שורה אחת פר-סיבת-SKIP פר-ריצה (~5-15 כתיבות/ריצה במקום 80-100) או rollup יומי ב-EOD לטאב ייעודי.
- **קבצים:** agent/logging/decision_logger.py (+אולי טאב חדש ב-setup). **בלי** לפתוח מחדש את סופת ה-429 ש-Route B פתר — תקציב הכתיבות חייב חישוב מראש.
- **תלות:** עצמאי; לפני קבוצה 3 (ה-gate החדש יצטרך counterfactual חי למדידת would-block).
- **Run-mode:** **PING-PONG** (נתיב לוגינג ייצורי שנכשל בעבר על quota — דורש עין).
- **Done:** יום מסחר מלא עם שורות skip-summary ב-Sheet, צריכת quota נמדדת < 20 כתיבות/דקה peak, ENTERs ללא רגרסיה.

### 1.4 ⬜ TASK-126 — חילוץ SKIPs היסטוריים מלוגי GitHub Actions (אופציונלי, יש דדליין)
- **מה ולמה:** ה-SKIPs של 12/5→היום חיים ב-stdout של Actions; retention ~90 יום → ריצות 12/5 פוקעות ~10/8. סקרייפר חד-פעמי (`gh run list` + `gh run view --log` + grep `[SKIP]`) ל-CSV מקומי.
- **תלות:** אין; עדיף מוקדם בגלל הדדליין.
- **Run-mode:** **goal** — auto-safe (repo/gh-scoped, קריאה בלבד, אין Sheets) + תנאי-סיום מדיד (CSV עם כיסוי כל ימי המסחר 12/5→היום).
- **Done:** CSV מקומי עם שורות SKIP לכל יום מסחר בטווח; ספירה ≥ צפי (~2K/יום).

## קבוצה 2 — ניתוק ה-Score מההחלטה (תלוי-דאטה + הכרעה)

### 2.1 ⬜ ולידציה מחודשת על הדאטה המשוחררת (חלק מ-TASK-127, שלב א')
- **מה ולמה:** לפני כל שינוי מדיניות — להריץ מחדש את קורלציות מדד↔תוצאה על ~115 שורות settled + מבחן re-anchor ל-D1_Gap (כניסת D1-open עם TP/SL מעוגנים אליה). ייתכן שהתמונה תשתנה עם הכפלת ה-n.
- **תלות:** **אחרי 1.1.** read-only.
- **Run-mode:** **goal** (auto-safe: קריאת CSV מקומי, תנאי-סיום = דוח עם n/r/p לכל מדד).
- **Done:** דוח קורלציות v2 על n≥110 + תוצאת re-anchor, שמור ב-research/.

### 2.2 ⬛ TASK-127 — הכרעת Filter 1 (Score→log-only?)
- **מה ולמה:** ה-Score חוסם כניסות בעודו חלש מכל רכיב בודד שלו. אופציות: השארת הסף, הורדתו, או Score כ-log-only עם gate חלופי. **הכרעת מדיניות מסחר — של עמיחי בלבד** (מקביל ל-TASK-69 הנעול).
- **קבצים (אם יוחלט):** config.py / decision_logic.py — נתיבי ליבה.
- **תלות:** אחרי 2.1; מתואם עם TASK-69.
- **Run-mode:** **PING-PONG** (עץ-החלטה ענף 1: הכרעה אסטרטגית).
- **Done:** החלטה מתועדת ב-PK + אם שונה קוד: TDD, PK bump, branch+PR.

## קבוצה 3 — ה-gate החדש מבוסס-מדדים (תלוי בכל הקודם)

### 3.1 ⬜ TASK-128 — בניית gate ב-shadow mode
- **מה ולמה:** gate מהמדדים ששרדו ולידציה בלבד (כרגע: רצועת Price $5-10 החזק היחיד; D1-gap רק אם עבר re-anchor). נבנה כשכבת shadow (לוג would-block, בלי לחסום) — בדיוק כמו Sentinel shadow.
- **קבצים:** שכבה חדשה תחת agent/ (לא orchestrator עצמו ככל האפשר; חיווט מינימלי).
- **תלות:** 2.1 + 2.2 + 1.3 (צריך counterfactual חי למדידה).
- **Run-mode:** **PING-PONG** לבנייה (ליבת-מסחר); ההרצה היא shadow מטבעה.
- **Done:** ≥2 שבועות shadow רב-משטרי; would-block WR נמדד מול actual; קריטריון הפעלה כמותי כתוב מראש (לקח TASK-66: לא להפעיל active על משטר-יחיד n=36).

## קבוצה 4 — ניקוי drift וקוד מת (ודאי, לא דחוף, אחרי 2.2 כדי לא לגעת ב-Score פעמיים)

### 4.1 ⬛ TASK-129 — RSI dead-config + יישור PK
- **מה ולמה:** למחוק/לחווט את SCORE_RSI_PARAMS + RSI_HIGH/LOW caps; ליישר docstring (formulas.py:388) ו-PK §18 (bell-curve→מדרגות, RSI_LOW 50→60). מסיר מוקש כיול-שווא.
- **קבצים:** config.py, formulas.py, PK — **נתיבים אסורים לאוטומציה** (כלל-2).
- **תלות:** אחרי 2.2 (אם Score מנותק — אולי נמחק יותר).
- **Run-mode:** **PING-PONG** (config+formulas).
- **Done:** test_formulas 107/107 + אין הפניה ל-SCORE_RSI_PARAMS; PK bump + changelog.

### 4.2 ⬜ ניקוי כפילויות inline (קיים חלקית ב-TASK-46; להרחיב שם, לא משימה חדשה)
- **מה ולמה:** scanner:235,243,906-907 + dashboard:382,388,409,562,568,593 inline במקום formulas; RSI/ATR כפולים ב-ticker_follow_up (scanner:865-886); is_market_hours כפול (utils מול orchestrator); normalize_*/peak_metrics מתים.
- **תלות:** עצמאי; עדיף אחרי 2.2.
- **Run-mode:** רובו **goal** (auto-safe: repo-scoped, תנאי מדיד "grep נקי + טסטים"); החלקים שנוגעים ב-orchestrator/formulas — **PING-PONG**.
- **Done:** grep אפס מופעי inline לנוסחאות ממופות; test_formulas 107/107; dashboard עולה.

---

## סדר ביצוע מומלץ (תלות, לא דחיפות בלבד)
```
1.1 (TASK-123) ─┬─→ 2.1 ─→ 2.2 (TASK-127) ─→ 3.1 (TASK-128) ─→ 4.1 (TASK-129) → 4.2
1.3 (TASK-125) ─┘            ↑
1.2 (TASK-124)  [אחרי 1.1]   │
1.4 (TASK-126)  [עצמאי, דדליין ~10/8] ──→ מזין את 2.1/3.1
```
**ודאי עכשיו:** 1.1, 1.2, 1.3, 1.4, 4.1, 4.2. **תלוי-דאטה/הכרעה:** 2.1→2.2→3.1.

*נכתב 2026-06-09 ~20:05 פרו. אפס מימוש — תכנון בלבד.*
