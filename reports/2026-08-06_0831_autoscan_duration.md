# פילוח משך הריצה של auto_scan

**נכתב 2026-08-06 08:31 Lima / 09:31 ET.** ⚠️ **חקירה בלבד — לא שיניתי שום קובץ.**
לא נגעתי ב-`.github/workflows/` (נשארים `M`), לא ב-Sheets/Drive/FINVIZ,
לא הרצתי workflow/scanner/collector. אין commit, אין push.
כל הראיות מלוגי Actions ומקריאת הקוד.

**סקילים:**
| סקיל | path | wc -l |
|---|---|---|
| rhpro-live | `~/.claude/skills/rhpro-live/SKILL.md` | 180 |
| superpowers/systematic-debugging | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/systematic-debugging/SKILL.md` | 296 |
| superpowers/verification-before-completion | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/verification-before-completion/SKILL.md` | 139 |

---

## 0. ⚠️ מלכודת מדגם שנמנעה — שווה לתעד

הפקודה שנתת, `gh run list --workflow=auto_scan.yml --limit 60`, החזירה עמוד שמכיל
כמעט רק ריצות **מחוץ לשעות המסחר**:
```
dates in page: ['2026-08-05', '2026-08-06']
success durations: min=23 p25=28 median=30 p75=34 max=43
```
**חציון 30 שניות — לא 269.** הסיבה: `is_market_hours` מפיל את הריצה מיד מחוץ לחלון,
ולכן ריצות ערב ובוקר-מוקדם נמשכות ~30 שניות. שקלול שלהן היה מייצר את המסקנה
השגויה "auto_scan כבר מהיר".

**מה שעשיתי במקום:** חזרתי למדגם המלא של 5/8 וסיננתי לחלון המסחר:
```
2026-08-05 auto_scan: n=400  success=337
  all-day    : min=23 p25=128 median=245 p75=314 max=472
  in-market (13:30-20:00Z) n=276  median=269  max=472
```
**269 שניות — מאושר, על 276 ריצות תוך-יומיות.**

---

## 1. פילוח לפי step

חמש ריצות סביב החציון + שתיים מהארוכות ביותר, כולן `success`, כולן בחלון המסחר:
```
step                      36825904  32887840  28264364  32165176  30219528  41088438  41629120    median
Set up job                       1         0         1         1         1         1         1         1
Checkout code                    2         1         1         2         3         1         1         1
Set up Python                    0         1         1         0         0         0         0         0
Install dependencies            19        17        18        16        18        16        16        17
Run scanner                    231       242       240       236       240       448       440       240
Post/Complete                    0         0         1         0         0         0         0         0
------------------------------------------------------------------------------------------------------------
SUM                            253       261       262       255       262       466       458
```

| רכיב | חציון |
|---|---|
| תקורה (`Set up job` + `Checkout` + `Set up Python`) | **2s** |
| `Install dependencies` (pip) | **17s** |
| **`Run scanner`** | **240s** |
| **סה"כ steps** | **~258s** |

**התקורה כאן קטנה יותר מ-agent_minute (19s מול 31s)** — ה-pip של `auto_scan` מתקין
רשימה מפורשת ולא `-r requirements.txt`. **93% מהזמן הוא הסקאנר עצמו.**

---

## 2. בתוך `run_scan` — ציר זמן מהלוג

הריצה: `31036825904`, `Run scanner` = 231s. הלוג **כן** נושא חותמות מיקרו-שנייה.
כל שורה עם פער >2 שניות מקודמתה:
```
  +   0.00s  18:53:36.565  Run python auto_scanner.py
  +   3.41s  18:53:44.087  [data_provider] Initialized fundamentals provider: yfinance-fundamentals
  +  51.75s  18:54:35.837  Alpaca get_daily_bars(ROCK) failed: {"message": "too many requests."}
  +  28.35s  18:55:04.183  Alpaca get_daily_bars(PCLA) failed: {"message": "too many requests."}
  +   9.24s  18:55:13.422  Alpaca get_daily_bars(RMCO) failed: {"message": "too many requests."}
  +   9.24s  18:55:22.662  Alpaca get_daily_bars(TATT) failed: {"message": "too many requests."}
  +  16.45s  18:55:39.116  Alpaca get_daily_bars(SAIH) failed: {"message": "too many requests."}
  +   9.24s  18:55:48.355  Alpaca get_daily_bars(NEOV) failed: {"message": "too many requests."}
  +  14.87s  18:56:03.225  Alpaca get_daily_bars(BIYA) failed: {"message": "too many requests."}
  +  15.86s  18:56:19.085  Alpaca get_daily_bars(GEG)  failed: {"message": "too many requests."}
  +  24.50s  18:56:43.589  Alpaca get_daily_bars(PDC)  failed: {"message": "too many requests."}
  +  43.62s  18:57:27.206  [Info] loading page [####################----------] 2/3

total scanner span: 231.2s
```

**המדדים:**
```
'too many requests' occurrences : 9
lines mentioning 429            : 0
'loading page' (finviz)         : 2      ← 1/3 ב-18:53:40, 2/3 ב-18:57:27
'✅' finviz tickers scored       : 37
'📌' tracked tickers scored      : 31     ← "📌 Tracking 40 missing tickers..."
total app lines in the step     : 134
throttling window               : 18:54:35 → 18:56:43 = 128s
```

### התשובות לשאלות ששאלת

| שאלה | תשובה |
|---|---|
| **קריאת FINVIZ — כמה זמן, כמה קריאות** | הלוג מראה **שני** סמני `loading page` — `1/3` ב-+3.6s ו-`2/3` ב-+230.6s. **הזמן ביניהם אינו זמן FINVIZ** אלא כל לולאת הטיקרים. **לא ניתן לחלץ מהלוג את משך קריאת FINVIZ עצמה** — אין חותמת סיום. מוצהר. |
| **`analyze_ticker` — כמה טיקרים, כמה זמן פר-טיקר** | **37 מ-FINVIZ + 31 מהמעקב = 68 טיקרים שהניבו תוצאה**, מתוך 37+40 שנוסו. הלוג **אינו** נושא חותמת לכל טיקר — רק לאלה שהצליחו (`✅`/`📌`) ולאלה שנחסמו. **זמן פר-טיקר אינו נגזר מהלוג.** מוצהר. |
| **הכתיבות לחמשת הטאבים** | **אין להן חותמת בלוג כלל.** לא מדדתי אותן. מוצהר. |
| **כמה קריאות/כתיבות API לגיליונות** | לא נגזר מהלוג. ראה §4 לניתוח סטטי. |

⚠️ **מה שכן נגזר חד-משמעית:** בין 18:54:35 ל-18:56:43 — **128 שניות, 55% מהריצה** —
הלוג מכיל **תשע** חסימות `too many requests` מ-Alpaca, עם פערים של 9 עד 52 שניות
ביניהן. **הפערים כוללים גם עבודה אמיתית וגם המתנה; הלוג אינו מפריד ביניהן.**

---

## 3. הקריאות פר-טיקר — ⚠️ אותו דפוס בדיוק, בקנה-מידה גדול יותר

### 3.1 — קריאות רשת פר-טיקר, `file:line`
```
auto_scanner.py:162   get_market_cap_smart(ticker, ...)          → utils.py:313, שרשרת fallback
auto_scanner.py:193   provider.get_daily_bars(ticker, days=252)  → Alpaca   ← רשת
auto_scanner.py:206   get_fundamentals_provider().get_fundamentals(ticker)  ← רשת (yfinance)
```
**שתי קריאות רשת ודאיות לכל טיקר מ-FINVIZ**, לשני ספקים שונים.

### 3.2 — לולאת המעקב מכפילה את זה
```
auto_scanner.py:374-382   for idx, row in finviz_df.iterrows():
                              data = analyze_ticker(ticker, row)
                              time.sleep(0.1)
auto_scanner.py:396-413   for ticker in missing:
                              hist = provider.get_daily_bars(ticker, days=60)   ← רשת #1
                              ...
                              data = analyze_ticker(ticker, finviz_row)          ← ובתוכה עוד
                                                                                 get_daily_bars(252)
                                                                                 + get_fundamentals
                              time.sleep(0.2)
```
**כל טיקר-מעקב עולה שלוש קריאות רשת** — `get_daily_bars(60)`, ואז בתוך `analyze_ticker`
עוד `get_daily_bars(252)` ועוד `get_fundamentals`.

**האומדן לריצה שנמדדה:** 37 טיקרי-FINVIZ × 2 + 40 טיקרי-מעקב × 3 = **~194 קריאות
רשת סדרתיות בריצה אחת, בכל דקה.**
⚠️ זהו **אומדן מהקוד**, לא ספירה מהלוג — הלוג אינו מונה קריאות מוצלחות.

### 3.3 — האם יש לולאה סדרתית שניתנת ל-batch
**כן — בדיוק אותה מחלקה שתוקנה ב-SMA20.**
`auto_scanner.py:193` קורא ל-`provider.get_daily_bars(ticker, days=252)` בלולאה, בעוד
`providers/alpaca_provider.py:224` כבר מכיל היום את `get_daily_bars_batch` שנוסף
ב-TASK-259 ותומך ב-`symbol_or_symbols` כרשימה.
⚠️ **אבל `get_fundamentals` הוא yfinance ופר-טיקר** — הוא **אינו** מכוסה ע"י ה-batch
של Alpaca. חצי מהקריאות יישארו סדרתיות.

### 3.4 — הקאש, ואיפה הוא נשמר
```
auto_scanner.py:115   _mc_cache = {}
auto_scanner.py:119   cache_path = os.path.expanduser("~/RidingHighPro/data/market_cap_cache.json")
auto_scanner.py:143   _shares_cache = {}

$ git check-ignore -v data/market_cap_cache.json
.gitignore:12:data/	data/market_cap_cache.json
```
**`data/` ב-.gitignore ⇒ הקאש תמיד קר על runner.** זהה מילה-במילה לאבחון של
`sma20_cache.json`. כל ריצה מתחילה ריקה ומושכת הכל מחדש.

### 3.5 — sleep מכוון
```
auto_scanner.py:382   time.sleep(0.1)   × ~37 טיקרי FINVIZ  =  ~3.7s
auto_scanner.py:412   time.sleep(0.2)   × 40 טיקרי מעקב     =  ~8.0s
auto_scanner.py:977   time.sleep(0.2)   ב-update_live_trades
```
**~12 שניות מתוך 240 הן sleep מכוון** — 5%. לא הגורם הדומיננטי.

---

## 4. הכתיבות — ⚠️ **הנחת ההוראה לא אושרה**

ההוראה שיערה "אותה מחלקת בעיה כמו `sentinel_events` — append פר-שורה במקום אחד מרוכז".
**בדקתי, וזה לא המצב:**
```
$ grep -n "safe_append_rows\|safe_append_row(\|\.append_row(\|\.append_rows(" auto_scanner.py
473:    sheets_manager.safe_append_rows(...)      ← timeline_live
991:    sheets_manager.safe_append_rows(ws_fu, rows_df...)   ← ticker_follow_up
1289:   sheets_manager.safe_append_rows(ws_st, new_df...)    ← score_tracker

$ grep -n -B3 "safe_append_row(" auto_scanner.py
(ריק — אין ולו קריאה אחת ל-safe_append_row בלשון יחיד)

$ grep -c "\.update(" auto_scanner.py   → 0
$ grep -c "get_worksheet" auto_scanner.py → 13
```
**שלוש קריאות `safe_append_rows` בלבד, אפס `safe_append_row` יחיד, אפס append בתוך לולאה.**
`update_portfolio_live` ו-`update_live_trades` משתמשים ב-`get_worksheet` + קריאה,
ולא בכתיבה פר-שורה.

**מסקנה: נתיב הכתיבה של `auto_scan` כבר מרוכז ואינו הבעיה.**
זו תוצאה שלילית משמעותית — היא שוללת מועמד ומצמצמת את החקירה לנתיב הקריאה.

---

## 5. השוואה ל-agent_minute

| רכיב | `agent_minute` (נמדד 5/8) | `auto_scan` (נמדד 5/8) |
|---|---|---|
| תקורה + pip | 31s (pip 29) | **19s** (pip 17) |
| הרצת הלוגיקה | 164s | **240s** |
| **הרכיב הדומיננטי** | SMA20: **106s**, 60 קריאות `get_daily_bars` סדרתיות | לולאת הטיקרים: **~194 קריאות** סדרתיות לשני ספקים |
| הקאש | `data/sma20_cache.json` — gitignored, תמיד קר | `data/market_cap_cache.json` — gitignored, תמיד קר |
| חסימות בלוג | `too many requests` ×2 | **`too many requests` ×9** |
| נתיב הכתיבה | `sentinel_events` — append **פר-סיגנל**, 55/60 נכשלו | **מרוכז** — 3 × `safe_append_rows` |
| sleep מכוון | ~0s | ~12s |

**התשובה: השורש דומה מאוד בקריאה, ושונה לגמרי בכתיבה.**
- **זהה:** לולאה סדרתית של `get_daily_bars` פר-טיקר, מול קאש ב-`data/` שתמיד קר
  ב-runner, שנתקלת ב-throttling של Alpaca.
- **חמור יותר ב-auto_scan:** ~194 קריאות מול 60, ותשע חסימות מול שתיים.
- **שונה:** ב-`auto_scan` הכתיבות כבר מרוכזות; ב-`agent_minute` הן פר-סיגנל.
- **שונה:** ל-`auto_scan` יש ספק שני — `get_fundamentals` מ-yfinance — שה-batch
  של Alpaca לא נוגע בו.

---

## 6. המסקנה — שלוש שורות

**לאן הולכות 269 השניות:** ~19s תקורה (מתוכן 17 pip) · ~240s בסקאנר, שבתוכו
**לולאת טיקרים סדרתית של ~194 קריאות רשת לשני ספקים** מול קאש שתמיד קר,
ועוד ~12s sleep מכוון. הכתיבות אינן גורם.

**הרכיב הגדול ביותר:** לולאת הטיקרים. לא ניתן להצמיד לה מספר מדויק מהלוג, אבל
**128 שניות — 55% מהריצה — הן החלון שבו נרשמו תשע חסימות `too many requests`**,
וזה החתך היחיד שהלוג מאפשר לכמת.

**האם מתחת ל-60 שניות אפשרי:** לא בלי לשנות את לולאת הטיקרים. גם אם ה-pip יורד
לאפס וה-sleep נמחק, זה חוסך ~29s מתוך 269 — הריצה תעמוד על ~240s.
**רק צמצום ~194 הקריאות הסדרתיות יכול לשנות סדר-גודל**, ו-`get_daily_bars_batch`
מכסה רק את חלק ה-Alpaca; `get_fundamentals` יישאר פר-טיקר.

⚠️ **אלה עובדות ואריתמטיקה על מה שנמדד. לא הצעתי תיקון ולא כתבתי קוד.**

---

## מה לא נמדד — הצהרה

1. **משך קריאת FINVIZ.** שני סמני `loading page` בלבד, בלי חותמת סיום.
2. **זמן פר-טיקר.** הלוג מתעד רק הצלחות וחסימות, לא כניסה/יציאה לכל טיקר.
3. **זמן הכתיבות לחמשת הטאבים.** אין להן חותמת בלוג.
4. **ספירת קריאות API בפועל.** ה-~194 הוא אומדן מהקוד, לא ספירה.
5. **הפרדה בין המתנת-throttle לעבודה אמיתית** בתוך 128 השניות. הלוג לא מפריד.
6. **מדידה של היום (6/8) אחרי הפריסה.** התור הזה נפתח ב-09:31 ET, דקה אחרי הפתיחה —
   אין עדיין מדגם תוך-יומי. כל המספרים כאן הם מ-5/8.
7. **האם ריצת auto_scan נגמרה תקין** — הלוג של הריצה שנדגמה מסתיים ב-`loading page 2/3`
   ומיד עובר לניקוי git, בלי סמן סיום מפורש. לא בדקתי אם זו התנהגות תקינה.
