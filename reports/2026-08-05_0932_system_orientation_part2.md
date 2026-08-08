# RidingHigh Pro — היכרות עם המערכת, חלק ב'

**מסמך תיאורי בלבד.** אין תוכנית, אין המלצות, אין דירוג, אין תיקונים.
נכתב 2026-08-05 09:32 Lima (10:32 EDT NY). המשך ישיר ל-`reports/2026-08-05_0853_system_orientation.md`.
מטרה: לסגור את הרבע שלא נקרא בדוח הראשון.

**סקילים:** נטען `rhpro-live` (`~/.claude/skills/rhpro-live/SKILL.md`, 180 שורות).
`ls ~/.claude/skills/`: anthropic-skills · backtest-expert · biotech-screener · data-quality-checker · position-sizer · rhpro-live · rhpro-session · signal-postmortem · time-check · trader-memory-core.

**כלל שנשמר לאורך הדוח:** לכל קביעה יש `file:line`. איפה שלא קראתי — כתוב במפורש "לא קראתי".

---

## 1. `health_audit.py` (2,079 שורות)

### 1.1 — המבנה

30 בדיקות, נקראות בזו אחר זו ב-`main()` (`health_audit.py:2006-2047`). כל בדיקה מחזירה
`CheckResult(check_id, name, category, status, message, details)` (`:241-267`).

ארבע דרגות חומרה (`:80-83`): `🔴 CRITICAL` · `🟠 WARNING` · `✅ PASSED` · `🔵 INFO`.

### 1.2 — 30 הבדיקות

| ID | שם | מה בודקת | מקור הנתון | סף | חומרה מרבית |
|---|---|---|---|---|---|
| C1 | Duplicate functions | פונקציה שמוגדרת ב-2+ קבצים בשורש | `REPO_ROOT.glob("*.py")` `:276` | כל כפילות; whitelist: `calculate_score`, `run`, `now_peru` `:309` | WARNING `:318` |
| C2 | Hardcoded thresholds | ספים קשיחים שהיו צריכים להיות ב-config, AST על צמתי Compare | קוד `:322-330` | — | WARNING `:410` |
| C3 | Imports consistency | ש-`dashboard.py` מייבא מ-`formulas`/`config` | קוד `:415` | — | WARNING `:436` |
| D1 | Timeline freshness | גיל השורה האחרונה ב-timeline_live | `_ha_col_values(timeline_live, 1)` `:457` | ≤1d PASS · ≤3d WARN · >3d **CRITICAL** `:474-484` | CRITICAL |
| D2 | Post-analysis completeness | האם יש שורות לכל יום-מסחר אחרון | post_analysis `:491` | — | — |
| D3 | GitHub Actions health | אחוז הצלחה ב-24ש' | GitHub API `:631` | ≥95% PASS · ≥80% WARN · אחרת CRITICAL — **מורד ל-WARNING** אם מדגם קטן (`GHA_SAMPLE_MIN`) או אם כל workflow כושל התאושש `:616-622` | CRITICAL |
| D4 | Post-analysis ran today | האם `post_analysis.yml` רץ בהצלחה היום (גלאי cron-drift) | GitHub API `:662` | — | — |
| Q1 | Score range | כל Score ב-[0,100] | post_analysis `:750` | ערך מחוץ לטווח = **CRITICAL** `:776` | CRITICAL |
| Q2 | Schema contract | כותרות חיות מול `SCHEMA.json` | `_load_schema_contract()` `:784` + הגיליונות | — | — |
| Q3 | Duplicate post_analysis rows | כפילות (Ticker, ScanDate) | post_analysis `:877` | — | — |
| Q4 | Outliers | `REL_VOL > 100` או `ScanPrice ≤ 0` | post_analysis `:924` | REL_VOL>100 `:944` · price≤0 `:957` | WARNING `:975` |
| Q5a | REL_VOL Sanity | האם REL_VOL "תקוע" על 1.0 | 200 שורות אחרונות `_load_recent_metrics` `:1132` | שונות <0.01 **וגם** ‖ערך−1.0‖<0.01 → **CRITICAL** `:1167` | CRITICAL |
| Q5b | Float% stuck | אותו דפוס ל-Float% | שם | — | WARNING (מפורש בדוקסטרינג `:1182` — Float% לא ב-Score v2) |
| Q5c | Gap outliers | Gap > 500% | שם | 500% `:1204` | WARNING |
| Q(29) | Interday artifacts | קפיצת close-to-close חשודה (split/halt) | post_analysis `:1252` | `formulas.is_interday_artifact` (100%) | advisory |
| Q(30) | Lineage sentinel | מחשב-מחדש שורה אקראית מיושבת מקצה-לקצה ומשווה למאוחסן | post_analysis `:1339` | סטייה > `_LINEAGE_TOL = 0.01` `:1279` | WARNING (recompute-drift) |
| Q8 | NaN ScanTime | המחרוזת `'nan'` בעמודות FirstScanTime/LastScanTime | post_analysis `:1618` | — | — |
| S1 | Sentinel health | קבצים, קונפיג ואירועים אחרונים של ה-Sentinel | sentinel_events `:1557` | — | — |
| A1 | Critic agent | האם רץ ביום-המסחר האחרון | `_check_agent_freshness` `:1483` | `_last_expected_trading_day()` `:1468` | — |
| A2 | Market Context agent | שם | market_context | שם | — |
| A3 | News Detective agent | שם | news_findings | שם | — |
| X1 | sheets_config current month | שהחודש הנוכחי קיים ב-`sheets_config.json` | קובץ `:986` | — | — |
| X2 | Score weights sum | ש-`SCORE_WEIGHTS_V2` מסתכם ל-100 (או 1.0) | `config.py` `:1008` | — | — |
| X3 | Critical files | שכל הקבצים הקריטיים קיימים | FS `:1041` | — | — |
| AS1 | Agent sheets complete | שלחודש הפעיל יש את כל טאבי-הסוכן | `sheets_config.json` `:1952` | — | — |
| R1 | Uncommitted files | ספירת `git status --porcelain` | git `:1063` | 0 PASS · ≤5 INFO · ≤15 WARN · >15 **CRITICAL** `:1071-1082` | CRITICAL |
| R2 | gitignore enforcement | קבצים בעץ שהיו אמורים להיות מוחרגים | FS `:1439` | — | — |
| P1 | Fundamentals provider | שהספק מחזיר דאטה תקין לטיקר ידוע | yfinance `:1372` | — | — |
| P2 | Daily bars provider | שהספק מחזיר OHLC תקין לטיקר ידוע | Alpaca `:1404` | — | — |
| S1(19) | PK sync | שהריפו מסונכרן מול origin/main + עקביות docs | git + `_check_docs_consistency()` `:1687`, `:1752` | — | — |

### 1.3 — מה קורה בכשל

**שלושה ערוצי-פלט, שלושתם תמיד:**

1. **מסך** — `print_report(results)` (`:1785`), נקרא תמיד `:2049`.
2. **Google Sheets** — `write_to_sheet(results, gc)` (`:1825`), אלא אם `--no-sheet`. כותב לגיליון `RidingHigh-Health-Audit`, מזהה מ-`.health_audit_sheet_id` (`:1832`, הקובץ ב-.gitignore). שלושה טאבים: **History** (append כל 30 השורות, `:1841`) · **Latest** (clear + כתיבה מלאה, `:1845-1849`) · **Failed** (clear + רק כשלים, `:1852-1856`).
3. **מייל** — `send_email_alert(results)` (`:1871`), **heartbeat mode: תמיד נשלח** (`:1888`), גם כשהכל ירוק. הנושא משתנה לפי החומרה: 🔴 CRITICAL / 🟡 WARNING / ✅ All clear (`:1889-1894`). דורש `GMAIL_USER`, `GMAIL_APP_PASS`, `REPORT_TO`; בלעדיהם מדלג בשקט (`:1878-1880`).

**קוד יציאה:** `CRITICAL → exit 1` (`:2066`). **WARNING → exit 0** במפורש — ההערה ב-`:2055-2059` מסבירה שאזהרות הן מצב בריא-ותקין (בעיות פתוחות מופיעות כאזהרות עד שנפתרות), וש-v2 החזיר 2 מה שגרם ל-GitHub Actions לסמן כשל-שווא בכל ריצה.

**אף בדיקה לא מעלה חריגה ואף אחת לא עוצרת שום דבר.** זו שכבת דיווח בלבד — היא לא חוסמת מסחר, לא עוצרת workflow אחר, ולא משנה קונפיג.

### 1.4 — מה הבדיקות *לא* מכסות

שלושת הפערים המפורשים הם בדיוק **TASK-252** הפתוח ("Three missing health checks: symbol sanity, position over HOLD, row count"):

| מה חסר | מה יש במקומו |
|---|---|
| **ולידציית סימבול** | אין. `formulas.classify_phantom_tier` (`formulas.py:441`) קיים ומזהה טיקרים כפולי-אות, אבל **אף בדיקת-בריאות לא קוראת לו.** אימות: `grep classify_phantom_tier health_audit.py` → אפס תוצאות. הטיקרים המשובשים של יולי היו עוברים את כל 30 הבדיקות. |
| **גיל פוזיציה** | אין. אף בדיקה לא סופרת פוזיציות `DRY_RUN_OPEN` ולא מודדת כמה זמן הן פתוחות. 83 הפוזיציות התקועות (TASK-246) לא מפעילות שום דגל. |
| **ספירת שורות** | חלקית בלבד. D1 בודק את **גיל** השורה האחרונה ב-timeline_live, לא את **מספר** השורות. הצניחה של 50% בנפח הסריקה מ-15/07 (TASK-245) לא הפעילה שום בדיקה, כי השורה האחרונה תמיד היתה טרייה. |

פערים נוספים שראיתי: אין בדיקה שסופרת ENTER-ים ליום, אין בדיקה על מגבלת ה-re-entry, ואין בדיקה שמשווה `decision_log` ל-`paper_portfolio` (זה TASK-49 הפתוח).

---

## 2. `dashboard.py` (5,330) + `agent/dashboard/` (1,632)

### 2.1 — 12 העמודים ומאיפה כל אחד קורא

הניווט: `st.sidebar.radio` על `_PAGE_NAMES` (`dashboard.py:5263-5282`), ה-dispatch ב-`:5304-5327`.

| עמוד | פונקציה | מאיזה טאב |
|---|---|---|
| 🏠 Home | `dashboard_home_page()` `:5121` | מצרפי — `_cached_*` |
| 💼 Portfolio Tracker | `portfolio_tracker_page()` `:2240` | `post_analysis` + `portfolio` |
| 🔬 Post Analysis | `post_analysis_page()` `:2345` | `post_analysis` (`_cached_post_analysis` `:1044`) |
| 📈 Score Tracker | `score_tracker_page()` `:2900` | `score_tracker` |
| 📅 Daily Summary | `daily_summary_page()` `:1587` | `daily_summary` (`:1142`) |
| 📦 Timeline Archive | `timeline_archive_page()` `:1681` | `timeline_live` (`:982`) |
| 🖥️ System Overview | `system_overview_page()` `:3776` | מטא — קוד + קונפיג |
| 🤖 Live Agent | `render_live_agent()` — `agent/dashboard/live_agent_page.py:43` | `paper_portfolio` + `decision_log` + `market_context` |
| 📊 Trade History | `render_trade_history()` — `trade_history_page.py` | `decision_log` (`:44`) |
| 🧠 Score Brain | `render_score_brain()` — `score_brain_page.py:37` | `score_analytics` + `pending_suggestions` |
| 🛡️ Sentinel Events | `render_sentinel_events()` — `sentinel_events_page.py` | `sentinel_events` (`:32`) |
| 🏆 דירוג סוכנים | inline `:5044` | `agent_scorecard` |

עמודים שהוסרו מהניווט אך הפונקציה קיימת: `score_comparison_page()` (`:3450`) ו-`live_trades_page()` (`:3280`) — לא מופיעים ב-`_PAGE_NAMES` וב-dispatch. **לא בדקתי אם הם נקראים מאיפשהו אחר.**

### 2.2 — איפה ה-dashboard מחשב מטריקה בעצמו

הוא **כן** מייבא מ-`formulas` (`:49-61`: `calculate_mxv`, `calculate_runup`, `calculate_atrx`, `validate_atrx`, `calculate_gap`, `calculate_vwap_dist`, `calculate_rel_vol`, `calculate_float_pct`, `normalize_mxv`, `normalize_atrx`, `fmt_rate_ci`) ומ-`utils` (`:63-69`: `classify_trade` וכו'). ובכל זאת מחשב inline במקומות האלה:

| שורה | מה מחושב inline | הנוסחה הקנונית |
|---|---|---|
| `dashboard.py:305` | `change = ((current.close − previous.close)/previous.close)*100` | `formulas.calculate_scan_change:250` — **לא מיובא כלל** |
| `dashboard.py:386` | `price_to_high` | `formulas.calculate_price_to_high:216` — **לא מיובא** |
| `dashboard.py:392` | `price_to_52w_high` | `formulas.calculate_price_to_52w_high:234` — **לא מיובא** |
| `dashboard.py:413` | `change` שוב | שם |
| `dashboard.py:566` | `price_to_high` שוב (מסלול שני) | שם |
| `dashboard.py:572` | `price_to_52w_high` שוב | שם |
| `dashboard.py:597` | `change` שוב (מסלול שני) | שם |
| `dashboard.py:914` | `change_pct = ((current−buy)/buy)*100` | `formulas.calculate_pnl_pct:529` |
| `dashboard.py:2117`, `:2125`, `:2127` | `pnl = shares*(entry−current)` — שלוש פעמים באותו בלוק | `formulas.calculate_pnl_pct:529` |
| `dashboard.py:2187` | `win_rate = wins/total*100` | `formulas.fmt_rate_ci:661` מיובא — ולא בשימוש כאן |
| `dashboard.py:2342` | `(n_win+r_win)/denom*100` | שם |
| `dashboard.py:2368` | `CurrentChange% = ((CurrentPrice−ScanPrice)/ScanPrice)*100` | `formulas.calculate_scan_change` |
| `dashboard.py:3046`, `:3266` | `(cur−scan)/scan*100` | שם |
| `dashboard.py:3256` | `drop_pct = (final_score−peak_score)/peak_score*100` | אין מקבילה — ייחודי ל-dashboard |
| `dashboard.py:3359` | `Change% = ((CurrentPrice−EntryPrice)/EntryPrice)*100` | `formulas.calculate_pnl_pct` |
| `dashboard.py:1928` | `_is_day_complete` | `utils.is_day_complete:166` — **זה TASK-222 הפתוח** |

**כן** משתמש נכון ב-formulas: `calculate_float_pct` (`:406`, `:586`), `calculate_net_pnl` (`:2407`, `:2423`, `:2424`, `:2432`), `classify_trade` (מיובא `:67`).

### 2.3 — היחס בין הקובץ היחיד ל-5 קבצי-העמוד

`dashboard.py:112` — `from agent.dashboard import render_live_agent, render_trade_history, render_score_brain, render_sentinel_events`. הייבוא הוא **ברמת-המודול, לא עצל** — כלומר בכל טעינה של ה-dashboard נטענים כל 5 הקבצים ב-`agent/dashboard/` (`__init__.py:12-15`).

`agent/dashboard/_data_loaders.py` (247 שורות) הוא שכבת-הקריאה המשותפת של ארבעת עמודי-הסוכן — `_get_worksheet()` (`:36`) עוטף את `sheets_manager.get_worksheet` (`:40`).

זה סותר חלקית את **ADR-008** ("קובץ dashboard יחיד, לא Streamlit pages") — ההחלטה נשמרת ל-8 העמודים הוותיקים ולא ל-4 עמודי-הסוכן.

### 2.4 — האם ה-dashboard כותב ל-Sheets

**כן, בשישה מקומות.** זו לא ממשק לקריאה בלבד:

| שורה | הכתיבה |
|---|---|
| `dashboard.py:747` | `save_snapshot_to_sheets(df)` — שמירת snapshot ידנית מכפתור בסיידבר |
| `dashboard.py:785` | `save_timeline_to_sheets(archive_df, today)` — ארכוב timeline |
| `dashboard.py:882` | `save_portfolio_to_sheets(combined_df)` — הוספת פוזיציות ל-portfolio |
| `dashboard.py:3326-3327` | `ws.clear()` ואז `ws.update("A1", ...)` על **live_trades** — מוחק את הגיליון וכותב מחדש רק את הפתוחות, אחרי `archive_live_trades` |
| `agent/dashboard/_data_loaders.py:179-194` | `update_suggestion_status()` — כותב ל-`pending_suggestions` |
| `agent/dashboard/_data_loaders.py:222-228` | `log_emergency_stop()` — כותב שורת `EMERGENCY_STOP_REQUESTED` ל-`system_events`. **זה המנגנון שעוצר את הסוכן** (`agent/orchestrator.py:165`) |

בסיידבר יש גם כפתורי "Scan Now" (`:1327`) ו-"Daily snapshot" (`:1343`) שמריצים את הסקאנר ישירות מה-UI.

---

## 3. `agent/critic/critic_v1.py` (942) + 3 האורקסטרטורים

### 3.1 — מה ה-Critic מחשב ומאיפה

`review_completed_trades()` (`:79`) קורא **שני** טאבים: `paper_portfolio` (`:90`) ו-`decision_log` (`:114`), ומצליב לפי `PositionID → DecisionID` (`:122-124`, `:157`).

מסנן רק שורות שה-Status שלהן ב-`_CLOSED_STATUSES` (`:140`). הפסיקה (`:145-151`):
```
pnl > 0  → WIN
pnl < 0  → LOSS
pnl == 0 → FLAT
```
ומצרף לכל עסקה את מדדי-הכניסה מ-decision_log: Score, MxV, RunUp, ATRX, FloatPct (`:158-162`).

`summarize()` (`:188`) מייצר שתי קבוצות במקביל — `all` ו-`clean` (בלי `DataQuality="PRE_FIX"`, `:218`). לכל קבוצה: total, wins, losses, flat, win_rate, avg_win_pct, avg_loss_pct (`:212-217`).

`daily_facts()` (`:445`) קורא **ארבעה** טאבים, אחד לכל סוכן:
1. `decision_log` (`:477`) — The Trader
2. `sentinel_events` (`:516`) — Data Sentinel
3. `market_context` (`:537`) — Market Context
4. `news_findings` (`:561`) — News Detective

ואז מריץ גלאי-חריגות (`:577`). `write_scorecard()` (`:624`) כותב ל-`agent_scorecard` (`:648`).

### 3.2 — האם משתמש ב-formulas

**לא. אפס.** `grep "from formulas\|import formulas\|calculate_" agent/critic/critic_v1.py` → **אפס תוצאות.**

הוא מחשב הכל בעצמו:
- `win_rate = round(len(wins)/total*100, 1)` (`:212`) — במקום `formulas.fmt_rate_ci:661` (שמוסיף Wilson CI)
- `avg_win_pct = sum(win_pcts)/len(win_pcts)` (`:213`)
- ה-verdict נגזר מסימן ה-PnL (`:145-151`) — **לא** מ-`utils.classify_trade:513`

זה אומר שיש **שתי הגדרות שונות של "ניצחון" במערכת**: `utils.classify_trade` (TP/SL day-by-day, מייצר WIN/LOSS/WHIPSAW/NO_TOUCH/PENDING) מול ה-Critic (סימן PnL, מייצר WIN/LOSS/FLAT). ל-Critic אין קטגוריית WHIPSAW בכלל. **את ההשלכה על המספרים לא מדדתי** — היא דורשת דאטה חי.

### 3.3 — ההבדל בין שלושת האורקסטרטורים

| קובץ | שורות | cron | מה עושה |
|---|---|---|---|
| `orchestrator_critic.py` | 117 | `0 22 * * 1-5` = 17:00 Peru | `write_scorecard()` + `unified_positions()` — טבלת-עמדות חוצת-סוכנים, רישום קונפליקטים (docstring `:5-8`) |
| `orchestrator_critic_weekly.py` | 78 | `0 23 * * 5` = שישי 18:00 | `build_weekly_row` → `write_weekly_summary` → `render_weekly_email` → שליחה (docstring `:12-14`) |
| `orchestrator_critic_monthly.py` | 88 | `0 6 1 * *` = 1 לחודש 01:00 | אותו רצף על החודש **הקודם** (docstring `:8`) |

ההפרדה היא החלטת-מוצר נעולה, מנומקת בשלושה נימוקים בדוקסטרינג של השבועי (`orchestrator_critic_weekly.py:4-9`): השבועי רץ שעה **אחרי** היומי כדי שכל 5 ימי-המסחר עובדו; כשל בשבועי לא נוגע ביומי ולהפך; ושלושה מיילים נפרדים.

שניהם שולחים **רק אם היו עסקאות** באותה תקופה — "no empty weekly spam" (`orchestrator_critic_weekly.py:14`).

⚠️ **דריפט תיעוד-מול-קוד:** הדוקסטרינג של `orchestrator_critic.py:4` אומר "Triggered by GitHub Actions at 19:00 Peru (00:00 UTC+1)". ה-cron ב-`agent_critic.yml:8` הוא `0 22 * * 1-5` = **17:00 Peru**. הקוד מנצח.

⚠️ **המייל היומי לא בא מכאן.** `orchestrator_critic.py` כותב scorecard ולא שולח מייל; המייל היומי מגיע מ-`agent/orchestrator_email_daily.py` דרך `agent_email_daily.yml` ב-16:30. שני workflows שונים.

---

## 4. `sheets_manager.py` (732) + `agent/utils/sheets_cache.py` (171)

### 4.1 — איך נפתר גיליון-חודש לקובץ

```
get_worksheet(tab, month=None)                 sheets_manager.py:605
 └─ month = now(Peru).strftime("%Y-%m")  אם None   :613
 └─ get_sheet_id(tab, month)                       :615 → :361
      └─ _load_config()  — קורא sheets_config.json  :369
      └─ אם (month, tab) בקונפיג → מחזיר id         :370-371
      └─ אחרת _ensure_month(month) — יוצר גיליונות  :373 → :329
 └─ gc.open_by_key(sheet_id)                       :624   ← קריאת API
 └─ spreadsheet.worksheet(tab)                     :626
 └─ אם הטאב לא קיים → spreadsheet.sheet1           :628   ← נפילה שקטה
```

**שתי נקודות מהותיות:**
1. `gc.open_by_key()` בשורה `:624` הוא **קריאת API שלמה, בלי קאש**. כל `get_worksheet()` = קריאה אחת ל-Google.
2. הנפילה ל-`sheet1` בשורה `:628` היא **שקטה** — אם הטאב המבוקש חסר, הקוד כותב/קורא מהטאב הראשון בלי אזהרה. זה בדיוק מה ש-TASK-251 מתאר לגבי live_trades של אוגוסט.

### 4.2 — הקאש

**קאש אחד בלבד, בזיכרון-התהליך:**
- `_sheet_values_cache = {}` — מפתח `(tab_name, month)`, ערך `(timestamp, rows)` (`:392`)
- **TTL = 60 שניות** (`_SHEET_CACHE_TTL`, `:391`)
- מוגש דרך `get_sheet_values()` (`:446`) ו-`get_sheet_records()` (`:468`, שהוא עטיפה מעל הראשון)
- `invalidate_cache(tab, month)` (`:477`) — למחיקה אחרי כתיבה
- ספירת פגיעות: `record_read()` נקרא **רק בפספוס** (`:451`), ולכן `get_read_counts()` מודד קריאות-API אמיתיות

**תוחלת חיים אפקטיבית: ריצה אחת.** הקאש הוא `dict` גלובלי בתהליך; כל ריצת GitHub Actions היא תהליך חדש. בין ריצות דקתיות — אפס שיתוף.

⚠️ **`agent/utils/sheets_cache.py` הוא קוד מת.** 171 שורות שמממשות `TTLCache` ו-`SheetsCache` עם קאש-קריאה + תור-כתיבה מקובץ. אימות: `grep -rn "sheets_cache\|SheetsCache\|TTLCache"` על כל הריפו (בלי backups/research) → **התוצאות היחידות הן ההגדרות בתוך הקובץ עצמו**. אפס מייבאים, אפילו לא טסט.

**קאש שני, נפרד:** `health_audit._ha_cached_read` (`health_audit.py:1092`) עם `_HA_CACHE_TTL_SEC = 600` (`:1089`) ו-`retries=5`. הוא לא מדבר עם הקאש של `sheets_manager`.

### 4.3 — כל נתיב שקורא ל-Sheets בלי קאש

**א. כל `get_worksheet()` — 54 קריאות ב-`agent/` + השורש.** כל אחת = `open_by_key`.
דוגמאות בנתיב הדקתי החם:
- `agent/orchestrator.py:345` — `get_worksheet("timeline_live")`, ואז **בנוסף** `get_sheet_records("timeline_live")` בשורה `:350`. שתי גישות לאותו טאב באותה פונקציה, הראשונה רק כדי לבדוק `is None`.
- `agent/orchestrator.py:651` — `get_worksheet("paper_portfolio")` בכל ריצה
- `agent/sentinel/data_sentinel.py:58` — `get_worksheet("sentinel_events")` בכל אירוע נרשם

**ב. `get_all_records()` / `get_all_values()` ישירים — עוקפים את הקאש לגמרי:**

| קובץ:שורה | מה |
|---|---|
| `agent/orchestrator.py:635` | `_read_decision` — `ws.get_all_records()` לכל postmortem |
| `agent/orchestrator.py:652` | `_portfolio_ws.row_values(1)` |
| `agent/orchestrator.py:466` | `ws.col_values()` — מסלול-גיבוי ב-batch writer |
| `agent/execution/position_manager.py:191` | `ws.get_all_records()` |
| `agent/execution/reconciler.py:290` | `ws.get_all_records()` |
| `agent/perception/borrow_collector.py:142`, `:171` | `get_all_values()` ×2 |
| `agent/orchestrator_email_daily.py:63`, `:83`, `:161` | ×3 |
| `agent/orchestrator_email_morning.py:45`, `:57` | ×2 |
| `agent/orchestrator_eod.py:59` | `get_all_values()` |
| `agent/critic/critic_v1.py:928` | `get_all_records()` |
| `agent/setup/create_agent_sheets.py:330` | `gc.open_by_key(...).sheet1.row_values(1)` — בלולאה על 16 טאבים |
| `agent/dashboard/_data_loaders.py:70`, `:90`, `:148`, `:167` | ×4 |
| `agent/dashboard/trade_history_page.py:47`, `sentinel_events_page.py:35` | ×2 |
| `auto_scanner.py:492`, `:506`, `:612`, `:642`, `:662`, `:839`, `:1022`, `:1169`, `:1287`, `:1331`, `:1355` | **11 קריאות לא-מקושרות** בקובץ הסקאנר לבדו |
| `sheets_manager.py:545`, `:592` | `col_values()` בתוך dedup של append |

**ג. `get_sheet_values` עצמו** קורא `_with_retry(get_worksheet, ...)` בפספוס (`:459`) — כלומר גם המסלול המקושר משלם `open_by_key` בכל פספוס.

### 4.4 — retry ו-backoff

```python
_RETRY_MAX = 3                sheets_manager.py:383
_RETRY_BACKOFF_BASE = 2       :384      →  המתנות 2s, 4s (2 המתנות ב-3 ניסיונות)
_APPEND_RETRY_MAX = 4         :389      →  append מקבל ניסיון רביעי
```

`_with_retry(fn, ...)` (`:401`):
- שגיאה **שאינה** quota → **raise מיידי** (`:415`, "no point retrying those")
- זיהוי quota: `_is_quota_error` (`:394`) — מחפש `429` / `quota` / `resource_exhausted` / `rate limit` במחרוזת השגיאה, case-insensitive
- במיצוי: מדפיס `all 3 retries exhausted` ואז **`raise last_error`** (`:421`) — כלומר החריגה מתפשטת לקורא

זה מסביר את התנהגות הקריסה תחת 429: `build_account_state` תופס אותה (`orchestrator.py:223-229`) ומחזיר ברירות-מחדל — וזה בדיוק השורש של TASK-244.

`_APPEND_RETRY_MAX = 4` מנומק ב-`:385-388`: כתיבת-הכניסה ל-`paper_portfolio` מקבלת ניסיון נוסף, ו-`safe_append_row` מבצע dedup לפי PositionID לפני כל ניסיון, כך שהניסיון הרביעי לא יכול לכתוב כפול.

`_track_write_quota()` (`:483`) קורא ל-`quota_health.record_write()` — התיקון של AUDIT.2 מ-2026-05-24, שבו התגלה שהמונה קיים אבל **אף אחד לא קרא לו**, ולכן `check_quota_health` תמיד החזיר ALLOW (`:485-489`).

---

## 5. שכבת הספקים — `data_provider.py` (450) + `providers/` (734)

### 5.1 — סדר ה-fallback

**ברירות מחדל** (`data_provider.py:70-74`):
```
DATA_PROVIDER          = env או "alpaca"
FUNDAMENTALS_PROVIDER  = env או "yfinance"   ← Alpaca לא חושף sharesOutstanding/floatShares
```

`get_data_provider()` (`:298`):
```
if provider == "alpaca":
    try:    AlpacaDataProvider()                    :322-324
    except: → YFinanceDataProvider()  (fallback)    :325-332
elif provider == "yfinance": YFinanceDataProvider() :333-335
else: raise ValueError                              :336-340
```

**מה מפעיל את המעבר: אך ורק כשל ב-`__init__` של AlpacaDataProvider** — חוסר credentials, ImportError של ה-SDK. **זה מכריע פעם אחת בלבד** — הספק נשמר כ-singleton (`:317-318`, `:342-343`).

⚠️ **אין fallback ברמת-הקריאה.** אם Alpaca אותחל בהצלחה ואז `get_daily_bars` נכשל, **המערכת לא עוברת ל-yfinance.** היא מחזירה DataFrame ריק. אימות: `providers/alpaca_provider.py:220-222` — `except Exception → return pd.DataFrame(columns=[...])`, ואין שם שום ניסיון-חלופה.

### 5.2 — לולאות ה-retry ב-`fetch_ohlc_for_days`

`post_analysis_collector.py:205-251`:
```
for attempt in range(1, 6):           :216   ← 5 ניסיונות
    bars = provider.get_daily_bars(ticker, days=COLLECT_DAYS_FORWARD+15, end_date=...)
    if bars.empty:  time.sleep(2); continue                       :224
    ... מיפוי D1..D25 ...
    return result                                                 :244
  except Exception:  print(...); time.sleep(2)                    :245-247
return {}                                                          :248
```

**עלות בזמן במקרה הגרוע: 5 ניסיונות × 2 שניות = 10 שניות לטיקר**, לפני `return {}`.
זה מוכפל במספר הטיקרים שהקולקטור מעבד — וזה מסביר את `timeout-minutes: 45` ב-`post_analysis.yml:19` ואת TASK-249 ("Collector reprocesses the whole month every night").

⚠️ **הלולאה לא מבחינה בין 429 לשגיאה אחרת.** בניגוד ל-`sheets_manager._with_retry` שעושה fail-fast על שגיאה שאינה quota, כאן `except Exception` תופס הכל ומנסה 5 פעמים — גם על טיקר שנמחק מהמסחר.

`n_bars = COLLECT_DAYS_FORWARD + 15` (`:223`) — 40 מוטות, מנומק ב-`:221-222` (הבאפר גדל עם אופק-האיסוף; היה 15 קבוע כשהאופק היה 5 ימים).

### 5.3 — מה מוחזר בכשל מלא

**זו הנקודה החשובה בסעיף.** כל שכבות-הספק מחזירות מבנה **תקין-למראה**, לא חריגה:

| פונקציה | בכשל | קובץ:שורה |
|---|---|---|
| `AlpacaDataProvider.get_daily_bars` | `pd.DataFrame(columns=["open","high","low","close","volume"])` — **DataFrame ריק עם עמודות נכונות** | `providers/alpaca_provider.py:220-222` |
| `AlpacaDataProvider.get_5day_ohlc` | `empty` — dict עם כל המפתחות D1..D5 ו-`None` בערכים | `providers/alpaca_provider.py:285-287` |
| `get_latest_quote` / `get_latest_bar` | `None` | `alpaca_provider.py:307-309`, `:331-333` |
| `fetch_ohlc_for_days` | `{}` — dict ריק | `post_analysis_collector.py:248` |
| `YFinance` המקבילים | אותו דפוס | `yfinance_provider.py:216-218`, `:236-238` |

**המשמעות:** קוד שקורא לספק ולא בודק `.empty` או `is None` יראה נתונים "תקינים" שהם למעשה כלום. בפועל הקוד כן בודק — `auto_scanner.py:198` (`if not hist_full.empty and len(hist_full) >= 2`), `post_analysis_collector.py:224` (`if bars.empty`). אבל השגיאה עצמה **לא מתפשטת** — היא נרשמת ל-log בלבד (`logger.warning`), ולכן כשל של ספק לא סופר כשגיאה בשום סיכום-ריצה.

ההבדל מול Sheets: `sheets_manager._with_retry` **כן** מעלה חריגה במיצוי (`:421`). שכבת-הספקים לא.

---

## 6. `docs/HYPOTHESES.md` (318 שורות)

### 6.1 — המרשם

| ID | שם | סטטוס | נרשמה | תוצאה |
|---|---|---|---|---|
| HYP-001 | crossover-short | **REGISTERED** | 2026-06-23 | ולידציה ממתינה — TASK-179, n≥150 |
| HYP-002 | minimal-MxV-gate | **VOIDED** 2026-08-03, **נרשמה-מחדש** באותו יום | 2026-07-02 (מקורי) / 2026-08-03 (חדש) | הריצה המקורית מתה — ראה 6.3 |
| HYP-003 | 4-dim-gate | **DRAFT** | — | מעקב-בלבד, קריטריון לא נעול |

(`docs/HYPOTHESES.md:87-91`)

### 6.2 — HYP-001 crossover-short (`§D`, `:95-174`)

**התזה:** שורט על אירוע-שבירה ב-DropsLab בטיקר שהיה pump של RidingHigh ≤10 ימים קודם — הימור על המשך-הנפילה (`:103-105`).

**מה נעול (LOCKED):**
- חלון-crossover: ≤10 ימים קלנדריים (`:114`)
- כניסה: SHORT ב-`d1_close` של יום אירוע-הנפילה (`:125-126`)
- **יציאה: `D5_Close` — בדיוק 5 ימי-מסחר, זמן-בלבד, אפס שיקול-דעת, ללא TP/SL** (`:128-129`)
- fitness: `calculate_net_pnl` @ borrow 500%/שנה × 5/365 ≈ **6.85%** + slip **2%/צד** (`:137-141`)
- GO רק אם כל ה-bootstrap CI נשאר רווחי על n≥150 אירועים חדשים (`:139`)

**למה slip 2× ולא 0.5%:** הטיקרים בקריסה פעילה — HTB, נזילות דקה, ספרד רחב (`:144-146`).

**סיגנל-הגילוי (נעול, לעולם לא נמדד-מחדש):** 66% (123/185) מ-pumps של RH חוצים ל-DropsLab תוך ≤10 ימים; המשך-נפילה **−17.75% [−24.5, −11.0], n=62** על 5 ימים (`:148-152`). מסומן במפורש: **MEDIUM confidence, NOT evidence** — סלקציה על אירוע ידוע, borrow לא מתומחר.

**מה נדחה במפורש:** חלון החזקה D6–D15 — "חלון לא-נבדק, ואימות חלון שונה מזה שהגילוי מדד הוא לא-תקין מתודולוגית" (`:117-121`).

**מה חוסם:** TASK-179. יעד-הכוח n≥150 אירועים חדשים ≈ 450 שורות RH ≈ 4-5 חודשים בקצב הנוכחי (`:165`). ההערכה המקורית היתה "~mid-July" (`:174`) — **התאריך הזה עבר.**

### 6.3 — HYP-002 minimal-MxV-gate — נפסלה 2026-08-03 (`§F`, `:178-263`)

**התזה שנבדקה:** ששער-הכניסה המינימלי (`MxV ≤ −100 ∧ price ≥ $3`, עם Score ו-6 הפילטרים המגנים כבויים) ייתן תוצאות-נטו קדימה **לפחות כמו** שער ה-Score+פילטרים המלא (`:190-192`).

**כלל-העצירה:** להכריע רק ב-n≥150 כניסות post-flip **או** 45 ימי-מסחר מ-2026-06-29, המוקדם מביניהם (`:205-209`).

**מה קרה (`:230-247`):** כלל-העצירה ירה — n=173 מול סף 150 — **והמדגם לא ניתן לניקוד. שניהם נכונים בו-זמנית, ולכן הריצה נפסלה ולא הוכרעה.**

ארבע עובדות מדודות (read-only, 2026-08-03, מ-decision_log 06/07/08 + paper_portfolio 07/08):
1. n post-flip ENTERs = **173**. הכלל ירה על n, לא על הלוח.
2. פילוח-שכבות: **82 PHANTOM_CONFIRMED, 4 PHANTOM_SUSPECT, 87 CLEAN**. 86 מתוך 173 מזוהמים = **49.7%**.
3. **84 כניסות ללא תוצאה בכלל** — נספרות ב-n ולעולם לא יתרמו ל-expectancy.
4. הקונפיג הקפוא מתיר re-entry ≤1 לטיקר ליום. **11 זוגות טיקר-יום חצו 2, עם 54 כניסות מעבר לתקרה**: LLABT 11, IINLF 11, AADVB 11, ZZCMD 10 ב-22/07, AATPC 9 ו-VVEEE 8 ב-16/07.

**איך התקרה נפרצה בלי לשנות קונפיג (`:244-247`):** תחת 429 מ-Sheets, `build_account_state` החזיר ברירות-מחדל ושלושת פילטרי-החשיפה עברו יחד — הסוכן נכנס כאילו החשבון ריק.

**למה לא הצילו את 87 השורות הנקיות (`:249-252`):** "בחירת תת-קבוצה אחרי שראית את הדאטה היא בדיוק הכשל שהרישום-המקדים קיים כדי למנוע. תת-הקבוצה לא נבחרה בכלל שנקבע מראש; היא נבחרת מתוך ידיעה אילו שורות התקלקלו. ה-expectancy שלה **לא חושבה בכוונה**, כדי שאף מספר מהריצה הזו לא יעגן את הבאה."

**הריצה החדשה (`:254-263`):** מתחילה 2026-08-03, אותו קריטריון, אותו קונפיג קפוא, אותו כלל-עצירה. 45 ימי-מסחר מגיעים לתחילת אוקטובר. **CARRIED FORWARD: nothing** — אף שורה מלפני 03/08 לא נכנסת.
**מה יפסול גם את החדשה:** פריצה נוספת של תקרת ה-re-entry, או כל שינוי ב-TP/SL/HOLD/שער. הדבר שצריך לעקוב אחריו: אם ה-guard של TASK-244 עובד, 429 מייצר עכשיו SKIP עם `ACCOUNT_STATE_UNAVAILABLE` במקום כניסה עיוורת.

### 6.4 — HYP-003 4-dim-gate — DRAFT (`§G`, `:267-287`)

מוסיף TPD≥6 (מנוע-רווח, +6.5pp במחקר-199) ומסנני-זנב REL_VOL≥15 ו-Float%≥60 לשער הדו-תנאי (`:272-274`).
**הקריטריון לא נעול בכוונה** — ממתין ל-n: גבול-האמינות של מחקר-199 הוא n=28 ב-3 ממדים, ומתמוטט ל-**n=13** כשמוסיפים Float% (`:278-279`).

### 6.5 — NULL RESULTS (`§H`, `:291-304`, נמדדו 2026-07-02)

| מה נבדק | תוצאה |
|---|---|
| **(א) MxV/ATRX כמנבא פר-עסקה (TASK-62)** | **אין הפרדה, n=229.** MxV חציון WIN −698 מול LOSS −559 — **הפוך**. ATRX 5.00 מול 4.90 — זניח. מסקנה: MxV הוא מנוע **בחירת-מועמדים**, לא מנבא פר-עסקה; ATRX ≈ רעש. |
| **(ב) WR לפי משטר-VIX (TASK-70/170)** | **לא-מכריע.** VIX<20 n=205 WR 53.7% · 20-30 n=14 WR 57.1% · >30 **n=0**. כל חלון 05-07 היה low-vol → אפס שונות-משטר. הממצא המקורי (72% מול 58%) **לא שוחזר**. |

שניהם **לא קודמו**. טריגרים לבדיקה-מחדש: שונות-VIX אמיתית (כניסות ב->30), או n גדול יותר בדלי-האמצע.

---

## 7. `tests/`

### 7.1 — היקף

- **10,101 שורות** ב-`tests/` על פני **104 קבצי-טסט**
- **674 פונקציות `def test_`** תחת `tests/`
- בנוסף, 3 קבצי-טסט סקריפטיים בשורש שאינם pytest-collectible: `test_formulas.py` (18 טסטים), `test_utils.py` (6), `test_data_provider.py` (3). `tests.yml:10-12` מסביר: `pytest.ini` מגביל איסוף ל-`tests/`, ולכן שני הראשונים רצים כסקריפטים רגילים.

### 7.2 — מה מכוסה, לפי תיקייה

| תיקייה | קבצים | מה מכוסה |
|---|---|---|
| `tests/agent/unit/` | ~30 | `decision_logic` (346 שורות — הגדול ביותר), `position_manager`, `orchestrator`, `reconciler`, `order_manager`, `alpaca_broker`, `postmortem_engine`, `score_analytics`, `decision_logger`, `borrow_collector`, `tradability`, `trader`, `email_sender`, תבניות-מייל, `create_agent_sheets` dry-run, שערי-הצל |
| `tests/agent/integration/` | 2 | `test_scanner_agent_match.py` (205) — שהסקאנר והסוכן מפיקים Score זהה · `test_decision_logger_writes.py` (142). **שניהם מסומנים אוטומטית `integration` לפי נתיב** (`tests/conftest.py:13-16`) ו-CI מדלג עליהם עם `-m "not integration"` |
| `tests/overnight/` | 5 | `core_unsafe`, `guardrails`, `triage_filter`, `night_config`, `build_report` — כל זה על רץ-הלילה **שנוטרל ב-2026-07-02** |
| `tests/` (שורש) | ~65 | נוסחאות (`net_pnl`, `wilson_ci`, `fmt_rate_ci`, `classify_trade`), DST (`market_hours`, `snapshot_time`, `mintoclose`), פנטומים, schema contract, קרדנציאלים, backfill, cross-month |

### 7.3 — טסטים שנוגעים ברשת או ב-Sheets

**TASK-250 מזהה קובץ אחד, שבע פונקציות.** גוף התיק:

> `tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py` נכנס לאדום בסוויטה המקומית אחרי שהיה ירוק כל היום, בלי שום עריכה שלו. הדוקסטרינג של הקובץ אומר "All-mocked (MagicMock + patch), zero real API/Sheets". **זה שקר.** הטסטים עושים patch ל-`agent.orchestrator.build_account_state`, אבל ל-`orchestrator_eod.collect_borrow_snapshot` יש **מקור-טיקרים שני שאיש לא עושה לו patch**: `agent/orchestrator_eod.py:57` קורא `sheets_manager.get_worksheet("daily_snapshots")` ו-`:59` קורא `get_all_values()`. ה-helper מחזיר את **האיחוד** של שני המקורות.

למה זה נצבע אדום דווקא אז: החודש הפעיל התגלגל לאוגוסט ב-1/8, וטאב `daily_snapshots` של אוגוסט היה ריק עד 3/8. מהרגע שנכתבו שורות היום — טיקרים אמיתיים נכנסו ל-assertion. הכשל שנצפה: `assert [...,'HYFM',...] == ['AAA','BBB','CCC']`, הפריט העודף הראשון `DFNS`, שהיה בסריקה החיה של 3/8.

**שלוש השלכות שהתיק מציין:**
1. שבעה טסטים בקובץ קוראים ל-`collect_borrow_snapshot`, כלומר **כל ריצת pytest מקומית מבצעת שבע קריאות Sheets חיות** — מקובץ שמצהיר שהוא לא נוגע בכלום.
2. **CI ירוק רק כי ל-`tests.yml` אין credentials**, אז הקריאה מעלה חריגה ו-`scanned` נופל לקבוצה ריקה. **ירוק-שווא** — חוזה ה-mock אף פעם לא נבדק באמת.
3. הסוויטה אדומה מקומית לכל מי שיש לו OAuth עובד, מה שמסתיר רגרסיות אמיתיות.

**התיק מציין במפורש שלא בוצע:** "Not verified: whether other unit tests outside this file also reach live Sheets. That sweep has not been run."
**גם אני לא הרצתי את הסריקה הזו** — האיסור על הרצת pytest חל, וניתוח סטטי לבדו לא מוכיח מה קורה בזמן-ריצה.

מה שכן ראיתי בקריאה סטטית: `tests/test_account_state_v1.py:43-61` ו-`:96-113` עושים monkey-patch ידני ל-`sheets_manager.get_worksheet` ו-`get_sheet_records` עם שחזור ב-`finally` — דפוס נכון. `tests/test_position_manager_cached_reader_v1.py` בודק במפורש שהקורא **לא** נופל למסלול הלא-מקושר.

### 7.4 — מה בנתיב-המסחר החם חסר כיסוי

לפי מיפוי קבצי-הטסט מול הנתיב שתואר בחלק א' §B.2:

| רכיב חם | כיסוי |
|---|---|
| `decision_logic._check_filters` | ✅ 346 שורות + `test_entry_gate_minimal_v1` + `test_score_gate_flip_v1` |
| `orchestrator.build_account_state` | ✅ `test_account_state_v1.py` (189) |
| `position_manager` TP/SL | ✅ `test_position_manager.py` (287) |
| `order_manager` כתיבה | ✅ `test_order_manager_write_surfaced_v1` |
| `utils.classify_trade` | ✅ `test_classify_trade_day_v1`, `test_task46_classify_dedup_v1` |
| **`auto_scanner.run_scan()`** | ❌ **אין קובץ טסט.** אימות: `ls tests/ \| grep -i "auto_scan\|run_scan"` → כלום. הפונקציה שכותבת ל-timeline_live בכל דקה לא נבדקת מקצה-לקצה |
| **`auto_scanner.analyze_ticker()`** | ❌ אין. הפונקציה שמייצרת כל מטריקה |
| **`dashboard.py`** | ❌ כמעט כלום — רק `test_page_visit_v1.py` (38 שורות) ו-`test_expectancy_bounds_v1` |
| **`health_audit.py`** | חלקי — `test_health_audit_lineage_v1` (191), `test_health_audit_actions_v1` (113), `test_health_audit_interday_v1` (57). 3 בדיקות מתוך 30 |
| **`sheets_manager._with_retry`** | ❌ לא ראיתי קובץ ייעודי |
| **`critic_v1.py`** | חלקי — `test_weekly_row`, `test_monthly_row`, `test_write_weekly/monthly`, `test_monthly_section_c_median_v1`. אין טסט ל-`review_completed_trades` או ל-`summarize` |
| `post_analysis_collector.fetch_ohlc_for_days` | ❌ לא ראיתי טסט ללולאת ה-5-ניסיונות |

---

## 8. הקבצים שנשארו בשורש

47 קבצי py בשורש. הטבלה: מה עושה · מי קורא · חי-בפרודקשן או כלי.

### 8.1 — חי בנתיב הפרודקשן

| קובץ | מה עושה | מי קורא | ראיה |
|---|---|---|---|
| `auto_scanner.py` | הסקאנר | `auto_scan.yml:36` + `post_analysis.yml:40` (`--eod`) + 3 מייבאים | ✅ |
| `config.py` | קבועים | **41 מייבאים** | ✅ |
| `formulas.py` | נוסחאות | **22 מייבאים** | ✅ |
| `utils.py` | עזר משותף | **32 מייבאים** | ✅ |
| `sheets_manager.py` | גישה ל-Sheets | **60 מייבאים** — הכי מרכזי בריפו | ✅ |
| `data_provider.py` | הפשטת-ספקים | 19 מייבאים | ✅ |
| `dashboard.py` | Streamlit | Streamlit Cloud | ✅ |
| `post_analysis_collector.py` | איסוף D1-D25 | `post_analysis.yml:50` + 6 מייבאים | ✅ |
| `enrich_post_analysis.py` | העשרה | `post_analysis.yml:60` | ✅ |
| `health_audit.py` | 30 בדיקות | `health_audit.yml:49` + 7 מייבאים | ✅ |
| `backup_manager.py` | גיבוי CSV | `backup.yml:31` | ✅ |
| `monthly_rotation.py` | רוטציה חודשית | `monthly_rotation.yml:34` | ✅ |
| `prepare_next_month.py` | יצירת חודש-הבא | `prepare_next_month.yml` | ✅ |
| `warm_oauth_token.py` | **גלאי** בריאות-OAuth (לא מונע — דוקסטרינג) | `warm_oauth_token.yml` | ✅ |
| `backfill_ohlc_v2.py` | מילוי פערי-OHLC | `backfill_ohlc.yml:43` (`--recent 2 --apply`) | ✅ |
| `gsheets_sync.py` | 9 מייבאים | `dashboard.py:46` ואחרים | ✅ |
| `cross_month_loaders.py` | טעינה חוצת-חודשים | 7 מייבאים | ✅ |
| `metrics_bounds.py` | גבולות-מטריקה טהורים (בלי Streamlit, בלי I/O) | 4 מייבאים | ✅ |
| `ta_helpers.py` | RSI/ATR קנוני של Wilder (TASK-137) | 2 מייבאים | ✅ |
| `intraday_cache.py` | קאש מוטות-דקה (TASK-155) | 1 מייבא | ✅ |
| `data_logger.py` | `class DataLogger` | 1 מייבא (`dashboard.py:41`) | ✅ |
| `health_check.py` | בדיקת-בריאות (נפרד מ-health_audit) | 1 מייבא | ✅ |
| `backfill_interday_v1.py` · `backfill_netpnl.py` · `backfill_ohlc.py` | backfill-ים | 1-2 מייבאים כל אחד | חלקי |

### 8.2 — כלים / חד-פעמיים (אפס מייבאים, אפס workflow)

| קובץ | מה |
|---|---|
| `apply_text_format_v1.py` | עיצוב טקסט חד-פעמי |
| `backfill_fundamentals.py` | מסומן "חד-פעמי" בדוקסטרינג |
| `check_sync.py` | "Quick standalone sync check" |
| `code_auditor.py` | "Deep Code Auditor" |
| `daily_audit.py` | "Daily System Audit" — **לא מופעל משום workflow** |
| `deep_scan.py` | סריקה עמוקה, 2026-04-17 |
| `drop_analysis.py` | ניתוח נפילות |
| `enrich_data.py` | העשרה (שונה מ-`enrich_post_analysis`) |
| `generate_project_state.py` | מייצר `PROJECT_STATE.md` (ב-.gitignore) |
| `get_oauth_token.py` | "חד-פעמי: קבלת refresh_token" — **ב-.gitignore** |
| `metric_quality_analysis.py` | ניתוח איכות-מדדים, 2026-04-17 |
| `morning_health_check.py` | בדיקת-בוקר v2, 2026-04-17 |
| `score_backtest.py` | השוואת v1/v2/v3 מול MaxDrop%. **מסומן research-only** (TASK-189) |
| `score_distribution.py` | התפלגות Score |
| `setup_health_audit_sheet.py` | הקמת גיליון-הבריאות (חד-פעמי) |
| `setup_summaries_sheet.py` | "one-time, live" — הקמת RH-Summaries |
| `smoke_test_port_month.py` | smoke test |
| `sync_pk_to_sheet.py` | **⚠️ DEPRECATED 2026-06-12 (TASK-152)** — מראת ה-PK ל-Sheets פרשה. הקוד עדיין בריפו |
| `validate_providers.py` | השוואת A/B בין Alpaca ל-yfinance |
| `test_position_sync_v1.py` | טסט בשורש שלא נאסף ע"י pytest |
| `test_formulas.py` · `test_utils.py` | **רצים ב-CI כסקריפטים** (`tests.yml:34-35`) |
| `test_data_provider.py` | לא רץ ב-CI |

---

## 9. `CLAUDE.md` + `SCHEMA.json` + `OPEN_ISSUES.md`

### 9.1 — `CLAUDE.md`

חוזה-התנהגות ל-Claude Code, לא לקוד. 14 כללים ממוספרים. הרלוונטיים למה שראיתי:
- **RULE #4** — גיבוי → `str_replace` → `py_compile` → הרצת טסטים → דיווח, בלי commit
- **RULE #5/#5b** — אף commit בלי אישור מפורש; אף פעם לא `git commit` פעמיים לאותו שינוי
- **RULE #8** — היררכיית מקורות-אמת: `config.py` (משקלים/ספים) · `formulas.py` (**כל** החישובים) · `auto_scanner.py` (I/O ותזמור, **לא** חישובים) · `dashboard.py` (UI, **לא** חישובים) · `utils.py` (עזר). **סעיף 2.2 של הדוח הזה מתעד 16 הפרות של הכלל הזה ב-`dashboard.py`.**
- **RULE #10** — Peru = UTC−5 בלי DST; ET כן עם DST. "אל תנחש"
- **RULE #12** — כל פקודת Bash דרך `.rh-run.sh`
- **RULE #14** — אף פעם לא להדפיס את גוף ה-PK; לקרוא את החדש-ביותר לפי mtime
- `@.claude-startup.md` — נטען אוטומטית, מוסיף פרוטוקול-פתיחה

### 9.2 — `SCHEMA.json` (8,942 בתים)

חוזה-סכמה **נגזר**, לא מקור. `_meta` (`SCHEMA.json:2-11`):
```json
"do_not_edit": true,
"generated_by": "scripts/generate_sheets_schema.py",
"schema_version": 1,
"sources": ["create_agent_sheets.AGENT_SHEET_HEADERS",
            "sheets_manager.TIMELINE_LIVE_COLS",
            "post_analysis stable-subset (authored) + config forward-window"]
```
לכל גיליון: `columns` (רשימה מסודרת), `mode` (`"exact"`), `source`.
נקרא ע"י `health_audit._load_schema_contract()` (`health_audit.py:784`) לבדיקה Q2, ומ-הדיסק ע"י טסט round-trip ב-CI — לכן הוא **חריג מפורש ב-.gitignore** (השורה "TASK-167 — derived sheet-schema contract; CI round-trip test reads it from disk").

### 9.3 — `OPEN_ISSUES.md` (30 שורות) — **אין התנגשות**

הקובץ **מוותר על עצמו במפורש**. `OPEN_ISSUES.md:3-4`:
> "As of 2026-05-23, all task tracking has moved to `Backlog.md`. This file is intentionally minimal — do not add new issues here."

הוא מפנה ל-`backlog task list --plain` כמצב-חי (`:8`), ל-`backlog/tasks/` לגופי-התיקים (`:9`), ול-PK ול-`research/` להקשר היסטורי (`:15-16`). מנומק ב-`:19-24`: הפורמט החופשי הפך בלתי-נסבל עם הצמיחה, ו-Backlog.md נותן עדיפויות מובנות, מעקב-סטטוס, קריטריוני-קבלה, ומקור-אמת יחיד.

**אין בו אף issue פתוח** ולכן אין מה שיתנגש. עודכן לאחרונה 2026-05-23 (`:30`).

---

## 10. מה השתנה בתמונה

### 10.1 — תיקונים לחלק א'

**תיקון 1 — D14 היה שגוי. 83 הפוזיציות התקועות אינן חוסמות את הסוכן היום.**
בחלק א' העליתי חשש ש-83 השורות `DRY_RUN_OPEN` של יולי אוכלות את מגבלת 5-המקבילות ולכן הסוכן משותק. **זה לא נכון.**
ראיה: `build_account_state` קורא `sheets_manager.get_sheet_records("paper_portfolio")` **בלי פרמטר month** (`agent/orchestrator.py:222`). `get_sheet_values` מעביר `month=None` ל-`get_worksheet` (`sheets_manager.py:459`), שממלא `month = now(Peru).strftime("%Y-%m")` (`:613`). מאז רוטציית 1/8, `paper_portfolio` מצביע על **הקובץ של אוגוסט**. 83 השורות יושבות בקובץ של יולי ולא נספרות. החשש מבוטל.

**תיקון 2 — D1 היה שאלה על סתירה שלא קיימת, והתשובה האמיתית נמצאה.**
שאלתי איך 60 פוזיציות סגורות (TASK-254) מתיישבות עם 83 תקועות (TASK-246). **הן פשוט מתקיימות יחד** — יולי סגר 60 והשאיר 83 פתוחות.
ולמה `score_analytics` מדווח n=0: **הקורא לא מוזרק בכלל.** `orchestrator_eod.py:173` עושה `ScoreAnalytics()` — בלי ארגומנטים. `__init__` מקבל `postmortem_reader=None` (`score_analytics.py:63`) ושומר `self._postmortem_reader = None` (`:73`). `_load_postmortems` פותח ב-`if not self._postmortem_reader: return pd.DataFrame()` (`:131-132`). **n=0 מובנה בקוד, לא תלוי בדאטה.** גם הקריאה השבועית (`orchestrator_eod.py:191`) זהה.

**תיקון 3 — D5 נענה. `SanitizedOverview` לא עוקף את התלות השבורה, ה-workflows עוקפים אותה.**
שאלתי אם ה-proxy עוקף את הפגם של finvizfinance 0.14.6 במלואו. גוף TASK-248: הסקאנר שורד **רק כי שלושת ה-workflows מתקינים `finvizfinance` בלי pin ומקבלים 1.3.0**, כלומר מתעלמים מה-pin לגמרי. `requirements.txt` שורה 4 מצמיד `==0.14.6`, שמחפש טבלה עם class `table-light` שכבר לא קיימת בדף — fetch אמיתי תחתיו מעלה `AttributeError`. התיק מנסח: "הפין אינו רק מיושן, הוא רעיל." מי שמריץ `pip install -r requirements.txt` מקבל סקאנר מת.

**תיקון 4 — D2 נענה חלקית ובאופן חד יותר משחשבתי.**
צניחת נפח-הסריקה: החציון היומי נפל מ-~46 שורות ל-~20 מ-15/07 (מדוד מ-`daily_snapshots` של יולי). **שתי הסברים מתחרים, אף אחד לא מאומת:** (א) אותו שורש כמו שינוי-הפרסור של finviz — שורה מקולקלת נופלת במורד-הזרם ולכן האובדן הוא ארטיפקט; (ב) שינוי אמיתי ברוחב-השוק או במה שהפילטר קלט. התיק מדגיש שלהסברים יש **השלכות הפוכות** ושההבחנה חייבת להימדד. חסום בפועל על היקף-הזיהום.

**תיקון 5 — D13 נענה. אוגוסט הוא החריג, לא השאר.**
`sheets_manager.SHEET_NAMES` (9 ערכים) כולל `live_trades` כקובץ עצמאי. `prepare_next_month.SHEET_NAMES` (8 ערכים) משמיט אותו, ושורה 240 שם עושה `created_ids['live_trades'] = created_ids['score_tracker']` — **הקונבנציה האוטומטית היא alias**. `scripts/fix_august_provisioning_v1.py:305` איטרר על הרשימה של `sheets_manager` ולכן התיקון הידני של 29/7 יצר לאוגוסט קובץ עצמאי. שתי רשימות של אותו דבר שחלוקות — הפרת §10.

**תיקון 6 — D4 נענה. TASK-244 פתוח כי החקירה לא בוצעה, לא כי התיקון חסר.**
גוף התיק מגדיר "SCOPE OF INVESTIGATION: לקרוא את ערכי ExistingPosition לשורות 22/7, לאתר את נתיב-הקוד שאוכף re-entry, ולקבוע אם ה-guard נעדר, קורא-מצב-שגוי, או עוקף כדין תחת DRY_RUN" ומסיים "Do not fix without live verification. Quota heavy, run outside market hours." הפילטר F6b שנחת ב-3/8 סוגר את המקרה קדימה; החקירה הרטרוספקטיבית עדיין פתוחה.

### 10.2 — כפילויות SSoT חדשות (תוספת לרשימת חלק א')

חלק א' מנה 6. הנה 5 נוספות:

**7. `dashboard.py` מחשב inline 16 מטריקות שיש להן מימוש ב-`formulas.py`** — ראה טבלה מלאה ב-§2.2. הבולטות: `change` ב-`:305`/`:413`/`:597`, `price_to_high` ב-`:386`/`:566`, `price_to_52w_high` ב-`:392`/`:572`, `pnl` שלוש פעמים ב-`:2117`/`:2125`/`:2127`. **הפונקציות המקבילות ב-`formulas.py` אפילו לא מיובאות** לקובץ.

**8. `critic_v1.py` מגדיר "ניצחון" בנפרד מ-`utils.classify_trade`.** ה-Critic: סימן PnL → WIN/LOSS/FLAT (`:145-151`). `utils.classify_trade:513`: הליכה יומית D1→D5 מול TP/SL → WIN/LOSS/WHIPSAW/NO_TOUCH/PENDING. **שתי הגדרות, שני מרחבי-ערכים, אפס קטגוריית WHIPSAW אצל ה-Critic.**

**9. `critic_v1.py` מחשב win_rate לבד** (`:212`) בעוד `formulas.fmt_rate_ci:661` קיים בדיוק לזה ומוסיף Wilson CI. הקובץ לא מייבא מ-`formulas` בכלל.

**10. שתי רשימות `SHEET_NAMES` שחלוקות** — `sheets_manager.SHEET_NAMES` (9, `sheets_manager.py:38-48`) מול `prepare_next_month.SHEET_NAMES` (8, משמיט `live_trades`). זה השורש של TASK-251.

**11. שתי שכבות-קאש נפרדות ל-Sheets** — `sheets_manager._sheet_values_cache` (TTL 60s, `:391`) ו-`health_audit._ha_cached_read` (TTL 600s, `:1089`). לא מדברות ביניהן. **ושלישית שהיא מתה:** `agent/utils/sheets_cache.SheetsCache` (171 שורות, אפס מייבאים).

---

## 11. מה עדיין לא ברור

**E1. האם עוד טסטי-יחידה מחוץ ל-`test_orchestrator_eod_borrow_wiring_v1.py` מגיעים ל-Sheets חיים.**
TASK-250 מציין במפורש שהסריקה לא בוצעה. אני ביצעתי סריקה **סטטית** בלבד (grep על `sheets_manager`/`get_worksheet`/`gspread` ב-`tests/`), והיא לא מכריעה: קריאה יכולה להיות מוסתרת מאחורי import עקיף או fixture. **מה שיפתור:** הרצת הסוויטה עם conftest שמפיל כל טסט שפותח לקוח אמיתי — כלומר הרצת pytest, שאסורה בתור הזה.

**E2. איזה מהעמודים `score_comparison_page()` (`dashboard.py:3450`) ו-`live_trades_page()` (`:3280`) עדיין נגיש.**
שניהם מוגדרים אבל לא ב-`_PAGE_NAMES` (`:5263-5275`) ולא ב-dispatch (`:5304-5327`). זה 500+ שורות שאולי מתות. **מה שיפתור:** `grep -n "score_comparison_page\|live_trades_page" dashboard.py` — פקודה אחת. לא הרצתי כי לא הייתה בהיקף שהוגדר.

**E3. מה בעצם קורה כשמסלול-הנפילה ל-`sheet1` יורה** (`sheets_manager.py:628`).
TASK-251 אומר במפורש "Not verified: whether a tab named live_trades exists inside 1b0Vb, or whether writes are landing on sheet1 through the fallback." אם הכתיבות נוחתות על `sheet1`, אז נתוני live_trades של אוגוסט יושבים במקום אחר מכל חודש אחר. **מה שיפתור:** פתיחת הקובץ ובדיקת שמות-הטאבים — קריאת Sheets, חסום היום.

**E4. `enrich_post_analysis.py` (223 שורות) — לא קראתי.**
רץ כל יום ב-`post_analysis.yml:60`, אחרי הקולקטור. **אין לי מושג מה הוא מעשיר ומאיזה מקור.** **מה שיפתור:** קריאת הקובץ.

**E5. `gsheets_sync.py` (404 שורות) — לא קראתי.**
9 מייבאים, כולל `dashboard.py:46` עבור `save_snapshot_to_sheets` / `save_timeline_to_sheets` / `save_portfolio_to_sheets` — כלומר **הוא נתיב-כתיבה חי מה-UI**. **מה שיפתור:** קריאת הקובץ.

**E6. `agent/logging/decision_logger.py` (358) — לא קראתי.**
זה הרכיב שכותב את `decision_log`, המקור שממנו נמדדת HYP-002. `flush_skip_summary` ו-`flush_shadow_gate_summary` נקראים מהאורקסטרטור (`orchestrator.py:781`, `:787`) ולא בדקתי מה הם כותבים. **מה שיפתור:** קריאת הקובץ.

**E7. 7 בדיקות ה-Sentinel ב-`agent/sentinel/checks/` — לא קראתי אף אחת.**
`completeness` (41) · `position_sync` (131) · `price_freshness` (119) · `price_sanity` (79) · `provider_heartbeat` (81) · `quota_health` (81) · `scan_freshness` (83). ידוע לי רק ש-`position_sync` מחזיר `POSITION_SYNC_DEFERRED` (`:46`) ושהמצב הוא shadow. **מה חוסם:** לא הבנתי מה כל בדיקה בודקת בפועל ומה הספים. **מה שיפתור:** קריאת 7 הקבצים — 615 שורות.

**E8. `agent/execution/reconciler.py` (371) — לא קראתי.**
רץ כל EOD (`orchestrator_eod.py`), מזהה drift מול Alpaca, והתיקון-האוטומטי שלו כבוי. לא יודע מה הוא מדווח כשהוא מוצא drift. **מה שיפתור:** קריאת הקובץ.

**E9. `agent/notifications/` — 5 תבניות-מייל + `email_sender.py`, אף אחד לא נקרא.**
`critic_brief` (264) · `monthly_brief` (224) · `daily_brief` (214) · `weekly_brief` (105) · `morning_brief` (58) · `email_sender` (117). אלה הדברים שעמיחי בעצם רואה בתיבה כל יום. **מה שיפתור:** קריאת 6 הקבצים — 982 שורות.

**E10. `cross_month_loaders.py` (395) — לא קראתי.**
7 מייבאים. TASK-202 ("collector cross-month backfill — thread month through all 5 read/write points") נוגע בדיוק בזה. **מה שיפתור:** קריאת הקובץ + גוף TASK-202.

**E11. האם `daily_audit.py` (673) הוא באמת קוד מת.**
אפס מייבאים, אפס workflow. אבל 673 שורות בשם "Daily System Audit" — אם הוא באמת לא רץ, אז יש בדיקה יומית שלמה שאיש לא מריץ. **מה שיפתור:** `git log -1 --date=short -- daily_audit.py` לראות מתי נגעו בו לאחרונה.

**E12. מה קרה לתקציב ה-45 ימי-מסחר של HYP-002 המקורית.**
ה-flip היה 29/06. 45 ימי-מסחר משם ≈ סוף אוגוסט. הכלל אמר "n≥150 **או** 45 ימים, המוקדם" — ו-n ירה ב-3/8. אבל **אני לא יודע כמה ימי-מסחר עברו בפועל** ולכן לא יכול לאמת שה-n אכן קדם. **מה שיפתור:** ספירת ימי-מסחר 29/06→03/08 מול `utils.is_trading_day`.

### 11.1 — האם נשאר קובץ py חי שלא נקרא באף אחת משתי הריצות

**כן. 145 קבצי py חיים בריפו (ללא `tests/`, `backups/`, `project_sync/`, `research/`). קראתי במלואם או בחלקם משמעותיים — 24.**

**קבצים חיים שלא נפתחו כלל — הרשימה המלאה:**

| קובץ | שורות | למה זה משנה |
|---|---|---|
| `gsheets_sync.py` | 404 | נתיב-כתיבה חי מה-dashboard, 9 מייבאים |
| `cross_month_loaders.py` | 395 | 7 מייבאים, TASK-202 |
| `agent/logging/decision_logger.py` | 358 | כותב את decision_log — מקור HYP-002 |
| `agent/execution/reconciler.py` | 371 | EOD drift detection |
| `agent/execution/alpaca_broker.py` | 354 | קראתי 4 שורות בלבד (grep) |
| `agent/execution/order_manager.py` | 314 | קראתי 40 שורות |
| `daily_audit.py` | 673 | ייתכן קוד מת |
| `code_auditor.py` | 449 | כלי |
| `deep_scan.py` | 409 | כלי |
| `agent/dashboard/trade_history_page.py` | 625 | העמוד הגדול ביותר בסוכן |
| `agent/dashboard/live_agent_page.py` | 390 | |
| `agent/dashboard/score_brain_page.py` | 238 | |
| `agent/dashboard/sentinel_events_page.py` | 132 | |
| `agent/dashboard/_data_loaders.py` | 247 | קראתי grep בלבד |
| `agent/setup/create_agent_sheets.py` | 500 | קראתי 30 שורות |
| `agent/analytics/postmortem_engine.py` | 407 | קראתי דוקסטרינג בלבד |
| `agent/news_detective/news_detective_v1.py` | 280 | קראתי דוקסטרינג בלבד (וכבוי) |
| `agent/market_context/market_context_v1.py` | 202 | קראתי דוקסטרינג בלבד |
| `agent/perception/borrow_collector.py` | 191 | קראתי דוקסטרינג בלבד |
| `agent/perception/data_quality.py` | 132 | **מפעיל את פילטר F6 החי** |
| `agent/perception/tradability.py` | 102 | נקרא בכל ENTER |
| `agent/enrichment/sma20_cache.py` | 95 | |
| `agent/trader/trader.py` | 94 | |
| `agent/sentinel/checks/*` (7 קבצים) | 615 | |
| `agent/sentinel/sentinel_selftest_v1.py` | 146 | |
| `agent/sentinel/shadow_audit_v1.py` | 143 | |
| `agent/notifications/*` (6 קבצים) | 982 | המיילים היומיים |
| `agent/orchestrator_email_daily.py` | 194 | |
| `agent/orchestrator_email_morning.py` | 99 | |
| `agent/orchestrator_critic*.py` (3) | 283 | קראתי 16 שורות מכל אחד |
| `agent/logging/decision_id_generator.py` | 97 | |
| `agent/market_context/run_market_context.py` | 39 | |
| `agent/utils/sheets_cache.py` | 171 | ✅ נקרא — ומת |
| `enrich_post_analysis.py` | 223 | רץ כל יום |
| `backfill_ohlc_v2.py` | 235 | רץ כל יום |
| `metrics_bounds.py` · `intraday_cache.py` · `ta_helpers.py` · `data_logger.py` · `health_check.py` · `backup_manager.py` | ~900 | |
| `monthly_rotation.py` · `prepare_next_month.py` | 474 | |
| `scripts/*` (10 קבצים) | ~1,900 | כלים |
| שאר כלי-השורש (17 קבצים) | ~2,800 | |

**מהערכה גסה: כ-13,000 שורות py חיות נקראו, כ-35,000 לא.**
הפער הגדול ביותר בנתיב החם: **`agent/perception/data_quality.py`** — 132 שורות שמכריעות את פילטר F6, אחד מ-9 הפילטרים החיים היחידים, ולא פתחתי אותו.

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
הכתיבות היחידות: קובץ הדוח הזה ו-`reports/INDEX.md`.
