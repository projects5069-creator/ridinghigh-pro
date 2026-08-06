# RidingHigh Pro — היכרות עם המערכת, חלק ד' (אחרון)

**תיאור בלבד.** אין תוכנית, אין המלצות, אין דירוג, אין "מה שיפתור", אין הצעת תיקון.
נכתב 2026-08-05 10:45 Lima (11:45 EDT NY).
מטרה: לסגור את מה ש-part3 §10.3 סימן כנקרא-חלקית בנתיב הכתיבה החי.
מחוץ להיקף מוצהר: F1–F7 של part3 §10.4 · גוף 8 עמודי dashboard הוותיקים · גוף 20 בדיקות health_audit · `scripts/` · `tests/` · כלי-שורש חד-פעמיים · רץ-הלילה.

**סקילים:** נטען `rhpro-live` (`~/.claude/skills/rhpro-live/SKILL.md`, 180 שורות).
`ls ~/.claude/skills/`: anthropic-skills · backtest-expert · biotech-screener · data-quality-checker · position-sizer · rhpro-live · rhpro-session · signal-postmortem · time-check · trader-memory-core.

---

## 1. `auto_scanner.py` — חמש הפונקציות שרצות כל דקה

### 1.0 — סדר הקריאה מתוך `run_scan()`

```
run_scan()                                              :355
 ├─ אם אין תוצאות (מסלול early-return):                 :418
 │     update_portfolio_live(gc2, now_peru)              :423
 │     update_live_trades(gc2, now_peru, results=[])     :424
 │     return                                            :427
 ├─ כתיבת timeline_live                                  :442-478
 ├─ אם is_snapshot_time():                                :487
 │     daily_snapshots · portfolio · _save_daily_summary  :488-528
 ├─ update_portfolio_live(_gc, now_peru)                  :539
 ├─ update_ticker_follow_up(_gc_fu, now_peru)             :547
 ├─ update_live_trades(_gc3, now_peru, results=results)   :555
 └─ אם now_peru.minute % 5 == 0:
       sync_score_tracker(_gc2, now_peru)                 :564
```
שני המסלולים בלעדיים. במסלול חסר-התוצאות `update_ticker_follow_up` ו-`sync_score_tracker` **לא** נקראות.
`run_eod()` (`:1312`) נקראת רק מ-`python auto_scanner.py --eod` (`:1400-1401`), שמופעל מ-`post_analysis.yml:40` ב-16:05 Peru.

### 1.1 — הטבלה המסכמת

| פונקציה | קוראת מ- | כותבת ל- | דורסת/מצרפת | פעולות API (Sheets) | פעולות ספק |
|---|---|---|---|---|---|
| `update_portfolio_live` (`:625`) | `portfolio` (`:639-642`) · `portfolio_live` (`:661-662`) | `portfolio_live` (`:755`) | **דורסת** — `df_to_sheet` = `ws.clear()` ואז `update` | ~6 | `get_latest_bar` × מספר הפוזיציות הפתוחות (`:704`) |
| `update_ticker_follow_up` (`:768`) | `timeline_live` **דרך הקאש** (`:797`) · `ticker_follow_up` (`:839`) | `ticker_follow_up` (`:989` / `:991`) | **מצרפת** אם יש כותרת · **דורסת** בכתיבה ראשונה | ~4 | **4 לכל טיקר** (`:862`, `:869`, `:877`, `:884`) |
| `update_live_trades` (`:999`) | `live_trades` (`:1016-1022`) | `live_trades` (`:1143`) | **דורסת** — `df_to_sheet` | ~4 | `get_latest_bar` × מספר שורות Pending (`:1046`) |
| `sync_score_tracker` (`:1151`) | `portfolio` (`:1168-1169`) · כותרת `score_tracker` (`:1287`) | `score_tracker` (`:1289` / `:1293`) | **מצרפת** אם הכותרת תואמת · **דורסת** (`clear`+`update`) אם לא | ~5 | 2 לכל טיקר פעיל (`:1199`, `:1205`) |
| `run_eod` (`:1312`) | `timeline_live` (`:1328-1331`) · `portfolio` (`:1355`) | `portfolio` (`:1378`) · `daily_summary` (דרך `_save_daily_summary` `:1387`) | **דורסת** את שניהם | ~8 | 0 |

### 1.2 — מה קורה בכשל

| פונקציה | מנגנון | שורה |
|---|---|---|
| `update_portfolio_live` | `try/except` יחיד סביב הכל → `print("⚠️ portfolio_live error: {e}")`. **בליעה שקטה** | `:758-759` |
| ↳ פנימי: כשל משיכת מחיר | `except Exception: continue` — הטיקר מדולג בשקט, בלי הודעה | `:709-710` |
| `update_ticker_follow_up` | `try/except` חיצוני → `print("⚠️ ticker_follow_up error")`. **בליעה** | `:995-996` |
| ↳ פנימי: כשל fundamentals | `print` + `fund = {}` — ממשיך עם dict ריק | `:863-865` |
| ↳ פנימי: מחיר | `except Exception: price = 0.0`, ואז `if price <= 0: continue` | `:871-874` |
| ↳ פנימי: intraday | `print` + `continue` | `:885-887` |
| ↳ פנימי: כל השאר | `except Exception as e: print; continue` | `:978-980` |
| `update_live_trades` | `try/except` חיצוני → `print("⚠️ live_trades error")`. **בליעה** | `:1147-1148` |
| ↳ פנימי: מחיר | **`except:` עירום** (bare) ואז `continue` | `:1051-1052` |
| `sync_score_tracker` | `try/except` חיצוני → `print("[ScoreTracker] ⚠️ {e}")`. **בליעה** | `:1297-1298` |
| ↳ פנימי: RSI/ATR/rel_vol/run_up/gap/TPD | **שישה `except Exception: pass` נפרדים** — כל מדד שנכשל נשאר על ברירת-המחדל שלו (`rsi=50.0`, `atrx=0.0`, `rel_vol=1.0`, `run_up=0.0`, `gap=0.0`, `tpd=0.0`) והשורה **נכתבת בכל זאת** | `:1225`, `:1230`, `:1234`, `:1237`, `:1242`, `:1247` |
| ↳ פנימי: שגיאת טיקר | `print(f"  [ScoreTracker] {ticker}: {e}")` | `:1275-1276` |
| `run_eod` | `return` מוקדם עם `print` על 4 תנאים (`:1325`, `:1330`, `:1333`, `:1338`); שני `try/except` נפרדים לחלק ה-portfolio (`:1382-1383`) ולחלק ה-daily_summary (`:1388-1389`) | — |

**אין אף אחת מהחמש שמעלה חריגה החוצה, ואף אחת לא מגדילה מונה-שגיאות.** כל כשל מודפס ל-stdout ונעלם עם לוג ה-Actions.

⚠️ הדפוס ב-`sync_score_tracker` שונה מהותית מהשאר: **שישה `except Exception: pass`** שמותירים ערכי-ברירת-מחדל, ואז `calculate_score` רץ עליהם (`:1251-1255`) והשורה נכתבת. שורה שבה כל ששת המדדים נכשלו תיראה בגיליון כמו שורה תקינה עם `RSI=50, ATRX=0, REL_VOL=1, RunUp=0, Gap=0, TypicalPriceDist=0`.

### 1.3 — חישובי inline שיש להם מקבילה ב-`formulas`

**`update_portfolio_live` — ארבעה:**

| שורה | inline | מקבילה ב-`formulas` |
|---|---|---|
| `:684` | `tp10_price = round(scan_price * (1 - TP_PCT), 4)` | אין פונקציה ייעודית; אותו ביטוי מופיע ב-`decision_logic._calculate_position:147` וב-`utils.classify_trade:573` |
| `:685` | `sl_price = round(scan_price * (1 + SL_PCT), 4)` | אותו דבר, `decision_logic:148`, `utils.py:574` |
| `:725-726` | `sl_hit = new_high >= sl_price` / `tp_hit = new_low <= tp10_price` | `utils.classify_trade:586-587` (`tp_hit = lo <= tp_price`, `sl_hit = hi >= sl_price`) |
| `:728-733` | סדר ההכרעה — SL גובר על TP | `utils.classify_trade:588-593` מחזירה `WHIPSAW` באותו מצב; כאן `"SL ❌"` |

**`update_live_trades` — חמישה:**

| שורה | inline | מקבילה |
|---|---|---|
| `:1114-1115` | `tp10_price` / `sl_price` | כנ"ל |
| `:1059-1060` | `sl_hit` / `tp_hit` | `utils.classify_trade:586-587` |
| `:1065` | `pnl = round((entry_price - sl_price) / entry_price * 100, 2)` | **`formulas.calculate_pnl_pct(entry, exit, is_short=True)`** (`formulas.py:529`) — אותה נוסחה בדיוק |
| `:1069` | `pnl = round((entry_price - tp10_price) / entry_price * 100, 2)` | **`formulas.calculate_pnl_pct`** |
| `:1073` | `pnl = round((entry_price - live_price) / entry_price * 100, 2)` | **`formulas.calculate_pnl_pct`** |
| `:1062-1064` | סדר ההכרעה — SL גובר | `utils.classify_trade:588-593` |

`formulas.calculate_pnl_pct` **אינו מיובא** ל-`auto_scanner.py` (רשימת הייבוא `:26-40`).

**`update_ticker_follow_up` — אחד:**

| שורה | inline | מקבילה |
|---|---|---|
| `:933` | `typical_price = (high_today + low_today + price) / 3` | `formulas.calculate_typical_price_dist:160` מחשב את אותו ביטוי בפנים. ההערה בשורה מציינת שהוא נשמר "for the TypicalPrice column" |

שאר הפונקציה **כן** משתמשת ב-formulas באופן עקבי: `calculate_mxv` (`:924`), `calculate_runup` (`:925`), `calculate_atrx` (`:926`), `calculate_gap` (`:927`), `calculate_rel_vol` (`:928`), `calculate_float_pct` (`:929`), `calculate_price_to_high` (`:930`), `calculate_price_to_52w_high` (`:931`), `calculate_scan_change` (`:932`), `calculate_typical_price_dist` (`:936`), `calculate_score` (`:943`). ההערה ב-`:934-935` מציינת מפורשות שזה נעשה בכוונה: "TASK-137 pt2: route through the canonical (same as D0:227) — DRY/§10".

**`sync_score_tracker` — אפס inline.** כולם עוברים דרך formulas: `calculate_atrx` (`:1228`), `validate_atrx` (`:1229`), `calculate_rel_vol` (`:1233`), `calculate_runup` (`:1236`), `calculate_gap` (`:1241`), `calculate_typical_price_dist` (`:1246`), `calculate_mxv` (`:1249`), `calculate_scan_change` (`:1250`), `calculate_score` (`:1251`).

**`run_eod` — אפס inline** (אין חישוב מדדים; קורא ערכים מוכנים מ-`timeline_live`).

### 1.4 — מי כותב ל-`live_trades` מלבד `update_live_trades`

מה שראיתי:

1. **`update_live_trades` עצמה** — `df_to_sheet(ws, lt_df)` (`:1143`), דריסה מלאה של הגיליון בכל דקה.
2. **`dashboard.py:3326-3327`** — בתוך עמוד `live_trades_page()`:
   ```python
   n = sheets_manager.archive_live_trades(gc, closed_df)   dashboard.py:3321
   open_clean = open_df.reindex(columns=LIVE_TRADES_COLS, fill_value="")
   ws.clear()                                               :3326
   ws.update("A1", [LIVE_TRADES_COLS] + open_clean...)      :3327
   ```
   part3 §8 קבע ש-`live_trades_page()` אינה מופיעה ב-`_PAGE_NAMES` ואינה ב-dispatch, ולכן הקוד הזה אינו נגיש מהניווט.
3. **`sheets_manager.archive_live_trades(gc, closed_df)`** (`:690`) — לא כותב ל-`live_trades` עצמו אלא לטאב `live_trades_archive` **בתוך אותו spreadsheet** (`:707-717`), ויוצר את הטאב אם חסר. הדוקסטרינג (`:695-696`): "Safety contract: RAISES on any failure — caller must NOT delete from live_trades unless this returns successfully. Never silently drops data."
4. **`prepare_next_month.add_live_trades_tab(gc, score_tracker_id)`** (`:172-183`) — יוצר טאב בשם `live_trades` בתוך קובץ ה-`score_tracker`, ואז `created_ids['live_trades'] = created_ids['score_tracker']` (`:240`). לא כותב שורות — יוצר מבנה.

⚠️ ראיתי גם ש-`update_live_trades` מייבא את `LIVE_TRADES_COLS` מ-`auto_scanner` (`:762-766`), ו-`dashboard.py:3325` עושה `from auto_scanner import LIVE_TRADES_COLS` — כלומר שני הכותבים חולקים את אותה רשימת עמודות.

### 1.5 — נקודות נוספות שראיתי

**קריאות `portfolio` באותה דקה.** בתוך ריצה אחת של `run_scan`, הטאב `portfolio` נקרא ב-`get_all_values()` מ-3 מקומות: `:506` (רק בחלון ה-snapshot), `:642` (`update_portfolio_live`), `:1169` (`sync_score_tracker`, כל 5 דקות). אף אחת מהן לא עוברת דרך `sheets_manager.get_sheet_values` המקושר.

**שני `df_to_sheet` עם סמנטיקת-בטיחות הפוכה:**
```python
# auto_scanner.py:97-100
def df_to_sheet(ws, df):
    data = [...]
    sheets_manager._with_retry(ws.clear)     ← מנקה קודם
    sheets_manager.safe_update(ws, data)
```
```python
# gsheets_sync.py:110-113
def _df_to_sheet(ws, df, include_index=False):
    """Safe pattern: write data first, then trim excess rows —
       never clears before writing."""
```
`auto_scanner.df_to_sheet` מנקה לפני הכתיבה; `gsheets_sync._df_to_sheet` מצהיר במפורש שהוא **לא** עושה זאת. `portfolio_live`, `live_trades`, `daily_summary`, `daily_snapshots` ו-`portfolio` נכתבים דרך הראשון.

**ההגבלה של `update_ticker_follow_up`.** שלושה תנאי-יציאה מוקדמים בראש הפונקציה: `minute % 5 != 0` (`:783`), `not is_trading_day` (`:786`), `not is_market_hours` (`:788`). הדוקסטרינג (`:771`) מציין "heavy: ~85 tickers, ~3-4 min runtime" — ו-`auto_scan.yml` מוגדר עם `timeout-minutes: 8`.

**`sync_score_tracker` משתמש ב-`sheets_manager.trading_days_after`** (`:1174`), שקיים ב-`sheets_manager.py:673` — נפרד מ-`utils.get_trading_days_after` (`utils.py:215`).

**חלון D0–D3 ב-`sync_score_tracker`:** `if today == sd or today in _tdays_after(sd, 3)` (`:1183`) — יום הכניסה עצמו ועוד 3 ימי-מסחר.

**`run_eod` בוחר את שיא-ה-Score לטיקר:** `high_score.sort_values("Score", ascending=False).drop_duplicates("Ticker")` (`:1352-1353`) — בניגוד ל-`run_scan:504` שלוקח את כל השורות מעל הסף מתוך `results_df` של הסריקה הנוכחית.

⚠️ `run_eod:1349` מסנן `today_tl["Score"] >= TRADE_ENTRY_MIN_SCORE`. העמודה `Score` ב-`timeline_live` **כן** נכתבת (היא לא בין המוקפאות — `score_write_value` מוחל על `portfolio`, `daily_snapshots`, `ticker_follow_up`, `score_tracker` ו-`live_trades`, אבל `timeline_live` נכתב מ-`results_df` הגולמי ב-`:445-448`). זה מה שראיתי בקוד; לא בדקתי דאטה חי.

---

## 2. `monthly_rotation._copy_open_portfolio` (`:49-106`)

### התשובה החדה

**מועתק טאב אחד בלבד: `portfolio`.**

```python
ws_src = sheets_manager.get_worksheet("portfolio", month=from_month, gc=gc)   :57
ws_dst = sheets_manager.get_worksheet("portfolio", month=to_month, gc=gc)     :85
```
שתי הקריאות היחידות ל-`get_worksheet` בפונקציה כולה, שתיהן על `"portfolio"`.
**`paper_portfolio` אינו מוזכר בפונקציה.** אימות: `grep "paper_portfolio" monthly_rotation.py` → אפס תוצאות.

### הקריטריון לשורה שמועתקת

```python
status_idx = headers.index("Status") if "Status" in headers else None      :71
open_rows  = [r for r in rows if status_idx is not None and
              len(r) > status_idx and r[status_idx].strip() == "Open"]     :72-73
```
שלושה תנאים במצטבר:
1. קיימת עמודה בשם `"Status"` בכותרת המקור
2. אורך השורה גדול מאינדקס העמודה (שורה קטועה מדולגת)
3. הערך אחרי `.strip()` שווה **בדיוק** למחרוזת `"Open"` — התאמה מדויקת, תלוית רישיות

### מה קורה לשורה שלא עומדת בקריטריון

**היא לא מועתקת. היא נשארת בגיליון של החודש המקורי ולא מופיעה בחודש החדש.** אין מחיקה, אין סימון, אין רישום. הפונקציה מדפיסה רק ספירה מצטברת: `f"[Rotation] Found {len(open_rows)} Open positions to copy"` (`:79`) — בלי לציין כמה נדחו.

אם **אף** שורה לא עמדה בקריטריון: `print("[Rotation] No Open positions to carry over")` ו-`return` (`:75-77`).

### שני מסלולי-הכתיבה ביעד

```python
dst_data = ws_dst.get_all_values()                                :90
if len(dst_data) <= 1:
    ws_dst.update("A1", [headers] + open_rows)                    :94   ← כותרת + שורות
else:
    dst_keys = set(r[0] for r in dst_data[1:])                    :98   ← עמודה 0
    new_rows = [r for r in open_rows if r[0] not in dst_keys]     :99
    if new_rows:
        ws_dst.append_rows(new_rows)                              :101
```
ה-dedup ביעד הוא על **עמודה 0 בלבד** — לא על שם-עמודה. הדוקסטרינג (`:53`) אומר "Skips rows that already exist in the target (by PositionKey or Ticker+Date)"; מה שהקוד עושה בפועל הוא השוואת `r[0]`.

### תנאי-הכניסה לפונקציה

`main()` קורא לה רק **אחרי** ש-`_already_done(next_key)` החזיר `False` ו-`_ensure_month` הצליח (`:158-161`, `:178`, `:190`). היא עטופה ב-`try/except` שמדפיס `"[Rotation] ⚠️ Portfolio copy failed (non-fatal)"` וממשיך ל-commit (`:188-192`).

שני `return` שקטים נוספים: מקור לא נפתח (`:58-60`), מקור ריק (`:63-65`).

---

## 3. `utils.py` — שלושת החלקים שלא נקראו

### 3.1 — `resolve_whipsaw` (`:640-682`)

**מקבל:** `entry_price`, `minute_bars_df` (DataFrame של מוטות-דקה עם עמודות `low` ו-`high`), ואופציונלית `tp_frac` / `sl_frac` (ברירת-מחדל `TP_THRESHOLD_FRAC` / `SL_THRESHOLD_FRAC`).

**מחזיר** אחת משלוש מחרוזות:
| ערך | מתי | שורה |
|---|---|---|
| `"WIN"` | הדקה הראשונה שנוגעת ב-TP קודמת לראשונה שנוגעת ב-SL | `:678-679` |
| `"LOSS"` | הראשונה שנוגעת ב-SL קודמת | `:680-681` |
| `"UNRESOLVED"` | קלט לא-תקין · צד אחד בלבד מופיע במוטות · שני הצדדים נגעו **באותה דקה** | `:662-667`, `:675-676`, `:682` |

**ההיגיון המרכזי** (דוקסטרינג `:644-657`): WHIPSAW יומי אומר שמוט יומי **אחד** הראה גם TP וגם SL — כלומר **ידוע** ששני הרמות הושגו; המוט היומי פשוט לא יכול לסדר אותן. המוטות הדקתיים פותרים **רק אם** הם לוכדים את שתי הנגיעות בדקות **נפרדות**.
המשפט המפורש: "a one-sided minute view is NOT a verdict. Since daily proves both levels were hit, seeing only one side means the other is hidden — we cannot order them, so UNRESOLVED. **Never a guessed verdict**."

הפונקציה טהורה — `df.sort_index()` (`:672`) ואז השוואת אינדקסים. מסומנת בדוקסטרינג (`:660`): "Analysis only — does NOT feed official metrics".

**קוראים:** רק `tests/test_resolve_whipsaw_v1.py` (7 טסטים). `intraday_cache.py:14` מזכיר אותה בדוקסטרינג ("utils.resolve_whipsaw and the offline study consume this") אך אינו קורא לה. **אין קורא בקוד הפרודקשן.**

### 3.2 — התפקיד של `whipsaw_verdicts.json`

**הקובץ עצמו** (946 בתים, mtime 2026-06-12):
```json
{
  "snapshot_date": "2026-06-12",
  "source": "TASK-155 docs/research/WHIPSAW_RESOLUTION_2026-06-12/whipsaw_resolution.csv",
  "verdicts": {
    "MNTS|2026-04-13": "WIN",
    "XNDU|2026-04-15": "UNRESOLVED",
    "MAAS|2026-04-17": "LOSS",
    ...
  }
}
```
מפתח = `TICKER|SCAN_DATE`, ערך = אחת משלוש התוצאות של `resolve_whipsaw`.

**איך הוא משמש:**
```
dashboard._load_whipsaw_verdicts()          dashboard.py:2310
  └─ קורא את הקובץ מהתיקייה של dashboard.py  :2318-2320
  └─ בכשל/היעדר → (None, None)               :2323-2324
dashboard._resolved_wr_pct(df, outcomes, n_win, n_loss, vlookup)   :2327
  └─ לכל שורה שסווגה WHIPSAW:
       eff = resolved_class(vlookup.get(f"{Ticker}|{ScanDate[:10]}"))   :2338
  └─ (n_win + r_win) / denom * 100                                      :2342
metrics_bounds.resolved_class(verdict, fallback="LOSS")   metrics_bounds.py:45
  WIN → WIN · LOSS → LOSS · UNRESOLVED → None (מוחרג) · חסר → fallback
```
**ה-fallback פסימי בכוונה** (`metrics_bounds.py:54-57`): שורת WHIPSAW שאינה בתצלום נספרת כהפסד, "so the resolved bound never *over*-states the edge as the dataset grows past the snapshot".

**המשמעות המבנית:** הקובץ הוא **תצלום סטטי מ-12/06/2026** — 26 verdicts, לא מתעדכן. הוא חריג מפורש ב-`.gitignore` (`!whipsaw_verdicts.json`, עם ההערה "TASK-164 — committed WHIPSAW intraday verdict snapshot (deploy-visible)") כדי שיהיה זמין ל-Streamlit Cloud. שתי נקודות-קריאה ב-dashboard: `:2400` (עמוד Post Analysis) ו-`:5241` (עמוד Home).

**כלומר:** `resolve_whipsaw` הריצה שהפיקה את הקובץ הזה בוצעה פעם אחת ב-06/2026; הפונקציה עצמה כבר לא רצה, וה-dashboard קורא את התוצר הקפוא. כל WHIPSAW חדש מ-13/06 ואילך נופל ל-fallback `LOSS`.

### 3.3 — `get_market_cap_smart` (`:313-419`)

**שרשרת חמש עדיפויות** (הדוקסטרינג `:327-333`, והקוד):

| # | מקור | תנאי | שורות | כותב לקאש? |
|---|---|---|---|---|
| 1 | **FINVIZ** (`finviz_mc`) | `is not None and > 0` | `:368-372` | ✅ `_persist` |
| 2 | **fundamentals_provider** `market_cap` | `mc_raw and mc_raw > 0` | `:375-387` | ✅ |
| 3 | **shares × price** | `shares > 0 and price > 0` | `:390-393` | ✅ |
| 4 | **history_lookup** callback | הועבר **וגם** החזיר `> 0` | `:398-406` | ✅ |
| 5 | **cache_get** callback | הועבר **וגם** החזיר `> 0` | `:409-417` | ❌ במפורש — "Don't re-persist on read" (`:414`) |
| 6 | כשל מלא | — | `:419` | — |

**מתי נופל למי:**
- **1→2:** אם `finviz_mc` הוא `None` או `<= 0`
- **2→3:** אם `market_cap` מה-provider ריק או `<= 0`, **בתוך אותו בלוק `try`**
- **2/3→4:** בכשל, ה-`try` נבלע ב-`except Exception: pass` (`:394-395`) — כלומר גם חריגה של ה-provider עוברת בשקט
- **4→5, 5→6:** כל אחת ב-`try/except` נפרד שבולע

**מה מוחזר בכשל מלא:**
```python
return (None, None) if return_tuple else None      :419
```
כלומר `None`, לא `0`. הקורא ב-`auto_scanner.analyze_ticker:178` בודק `if not market_cap or market_cap == 0: return None` — הטיקר יורד מהסריקה.

**נקודות שראיתי:**
- **עדיפות 1 לא מאמתת מול שום מקור אחר.** אם FINVIZ מחזיר ערך חיובי, הוא מנצח מיד ונשמר לקאש (`:371`). ה-shares מוחזרים מ-`shares_cache` בלבד ולא נבדקים.
- **עדיפויות 4 ו-5 הן "dashboard-only feature"** לפי ההערות (`:397`, `:408`). `auto_scanner:162-168` קורא בלי `history_lookup` ובלי `cache_get`, כלומר בסקאנר השרשרת נעצרת אחרי עדיפות 3. הנפילה-לקאש בסקאנר מתבצעת **אחרי** הקריאה, ידנית ב-`analyze_ticker:173-177`.
- `_persist` (`:359-365`) עטוף ב-`try/except: pass` — כשל כתיבה לקאש נבלע.

### 3.4 — `SanitizedOverview` (`:836-925`)

**מה בדיוק עוקף.** הבעיה מתועדת בהערה מעל הקוד (`:828-834`):
```
    AAMIX      AMIX
    AA         A            (Agilent)
    AAA        AA           (Alcoa)
```
"The last two rows are why this is **not** a string sanitizer. Stripping a doubled first character breaks Alcoa; leaving short symbols alone leaves Agilent broken. **The clean value is in the DOM twice, so read it instead of guessing.**"

**המנגנון:** תת-מחלקה של `finvizfinance.screener.overview.Overview` שדורסת שיטה אחת — `_get_table` (`:884`). הדוקסטרינג (`:879-881`): "`_get_table` is the single funnel both 0.14.6 and 1.3.0 route every page through, with an identical signature, so one override covers the pinned version and whatever CI resolves to."

**מה משתנה בעמודה אחת בלבד:**
```python
ticker_pos = list(table_header).index("Ticker")       :892
...
if i == ticker_pos:
    info[table_header[i]] = extract_finviz_ticker(col)   :904   ← העקיפה
elif i not in num_col_index:
    info[table_header[i]] = col.text                     :906   ← המקור
else:
    info[table_header[i]] = number_covert(col.text)      :908   ← המקור
```

**`extract_finviz_ticker(td)` (`:839`) — ארבע עדיפויות:**
| # | מקור | שורה |
|---|---|---|
| 1 | תכונת ה-DOM `data-boxover-ticker` | `:853-855` |
| 2 | טקסט של `<a class="tab-link">` | `:857-860` |
| 3 | ה-`stripped_string` **האחרון** בתא (אות-הלוגו באה ראשונה) | `:862-865` |
| 4 | `td.text` הגולמי | `:867-868` |

טהורה — "no IO, no pandas, no network. Returns `""` for anything unusable" (`:848`).

**אילו שדות עדיין עוברים דרך finvizfinance המקורי — כל השאר.**
העקיפה נוגעת **אך ורק** לעמודת `Ticker`. כל שדה אחר בשורה עובר או דרך `col.text` (`:906`) או דרך `number_covert(col.text)` של finvizfinance (`:908`, מיובא ב-`:874`). בפילטר שהסקאנר מגדיר (`Price: Over $2`, `Performance: Today +15%` — `auto_scanner.py:347`) העמודות שנצרכות בפועל הן `Price`, `Change`, `Volume`, `Market Cap` (`analyze_ticker:151-161`) — **כל ארבעתן עוברות דרך הנתיב המקורי**.

**מבנה הטעינה** (`:918-925`): `SanitizedOverview` ברמת-המודול הוא **proxy**, לא מחלקה:
```python
class _SanitizedOverviewProxy:
    def __call__(self, *args, **kwargs):
        return _sanitized_overview_class()(*args, **kwargs)

SanitizedOverview = _SanitizedOverviewProxy()
```
`_sanitized_overview_class()` (`:871`) מייבא את `finvizfinance` רק בזמן הקריאה — "so utils stays import-light" (`:872`).

---

## 4. עדכון התמונה

### 4.1 — תיקונים

**תיקון 1 — part1 §B.2 תיאר את `update_ticker_follow_up` כרצה "כל דקה". לא נכון.**
ראיה: `auto_scanner.py:783` — `if now_peru.minute % 5 != 0: return`. היא נקראת כל דקה מ-`run_scan:547` אבל **יוצאת מיד** ב-4 מתוך 5 דקות. הדוקסטרינג שלה (`:771`) אומר "Runs every 5 minutes during market hours". גם part1 §B.7 ("`ticker_follow_up` | כל דקה") שגוי מאותה סיבה.
בנוסף, שני תנאי-יציאה נוספים שלא תיארתי: `not is_trading_day` (`:786`) ו-`not is_market_hours` (`:788`).

**תיקון 2 — part1 §B.7 טען ש-`portfolio_live` נכתב "כל דקה". מדויק יותר: כל דקה שבה יש פוזיציה פתוחה.**
`update_portfolio_live` יוצאת מוקדם ב-`if open_pos.empty: return` (`:656-658`) אחרי סינון ל-`Status == "Open"` ולחלון 7 הימים האחרונים (`:649-651`). אין כתיבה כשאין פוזיציות.

**תיקון 3 — part3 §9.3 מנה את `dashboard.live_trades_page()` כקוד מת, ולא ציינתי שהוא מכיל את היחיד שקורא ל-`archive_live_trades`.**
`sheets_manager.archive_live_trades` (`:690`, ~40 שורות עם חוזה-בטיחות מפורש שמעלה חריגה) — הקורא היחיד שלו הוא `dashboard.py:3321`, בתוך עמוד בלתי-נגיש. כלומר גם הפונקציה הזו למעשה לא נורית.

**תיקון 4 — part2 §3.1 תיאר את `_df_to_sheet` של `gsheets_sync` כ"המנוע המשותף". הוא לא משותף.**
יש **שני** מימושים נפרדים עם סמנטיקה הפוכה: `auto_scanner.df_to_sheet` (`:97-100`) מנקה לפני הכתיבה, `gsheets_sync._df_to_sheet` (`:110-131`) מצהיר במפורש שהוא לא. הראשון משמש את `portfolio_live`, `live_trades`, `daily_summary`, `daily_snapshots`, `portfolio`; השני את מסלולי ה-dashboard.

**תיקון 5 — part3 §10.4 F5 הציג את `resolve_whipsaw` כשאלה פתוחה על "איך הוא פותר whipsaw". התשובה כוללת עובדה שלא ציפיתי לה: אין לו קורא בפרודקשן.**
אימות: `grep -rn "resolve_whipsaw"` על כל הריפו (ללא backups/project_sync) מחזיר את ההגדרה, אזכור בדוקסטרינג של `intraday_cache.py:14`, ו-7 טסטים. אפס קריאות בקוד רץ. מה שכן חי הוא **התוצר** שלו — `whipsaw_verdicts.json`, תצלום מ-12/06.

**תיקון 6 — part2 §5.3 טען שכשל-ספק "לא מתפשט, נרשם ל-log בלבד". ב-`sync_score_tracker` זה חמור יותר ממה שתיארתי.**
שם הכשל לא רק לא מתפשט — הוא **גם לא נרשם**. שישה `except Exception: pass` (`:1225`, `:1230`, `:1234`, `:1237`, `:1242`, `:1247`) בולעים בלי `print`, והשורה נכתבת לגיליון עם ערכי-ברירת-המחדל.

### 4.2 — כפילויות SSoT (המשך המספור מ-16)

**17. שני מימושי `df_to_sheet` עם סמנטיקת-בטיחות הפוכה.** `auto_scanner.py:97-100` (clear→update) מול `gsheets_sync.py:110-131` ("never clears before writing").

**18. `calculate_pnl_pct` מוכפל 3 פעמים ב-`update_live_trades`.** `auto_scanner.py:1065`, `:1069`, `:1073` — כל שלושתם `(entry − exit)/entry × 100`, שהוא בדיוק `formulas.calculate_pnl_pct(entry, exit, is_short=True)` (`formulas.py:529`). הפונקציה לא מיובאת ל-`auto_scanner`.
(מצטבר עם part2 §2.2: אותה נוסחה מוכפלת גם 4 פעמים ב-`dashboard.py` — `:914`, `:2117`, `:2125`, `:2127` — ופעם ב-`position_manager.py:257`. **סה"כ 8 מופעים inline** של נוסחה שקיימת ב-formulas.)

**19. חישוב TP/SL מוכפל ב-4 מקומות.** `auto_scanner.py:684-685` · `auto_scanner.py:1114-1115` · `decision_logic.py:147-148` · `utils.classify_trade:573-574`. שני האחרונים מעגלים ל-4 ספרות; `decision_logic` לא מעגל בכלל את הביטוי לפני `round` הסופי.

**20. לוגיקת "SL גובר על TP" מוכפלת ב-3 מקומות.** `auto_scanner.py:728-733` (`"SL ❌"`) · `auto_scanner.py:1062-1069` (`"SL"`) · `utils.classify_trade:588-593` (מחזירה `WHIPSAW`). **שלוש התנהגויות שונות לאותו מצב:** שתי הראשונות מכריעות לטובת SL, השלישית מסרבת להכריע.

**21. שתי פונקציות `trading_days_after`.** `sheets_manager.py:673` (בשימוש ב-`auto_scanner:1174`) ו-`utils.get_trading_days_after` (`utils.py:215`, בשימוש ב-`backfill_ohlc_v2:40`).

### 4.3 — קוד מת חדש

| מה | היקף | ראיה |
|---|---|---|
| `utils.resolve_whipsaw` | 43 שורות (`:640-682`) | אפס קוראים בפרודקשן; רק טסטים |
| `sheets_manager.archive_live_trades` | ~40 שורות (`:690-730`) | הקורא היחיד הוא `dashboard.py:3321` בתוך `live_trades_page()` הבלתי-נגישה |
| `gsheets_sync.save_timeline_to_sheets` | no-op (`:170-173`) | (מ-part3) מחזירה `True` בלי לכתוב |

**קוד מת מצטבר על פני ארבע הריצות: ~1,730 שורות.**

---

## 5. הספירה הסופית

### 5.1 — המצטבר

| ריצה | קבצים חדשים | שורות חדשות |
|---|---|---|
| part1 | 24 | ~13,000 |
| part2 | +10 | +3,500 |
| part3 | +34 | +5,900 |
| **part4** | **+0 חדשים · 4 הושלמו** | **+2,400** |
| **סה"כ** | **~68 מתוך 145** | **~24,800 מתוך ~48,000 (≈52%)** |

part4 לא פתח קובץ חדש — הוא **השלים** ארבעה שנקראו חלקית: `auto_scanner.py` (5 פונקציות, ~780 שורות), `monthly_rotation.py` (`_copy_open_portfolio`, 57 שורות), `utils.py` (3 בלוקים, ~210 שורות), ובדרך גם `whipsaw_verdicts.json` + `metrics_bounds.resolved_class` + `sheets_manager.archive_live_trades`.

### 5.2 — ההצהרה

**לא נשאר קוד בנתיב ההחלטה שלא נקרא.**
השרשרת `timeline_live → _signal_from_timeline_row → sentinel.check_signal (7 בדיקות) → data_quality.validate → score_calculator → decision_logic._check_filters (11 פילטרים + 2 observers) → tradability → decision_logger → order_manager → alpaca_broker → position_manager → postmortem_engine` נקראה במלואה, פונקציה-פונקציה, על פני part1 ו-part3.

**לא נשאר קוד בנתיב הכתיבה החי שלא נקרא.**
כל טאב שנכתב אליו בפרודקשן, והכותב שלו:

| טאב | הכותב | נקרא |
|---|---|---|
| `timeline_live` | `run_scan:442-478` | part1 |
| `daily_snapshots` | `run_scan:487-500` · `gsheets_sync.save_snapshot_to_sheets` | part1 · part3 |
| `portfolio` | `run_scan:503-525` · `run_eod:1378` · `gsheets_sync.save_portfolio_to_sheets` | part1 · **part4** · part3 |
| `daily_summary` | `_save_daily_summary:571-624` | part1 (חלקי) · **part4** |
| `portfolio_live` | `update_portfolio_live:755` | **part4** |
| `ticker_follow_up` | `update_ticker_follow_up:989/991` | **part4** |
| `live_trades` | `update_live_trades:1143` · `dashboard:3327` (מת) | **part4** |
| `score_tracker` | `sync_score_tracker:1289/1293` | **part4** |
| `post_analysis` | `post_analysis_collector` · `enrich_post_analysis` · `backfill_ohlc_v2` | part1 · part3 |
| `decision_log` | `decision_logger.log:349-355` | part3 |
| `paper_portfolio` | `order_manager._write_to_portfolio:248` · `position_manager._update_position` | part3 · part1 |
| `postmortems` | `postmortem_engine.generate` | part3 (מיפוי-טריגר) |
| `skip_summary` | `flush_skip_summary:171` | part3 |
| `shadow_gate_events` | `flush_shadow_gate_summary:264` | part3 |
| `sentinel_events` | `_log_sentinel_event:30` | part3 |
| `system_events` | `orchestrator_eod._system_events_alert:129` · `_data_loaders.log_emergency_stop:222` | part3 |
| `borrow_data` / `borrow_coverage` | `borrow_collector:153/125` | part3 |
| `market_context` | `market_context_v1.write_context` | part3 |
| `weekly_summary` / `monthly_summary` | `critic_v1.write_weekly_summary:422` / `write_monthly_summary:399` | part3 |
| `agent_scorecard` | `critic_v1.write_scorecard:624` | **לא נקרא** — F6 של part3, מחוץ להיקף |
| `pending_suggestions` | `_data_loaders.update_suggestion_status:179` | part3 |
| `score_analytics` | `score_analytics._write_*` | part3 (מסלול-הכתיבה לא מגיע — n=0) |
| Health-Audit (3 טאבים) | `health_audit.write_to_sheet:1825` | part2 |
| `live_trades_archive` | `sheets_manager.archive_live_trades:690` | **part4** (ומת) |
| `news_findings` | `news_detective.write_findings` | **לא נקרא** — הסוכן כבוי (`config.py:364`) |

שני החריגים היחידים בטבלה מסומנים מפורשות: `write_scorecard` (F6, מחוץ להיקף שהגדרת) ו-`news_detective.write_findings` (הסוכן כבוי מאז 01/07).

### 5.3 — מה נשאר לא-נקרא, ולמה

| מה | שורות | הנימוק |
|---|---|---|
| גוף 8 עמודי `dashboard.py` הוותיקים | ~4,000 | **מחוץ להיקף** — הוגדר מפורשות |
| גוף 20 בדיקות `health_audit.py` | ~1,200 | **מחוץ להיקף** — הוגדר מפורשות (החתימות, הספים והחומרות כן נקראו ב-part2) |
| `tests/` פרטני | 10,101 | **מחוץ להיקף** — הוגדר מפורשות |
| `scripts/` (10 קבצים) | ~1,900 | **מחוץ להיקף** — הוגדר מפורשות |
| `scripts/overnight/` (3 קבצים) + `tests/overnight/` | ~570 | **מחוץ להיקף** — רץ-הלילה נוטרל 02/07 |
| כלי-שורש חד-פעמיים (23 קבצים: `code_auditor`, `deep_scan`, `daily_audit`, `drop_analysis`, `enrich_data`, `metric_quality_analysis`, `morning_health_check`, `score_backtest`, `score_distribution`, `setup_*`, `smoke_test_*`, `sync_pk_to_sheet`, `validate_providers`, `check_sync`, `apply_text_format_v1`, `backfill_fundamentals`, `get_oauth_token`, `generate_project_state`, `test_position_sync_v1`) | ~5,200 | **מחוץ להיקף** — part2 §8.2 |
| `critic_v1.unified_positions` (`:673-822`) · `build_monthly_detail` (`:315-398`) · `write_scorecard` (`:624-672`) | ~300 | **מחוץ להיקף** — F1/F6 של part3 §10.4 |
| `market_context_v1._derive_regime` (`:98-108`) | 11 | **מחוץ להיקף** — F3 של part3 |
| `order_manager` קבועי-הריטריי (`:1-108`) | ~50 | **מחוץ להיקף** — F7 של part3 |
| `post_analysis_collector.fetch_d0_and_fundamental` (`:256`) · `fetch_timeline_stats` (`:333`) · גוף `run` (`:389`) | ~260 | לא הוגדר בהיקף של אף אחת מארבע הריצות |
| `backups/` · `project_sync_20260418/` · `research/` | ~49,700 | ארכיון — **מחוץ להיקף** מהריצה הראשונה |

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
