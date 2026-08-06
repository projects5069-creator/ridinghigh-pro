# RidingHigh Pro — היכרות עם המערכת, חלק ג'

**מסמך תיאורי בלבד.** אין תוכנית, אין המלצות, אין דירוג, אין תיקונים.
נכתב 2026-08-05 09:51 Lima (10:51 EDT NY).
מטרה: לסגור את רשימת §11.1 של part2 — כל קובץ py חי בנתיב הפרודקשן שטרם נפתח.
מחוץ להיקף מוצהר: כלי-שורש חד-פעמיים (part2 §8.2), `scripts/`, `tests/` פרטני, רץ-הלילה שנוטרל, `backups/`.

**סקילים:** נטען `rhpro-live` (`~/.claude/skills/rhpro-live/SKILL.md`, 180 שורות).
`ls ~/.claude/skills/`: anthropic-skills · backtest-expert · biotech-screener · data-quality-checker · position-sizer · rhpro-live · rhpro-session · signal-postmortem · time-check · trader-memory-core.

---

## 1. נתיב ההחלטה שלא נקרא

### 1.1 — `agent/perception/data_quality.py` (132) — פילטר F6 החי

`validate(metrics)` (`:32`) מקבל 5 שדות: `atrx`, `change`, `rsi`, `price`, `volume`.
הספים ב-`QUALITY_RULES` (`:23-29`):

| # | בדיקה | סף | מה מפיל | שורה |
|---|---|---|---|---|
| 1 | `SUSPICIOUS_ATRX` | `atrx > 50.0` | ATRX מעל 50, **או ערך לא-מספרי** | `:58`, `:63-65` |
| 2 | `SUSPICIOUS_CHANGE` | `change > 200.0` | תנועה מעל 200%, או לא-מספרי | `:71`, `:76-78` |
| 3 | `INVALID_RSI` | `rsi < 0` או `rsi > 100` | RSI מחוץ לטווח, או לא-מספרי | `:85`, `:90-92` |
| 4 | `INVALID_PRICE` | `price < 0.01` | מחיר תת-סנט, לא-מספרי, **או `None`** | `:98`, `:103-108` |
| 5 | `INVALID_VOLUME` | `volume < 0` | נפח שלילי, `None`, או לא-מספרי | `:112-122` |

**חישוב הציון (`:125`):**
```python
quality_score = max(0.0, 1.0 - len(flags) * 0.25)
is_trustworthy = quality_score >= 0.5
```

**המשמעות המדויקת: שורה נופלת רק אם היא כשלה ב-3 בדיקות או יותר.**
- 0 דגלים → 1.00 → עובר
- 1 דגל → 0.75 → עובר
- 2 דגלים → 0.50 → **עובר** (התנאי הוא `>=`)
- 3 דגלים → 0.25 → נופל
- 4 דגלים → 0.00 → נופל

⚠️ שני דברים שראיתי בקוד:
1. הבדיקות **לא סימטריות** — 1, 2 בודקות רק את הצד העליון (`> max`), אין רצפה. ATRX שלילי או Change של −500% עוברים בשקט.
2. `atrx`, `change`, `rsi` נבדקים **רק אם אינם `None`** (`:56`, `:69`, `:82`). `None` בשלושתם = אפס דגלים. רק `price` ו-`volume` מדגילים על `None` (`:106-108`, `:112-114`).
3. הדוקסטרינג (`:5-7`) מדגיש: "Does NOT reject signals — only flags them... The decision_logic module decides whether to SKIP" — ההפרדה מכוונת.

### 1.2 — `agent/perception/tradability.py` (102) — מתי נקרא, מה חוסם

**נקרא פעם אחת בלבד** — `decision_logic.py:325`, **אחרי** ש-`_check_filters` החזיר `None` (כל הפילטרים עברו). כלומר הוא לא יכול לחסום כניסה; הוא רק ממלא 4 שדות ב-Decision.

```python
if broker is None or AGENT_DRY_RUN:      tradability.py:62
    return _mock_check(ticker)
```
הקריאה ב-`decision_logic.py:325` היא `check_tradability(d.ticker)` — **בלי `broker`**. גם אילו הועבר, `AGENT_DRY_RUN=True` היה מכריע.

**מה נכתב ל-decision_log בפועל, בכל ENTER, קבוע (`MOCK_DEFAULTS` `:28-33`):**
```
is_shortable   = True
borrow_fee_pct = 12.5      ← מספר קבוע מומצא
borrow_available = True
locate_status  = "MOCK"
```
⚠️ **עמודת `BorrowFee` ב-decision_log היא 12.5 קבוע, לא נתון.** זה נפרד לגמרי מ-`borrow_data` (שם `BorrowFeePct` הוא NULL מפורש כי ל-Alpaca אין שדה כזה — `borrow_collector.py:119`). שני מקומות, שני ערכים, שניהם לא-אמיתיים, ואף אחד מהם לא מזין את מודל-העלות של `calculate_net_pnl` (שמקבל `borrow_annual_rate` מ-`config.BORROW_SCENARIOS`).

מסלול ה-broker האמיתי (`_real_check_cached` `:74`) קיים עם קאש של שעה (`_CACHE_TTL_SECONDS = 3600` `:37`), ובו `borrow_fee_pct` הוא **0.0** עם הערה "Alpaca paper doesn't expose real fees" (`:89`). בכשל — נופל למוק (`:95-97`).

### 1.3 — `agent/trader/trader.py` (94) + `score_calculator.py` (45)

`Trader` הוא **עטיפה דקה וחסרת-מצב**. `evaluate()` (`:55`) עושה בדיוק שני דברים:
```python
decision = evaluate_signal(signal, account_state)   trader.py:71
decision.agent_mode = self.mode                     trader.py:72
```
`self.mode` נקבע פעם אחת ב-`__init__` (`:53`): `"LIVE_PAPER" if AGENT_LIVE_PAPER else "DRY_RUN"` → היום תמיד `"DRY_RUN"`.

הדוקסטרינג (`:9-16`) מסביר למה חסר-מצב: המצב עובר כ-`account_state` בכל קריאה, נשמר ב-Sheets ו-Alpaca ולא במחלקה — כדי שהבדיקות יהיו טריוויאליות, שהמקביליות תהיה בטוחה, ושהמעבר ל-M5 לא ידרוש refactor.

`evaluate_batch()` (`:75`) קיים אבל **האורקסטרטור לא משתמש בו** — `orchestrator.py:740` קורא `trader.evaluate()` בלולאה. הדוקסטרינג (`:83-85`) מסביר למה: ב-batch, `account_state` משותף לכל הסיגנלים ולא מצטבר, ולכן מונה ה-cold-start לא היה מתעדכן בין כניסות באותה ריצה.

`score_calculator.calculate_agent_score` (`:26`) הוא עטיפה של `formulas.calculate_score` עם ולידציית-מפתחות בלבד (`REQUIRED_METRICS`, `:24`), ומעלה `ValueError` על מפתח חסר (`:42`). הדוקסטרינג (`:4-6`): "The agent MUST produce identical scores to the scanner — any divergence is a critical bug caught by `test_scanner_agent_match.py`".

### 1.4 — `decision_logger.py` (358) + `decision_id_generator.py` (97)

**42 שדות ממופים 1:1** ב-`FIELD_MAPPING` (`:47-100`) — רשימת tuples מסודרת `(שדה ב-Decision, שם עמודה בגיליון)`. ההערה (`:45-46`) מדגישה שהסדר **חייב** להתאים לכותרות ב-`create_agent_sheets.py`.

**המרות ערך** (`_format_value` `:103`): `None → ""` · `bool → "True"/"False"` · השאר as-is.

⚠️ **ההבדל המהותי בין SKIP ל-ENTER — Route B (`:322-346`):**

| | SKIP | ENTER |
|---|---|---|
| נכתב ל-`decision_log`? | **❌ לא** | ✅ כן |
| מה כן קורה | שורת `stdout`: `[SKIP] {id} {ticker} Score={score} -> {reason}` (`:330-334`) — נשמרת רק בלוגי GitHub Actions | `safe_append_row` עם dedup על DecisionID (`:353`) + `invalidate_cache("decision_log")` (`:354`) |
| צבירה | `_accumulate_skip` (`:338`) + `_accumulate_shadow_gate` (`:343`) | — |
| ערך מוחזר | `decision.decision_id` — **הצלחה, לא שגיאה** (`:346`) | `decision_id` או `None` בכשל |

הנימוק בקוד (`:322-324`): "~80-100 SKIPs/minute were blowing Sheets API quota (429). Only ENTER decisions reach the sheet".

**המשמעות:** `decision_log` מכיל **רק ENTER-ים**. כל ניתוח שסופר SKIP-ים מהטאב הזה יראה אפס. זה גם למה TASK-126 ("חילוץ SKIPs היסטוריים מלוגי GitHub Actions לפני פקיעת retention") קיים.

**`flush_skip_summary()` (`:171`) — מה נכתב:**
שורה אחת לכל **סיבת-SKIP** (לא לכל SKIP), עם 7 עמודות (`:194-202`):
`run_start · run_id · reason_key · count · tickers · score_min · score_max`
- `reason_key` = החלק שלפני הנקודתיים (`:146`) — למשל `MXV_TOO_HIGH` ולא `MXV_TOO_HIGH: -45 > -100`
- `tickers` חתוך ל-25 ואז `+N more` (`SKIP_SUMMARY_TICKER_CAP = 25`, `:41`, `:189-193`)
- Score הוא absence-safe: מחרוזת ריקה → `None`, לעולם לא נצבר כ-0 (`:147-153`, TASK-127.1)
- כתיבה אחת בלבד לריצה, dedup על `run_id` (`:203-205`)

**`flush_shadow_gate_summary()` (`:264`) — מה נכתב:**
**שורה אחת לריצה** עם 8 עמודות (`_build_shadow_gate_row` `:253-262`):
`run_start · run_id · mode · score_skips · would_allow_count · would_allow_tickers · mxv_price_enter_count · mxv_price_enter_tickers`
- `score_skips` נספר רק על SKIP-ים שהסיבה שלהם מתחילה ב-`SCORE_TOO_LOW` (`:226-228`)
- `would_allow` = אותם SKIP-ים שהשער-המפורש היה מאשר (`:229-230`)
- `mxv_price_enter` נספר על **כל** החלטה, לא רק על SKIP-ים של Score (`:221-224`)
- לא נכתבת שורה כלל אם `mode == "off"` **וגם** אין ticker אחד ב-mxv_price (`:243-245`)

⚠️ **מאז ה-flip ב-6/29, `EXPLICIT_GATE_MODE="active"` ⇒ פילטר Score כבוי ⇒ אף SKIP לא מקבל את הסיבה `SCORE_TOO_LOW` ⇒ `score_skips` תמיד 0.** מה שנרשם ב-`shadow_gate_events` היום הוא **רק** החלק של `mxv_price_enter`.

**`decision_id_generator` (97):** פורמט `DEC-YYYY-MM-DD-TICKER-HHMMSS-ff` (`:88`). **אין מונה, אין קריאת Sheets ב-init** (`:64-67`, תיקון Bug #3 מ-16/05) — זה ביטל את מרוץ read-increment-write שייצר PositionID כפולים תחת ריצות מקבילות ו-429. הטיקר עובר סניטציה לאלפאנומרי בלבד, ברירת-מחדל `"X"` (`:87`).

⚠️ `decision_logger.log` כותב ל-**`sheet1`**, לא לטאב בשם `decision_log`: `gc.open_by_key(self.sheet_id).sheet1` (`:351`). זה מסלול נפרד מ-`sheets_manager.get_worksheet` (שיש לו נפילה-לאחור ל-sheet1 אבל מנסה קודם את הטאב בשם).

### 1.5 — מסלול DRY_RUN מלא: `order_manager.py` (314) + `alpaca_broker.py` (354)

```
order_manager.execute(decision)                              :109
 ├─ אם action != "ENTER" → מחזיר כמו שהוא                    :117
 ├─ _submit_with_retry()                                     :176
 │    └─ broker.submit_bracket_order(...)                    :181
 │         └─ if self.dry_run: _sim_bracket_order()          alpaca_broker.py:153-154
 │              └─ SimulatedOrder(id=f"SIM-{uuid4[:12]}", status="filled")   :326
 │         └─ אחרת, אם AGENT_LIVE_PAPER False → RuntimeError  alpaca_broker.py:156-160
 ├─ _wait_for_fill(order)                                    :209
 │    └─ isinstance SimulatedOrder → מחזיר מיד ("already filled")   :211-212
 ├─ decision.execution_price = filled_avg_price או decision.price   :144-147
 ├─ ⚠️ DRY_RUN override: מושך מחיר חי ומחשב TP/SL מחדש       :150-158
 ├─ _extract_leg_ids(order) → ("", "") ב-DRY_RUN (אין legs)  :232-242
 └─ _write_to_portfolio()                                    :248
      └─ Status = "DRY_RUN_OPEN"                             :251-252
      └─ build_portfolio_row(BY NAME, לא לפי מיקום)           :267-284  ← TASK-217
      └─ _default_sheet_write → safe_append_row + invalidate  :297-314
```

**מה נשלח בפועל ב-DRY_RUN: כלום.** `submit_bracket_order` מחזיר `SimulatedOrder` לפני שנוגעים ב-SDK של Alpaca. הקוד האמיתי (`:162-187`) בונה `LimitOrderRequest` עם `OrderSide.SELL`, `OrderClass.BRACKET`, TP כ-`TakeProfitRequest(limit_price)` ו-SL כ-`StopLossRequest(stop_price)` — ולא מגיע לשם.

**מה כן קורה ב-DRY_RUN שמשנה נתונים (`:150-158`):**
```python
if isinstance(final_order, SimulatedOrder) and self._data_provider:
    bar = self._data_provider.get_latest_bar(decision.ticker)
    if bar and bar.get("close"):
        live_price = float(bar["close"])
        decision.execution_price = live_price
        decision.tp_price = round(live_price * (1 - AGENT_TP_PCT/100), 4)
        decision.sl_price = round(live_price * (1 + AGENT_SL_PCT/100), 4)
```
כלומר **מחיר הכניסה ו-TP/SL מחושבים מחדש מהמחיר החי של Alpaca, לא מהמחיר של FINVIZ שהופיע ב-decision_log.** זה נועד לריאליזם, אבל המשמעות היא שהערכים שנכתבו קודם ל-`Decision` (`_calculate_position` ב-`decision_logic.py:143`) אינם אלה שנשמרים ב-`paper_portfolio`. אם קריאת המחיר החי נכשלת — נשארים הישנים (`:159-160`).

**25 עמודות `paper_portfolio`** (`:258-264`): PositionID, Ticker, EntryDate, EntryTime, EntryPrice, Quantity, PositionSizeUSD, Side, EntryOrderID, TPOrderID, SLOrderID, TPPrice, SLPrice, CurrentPrice, UnrealizedPnL, UnrealizedPnLPct, Status, ExitPrice, ExitDate, ExitTime, ExitReason, RealizedPnL, RealizedPnLPct, LastUpdated, DataQuality.
`Side` קבוע `"short"` (`:275`), `DataQuality` קבוע `"CLEAN"` (`:283`).

**שני שומרי-בטיחות ב-`AlpacaBroker.__init__`** (`_assert_paper_only` `:100`):
1. `base_url` חייב להכיל `"paper"` — אחרת `RuntimeError: SAFETY BLOCK` (`:102-105`)
2. אם יש `api_key` והוא לא מתחיל ב-`"PK"` — `RuntimeError` (`:106-110`)

`is_shortable` ו-`get_asset_info` מחזירים **מוק** ב-DRY_RUN (`:260-261`, `:268-275`): `shortable=True, easy_to_borrow=True, tradable=True`.

---

## 2. שבע בדיקות ה-Sentinel — `agent/sentinel/checks/` (615)

### 2.1 — הטבלה

| בדיקה | רמה | מה בודקת | מקור הנתון | סף | מחזירה |
|---|---|---|---|---|---|
| **completeness** (41) | סיגנל | 7 שדות חובה: `ticker, score, price, mxv, run_up, atrx, rsi` — `None`/`""`/`"nan"`/`"none"`/`"null"` נחשבים חסרים | ה-signal dict בזיכרון | ולו שדה אחד חסר | `BLOCK: MISSING_METRICS` (`:24-33`) |
| **scan_freshness** (83) | סיגנל | גיל הסריקה בדקות = `now_minute − scan_minute` | `signal["scan_time"]` (מ-`timeline_live`) | `>= 10` → BLOCK · `>= 5` → WARN (`config.py:395-396`) | `BLOCK: STALE_SCAN` / `WARN: AGING_SCAN` / `WARN: UNPARSEABLE_SCAN_TIME` |
| **price_sanity** (79) | סיגנל | (א) `0.01 <= price <= 10000` (ב) `low <= price <= high` | ה-signal dict | מחוץ לגבולות → BLOCK · `low > high` → BLOCK · מחיר מחוץ ל-OHLC → WARN | `BLOCK: PRICE_MISSING` / `PRICE_OUT_OF_BOUNDS` / `OHLC_INVERTED` · `WARN: PRICE_OUTSIDE_OHLC` |
| **price_freshness** (119) | סיגנל | פער בין מחיר FINVIZ למחיר החי של Alpaca | `data_provider.get_latest_bar()`, קאש 60ש' בזיכרון (`:26-27`) | `delta > 2%` (`SENTINEL_PRICE_DELTA_MAX_PCT`) | **`WARN` בלבד** — `STALE_FINVIZ_PRICE` (`:96`). לעולם לא BLOCK |
| **quota_health** (81) | מערכת | כתיבות/דקה בחלון מתגלגל של 60ש' | `deque` בזיכרון, מוזן ב-`record_write()` מ-`sheets_manager._track_write_quota` | `>= 60` → BLOCK · `>= 50` → WARN | `BLOCK: QUOTA_SATURATED` / `WARN: QUOTA_HIGH` |
| **provider_heartbeat** (81) | מערכת | קנרית: `get_latest_bar("AAPL")` | Alpaca/yfinance | 3 כשלים ב-5 דקות (`_MIN_FAILURES_FOR_HALT=3`, `_FAILURE_WINDOW_SEC=300`) | `BLOCK: PROVIDER_DOWN` / `WARN: HEARTBEAT_FAILED` |
| **position_sync** (131) | מערכת | ENTER-ים היום מול פוזיציות פתוחות | `account_state` (כבר בזיכרון) | ראה 2.2 | 5 תוצאות שונות |

### 2.2 — `position_sync` — עץ ההחלטה המלא

זו הבדיקה המורכבת ביותר, ויש בה 3 שכבות-חיסון שנוספו אחת אחרי השנייה:

```
1. paper_portfolio_fetch_failed?  → WARN: POSITION_SYNC_DEFERRED     :45-55
     (2026-05-20 — כשל fetch הוא 429, לא drift אמיתי)
2. today_enters == 0?             → ALLOW: NO_ENTERS_TODAY           :57-63
3. today_enters>0 ו-open_count==0:
   3a. pf_total>0 אבל pf_recognized==0 → WARN: POSITION_SYNC_DATA_QUALITY  :78-90
        (2026-06-03 — גיליון בלתי-קריא, בעיית סכמה, לא פוזיציות חסרות)
   3b. closed_today >= today_enters   → ALLOW: POSITION_SYNC_CLOSED_SAME_DAY :98-109
        (TASK-107 — פתיחה+סגירה באותו יום היא לגיטימית)
   3c. אחרת                            → BLOCK: POSITION_SYNC_FAILED  :110-118
4. today_enters>=3 ו-open_count < today_enters//3 → WARN: POSITION_SYNC_PARTIAL  :121-129
5. אחרת → ALLOW
```
ההערה ב-`:31-34` מתעדת תיקון: `open_count` חייב להיות `open_position_count` (שורות OPEN אמיתיות) ולא `len(existing_positions)` — הסט האחרון מכיל גם טיקרים של ENTER-ים היום, מה שהיה **מסתיר** כשל-סנכרון אמיתי.

### 2.3 — כמה קריאות Sheets כל בדיקה עושה

**התשובה המפתיעה: אפס. אף אחת מ-7 הבדיקות לא קוראת מ-Sheets.**

| בדיקה | Sheets | קריאות חיצוניות אחרות |
|---|---|---|
| completeness | 0 | 0 — עובדת על ה-dict בזיכרון |
| scan_freshness | 0 | 0 — פרסור מחרוזת + שעון |
| price_sanity | 0 | 0 |
| price_freshness | 0 | **1 קריאת Alpaca לטיקר**, מקוששת 60ש' (`:26-27`, `:34-37`) |
| quota_health | 0 | 0 — `deque` בזיכרון |
| provider_heartbeat | 0 | **1 קריאת Alpaca לריצה** (AAPL) |
| position_sync | 0 | 0 — קורא `account_state` שכבר נבנה |

**המקור האמיתי של עלות-ה-Sheets של ה-Sentinel הוא `_log_sentinel_event`** (`data_sentinel.py:30`), שנקרא על כל BLOCK/WARN — **לא** על ALLOW (`:83-85`, "to keep Sheets quota low"). כל קריאה עושה:
```python
ws = sm.get_worksheet("sentinel_events")   data_sentinel.py:60   ← open_by_key, בלי קאש
sm.safe_append_row(ws, row)                              :61     ← כתיבה
```
כלומר **2 פעולות API לכל אירוע**. ב-shadow mode ה-`action_taken` הוא `"SHADOW_LOGGED"` (`:203-204`) אבל האירוע **עדיין נכתב**. זה מתיישב עם TASK-218 הפתוח ("agent_minute 429: sentinel worksheet-handle cache, remaining 45/91") — 45 מתוך 91 בקשות-הקריאה שנותרו הן ה-`get_worksheet` החוזר הזה.

### 2.4 — שני ממצאים בקוד

⚠️ **`price_freshness.py:41` מייבא מודול שלא קיים:**
```python
from providers.data_provider_factory import get_data_provider
```
`ls providers/` מחזיר `__init__.py`, `alpaca_provider.py`, `yfinance_provider.py` בלבד. **אין `data_provider_factory`.** זה מסלול-הגיבוי שרץ רק כאשר `market_state["data_provider"]` הוא `None`; במסלול החי האורקסטרטור כן מעביר אותו (`orchestrator.py:727`), אז המסלול השבור כמעט לא נורה — וכשהוא כן נורה, ה-`except` (`:42-45`) בולע והבדיקה מחזירה `WARN: LIVE_PRICE_UNAVAILABLE`. להשוואה, `provider_heartbeat.py:35` מייבא נכון: `from data_provider import get_data_provider`.

⚠️ **`price_freshness` היא היחידה שלעולם לא חוסמת.** למרות שהדוקסטרינג שלה (`:6-7`) מכנה אותה "the most critical check — caught the ELPW bug where scanner said $8.07 but market was actually $7.24 (10% stale → instant false TP)", ההחזרה בפועל היא `WARN` (`:96`), לא `BLOCK`.

---

## 3. נתיבי כתיבה חיים

### 3.1 — `gsheets_sync.py` (404) — שלוש פונקציות ה-save

**המנוע המשותף: `_df_to_sheet(ws, df)` (`:110`).** הדוקסטרינג מדגיש: "Safe pattern: write data first, then trim excess rows — **never clears before writing**" (`:112-113`). הרצף:
1. `inf/-inf → ''`, `NaN → ''` (`:119`) — JSON RFC לא תומך בהם ו-`ws.update()` היה נכשל
2. `ensure_grid_width(ws, n_cols)` (`:122`) — הגדלת הרשת לפני כתיבה רחבה יותר (TASK-177/123: `ws.update` מעבר ל-`col_count` מחזיר 400)
3. `ws.update("A1", data)` (`:124`) — **דריסה מ-A1**
4. `ws.delete_rows(new_last+1, total_rows)` (`:127-130`) — קיצוץ שורות ישנות, בתוך `try/except` כי "trim failure is non-critical"

| פונקציה | מה דורסת |
|---|---|
| `save_snapshot_to_sheets(df)` (`:137`) | `daily_snapshots`. שלושה מסלולים (`:148-158`): גיליון ריק → כתיבה מלאה · התאריך של היום כבר קיים → **מסנן את היום החוצה, מאחד, ודורס הכל** · התאריך חדש → `append_rows` בלבד |
| `save_portfolio_to_sheets(df)` (`:234`) | `portfolio` — **דריסה מלאה ללא תנאי** (`:240`). אין מיזוג, אין dedup |
| `save_timeline_to_sheets(df, date)` (`:170`) | **no-op.** "Deprecated: timeline_archive removed" — מדפיס הודעה ומחזיר `True` (`:171-173`) |

⚠️ ה-dashboard עדיין מייבא את `save_timeline_to_sheets` (`dashboard.py:46`) וקורא לו (`:785`) — קריאה למת שמחזירה הצלחה.

`_get_ws` (`:47`) מעביר `month` הלאה ל-`sheets_manager.get_worksheet`, אבל `_get_post_analysis_ws(gc=None)` (`:52`) **לא מקבל `month`** — זה AC#2 של TASK-202.

### 3.2 — `cross_month_loaders.py` (395) — ואיפה TASK-202 נוגע

**הבעיה שהוא פותר** (דוקסטרינג `:6-11`): `get_worksheet(month=None)` נופל לחודש הנוכחי, ולכן עמודי ה-dashboard רואים רק את החודש הזה — חודשים היסטוריים הרשומים ב-`sheets_config.json` בלתי-נראים.

**הפתרון:** קורא מ**כל** חודש ב-`sheets_config.json` ומשרשר, עם dedup last-write-wins על `(Ticker, ScanDate)` לגיליונות מסחר ועל `(Date)` ל-`daily_summary` (`:15-17`).

**חמישה כללי-עיצוב מוצהרים** (`:20-29`):
1. **תוספתי בלבד** — הפונקציות המקוריות של `gsheets_sync` לא שונו
2. `try/except` **לכל חודש** — גיליון אחד שבור לא מרעיל את התוצאה (`_read_one_month` `:97`, `:114`)
3. **last-write-wins** — כשמפתח קיים בכמה חודשים, השורה מהחודש המאוחר מנצחת. חשוב כי `monthly_rotation._copy_open_portfolio` מעתיק פוזיציות פתוחות מעבר לגבול-החודש
4. המרה נומרית **פעם אחת** על הפריים המאוחד (`_coerce_numeric` `:118`)
5. חודשים ריקים מדולגים בשקט

**5 פונקציות ציבוריות** (`:32-36`): `load_post_analysis_all_months`, `load_portfolio_all_months`, `load_score_tracker_all_months`, `load_daily_summary_all_months`, `get_active_months`.
כל שורה מתויגת `_source_month` לצורך סינון/דיבוג (`:110-111`).

**איפה TASK-202 נוגע — מגוף התיק:**
> `post_analysis_collector.run()` פותר כל פעולת-גיליון לחודש **הנוכחי**, ולכן backfill היסטורי חוצה-חודש עם `--date` **קורא וכותב לטאב החודשי הלא-נכון**. התגלה במהלך ה-backfill של יוני ב-TASK-200; יוני עבד רק כי החודש הנוכחי היה יוני (כל 5 הנקודות הסכימו במקרה. תיקון קריאה-בלבד מסוכן: הוא היה בונה שורות של חודש-עבר ושומר אותן בטאב של החודש הנוכחי = דאטה במקום הלא-נכון.

חמש הנקודות השבורות לפי ה-AC: `collector:396` (`daily_snapshots`), `:411` (`timeline_live` fallback), `:454` (`timeline_live` stats), `:461` (`load_post_analysis_from_sheets`), `:617` (`save_post_analysis_to_sheets`). כולן מנותבות דרך `_get_post_analysis_ws` (`gsheets_sync.py:52`) שקורא ל-`get_worksheet` בלי חודש. **backfill של מאי/אפריל החזיר 0 מועמדים כי קרא את הטאב של יוני.** מצוין בתיק כ-"documented debt; not started".

⚠️ `cross_month_loaders` **פותר את זה לקריאה ב-dashboard בלבד.** הקולקטור לא משתמש בו.

### 3.3 — `enrich_post_analysis.py` (223)

**מה מעשיר** (דוקסטרינג `:2-6`), משני מקורות:
- **מ-`timeline_live`:** `IntraHigh`, `IntraLow`, `PeakScoreTime`, `PeakScorePrice`, `PeakScore`, `DayRunUp%`
- **מ-Yahoo Finance** (דרך `data_provider`, `:19`): `D0_Close`, `D0_Volume`, `D0_Drop%`, `IntraDay_TP10`

**`_min_to_close(peak_time, scan_date)` (`:22`)** — דקות בין רגע-שיא-ה-Score לנעילת השוק. DST-מודע (TASK-231): גוזר את הנעילה מ-16:00 ET בתאריך הסריקה, כי קיבוע ל-15:00 Peru החזיק רק בקיץ ובחורף (EST) הנעילה היא 16:00 Peru — ה-15:00 הקבוע **גרע 60 דקות** מכל חישוב חורפי. מראה של `utils.is_day_complete` ו-`auto_scanner.is_snapshot_time`.

**מה קורה בכשל:** `except Exception: return ""` (`:40-42`) ב-`_min_to_close`, ו-`except Exception as e` ב-`fetch_d0_data` (`:67`). **הכשלים בולעים בשקט ומחזירים ערך ריק** — אין ספירת-שגיאות, אין העלאת חריגה. שורה שהעשרתה נכשלה נראית בדיוק כמו שורה שאין לה נתון.

⚠️ הקובץ מייבא `load_post_analysis_from_sheets` ו-`save_post_analysis_to_sheets` מ-`gsheets_sync` (`:16`) — שתי הפונקציות שאין להן פרמטר `month`. כלומר ההעשרה כפופה לאותו כשל חוצה-חודש של TASK-202.

### 3.4 — `backfill_ohlc_v2.py` (235) — מה `--recent 2 --apply` עושה

הקובץ קיים במקביל ל-`backfill_ohlc.py` v1 **בכוונה**, לפי Iron Rule §12 (`:5-6`). חמישה הבדלים מוצהרים (`:8-17`):

1. **טריגר רחב יותר** — כל תא OHLC ריב ב-`D1..D5` שיומו כבר הסתיים, לא רק `D1_Open`
2. **טווח** — איטרציה מפורשת על חודשים (ברירת-מחדל: כל מה שב-`sheets_config`)
3. **בטיחות: מילוי-בלבד** — ערך קיים **לעולם לא נדרס**; הכתיבה היא `ws.batch_update` של התאים שמולאו בלבד. **אין כתיבה-מחדש של הגיליון ולכן אין סיכון-מרוץ עם הקולקטור**
4. **סטטיסטיקות** — `calculate_stats` מחושב מחדש רק לשורות שקיבלו לפחות תא אחד, מהתמונה **המאוחדת** (קיים+חדש)
5. **ברירת-המחדל היא dry-run** — שום דבר לא נכתב בלי `--apply`

**`--recent 2`** → `recent_months(2)` (`:49`) — שני החודשים האחרונים מ-`sheets_config`.
**`--apply`** → הופך את `apply=True` ומאפשר את ה-`batch_update` (`:225-226`).

הפוקציה מייבאת מחדש את ה-fetcher של v1: `from backfill_ohlc import fetch_ohlc` (`:38`) — "4 attempts, 15-day window".
נתיבים repo-יחסיים (`:27-30`) — הליטרלים `~/RidingHighPro` הישנים קרסו על runners של GitHub Actions שבהם הריפו יושב תחת `/home/runner/work/...` (TASK-124).

---

## 4. EOD

### 4.1 — `reconciler.py` (371)

**שתי פונקציות-השוואה נפרדות:**

**א. `reconcile()` (`:226`) — גיליון מול Alpaca.**
```
sheet_positions = paper_portfolio, Status ב-(OPEN, DRY_RUN_OPEN)     :239 → :282
alpaca_positions = broker.list_positions()                            :240 → :300
for pos in sheet_positions:
    if Status == DRY_RUN_OPEN:  skipped_dry_run += 1;  continue       :262-264   ← ⚠️
    if ticker in alpaca: ok += 1
    else: phantom_open += 1 → _handle_phantom_open()                  :271-272
for ticker in alpaca אבל לא בגיליון: orphan_position → _handle_orphan  :275-278
```

⚠️ **הזרוע הזו אינרטית לחלוטין היום.** שורה `:262-264` מדלגת על כל `DRY_RUN_OPEN` — וכל הפוזיציות הן `DRY_RUN_OPEN`. התוצאה בפועל היא `{"ok":0, "phantom_open":0, "orphan_position":0, "skipped_dry_run": N}`. ההצהרה בדוקסטרינג הראשי (`:16`) מפורשת: "DRY_RUN positions are skipped (no Alpaca counterpart)".

`_handle_phantom_open` (`:320`) — גיליון אומר OPEN, ל-Alpaca אין פוזיציה. **מתקן את הגיליון**: `Status=CLOSED`, `ExitReason="RECONCILER_PHANTOM"`, חותמות זמן (`:340-346`) + התראה.
`_handle_orphan` (`:352`) — ל-Alpaca יש פוזיציה שאינה בגיליון. **התראה בלבד, ללא תיקון-אוטומטי** — `action_taken: "alert_only"` (`:361`).

**ב. `reconcile_decision_log_vs_portfolio()` (`:84`) — decision_log מול paper_portfolio.**
זו הזרוע ש**כן** עובדת ב-DRY_RUN (הדוקסטרינג מציין זאת מפורשות, `:92`).
```
לכל שורה ב-decision_log שהתאריך שלה הוא היום ו-Action == "ENTER":     :110-113
    אם DecisionID לא נמצא בין ה-PositionID של paper_portfolio:        :116
        missing_portfolio_row += 1                                    :118
        event = {type: MISSING_PORTFOLIO_ROW, action_taken: "flag"}   :119-130
        אם auto_repair: בונה שורה מחדש ומצרף                          :133-136
        alert_writer(event)                                           :137-138
```
ההתאמה נעשית **על כל הסטטוסים** כדי שסגירה באותו יום לא תהיה false positive (`:89-90`). האידמפוטנטיות **מבנית**: שורה שכבר קיימת לעולם לא מסומנת ולכן לעולם לא מצורפת שוב — ה-dedup העיוור של ה-append הראשון **לא נסמכים עליו** (`:94-96`).

**מה בדיוק כבוי ע"י `RECONCILE_AUTO_REPAIR=False`:**
בלעדיו הפרמטר `auto_repair` (`orchestrator_eod.py:160`) הוא `False`, ולכן שורות `:133-136` לא רצות — כלומר `_build_portfolio_row_from_decision` (`:169`) ו-`_append_portfolio_row` (`:209`) **לא נקראות אף פעם**. ה-`action_taken` נשאר `"flag"` ולעולם לא `"repaired"`. הזיהוי, הספירה, וההתראה ל-`system_events` **כן** עובדים.

`_system_events_alert` (`orchestrator_eod.py:129`) כותב 7 עמודות ל-`system_events` עם `EventType = "RECONCILE_" + type` ו-`Severity = "WARNING"`, עטוף ב-`try/except` — "best-effort; never breaks the EOD run" (`:128`).

### 4.2 — `postmortem_engine.py` (407) — מתי נקרא `decision_reader`

**הטריגר: פר-פוזיציה, מיד אחרי סגירה.** הדוקסטרינג (`:6-7`): "position_manager calls generate() right after closing. Writes one row to postmortems Sheet (17 columns)".

השרשרת: `position_manager._close_position` (`:307`) → `postmortem_engine.generate()`.
ה-`decision_reader` הוא ה-callback `_read_decision` שמוזרק ב-`orchestrator.py:629-644`, והוא זה שקורא `ws.get_all_records()` **בלי קאש** (`:635`).

**התדירות בפועל: פעם אחת לכל סגירת-פוזיציה.**
היום, עם `AGENT_FORCE_EOD_CLOSE=False`, סגירות מתרחשות רק כשמחיר חוצה TP או SL (`position_manager.py:244-251`). כלומר ה-`get_all_records` הלא-מקושר נורה **רק בדקות שבהן פוזיציה נסגרה**, לא בכל דקה. זו תשובה לחשש שהעליתי ב-part2 §E7: **זה לא מקור-429 של כל-דקה**, אבל בימים עם סגירות מרובות זה כן N קריאות מלאות של הטאב.

`AGENT_SCORE_VERSION = "v2.6"` (`config.py:345`) מתייג כל postmortem — הדוקסטרינג (`:17-19`) מסביר: "ScoreAtEntry preserves the score AT THAT TIME. If M7 changes the formula, old postmortems retain historical accuracy."

### 4.3 — `borrow_collector.py` (191)

**ארבע פונקציות טהורות + שתי פונקציות I/O.**

**`get_scanned_universe(snapshots_df, mxv_max=-100)` (`:33`)** — סט הטיקרים ב-`daily_snapshots` עם `MxV <= -100`.
ההערה (`:35-37`) היא ההסבר לשינוי TASK-208-B: "בעידן חסר-ה-Score (`SCORE_WRITE_FROZEN`) `daily_snapshots.Score` הוא `""` → `NaN` → **לא בוחר כלום**; MxV נשמר והוא נהג-הכניסה החי". טהורה, ללא I/O.

**`compute_coverage(universe, borrow_rows)` (`:54`)** — טהורה. **שני האחוזים מחושבים על מכנה זהה: גודל היקום** (`:75-76`), לא על מספר השורות שנמצאו. `pct=0.0` ביקום ריק.

**`build_borrow_row` (`:104`)** — 9 עמודות. שתי נקודות:
- `BorrowFeePct = ""` — **NULL מפורש**, "Alpaca exposes no fee" (`:107`, `:119`)
- `IsHTB = shortable AND NOT etb` (`:118`) — נגזר, לא נתון
- `SharesAvailable = asset_info.get("shares_available", "")` — ריק אלא אם נחשף (`:120`)

**`collect_borrow_data(tickers, broker)` (`:153`)** — dedup מוקדם על `(Ticker, CheckDate)` מהגיליון (`:171`, `:175-176`), כשל של טיקר בודד מדלג עליו בלבד (`:179-181`), **כתיבה מרוכזת אחת** (`:185-187`). לעולם לא מעלה חריגה (`:189-191`).

**`collect_borrow_coverage(universe)` (`:125`)** — קורא את שורות ה-`borrow_data` של היום, מחשב כיסוי, ומצרף שורה אחת ל-`borrow_coverage` עם dedup על `CheckDate` (שורה אחת ליום, `:146`).

⚠️ **הפרדוקס של ה-broker.** `orchestrator_eod.py:79` יוצר `AlpacaBroker(dry_run=False)` במפורש — "real read-only asset info, even under DRY_RUN". זה מעקף מכוון: אילו היה נוצר עם ברירת-המחדל, `get_asset_info` היה מחזיר את המוק (`alpaca_broker.py:268-275`) והטאב היה מתמלא ב-`shortable=True` קבוע לכל טיקר.

### 4.4 — `orchestrator_eod.py` (228) — הרצף המלא

```
run()                                              :105
 1.  AlpacaBroker() + Reconciler(alert_writer)      :123-150
     reconciler.reconcile()                         :151    ← אינרטי (כל הפוזיציות DRY_RUN)
     reconcile_decision_log_vs_portfolio(auto_repair=RECONCILE_AUTO_REPAIR=False)  :159-160
 1b. collect_borrow_snapshot(summary)               :168
     ├─ build_account_state() → existing_positions  :44
     ├─ get_worksheet("daily_snapshots").get_all_values()   :57-59   ← לא מקושר
     ├─ get_scanned_universe(df)  → MxV <= -100     :65
     ├─ universe = scanned | existing               :70   (יוצא אם ריק, :71-73)
     ├─ AlpacaBroker(dry_run=False)                 :79
     ├─ collect_borrow_data(tickers, broker)        :86
     └─ collect_borrow_coverage(universe)           :96
 2.  ScoreAnalytics().run_daily()                   :173-174   ← ⚠️ ההזרקה החסרה
 3.  אם שבת (weekday()==5): ScoreAnalytics().run_weekly()  :188-192   ← ⚠️ אותו דבר
 4.  אם summary["errors"]>0 → send_alert            :208-221
```

⚠️ **ההזרקה החסרה, מאומתת:**
```python
analytics = ScoreAnalytics()          orchestrator_eod.py:173   ← אפס ארגומנטים
```
```python
def __init__(self, postmortem_reader=None, ...):  score_analytics.py:61-63
    self._postmortem_reader = postmortem_reader   score_analytics.py:73
```
```python
def _load_postmortems(self, start_date, end_date):  score_analytics.py:129
    if not self._postmortem_reader:
        return pd.DataFrame()                        score_analytics.py:131-132
```
`run_daily` קורא ל-`_load_postmortems` (`:91`) ומקבל DataFrame ריק ⇒ `n = len(postmortems) = 0` (`:178`) ⇒ tier `INSUFFICIENT` ⇒ אין כתיבה. **זה מבני, לא תלוי-דאטה.** אותו דבר בדיוק ב-`run_weekly` (`:116`, orchestrator `:191`).

⚠️ **דוקסטרינג מיושן:** `collect_borrow_snapshot` (`:35`) עדיין אומר "the scanned universe (daily_snapshots, **Score >= MIN_SCORE_DISPLAY** today)" בעוד הקוד בשורה `:65` משתמש ב-MxV. יש הערה inline נכונה באותה שורה ("TASK-208-B: MxV<=-100 scoreless-era") — הדוקסטרינג עצמו לא עודכן.

⚠️ שלושה בלוקי `try/except` נפרדים ב-`collect_borrow_snapshot`, וכולם **לא מגדילים את `summary["errors"]`** (`:39-40`, `:45-47`, `:66-68`, `:80-82`, `:89-91`, `:101-102`). כשל מלא של איסוף-ההשאלה לא ייצור מייל-שגיאה ולא ייראה בשום מקום מלבד לוג ה-Actions.

---

## 5. מיילים — `agent/notifications/` (982) + האורקסטרטורים

### 5.1 — התשתית

`email_sender.py` (117) — עטיפת SMTP ל-Gmail. קורא 5 משתני-סביבה: `SMTP_HOST` (ברירת-מחדל `smtp.gmail.com`), `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO` (`:36-40`). שתי פונקציות ציבוריות: `send_email(subject, html)` (`:96`) ו-`send_alert(error_summary, details)` (`:102`).

⚠️ **שתי מערכות-מייל נפרדות עם משתני-סביבה שונים.** `health_audit.send_email_alert` (`health_audit.py:1874-1876`) קורא `GMAIL_USER` / `GMAIL_APP_PASS` / `REPORT_TO`. `agent/notifications/email_sender` קורא `SMTP_USER` / `SMTP_PASSWORD` / `EMAIL_TO`. אלה שני סטים שונים של secrets לאותו תפקיד.

### 5.2 — חמש התבניות: מקור, מספרים, נוסחה

| מייל | שעה | orchestrator | תבנית | קורא מ- |
|---|---|---|---|---|
| **Morning Brief** | 08:30 | `orchestrator_email_morning.py:85-87` | `morning_brief.render_morning_email` (58) | `paper_portfolio` (`:43`) · `postmortems` (`:55`) · `AlpacaBroker.get_account()` (`:69`) |
| **Daily Brief** | 16:30 | `orchestrator_email_daily.py:179-181` | `daily_brief.render_daily_email` (214) | `decision_log` (`:61`) · `paper_portfolio` (`:81`) · `sentinel_events` **או** `system_events` (`:159`) |
| **Critic Daily** | 17:00 | `orchestrator_critic.py:89-99` | `critic_brief.render_critic_email` (264) | `daily_facts()` → 4 טאבים · `unified_positions()` · `get_today_postmortems()` |
| **Critic Weekly** | שישי 18:00 | `orchestrator_critic_weekly.py:32,62` | `weekly_brief.render_weekly_email` (105) | `build_weekly_row` → `review_completed_trades` → `paper_portfolio` + `decision_log` |
| **Critic Monthly** | 1 לחודש 01:00 | `orchestrator_critic_monthly.py:31,72` | `monthly_brief.render_monthly_email` (224) | `build_monthly_row` + `build_monthly_detail` |

**מה כל מייל מציג:**
- **Morning:** מצב (`DRY_RUN`/`LIVE_PAPER`, `:36-37`), מספר פוזיציות פתוחות, ספירת postmortems ב-7 הימים האחרונים (`:60-63`), כוח-קנייה, `account_status`.
- **Daily:** PnL ממומש היום, `tp_hits` / `sl_hits` / `eod_closes`, WinRate, 10 ההחלטות המובילות לפי Score, טבלת עסקאות שנסגרו היום, טבלת פוזיציות פתוחות (`_build_closed_trades_section` `:24`, `_build_open_positions_section` `:63`).
- **Weekly:** שורה אחת של `weekly_summary` — 16 שדות (`build_weekly_row` `:268-272`): `WeekOf, Trades, Wins, Losses, WinRate, TotalPnL, AvgWin, AvgLoss, Enters, Skips, TickersChecked, Anomalies, Conflicts, Conclusion, SampleSizeFlag, GeneratedAt`. `SampleSizeFlag = "INSUFFICIENT"` אם `n < 10` (`:262`).
- **Monthly:** שורת-חודש + `build_monthly_detail` — שורת-שורה תחתונה, מספרי-מפתח + בר-WinRate, טבלת top-movers, **טבלת איכות פר-מדד** (מכונה "הלב" בדוקסטרינג `:5`), ומה-לבדוק.
- **Critic Daily:** `daily_facts` לכל 4 הסוכנים + חריגות + `unified_positions` + postmortems של היום.

### 5.3 — ⚠️ איזה WR מוצג בכל מייל — שלוש הגדרות שונות

זו כפילות #8 מ-part2, ובקריאה מלאה היא **גדולה יותר ממה שכתבתי: לא שתי הגדרות אלא שלוש.**

| מקור | הנוסחה | המונה | קובץ:שורה |
|---|---|---|---|
| **Daily Brief (16:30)** | `fmt_rate_ci(win_count, closed_total)` | `win_count = stats["tp_hits"]` — נספר לפי **התאמת-מחרוזת ב-`ExitReason`**: `"TP" in exit_reason` (`orchestrator_email_daily.py:122-123`). המכנה = `tp_hits + sl_hits + eod_closes` | `daily_brief.py:122-127` |
| **Weekly / Monthly Critic** | `fmt_rate_ci(wins, trades)` | `wins` = עסקאות עם `verdict == "WIN"`, וה-verdict נקבע לפי **סימן ה-PnL**: `pnl > 0 → WIN` (`critic_v1.py:145-151`) | `weekly_brief.py:82`, `critic_v1.py:257` |
| **Dashboard / post_analysis** | `utils.classify_trade` | **הליכה יומית D1→D5 מול TP/SL** עם 5 תוצאות אפשריות כולל WHIPSAW ו-NO_TOUCH | `utils.py:513-597` |

שלושתן יכולות לתת מספרים שונים על אותן עסקאות:
- שורה שנסגרה ב-EOD עם רווח: **Daily Brief** סופרת אותה במכנה ולא במונה (`eod_closes`), **Critic** סופר אותה כ-WIN.
- עסקה שנגעה גם ב-TP וגם ב-SL באותו יום: **classify_trade** מחזירה `WHIPSAW` (לא WIN ולא LOSS), ל-**Critic** אין קטגוריה כזו בכלל — היא תיפול ל-WIN או LOSS לפי הסימן.
- `verdict == "FLAT"` (PnL בדיוק 0) קיים אצל ה-Critic (`:151`) ונספר במכנה — אין לו מקבילה בשתי האחרות.

**מה שכן משותף:** שלוש-מתוך-שלוש מציגות דרך `formulas.fmt_rate_ci`, כלומר Wilson CI. אבל ה-CI מחושב מעל שלושה מונים שונים. `critic_v1.py` עצמו **לא מייבא מ-`formulas`** (אימות: `grep "from formulas\|import formulas" agent/critic/critic_v1.py` → אפס) — ה-CI מתווסף רק בשכבת-התבנית.

---

## 6. dashboard של הסוכן — `agent/dashboard/` (1,632)

### 6.1 — `_data_loaders.py` (247) — שכבת-הגישה המשותפת

`_get_worksheet(name)` (`:36`) עוטף את `sheets_manager.get_worksheet` (`:40`).

| פונקציה | טאב | קריאה/כתיבה |
|---|---|---|
| `load_paper_portfolio()` (`:47`) | `paper_portfolio` | קריאה |
| `load_decision_log_today()` (`:64`) | `decision_log` | קריאה — `get_all_records()` (`:70`) |
| `_cached_market_context()` (`:84`) | `market_context` | קריאה — `get_all_values()` (`:90`) |
| `render_regime_banner()` (`:99`) | ↑ | תצוגה |
| `load_score_analytics_latest()` (`:142`) | `score_analytics` | קריאה (`:148`) |
| `load_pending_suggestions()` (`:161`) | `pending_suggestions` | קריאה (`:167`) |
| **`update_suggestion_status()`** (`:179`) | `pending_suggestions` | **כתיבה** (`:194`) |
| **`log_emergency_stop()`** (`:222`) | `system_events` | **כתיבה** (`:228`) |

### 6.2 — ארבעת העמודים

| עמוד | קורא | כותב | חישוב inline |
|---|---|---|---|
| **Live Agent** (390) | `load_paper_portfolio` (`:61`), `load_decision_log_today` (`:62`) | **`log_emergency_stop`** (`:379`) — מאחורי כפתור `🚨 EMERGENCY STOP` (`:368`) | `win_rate = wins/closed_count*100` (`:268`) · `(entry−curr)/entry*100` (`:322`) |
| **Trade History** (625) | `_load_decision_log_all` (`:40-44`) — `get_all_records()` ישיר, **לא** דרך `_data_loaders` · `_fetch_live_prices` (`:55`) | — | `win_rate` **פעמיים**: `:237` (KPI) ו-`:484` (פר-טיקר) · `(entry−curr)/entry*100` (`:297`) |
| **Score Brain** (238) | `load_score_analytics_latest` (`:46`), `load_pending_suggestions` (`:204`) | **`update_suggestion_status`** (`:227` APPROVED / `:234` REJECTED) | — |
| **Sentinel Events** (132) | `_load_sentinel_events` → `sentinel_events` (`:32`) | — | — |

⚠️ **Score Brain מציג טאב שתמיד ריק.** `load_score_analytics_latest` קורא מ-`score_analytics`, ולפי §4.4 אותו טאב לא נכתב מעולם כי ה-reader לא מוזרק. העמוד קיים, מרנדר KPI-ים, גרף-tiers (`:102`), גרף-קורלציות (`:138`) והמלצה (`:177`) — כולם מעל מקור ריק.

⚠️ **`pending_suggestions` נכתב רק מה-dashboard.** `update_suggestion_status` (`_data_loaders.py:179`) מעדכן סטטוס של הצעה קיימת — אבל ההצעות עצמן היו אמורות להיכתב ע"י `score_analytics.run_weekly()`, שגם הוא מחזיר n=0. TASK-254 מציין זאת: "pending_suggestions and config_history are also empty in both months and genuinely have no writer anywhere in the code".

⚠️ **`win_rate` מחושב inline ב-3 מקומות נוספים** ב-`agent/dashboard/` (`live_agent_page.py:268`, `trade_history_page.py:237`, `:484`) — כולם `wins/closed*100` בלי `fmt_rate_ci`, למרות ש-`formulas.fmt_rate_ci` קיים. זו הגדרה **רביעית** של WR במערכת (הפעם לפי `RealizedPnL` בגיליון, כמו ה-Critic, אבל בלי CI).

---

## 7. תשתית

### 7.1 — `market_context_v1.py` (202) + `run_market_context.py` (39)

**מה נמדד** (`:11-13`):
- `spy_direction`, `iwm_direction` — `"UP"` / `"FLAT"` / `"DOWN"`
- `vix_level` — `"LOW"` (<20) · `"MEDIUM"` (20-30) · `"HIGH"` (>30) (`_vix_level` `:89`)
- `market_regime` — נגזר משלושתם (`_derive_regime` `:98`)

**סף הכיוון: 0.2%** (`_DIRECTION_THRESHOLD_PCT`, `:77`).
```
pct = (close − open)/open × 100
"UP"   אם pct > 0.2
"DOWN" אם pct < −0.2
"FLAT" אחרת
```
הנימוק מתועד (`:18-21`): נבחר מניתוח 5-שנתי של תנועות יומיות ב-SPY ו-IWM — ב-0.2%, כ-25% מימי ה-SPY וכ-16% מימי ה-IWM מתויגים FLAT, "מספיק כדי לסנן רעש תוך-יומי בלי לבלוע ימי-מגמה אמיתיים". ההתפלגות יציבה בחלונות של שנתיים וחמש שנים.

**מקורות ו-fallback:**
- SPY, IWM: `_fetch_bar_alpaca` (`:42`), ובכשל `_fetch_bar_yfinance` (`:55`) — נפילה מפורשת פר-טיקר (`:126-131`)
- VIX: **yfinance בלבד** (`_fetch_vix` `:69`) — "Alpaca doesn't support index symbols"

**מה נכתב:** שורה אחת ל-`market_context` דרך `write_context()`, ו-`run_market_context.main()` (`:24`) יוצא עם קוד 0 בהצלחה או 1 בכשל (`:31-35`) — כלומר כשל כתיבה **כן** מכשיל את ה-workflow, בניגוד לרוב הרכיבים האחרים.

### 7.2 — `monthly_rotation.py` (207) + `prepare_next_month.py` (267) — הרצף של 1 לחודש

**00:01 — `monthly_rotation.py`:**
```
current_key = החודש הנוכחי · next_key = החודש הבא            :152-153
if _already_done(next_key): יוצא                              :158-161
    (_already_done = כל SHEET_NAMES כבר ב-config, :41-46)
sheets_manager._ensure_month(next_key)                        :178
_copy_open_portfolio(gc, current, next)                       :190   ← מעתיק פוזיציות Open
_git_commit_push()                                            :195
```
`_ensure_month` (`sheets_manager.py:329`) יוצר גיליון לכל שם ב-`SHEET_NAMES` שחסר, ושומר את הקונפיג **אינקרמנטלית אחרי כל יצירה** (`:349-353`) — כך שכשל באמצע לא מאבד את מה שכבר נוצר.

**00:05 — `prepare_next_month.py`:** יוצר את החודש **שאחרי הבא**, עם רשימה משלו.

**⚠️ שתי הרשימות החלוקות (כפילות #10, מאומת בקוד):**

| | `sheets_manager.SHEET_NAMES` | `prepare_next_month.SHEET_NAMES` |
|---|---|---|
| מיקום | `sheets_manager.py:38-48` | `prepare_next_month.py:22-30` |
| מספר ערכים | **9** | **8** |
| `live_trades` | **קובץ עצמאי** | **חסר** — עם הערה בשורה `:29`: `"score_tracker",  # live_trades יהיה כ-tab נוסף בתוכו` |
| מה עושה במקום | — | `add_live_trades_tab(gc, score_tracker_id)` (`:172`) יוצר **טאב** בשם `live_trades` בתוך קובץ ה-`score_tracker`, ואז `created_ids['live_trades'] = created_ids['score_tracker']` (`:240`) |

**ההשלכה שראיתי בקוד:** מי שרץ ראשון קובע את המבנה.
- אם `prepare_next_month` הספיק — `live_trades` הוא **alias** ל-`score_tracker`, ואז `_already_done` של `monthly_rotation` מחזיר `True` (כל 9 השמות נמצאים, כי `live_trades` קיים כ-alias) והרוטציה **מדלגת**.
- אם `prepare_next_month` נכשל — `monthly_rotation._ensure_month` יוצר `live_trades` כ**קובץ נפרד**.

זה בדיוק התרחיש שגוף TASK-251 מתאר: `prepare_next_month` נכשל ב-1/7 עם `RuntimeError DUPLICATE MONTH GUARD` (TASK-143, שתי תיקיות בשם 2026-08), יצא לפני שלב ה-alias, ואוגוסט נשאר חצי-מוקצה. ואז `scripts/fix_august_provisioning_v1.py:305` — שאיטרר על `sheets_manager.SHEET_NAMES` — יצר את הקובץ העצמאי.

### 7.3 — `sma20_cache.py` (95) · `sentinel_selftest_v1.py` (146) · `shadow_audit_v1.py` (143)

**`sma20_cache`** — מחשב SMA על 20 ימי-מסחר ואת המרחק באחוזים ממנו. קאש **פר-טיקר פר-יום** בקובץ מקומי `data/sma20_cache.json` (`:17`), מפתח `f"{ticker}:{today_str}"` (`:51`). הדפוס הועתק מ-`market_cap_cache.json`. משמש את פילטר 4d (TOXIC_PROFILE).
⚠️ `data/` ב-.gitignore, וכל ריצת GitHub Actions מתחילה מ-checkout נקי ⇒ **הקאש ריק בכל ריצה**. וב-`decision_logic.py:409` הפילטר **מדלג** כאשר `price_vs_sma20 is None`. אבל מאז `ENTRY_GATE_MINIMAL=True` הפילטר כבוי בכל מקרה.

**`sentinel_selftest_v1.py`** — הרנס בדיקה-עצמית קריאה-בלבד (`:4`). מזין לכל בדיקה דאטה תקין ודאטה מקולקל-בכוונה ומוודא שההחלטה תואמת לצפי. הדוקסטרינג (`:6-7`): **"Required by PK v2.18 before switching SENTINEL_MODE shadow→active."** מריצים ידנית: `python3 -m agent.sentinel.sentinel_selftest_v1`.

**`shadow_audit_v1.py`** — אודיט-צל קריאה-בלבד (`:4-8`): מריץ כל בדיקה מול הסריקה האחרונה **האמיתית** של היום מ-`timeline_live` ומול `account_state` אמיתי, ומדווח את התפלגות ה-BLOCK/WARN/ALLOW שהיתה מתקבלת. "Used to measure the real false-positive BLOCK rate before switching SENTINEL_MODE shadow→active."

⚠️ **שניהם אינם מיובאים בשום מקום ואינם רצים בשום workflow.** אימות: `grep -rn "sentinel_selftest\|shadow_audit"` על כל הריפו מחזיר **רק את הקבצים עצמם**. שני כלים שנבנו במפורש כתנאי-מקדים למעבר shadow→active, ואף אחד לא מופעל אוטומטית.

---

## 8. שאלות מ-part2 שנסגרות בקריאה בלבד

### E2 — `score_comparison_page` / `live_trades_page` — **מתות. מאומת.**

```
grep -n "score_comparison_page\|live_trades_page" dashboard.py
3280:def live_trades_page():
3450:def score_comparison_page():
```
**רק ההגדרות. אפס קריאות.** סריקה על כל הריפו (`--include='*.py'`, ללא backups/research/project_sync) לא מצאה אזכור נוסף. שתיהן אינן ב-`_PAGE_NAMES` (`:5263-5275`) ואינן ב-dispatch (`:5304-5327`).
**היקף:** `live_trades_page` שורות 3280–3449 = **170 שורות**; `score_comparison_page` שורות 3450–3775 = **326 שורות**. סה"כ **~496 שורות בלתי-נגישות** ב-`dashboard.py`.

### E11 — `daily_audit.py` — **לא נגעו בו מאז 2026-04-18. מאומת.**

```
git log -1 --date=short -- daily_audit.py
2026-04-18 6ac86a0 fix: deduplicate strip_comments + remove _get_gc wrapper from dashboard
git log --oneline -- daily_audit.py | wc -l   →  2
```
**שני commits בסך הכל בכל ההיסטוריה שלו**, האחרון לפני 3.5 חודשים — והוא לא היה על הקובץ עצמו אלא על dedup גלובלי. אפס workflow, אפס מייבאים.
האזכורים היחידים: מחרוזת עזרה ב-`dashboard.py:3923` ("**daily_audit.py** — בדיקה יומית יותר מקיפה"), הערה ב-`utils.py:804`, ותרשים ב-PK `:1191`. ה-PK עדיין מציג אותו כחלק מהמערכת.
**673 שורות. אין ראיה שמישהו הריץ אותו מאז אפריל.**

### E12 — האם n אכן קדם ל-45 הימים — **כן, בפער גדול. מדוד.**

הרצתי ספירה מול `utils.is_trading_day` (שמשתמש ב-`pandas_market_calendars`, לוח NASDAQ, `utils.py:132-137`):

```
ימי-מסחר 2026-06-29 .. 2026-08-03 כולל       = 25
ימי-מסחר אחרי 2026-06-29 עד 2026-08-03       = 24
היום ה-45 אחרי 2026-06-29                    = 2026-09-01
```

**המסקנה:** כשכלל-העצירה ירה ב-3/8, עברו **24-25 ימי-מסחר מתוך 45**. הדדליין הקלנדרי היה נופל ב-**1 בספטמבר**. `n=173 >= 150` אכן קדם — בדיוק כפי ש-`HYPOTHESES.md:237` מנסח: "The rule fired on n, not on the calendar."
**המשמעות למספרים:** 173 ENTER-ים ב-24 ימי-מסחר = ממוצע **~7.2 כניסות ליום**. תחת תקרה של 10 ליום (`AGENT_COLD_START_MAX_DAILY`), זה קרוב לרוויה — ומסביר איך 43 כניסות ביום אחד (22/07) היו אפשריות רק כשמגבלות-החשיפה נשברו.

---

## 9. עדכון התמונה

### 9.1 — תיקונים ל-part1 ו-part2

**תיקון 1 — part2 §7.4 טען ש-"`sheets_manager._with_retry` אין לו קובץ טסט ייעודי". לא בדקתי מספיק.**
מה שכן מאומת עכשיו: `tests/test_scanner_timeline_cache_v1.py` (111 שורות) בודק את שכבת-הקאש, ו-`tests/test_position_manager_cached_reader_v1.py` בודק את ההבדל בין המסלול המקושר ללא-מקושר. **לא מצאתי טסט על ה-backoff עצמו.** אני משאיר את הטענה החלקית ומסמן אותה כלא-סגורה.

**תיקון 2 — part2 §E7 הניח ש-`_read_decision` הוא "מקור-429 שלא נספר, בתוך callback שמופעל לכל postmortem". הניסוח היה מטעה.**
ראיה: `postmortem_engine` נקרא מ-`position_manager._close_position` (`:307`) — כלומר **רק כשפוזיציה נסגרת**, לא בכל דקה. עם `AGENT_FORCE_EOD_CLOSE=False`, סגירות קורות רק בחציית TP/SL (`position_manager.py:244-251`). הקריאה הלא-מקושרת (`orchestrator.py:635`) יקרה כשהיא נורית, אבל **התדירות שלה היא מספר-הסגירות-ליום, לא 390**.

**תיקון 3 — part2 §2.4 מנה 6 נתיבי-כתיבה מה-dashboard. אחד מהם הוא no-op.**
`save_timeline_to_sheets` (`gsheets_sync.py:170`) הוא **פונקציה מתה שמחזירה `True`**: "Deprecated: timeline_archive removed — no-op" (`:171-173`). הקריאה ב-`dashboard.py:785` לא כותבת דבר. נתיבי-הכתיבה החיים הם **5**, לא 6.

**תיקון 4 — part2 §5.3 טען "אין fallback ברמת-הקריאה". הניסוח נכון אבל חסר חריג אחד.**
`market_context_v1.py:126-131` **כן** מבצע fallback ברמת-הקריאה: `_fetch_bar_alpaca("SPY")` ואם נכשל `_fetch_bar_yfinance("SPY")`, ואותו דבר ל-IWM. זה **fallback ידני בתוך הסוכן**, לא בשכבת `data_provider`. הטענה על `data_provider` נשארת נכונה; הסוכן הזה עוקף אותה.

**תיקון 5 — part2 §3.2 טען שה-Critic "מחשב win_rate לבד... הקובץ לא מייבא מ-formulas בכלל". שני החלקים נכונים, אבל התמונה חלקית.**
ה-CI **כן** מתווסף — בשכבת-התבנית: `weekly_brief.py:82` קורא `fmt_rate_ci(wins, trades)`. כלומר ה-Critic מייצר את המונה בהגדרה שלו, והתבנית עוטפת אותו ב-Wilson CI. הכפילות היא בהגדרת-הניצחון, לא בהצגה.

### 9.2 — כפילויות SSoT חדשות (המשך המספור מ-11)

**12. ארבע הגדרות שונות של Win Rate.** (הרחבה של #8 — התברר שיש 4, לא 2)
| # | הגדרה | קובץ:שורה |
|---|---|---|
| א | `"TP" in ExitReason` | `orchestrator_email_daily.py:122` |
| ב | `RealizedPnL > 0` | `critic_v1.py:145-151` |
| ג | הליכה יומית D1→D5 מול TP/SL | `utils.py:513` |
| ד | `wins/closed*100` ללא CI, 3 מופעים | `live_agent_page.py:268` · `trade_history_page.py:237` · `:484` |

**13. שני סטים של secrets למייל.** `GMAIL_USER`/`GMAIL_APP_PASS`/`REPORT_TO` (`health_audit.py:1874-1876`) מול `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`EMAIL_TO` (`email_sender.py:36-40`). אותו תפקיד, שני מקורות.

**14. שלושה מקומות שמחזיקים "עמלת השאלה", אף אחד מהם לא נתון.**
`tradability.MOCK_DEFAULTS["borrow_fee_pct"] = 12.5` (`:31`, נכתב ל-decision_log בכל ENTER) · `_real_check_cached` מחזיר `0.0` (`:89`) · `borrow_collector.build_borrow_row` כותב `""` (`:119`). ומודל-העלות בפועל (`formulas.calculate_net_pnl`) מקבל את הריבית מ-`config.BORROW_SCENARIOS = [0.50, 2.00, 5.00]` — **מקור רביעי, שאינו מדבר עם אף אחד מהשלושה**.

**15. שתי רשימות של עמודות `paper_portfolio`.** `order_manager.PORTFOLIO_COLUMNS` (משמש את `build_portfolio_row`, `:284`) מול `create_agent_sheets.AGENT_SHEET_HEADERS["paper_portfolio"]` (`:82`). TASK-217 הפך את הכתיבה ל-by-name בדיוק כדי שהן לא ייפרדו בשקט, ו-TASK-219 הוסיף guard — אבל שתי הרשימות עדיין קיימות בנפרד.

**16. שני מסלולי-כתיבה שונים לאותו `decision_log`.** `decision_logger.log` פותח ישירות `gc.open_by_key(sheet_id).sheet1` (`:351`), בעוד כל שאר הקוד עובר דרך `sheets_manager.get_worksheet("decision_log")` (שמנסה קודם טאב-בשם ורק אז נופל ל-`sheet1`).

### 9.3 — קוד מת חדש שהתגלה

| מה | היקף | ראיה |
|---|---|---|
| `dashboard.live_trades_page()` | 170 שורות | מוגדרת, אפס קריאות (`dashboard.py:3280`) |
| `dashboard.score_comparison_page()` | 326 שורות | מוגדרת, אפס קריאות (`dashboard.py:3450`) |
| `gsheets_sync.save_timeline_to_sheets()` | no-op | מחזירה `True` בלי לכתוב (`:170-173`), עדיין נקראת מ-`dashboard.py:785` |
| `agent/monitoring/` | חבילה ריקה | רק `__init__.py` בגודל **0 בתים**, נוצר 3/5 ולא נגעו בו מאז |
| `agent/sentinel/sentinel_selftest_v1.py` | 146 שורות | אפס מייבאים, אפס workflow |
| `agent/sentinel/shadow_audit_v1.py` | 143 שורות | אפס מייבאים, אפס workflow |
| `providers/data_provider_factory` | — | **מודול שלא קיים**, מיובא ב-`price_freshness.py:41` |
| `daily_audit.py` | 673 שורות | אחרון-שינוי 2026-04-18, 2 commits בסך הכל |
| `agent/utils/sheets_cache.py` | 171 שורות | (מ-part2) אפס מייבאים |
| `Trader.evaluate_batch()` | 20 שורות | מוגדרת (`trader.py:75`), האורקסטרטור משתמש בלולאה במקום |

**סה"כ קוד מת שאותר בשלוש הריצות: ~1,650 שורות.**

---

## 10. הספירה

### 10.1 — מה נקרא במצטבר

| ריצה | קבצים חדשים שנפתחו | שורות (מלא/משמעותי) |
|---|---|---|
| part1 | 24 | ~13,000 |
| part2 | +10 | +3,500 |
| **part3** | **+34** | **+5,900** |
| **סה"כ** | **~68 מתוך 145** | **~22,400 מתוך ~48,000** |

**מה נקרא ב-part3 (34 קבצים):**
`data_quality.py` (מלא) · `tradability.py` (מלא) · `trader.py` (מלא) · `decision_logger.py` (מלא) · `decision_id_generator.py` (מלא) · `order_manager.py` (משמעותי) · `alpaca_broker.py` (משמעותי) · 7 בדיקות Sentinel (כולן מלאות: `completeness`, `scan_freshness`, `price_sanity`, `price_freshness`, `quota_health`, `provider_heartbeat`, `position_sync`) · `data_sentinel.py` (הושלם) · `reconciler.py` (משמעותי) · `orchestrator_eod.py` (מלא) · `borrow_collector.py` (מלא) · `postmortem_engine.py` (מיפוי-טריגר) · `score_analytics.py` (הושלם) · `gsheets_sync.py` (מבני + write paths) · `cross_month_loaders.py` (מבני) · `enrich_post_analysis.py` (מבני) · `backfill_ohlc_v2.py` (מבני) · `email_sender.py` · 5 תבניות-מייל · `orchestrator_email_daily.py` (משמעותי) · `orchestrator_email_morning.py` · `orchestrator_critic{,_weekly,_monthly}.py` · 4 עמודי `agent/dashboard/` + `_data_loaders.py` · `market_context_v1.py` (מבני) · `run_market_context.py` (מלא) · `monthly_rotation.py` (משמעותי) · `prepare_next_month.py` (החלק הרלוונטי) · `sma20_cache.py` · `sentinel_selftest_v1.py` · `shadow_audit_v1.py` · `critic_v1.py` (הושלם)

### 10.2 — האם נשאר משהו בנתיב הפרודקשן שלא נפתח

**לא. רשימת §11.1 של part2 נסגרה במלואה.**

עברתי פריט-פריט על הטבלה שם. כל שורה שסומנה כ"נתיב פרודקשן" נפתחה בריצה הזו. שלושת הפריטים היחידים שנשארו מהרשימה ההיא הם מחוץ-להיקף המוצהר:

| מה | סטטוס | למה |
|---|---|---|
| `code_auditor.py` (449) | לא נקרא | כלי-שורש חד-פעמי — **מחוץ להיקף** (part2 §8.2) |
| `deep_scan.py` (409) | לא נקרא | כלי-שורש — **מחוץ להיקף** |
| `daily_audit.py` (673) | לא נקרא | כלי-שורש, ומאומת כלא-פעיל מאז 4/2026 — **מחוץ להיקף** |
| `scripts/*` (10 קבצים, ~1,900) | לא נקרא | **מחוץ להיקף** מפורש |
| `tests/*` פרטני (10,101) | לא נקרא | **מחוץ להיקף** מפורש |
| `scripts/overnight/*` | לא נקרא | רץ-הלילה שנוטרל — **מחוץ להיקף** מפורש |

### 10.3 — מה נקרא חלקית ומה עוד יש בו

| קובץ | מה נקרא | מה נשאר |
|---|---|---|
| `dashboard.py` (5,330) | ניווט, ייבואים, נתיבי-כתיבה, 16 חישובי-inline, מיפוי עמודים | גוף 8 העמודים הוותיקים (~4,000 שורות) — התצוגה עצמה |
| `health_audit.py` (2,079) | 30 הבדיקות + הספים + 3 ערוצי-הפלט | גוף 20 הבדיקות שקראתי רק את הדוקסטרינג והחתימה שלהן |
| `auto_scanner.py` (1,409) | `run_scan`, `analyze_ticker`, `fetch_finviz`, `is_snapshot_time`, כתיבת timeline_live | `update_portfolio_live` (`:625`), `update_ticker_follow_up` (`:768`), `update_live_trades` (`:999`), `sync_score_tracker` (`:1151`), `run_eod` (`:1312`) — ~780 שורות |
| `utils.py` (925) | `calculate_stats`, `classify_trade`, `is_trading_day` | `get_market_cap_smart` (`:313`), `resolve_whipsaw` (`:640`), `SanitizedOverview` (`:871-925`) |
| `post_analysis_collector.py` (650) | `fetch_ohlc_for_days`, `select_candidates`, מבנה `run` | `fetch_d0_and_fundamental` (`:256`), `fetch_timeline_stats` (`:333`), גוף `run` (`:389`) |
| `critic_v1.py` (942) | `review_completed_trades`, `summarize`, `build_weekly_row`, `daily_facts` (מקורות) | `unified_positions` (`:673`), `build_monthly_detail` (`:315`), `write_scorecard` (`:624`) |

### 10.4 — מה עדיין לא ברור

**F1. `unified_positions()` (`critic_v1.py:673`, ~150 שורות) — "טבלת-עמדות חוצת-סוכנים, רישום קונפליקטים".**
זה נשמע כמו הרכיב היחיד שמנסה לגשר בין הסוכנים, ולא קראתי אותו. **מה שיפתור:** קריאת `:673-822`.

**F2. האם `borrow_data` באמת מתמלא, ובאיזה כיסוי.**
הקוד תקין ומעקף את המוק בכוונה (`orchestrator_eod.py:79`). אבל הזיכרון שלי מציין "coverage 1-ticker/day". **מה שיפתור:** קריאת `borrow_coverage` — Sheets, חסום.

**F3. `_derive_regime` (`market_context_v1.py:98`) — מה בדיוק הטבלה.**
ראיתי את שלושת הקלטים ואת הספים, לא את מטריצת-הגזירה עצמה. **מה שיפתור:** קריאת `:98-108`.

**F4. מה קורה כשהחודש מתגלגל באמצע יום-מסחר.**
`build_account_state` פותר את `paper_portfolio` לחודש הנוכחי בכל דקה. ב-1 לחודש בשעה 00:01 הרוטציה מחליפה — אבל פוזיציות פתוחות שהועתקו הן של `portfolio`, לא של `paper_portfolio` (`monthly_rotation._copy_open_portfolio:49` מעתיק "Open portfolio positions"). **לא ברור לי אם `paper_portfolio` של הסוכן מועתק בכלל.** אם לא — כל פוזיציה פתוחה של הסוכן "נעלמת" ב-1 לחודש. זה עשוי להסביר חלק מ-83 השורות התקועות ביולי. **מה שיפתור:** קריאת `_copy_open_portfolio` (`monthly_rotation.py:49-106`) — 57 שורות שלא קראתי.

**F5. `resolve_whipsaw` (`utils.py:640`, ~95 שורות).**
מוזכר ב-`whipsaw_verdicts.json` שהוא חריג מפורש ב-.gitignore ("committed WHIPSAW intraday verdict snapshot"). לא קראתי איך הוא פותר whipsaw. **מה שיפתור:** קריאת `utils.py:640-735`.

**F6. האם `agent_scorecard` נכתב בפועל.**
`write_scorecard` (`critic_v1.py:624`) קיים ונקרא מ-`orchestrator_critic.py`, ויש עמוד dashboard שקורא ממנו (`dashboard.py:5044`). לא קראתי את הפונקציה. **מה שיפתור:** קריאת `:624-672`.

**F7. הפער בין `MAX_RETRIES` של `order_manager` ל-`_RETRY_MAX` של `sheets_manager`.**
ראיתי את הלולאה (`order_manager.py:179-197`) אבל לא את ערכי `MAX_RETRIES`, `BACKOFF_BASE`, `ORDER_FILL_TIMEOUT`, `POLL_INTERVAL`. **מה שיפתור:** קריאת הקבועים ב-`order_manager.py:1-108`.

---

## אימות

```
git status --porcelain
?? docs/auto-dancer/
?? reports/

git diff --stat
(ריק)
```

לא נגעתי בקוד, לא הרצתי pytest, לא נגעתי ב-Sheets/Drive/FINVIZ, לא commit, לא push, לא שיניתי סטטוס של אף תיק.
הכתיבות היחידות: הדוח הזה ו-`reports/INDEX.md`.
הרצה יחידה של פייתון: ספירת ימי-מסחר ל-E12 — חישוב בזיכרון מול `pandas_market_calendars`, אפס I/O לגיליונות, סקריפט ב-scratchpad מחוץ לריפו.
