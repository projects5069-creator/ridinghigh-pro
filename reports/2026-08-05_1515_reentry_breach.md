# חקירת הפרת re-entry 2026-08-05 — DFNS + SHPH

**נכתב 2026-08-05 15:15 Lima.** ⚠️ **חקירה בלבד — לא תיקנתי דבר.**
לא נגעתי בקוד/workflow/config, לא הרצתי pytest, לא הרצתי workflow/scanner/collector,
קריאה בלבד מ-Sheets, אין commit/push, לא שיניתי סטטוס תיק. HEAD = `9eb3893`.

**סקילים:**
| סקיל | path | wc -l |
|---|---|---|
| rhpro-live | `~/.claude/skills/rhpro-live/SKILL.md` | 180 |
| superpowers/systematic-debugging | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/systematic-debugging/SKILL.md` | 296 |
| data-quality-checker | `~/.claude/skills/data-quality-checker/SKILL.md` | 161 |
| superpowers/verification-before-completion | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/verification-before-completion/SKILL.md` | 139 |

---

## 1. העובדות מהגיליון

`decision_log` 2026-08 מכיל **5 שורות** לשני הטיקרים האלה בכל החודש (אחת מ-3/8, ארבע מ-5/8).
כל אחת הודפסה במלואה — 42 עמודות. להלן השדות המכריעים זה לצד זה:

| Timestamp | Ticker | Action | SkipReason | ExistingPosition | ColdStartConcurrentLeft | ColdStartDailyLeft | BuyingPower | Qty | Price |
|---|---|---|---|---|---|---|---|---|---|
| 2026-08-03T08:41:44.505768-05:00 | DFNS | ENTER | *(ריק)* | FALSE | 3 | 6 | 200000 | 20 | 49.94 |
| **2026-08-05T09:32:29.661066-05:00** | **DFNS** | ENTER | *(ריק)* | **FALSE** | **5** | **7** | 200000 | 17 | 55.79 |
| **2026-08-05T09:32:54.639026-05:00** | **DFNS** | ENTER | *(ריק)* | **FALSE** | **5** | **7** | 200000 | 17 | 55.79 |
| **2026-08-05T11:40:39.094717-05:00** | **SHPH** | ENTER | *(ריק)* | **FALSE** | **5** | **5** | 200000 | 232 | 4.30 |
| **2026-08-05T11:43:55.917359-05:00** | **SHPH** | ENTER | *(ריק)* | **FALSE** | **5** | **5** | 200000 | 231 | 4.32 |

DecisionIDs: `DEC-2026-08-05-DFNS-093229-66` · `DEC-2026-08-05-DFNS-093254-63` ·
`DEC-2026-08-05-SHPH-114039-09` · `DEC-2026-08-05-SHPH-114355-91`.
`OrderID`, `OrderStatus`, `ExecutionPrice` ריקים בכל החמש (DRY_RUN).

**הפרש הזמן: DFNS — 25 שניות. SHPH — 3 דקות ו-16 שניות.**

### ⚠️ הראיה המרכזית — המונים לא ירדו

בשתי הכניסות של DFNS **`ColdStartConcurrentLeft = 5` ו-`ColdStartDailyLeft = 7` — זהים**.
אילו הכניסה הראשונה נראתה, השנייה הייתה צריכה לראות `4` ו-`6`.
אותו דבר ב-SHPH: `5` ו-`5` בשתיהן.
כלומר **מצב החשבון שנקרא בריצה השנייה זהה לזה של הריצה הראשונה** — הכניסה הראשונה
לא הייתה נוכחת בו.

### שורות SKIP של אותם טיקרים באותו יום

ב-`decision_log` — **אין**, כי Route B לא כותב SKIP לגיליון:
```
decision_log rows dated 2026-08-05 = 7   Action counts: {'ENTER': 7}
tickers that day: {'DFNS': 2, 'SHPH': 2, 'YXT': 1, 'DBGI': 1, 'INLF': 1}
```
ב-`skip_summary` — **145 שורות** של 5/8 מזכירות DFNS או SHPH, כולן `MXV_TOO_HIGH`,
מ-08:31 והלאה. כלומר שני הטיקרים היו בתצוגה כל היום ונדחו על MxV עד שהמדד הצטלב.

---

## 2. paper_portfolio — והתשובה לשאלה המכריעה

```
PositionID=DEC-2026-08-03-DFNS-084144-50 | DFNS | entry 2026-08-03 8:41:45 | DRY_RUN_CLOSED | exit 2026-08-03 9:09:10 | TP_HIT
PositionID=DEC-2026-08-05-DFNS-093229-66 | DFNS | entry 2026-08-05 9:32:31 | DRY_RUN_CLOSED | exit 2026-08-05 10:45:06 | TP_HIT
PositionID=DEC-2026-08-05-DFNS-093254-63 | DFNS | entry 2026-08-05 9:32:55 | DRY_RUN_CLOSED | exit 2026-08-05 10:45:07 | TP_HIT
PositionID=DEC-2026-08-05-SHPH-114355-91 | SHPH | entry 2026-08-05 11:44:06 | DRY_RUN_OPEN  | exit (ריק)
```

### התשובה, במפורש, עם חותמות זמן

**DFNS — לא. הראשונה לא נסגרה לפני שהשנייה נפתחה.**
```
פוזיציה #1  נפתחה 2026-08-05 09:32:31   נסגרה 2026-08-05 10:45:06
פוזיציה #2  נפתחה 2026-08-05 09:32:55   ← 09:32:55 < 10:45:06
```
בין 09:32:55 ל-10:45:06 **שתי הפוזיציות היו פתוחות בו-זמנית באותו טיקר, למשך 72 דקות.**
זו **הפרה אמיתית**, לא התרחיש שתועד ב-TASK-107.
*(שים לב: ההשוואה האוטומטית בסקריפט החזירה `closed_before_opened = True` — אבל היא השוותה
את פוזיציית **3/8** מול פוזיציית **5/8**, כי המיון היה לפי `EntryTime` בלבד בלי התאריך.
ההשוואה הנכונה, לפי התאריך, היא זו שלמעלה.)*

**SHPH — לא ניתן לענות, כי יש רק פוזיציה אחת.**
```
ENTER #1  DEC-2026-08-05-SHPH-114039-09  @ 11:40:39   →  אין שורת paper_portfolio כלל
ENTER #2  DEC-2026-08-05-SHPH-114355-91  @ 11:43:55   →  נכתבה שורה, EntryTime 11:44:06
```
⚠️ **ה-ENTER הראשון של SHPH לא ייצר שורת paper_portfolio.** זה ENTER-בלי-שורה —
בדיוק המחלקה של TASK-105 / TASK-106 / TASK-198.
המשמעות לחקירה הזו: בשעה 11:43:55 **באמת לא הייתה פוזיציה לראות**, ולכן
`ExistingPosition=FALSE` היה **נכון עובדתית**. השורש ב-SHPH אינו ה-guard — הוא הכתיבה החסרה.

**שני הטיקרים אינם אותו באג.**

---

## 5. היקף

```
2026-08: ENTER=17  distinct (date,ticker)=15  pairs with >1 ENTER=2  entries beyond cap=2
   dup pairs by date: {'2026-08-05': 2}
      2026-08-05  DFNS  ENTERs=2
      2026-08-05  SHPH  ENTERs=2

2026-07: ENTER=153 distinct (date,ticker)=80  pairs with >1 ENTER=20  entries beyond cap=73
   dup pairs by date: {'2026-07-01': 3, '2026-07-06': 4, '2026-07-07': 2,
                       '2026-07-16': 2, '2026-07-22': 4, '2026-07-23': 3, '2026-07-31': 2}
      07-01 CANF 2 · JEM 2 · SDOT 2
      07-06 LHSW 2 · FXHO 2 · TDIC 2 · INLF 2
      07-07 CLRO 3 · TVRD 3
      07-16 AATPC 9 · VVEEE 8
      07-22 LLABT 11 · IINLF 11 · AADVB 11 · ZZCMD 10
      07-23 PPAVS 2 · NNVVE 2 · SSKYQ 2
      07-31 FCUV 4 · FFAI 3
```
**5/8 אינו היום היחיד — הוא היום היחיד באוגוסט.**
ביולי: **20 זוגות ב-7 ימים שונים, 73 כניסות מעבר לתקרה.**
22/7 הוא 4 זוגות ו-43 כניסות — כלומר **59% מהכניסות-מעבר-לתקרה של יולי היו ביום ההוא**,
אבל **16 מתוך 20 הזוגות היו בימים אחרים**, לפני ואחרי.
התופעה **כרונית ומקדימה את אירוע ה-429 של 22/7**; היקפה ירד מ-73 ל-2.

---

## 6. הצלבה עם 429 / ACCOUNT_STATE_UNAVAILABLE

```
skip_summary rows dated 2026-08-05 = 305 (of 1153 in the month)
aggregate by reason on 08-05:
   MXV_TOO_HIGH      5912
   REENTRY_LIMIT      269
   EXISTING_POSITION   48

ACCOUNT_STATE_UNAVAILABLE anywhere in skip_summary 2026-08 — 2 rows, BOTH on 08-04:
   {'Timestamp': '2026-08-04 8:36:47', 'RunID': '30914630866', 'Count': '1', 'Tickers': 'AMIX'}
   {'Timestamp': '2026-08-04 8:41:46', 'RunID': '30915039535', 'Count': '1', 'Tickers': 'AMIX'}
```

**ב-5/8 אין ולו אירוע `ACCOUNT_STATE_UNAVAILABLE` אחד.** שניהם ב-4/8, על AMIX.
**זה מחזק את הקביעה שהשורש שונה מזה של 22/7.**

ויותר מזה — **הגארדים כן פעלו ב-5/8, אלפי פעמים:**
`REENTRY_LIMIT` ירה **269** פעמים ו-`EXISTING_POSITION` **48** פעמים באותו יום.
כלומר לא מדובר בגארד מנוטרל או בשער שקרס — הוא עבד, ופספס בדיוק שני מקרים.

### קצב הריצות סביב שתי ההפרות

```
--- חלון DFNS 09:28-09:38 (ENTERs ב-09:32:29 וב-09:32:54) ---
   RunID=31015332944  09:28:48   gap=—
   RunID=31015419113  09:29:48   gap=60s
   RunID=31015512481  09:30:57   gap=69s
   RunID=31015595330  09:31:41   gap=44s   ← ENTER #1 (09:32:29) שייך לריצה הזו
   RunID=31015680057  09:32:50   gap=69s   ← ENTER #2 (09:32:54) שייך לריצה הזו
   RunID=31015765923  09:33:47   gap=57s

--- חלון SHPH 11:36-11:48 (ENTERs ב-11:40:39 וב-11:43:55) ---
   RunID=31026123205  11:37:51   ← הריצה היחידה בחלון שהופיעה ב-skip_summary

--- התפלגות מרווחים בין ריצות, כל היום (n=136) ---
   min=13s  p25=57s  median=64s  p75=115s  max=1795s
   מרווחים מתחת ל-40 שניות: 6
```
**ב-DFNS מדובר בשתי ריצות עוקבות ותקינות במרווח 69 שניות — לא ריצות חופפות.**
ENTER #1 ב-09:32:29 (ריצה שהחלה 09:31:41), ENTER #2 ב-09:32:54 (ריצה שהחלה 09:32:50).
בין כתיבת השורה של #1 (09:32:31) לבין ההחלטה של #2 (09:32:54) חלפו **23 שניות**.

**בחלון SHPH רק ריצה אחת הופיעה ב-skip_summary** — בין 11:37:51 ל-11:48 אין רשומות
נוספות, למרות ששני ENTER-ים התרחשו שם. לא קבעתי למה.


---

## 3. נתיב האכיפה בקוד

**Filter 9 — `agent/trader/decision_logic.py:443-446`:**
```python
    # Filter 9: Re-entry limit per ticker (Bug #5 fix)
    if d.reentries_used_today is not None and d.reentries_used_today >= AGENT_MAX_REENTRIES_PER_TICKER:
        return (f"REENTRY_LIMIT: {d.ticker} already entered {d.reentries_used_today}x today "
                f"(max {AGENT_MAX_REENTRIES_PER_TICKER})")
```
**Filter 7 — `decision_logic.py:432-434`:**
```python
    # Filter 7: Existing position
    if d.existing_position:
        return f"EXISTING_POSITION: already short {d.ticker}"
```

### א. מאיפה מגיע המונה, ואיך הוא נספר

`d.reentries_used_today` נגזר מ-`account_state["entries_today_by_ticker"][ticker]`,
שנבנה ב-`agent/orchestrator.py:179-313` משני מקורות ואיחוד ביניהם:

| מקור | שורות | מה נספר |
|---|---|---|
| `paper_portfolio` | `orchestrator.py:248-252` | כל שורה עם `EntryDate == today`, **בכל סטטוס** → `entries_today_by_ticker_pf` |
| `decision_log` | `orchestrator.py:276-286` | כל שורה עם `Timestamp.startswith(today)` ו-`Action == "ENTER"` → `entries_today_by_ticker` |
| **איחוד** | `orchestrator.py:294-299` | `max(dl_count, pf_count)` לכל טיקר |

ההערה ב-`:199-203` מסבירה למה יש שני מקורות:
> *"Google Sheets eventual-consistency can hide recent writes from decision_log for
> minutes, causing Filter 9 to leak (PIII×14, HCWB×5). Union via max() ensures whichever
> sheet has the latest count wins."*

`existing_position` (Filter 7) נבנה מ-`state["existing_positions"]` — קבוצה שמתמלאת
מ-`paper_portfolio` בסטטוס OPEN/DRY_RUN_OPEN (`:241-243`) ומ-`decision_log` ENTERs של
היום שלא יצאו היום (`:287-288`).

### ב. ENTER-ים מ-decision_log או שורות מ-paper_portfolio?
**שניהם, ב-`max()`.** decision_log הוא ה-SSoT הראשי (`:280-281`), paper_portfolio הוא גיבוי.

### ג. האם הספירה מוגבלת ליום הנוכחי, ובאיזה טיימזון

```python
orchestrator.py:214    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
orchestrator.py:249    if entry_date == today and ticker:          # paper_portfolio.EntryDate
orchestrator.py:278    if ts.startswith(today) and ... == "ENTER"  # decision_log.Timestamp
```
**Peru (America/Lima), לא UTC ולא ET.** וזה **עקבי** עם הכתיבה:
`decision_log.Timestamp` נכתב כ-ISO עם offset `-05:00` (ראה השורות ב-§1), ו-
`paper_portfolio.EntryDate` נכתב כ-`YYYY-MM-DD` בשעון Peru.
**אין כאן חוסר-התאמה בטיימזון.**

### ד. מה קורה כשפוזיציה נסגרה — האם היא עדיין נספרת בתקרה

**כן, במונה של Filter 9.** `entries_today_by_ticker_pf` סופר `EntryDate == today`
**בכל סטטוס** (`:246-252`, ההערה אומרת מפורשות "any status"), כך ש-`DRY_RUN_CLOSED`
עדיין נספר. גם `decision_log` סופר ENTER-ים בלי קשר לסגירה.

**אבל ב-Filter 7 — לא.** `exited_today` (`:255-257`) מוציא טיקר שיצא היום מ-
`existing_positions` (`:287`). זה מכוון ומתועד (TASK-107): כניסה מחדש אחרי יציאה
באותו יום אינה נחשבת "פוזיציה קיימת", ומי שחוסם אותה הוא Filter 9 ולא Filter 7.

---

## 4. חמש ההשערות — כל אחת נבדקה

### H1 · הראשונה נסגרה לפני השנייה — התנהגות מתועדת (TASK-107)
**נפסלת ל-DFNS. לא ישימה ל-SHPH.**

| בעד | נגד |
|---|---|
| הקוד אכן מתיר זאת (`orchestrator.py:255-257,287`) | פוזיציה #1 של DFNS נסגרה ב-**10:45:06**, פוזיציה #2 נפתחה ב-**09:32:55** — 72 דקות של חפיפה מלאה |
| — | ל-SHPH יש רק שורת pp אחת, אז אין "ראשונה שנסגרה" בכלל |

**הכרעה: אלה אינן כניסות-אחרי-יציאה. זו הפרה אמיתית.**

### H2 · המונה נספר מ-paper_portfolio וסטטוס CLOSED מוציא את השורה
**נפסלת בקוד.**

`orchestrator.py:246-252` סופר `EntryDate == today` **בכל סטטוס** —
ההערה בקוד אומרת מילולית *"per-ticker entries today from paper_portfolio (any status)"*.
שורה סגורה ממשיכה להיספר. אין מסלול שבו CLOSED מאפס את מונה ה-re-entry.

### H3 · גבול היום מחושב בטיימזון שגוי
**נפסלת בקוד.**

`today` נגזר מ-`PERU_TZ` (`:214`), וההשוואות ב-`:249` וב-`:278` מול שדות שנכתבו באותו
שעון. שתי הכניסות של DFNS ושל SHPH נושאות `-05:00` ותאריך `2026-08-05` זהה בשתיהן.
אין שום מסלול שבו הן ייראו בימים שונים.

### H4 · קריאה נכשלה או הוחזרה מקאש בן 60 שניות
**נפסלת כהסבר עיקרי, אך תורמת ל-SHPH.**

| בעד | נגד |
|---|---|
| הקוד עצמו מתעד את התופעה (`:199-203`, "hide recent writes for minutes") | ב-5/8 **אין ולו אירוע `ACCOUNT_STATE_UNAVAILABLE` אחד** — הקריאות הצליחו |
| ENTER #1 של SHPH לא ייצר שורת pp, כך ש-pp באמת לא הכיל אותו | הקאש (`_SHEET_CACHE_TTL=60`) הוא **per-process**; כל ריצת GH Actions היא תהליך חדש, ואינו יכול לרשת קאש מריצה אחרת |
| — | H5 מסבירה את אותה תצפית בלי להזדקק להשהיית התפשטות |

### H5 · שתי ריצות agent_minute חופפות — ✅ **מאושרת, עם מדידה**

זו לא השערה — זו עובדה מדודה. `gh run list --workflow=agent_minute.yml`, 400 ריצות של 5/8:

```
duration s: min=34  p25=136  median=292  p75=321  max=370
runs longer than 60s: 366 of 400 (91.5%)
consecutive pairs where run N+1 STARTS before run N ENDS = 369 of 399  (92.5%)
```
**ה-cron הוא דקתי, אבל חציון משך הריצה הוא 292 שניות — כמעט 5 דקות.**
91.5% מהריצות ארוכות מ-60 שניות, ולכן **92.5% מהזוגות העוקבים חופפים.**
חפיפה היא הנורמה, לא החריג.

**הריצות שהיו פעילות ברגע כל אחת מארבע הכניסות:**
```
DFNS ENTER #1  09:32:29  ->  3 ריצות פעילות
   31015512481  start 09:30:08  end 09:33:27  (199s)
   31015595330  start 09:31:02  end 09:33:15  (133s)
   31015680057  start 09:32:03  end 09:34:14  (131s)

DFNS ENTER #2  09:32:54  ->  אותן 3 ריצות בדיוק

SHPH ENTER #1  11:40:39  ->  5 ריצות פעילות
   31026043714 11:36:02→11:41:29 · 31026123205 11:37:02→11:41:59
   31026199301 11:38:02→11:43:25 · 31026276890 11:39:02→11:44:28
   31026360914 11:40:07→11:45:12

SHPH ENTER #2  11:43:55  ->  5 ריצות פעילות
   31026276890 11:39:02→11:44:28 · 31026360914 11:40:07→11:45:12
   31026433095 11:41:02→11:46:28 · 31026510454 11:42:02→11:47:21
   31026589938 11:43:02→11:48:30
```

**ההוכחה ל-DFNS:** שלוש הריצות המועמדות ל-ENTER #2 החלו ב-**09:30:08 · 09:31:02 · 09:32:03**.
כל השלוש החלו **לפני** ENTER #1 שהתקבל ב-**09:32:29**.
`build_account_state` נקרא **פעם אחת בתחילת הריצה** (`orchestrator.py:608-670`, לפני לולאת
הסיגנלים ב-`:721`), והמצב שנוצר משמש את **כל** הסיגנלים באותה ריצה.
לכן — יהיה אשר יהיה מזהה הריצה שהחליטה על ENTER #2, **הצילום שלה נוצר לפני
שההחלטה הראשונה בכלל התקיימה.** לא השהיית התפשטות, לא קאש: פשוט **צילום שקדם לאירוע**.

זה מסביר בדיוק את הראיה מ-§1: `ColdStartConcurrentLeft` ו-`ColdStartDailyLeft`
**זהים** בשתי הכניסות — הם נלקחו מאותו צילום-מצב לוגי, שנוצר לפני שאף אחת מהן קרתה.

זהו TOCTOU קלאסי (time-of-check ↔ time-of-use) **בין תהליכים**, ולא בתוך תהליך:
לשום מסנן אין נעילה, ואין מנגנון שמונע משתי ריצות חופפות להחליט על אותו טיקר.

**עובדה נלווית שלא הוסברה:** מתוך 400 הריצות של 5/8, **396 הן `workflow_dispatch`
ורק 4 הן `schedule`**. לא בדקתי מה מפעיל אותן.

---

## מה השורש הסביר ביותר

**DFNS — מוכרע.** ריצות `agent_minute` חופפות. חציון משך הריצה 292 שניות מול cron של
60 שניות, 92.5% מהזוגות העוקבים חופפים. שלוש ריצות היו פעילות בו-זמנית, וכולן צילמו את
מצב החשבון לפני 09:32:29. Filter 7 ו-Filter 9 בדקו נתון שהיה נכון בזמן הצילום ולא בזמן
ההחלטה. **הגארד לא נשבר — הוא נשאל שאלה על עולם שכבר לא היה קיים.**
זהו שורש **שונה לחלוטין** מזה של 22/7 (שם `build_account_state` נכשל תחת 429 והחזיר
ברירות-מחדל); כאן הקריאות הצליחו, ובאותו יום הגארדים ירו 269 + 48 פעמים.

**SHPH — מוכרע חלקית.** אותה חפיפה קיימת (5 ריצות במקביל), אבל **נוסף עליה באג שני
ובלתי-תלוי: ה-ENTER הראשון (`DEC-2026-08-05-SHPH-114039-09`) לא ייצר שורת
`paper_portfolio` כלל.** לכן גם צילום טרי לא היה מוצא אותו במקור ה-pp.
זו המחלקה של TASK-105 / TASK-106 / TASK-198 (ENTER בלי שורה מתאימה).

## מה עדיין לא הוכרע

1. **איזו ריצה בדיוק החליטה על כל ENTER.** שלוש/חמש מועמדות לכל אחת; לא פתחתי את לוגי
   הריצות כדי לשייך. ל-DFNS זה לא משנה — כל המועמדות מקיימות את התנאי. ל-SHPH ENTER #2
   כן משנה: שתיים מחמש המועמדות החלו לפני 11:40:39 ושלוש אחריו.
2. **למה ENTER #1 של SHPH לא כתב שורת paper_portfolio.** `_record_entry_outcome`
   (`orchestrator.py:316-334`) אמור לסמן כשל-כתיבה כ-error; לא בדקתי אם הוא ירה.
3. **למה 396 מ-400 הריצות הן `workflow_dispatch` ולא `schedule`.** לא נבדק.
4. **למה בחלון SHPH (11:36-11:48) רק ריצה אחת הופיעה ב-`skip_summary`** בעוד חמש היו פעילות.
5. **האם החפיפה גם מסבירה את הכפילויות ב-TASK-253.** אותה תופעה בדיוק בסקאנר —
   לא בדקתי את `auto_scan.yml`, רק את `agent_minute.yml`.
6. **מה קרה ב-16 הזוגות הכפולים של יולי שאינם מ-22/7.** ההיקף נמדד (§5), הסיבה לא.

**לא הצעתי תיקון ולא שיניתי דבר, כפי שהתבקש.**
