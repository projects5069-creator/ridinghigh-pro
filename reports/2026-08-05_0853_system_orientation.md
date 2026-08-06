# RidingHigh Pro — היכרות עם המערכת מהקוד

**מסמך תיאורי בלבד.** אין בו תוכנית, אין המלצות, אין דירוג משימות — כפי שביקשת.
נכתב 2026-08-05 08:53 Lima (09:53 EDT NY). מקור כל קביעה: קובץ:שורה מהריפו החי.

> ℹ️ **הערת-תהליך.** הדוח נכתב תחילה תחת Plan Mode (שחוסם כתיבה לכל קובץ מלבד קובץ-התוכנית),
> ולכן נוצר ב-`~/.claude/plans/shimmying-roaming-sutherland.md` והועתק לכאן מיד לאחר האישור.
> אפס שינוי קוד, אפס commit, אפס נגיעה ב-Sheets/Drive/FINVIZ.
>
> ⚠️ **RULE #12 — לא עטפתי ב-`.rh-run.sh`.** סיבה: כל הפקודות היו קריאה-בלבד לצורך הדוח, והפלט נועד לקובץ ולא ללוח.

---

## 0. סריקת סקילים

`ls ~/.claude/skills/`:
```
anthropic-skills  backtest-expert  biotech-screener  data-quality-checker
position-sizer    rhpro-live       rhpro-session     signal-postmortem
time-check        trader-memory-core
```

**נטענו:**

| סקיל | path | wc -l |
|---|---|---|
| rhpro-live | `~/.claude/skills/rhpro-live/SKILL.md` | 180 |
| time-check | `~/.claude/skills/time-check/SKILL.md` | 60 |

**superpowers marketplace cache — הרשימה המלאה (14):**
`brainstorming · dispatching-parallel-agents · executing-plans · finishing-a-development-branch · receiving-code-review · requesting-code-review · subagent-driven-development · systematic-debugging · test-driven-development · using-git-worktrees · using-superpowers · verification-before-completion · writing-plans · writing-skills`

**נדחו:** rhpro-session (לא ריטואל פתיחה/סגירה) · data-quality-checker (אין ניתוח דאטה חי, השוק פתוח) · backtest-expert · position-sizer · signal-postmortem · trader-memory-core · biotech-screener (ריפו אחר) · superpowers systematic-debugging/brainstorming/writing-plans/TDD (אין באג, אין בנייה, והמשימה אוסרת תוכנית) · anthropic docx/pdf/pptx/xlsx/frontend-design.

---

## 1. עובדות פתיחה (raw)

```
2026-08-05 08:53:15 Wednesday Lima
09:53 EDT NY

tail -3 /tmp/cc-copy-last.log
2026-08-03 19:54:27  copied 17660 bytes (try 6/20, fresh-stable, prev-stamp=[2678913837 17614])
2026-08-03 20:28:43  copied 10959 bytes (try 6/20, fresh-stable, prev-stamp=[980855883 17660])
2026-08-03 20:44:45  copied 10725 bytes (try 6/20, fresh-stable, prev-stamp=[2826345963 10959])

branch : docs/handoff-2026-07-29
HEAD   : 72d357d 2026-08-03 19:53:20 -0500 chore(backlog): three rulings and two accuracy fixes, 56 open down to 53
git rev-list --left-right --count origin/main...HEAD  →  11  0   (הענף 11 מאחורי origin/main, 0 לפניו)

git status --porcelain -uall
?? docs/auto-dancer/queue/QUEUE_2026-07-04.md
?? docs/auto-dancer/queue/QUEUE_2026-07-05.md
```

PK חי לפי mtime: `docs/RidingHigh_Pro_PK_v2.md` (3,889 שורות, גרסה 4.12).
תיקים פתוחים: **53** (To Do 50 + In Progress 3).

---

## A. מפת הריפו

### A.1 — רמה עליונה

| תיקייה | מה יש בה |
|---|---|
| שורש | 40+ סקריפטים py (סקאנר, dashboard, health, backfill, enrich) + `CLAUDE.md` `SCHEMA.json` `PROJECT_STATE.md` `OPEN_ISSUES.md` |
| `agent/` | מודול הסוכנים — 16 תת-תיקיות, 14,464 שורות py |
| `providers/` | `alpaca_provider.py` (380) · `yfinance_provider.py` (354) |
| `scripts/` | כלי-חקירה חד-פעמיים + `scripts/overnight/` (הרצת-לילה) + `claude_hooks/` + `git_hooks/` |
| `tests/` | pytest suite (`tests/agent/unit`, `integration`, `tests/overnight`) |
| `docs/` | 12,463 שורות md — PK, MASTER_TASK_LIST, handoffs, agent_spec, plans, overnight |
| `backlog/` | Backlog.md CLI store — `tasks/`, `archive/`, `completed/`, `decisions/`, `drafts/`, `milestones/` |
| `research/` | 24 תיקיות מחקר — **ב-.gitignore, לא נשמר ב-git** |
| `backups/` `project_sync_20260418/` | קוד ישן — ב-.gitignore |
| `data/` | קאשים מקומיים (`market_cap_cache.json`, `intraday_cache/`) — ב-.gitignore |
| `reports/` | ריקה, נוצרה עכשיו |

### A.2 — קבצי py חיים לפי גודל (ללא backups/project_sync/research)

```
5330 dashboard.py            467 agent/trader/decision_logic.py
2079 health_audit.py         465 generate_project_state.py
1409 auto_scanner.py         450 data_provider.py
 942 agent/critic/critic_v1.py       449 code_auditor.py
 925 utils.py                409 deep_scan.py
 847 agent/orchestrator.py   407 agent/analytics/postmortem_engine.py
 732 sheets_manager.py       404 gsheets_sync.py
 712 formulas.py             400 config.py
 673 daily_audit.py          395 cross_month_loaders.py
 650 post_analysis_collector.py      391 health_check.py
 625 agent/dashboard/trade_history_page.py   390 agent/dashboard/live_agent_page.py
 540 agent/analytics/score_analytics.py      387 agent/execution/position_manager.py
 500 agent/setup/create_agent_sheets.py      380 providers/alpaca_provider.py
 480 scripts/measure_phantom_coverage_v1.py  371 agent/execution/reconciler.py
                                             358 agent/logging/decision_logger.py
                                             354 providers/yfinance_provider.py
                                             354 agent/execution/alpaca_broker.py
                                             314 agent/execution/order_manager.py
                                             302 agent/sentinel/data_sentinel.py
                                             280 agent/news_detective/news_detective_v1.py
                                             247 agent/dashboard/_data_loaders.py
                                             228 agent/orchestrator_eod.py
                                             202 agent/market_context/market_context_v1.py
                                             191 agent/perception/borrow_collector.py
                                             171 agent/utils/sheets_cache.py
                                             132 agent/perception/data_quality.py
                                             102 agent/perception/tradability.py
                                              97 agent/logging/decision_id_generator.py
                                              95 agent/enrichment/sma20_cache.py
                                              94 agent/trader/trader.py
                                              45 agent/trader/score_calculator.py
```
**סה"כ py חי: 47,745 שורות** (מול 97,469 כולל backups — כלומר חצי מהקוד בריפו הוא גיבויים/ארכיון).

### A.3 — Workflows (22 קבצים, מהם 3 `.bak` שלא רצים; 19 חיים)

זמנים ב-Peru = UTC−5:

| workflow | cron (UTC) | Peru | timeout |
|---|---|---|---|
| `auto_scan.yml` | `*/1 13-21 * * 1-5` | 08:00–16:59 כל דקה | 8 |
| `agent_minute.yml` | `*/1 13-21 * * 1-5` | 08:00–16:59 כל דקה | 5 |
| `agent_market_context.yml` | `30 13` + `23 14-20` | 08:30 ואז :23 בכל שעה עד 15:23 | 5 |
| `agent_email_morning.yml` | `30 13 * * 1-5` | 08:30 | 5 |
| `health_audit.yml` | `0 11` / `30 20` / `0 3` | 06:00 / 15:30 / 22:00 | 10 |
| `backup.yml` | `7 13-21` + `7 20` + `30 21` | :07 כל שעה 08–16, 15:07, 16:30 | 10 |
| `agent_eod.yml` | `0 21 * * 1-6` | 16:00 (כולל שבת) | 10 |
| `post_analysis.yml` | `5 21 * * 1-5` | 16:05 | 45 |
| `agent_email_daily.yml` | `30 21 * * 1-5` | 16:30 | 5 |
| `backfill_ohlc.yml` | `45 21 * * 1-5` | 16:45 | 40 |
| `agent_critic.yml` | `0 22 * * 1-5` | 17:00 | 10 |
| `agent_critic_weekly.yml` | `0 23 * * 5` | שישי 18:00 | 10 |
| `agent_critic_monthly.yml` | `0 6 1 * *` | 1 לחודש 01:00 | 10 |
| `monthly_rotation.yml` | `1 5 1 * *` | 1 לחודש 00:01 | 10 |
| `prepare_next_month.yml` | `5 5 1 * *` | 1 לחודש 00:05 | — |
| `warm_oauth_token.yml` | `0 12 */3 * *` | 07:00 כל 3 ימים | — |
| `tests.yml` | on push/PR | — | — |
| `filename_guard.yml` | on push/PR | — | — |
| `overnight_report_email.yml` | on push to `overnight-reports` | — | — |

### A.4 — docs/*.md (הגדולים)

```
3889 RidingHigh_Pro_PK_v2.md    193 TASK_AUDIT_2026-06-15.md
1872 MASTER_TASK_LIST_2026-08-03.md   184 BACKLOG_DETAILED.md
 318 HYPOTHESES.md              181 SESSION_PROTOCOL.md
 266 NIGHT_RUN_2026-06-01.md    173 TASK_AUDIT_2026-05-26.md
 241 SYSTEM_REVIEW_2026-06-09_v1.md   166 PLAN_paper_portfolio_misalign_fix_v1.md
 220 MASTER_TASK_LIST.md        163 TASK-93_ROUTINE_RUNBOOK.md / INVESTIGATION_2026-06-23_edge_audit_v1.md
```
סה"כ `docs/*.md` = 12,463 שורות.

### A.5 — .gitignore ו-`reports/`

מה מוחרג ולמה (מהקובץ עצמו):
- `data/` `*.csv` `*.json` — דאטה מקומי; חריגים מפורשים: `sheets_config.json`, `whipsaw_verdicts.json`, `SCHEMA.json`, `.claude/settings.night.json` (CI קורא אותם מהדיסק).
- `backups/` `*.bak` `*.bak_*` `*.bak[0-9]*` `*_BEFORE_*` — גיבויי RULE #4. חריג: `!backlog/tasks/*.md` (כותרת תיק עלולה להכיל ".bak").
- `research/` — ארטיפקטי מחקר, מקומי בלבד (TASK-86).
- `docs/superpowers/` — ארטיפקטי brainstorm.
- `PROJECT_STATE.md` — נוצר-מחדש; commit שלו לכל ענף גרם קונפליקטים ועצר squash-merge (TASK-161).
- סודות: `google_credentials.json`, `oauth_*.json`, `.env`, `.health_audit_sheet_id`.

**`reports/` אינה ב-.gitignore.** אימות:
```
git check-ignore -v reports  → exit 1  (לא מוחרג)
git check-ignore -v research → exit 1
```
⚠️ **הערה על הראיה:** `research/` **כן** רשומה ב-.gitignore (שורה "Research artifacts — kept locally, not tracked (TASK-86)"), ובכל זאת `check-ignore` מחזיר exit 1 עליה. כלומר הבדיקה הזו לא הכריעה כאן — סביר ש-`research` כבר tracked ולכן ה-ignore לא חל, אבל **לא אימתתי זאת** ואני לא קובע. מה שכן מאומת: **אין שורה `reports` ב-.gitignore** (קראתי את הקובץ במלואו).

---

## B. מה המערכת עושה — מהקוד

### B.1 — מה נכנס, איפה, ובאיזה קצב

| מקור | מה מביא | קובץ:שורה | קצב |
|---|---|---|---|
| **FINVIZ** (scrape) | רשימת המועמדים הגולמית. פילטר: `Price: Over $2`, `Performance: Today +15%` | `auto_scanner.py:346-348` (`SanitizedOverview`) | כל דקה, 08:00–16:59 Peru |
| **Alpaca / yfinance** דרך `data_provider` | 252 ימי OHLCV לכל טיקר (60 האחרונים ל-RSI/ATR, כולם ל-52w-high) | `auto_scanner.py:193` · `data_provider.py` · `providers/*` | לכל טיקר בכל סריקה |
| **fundamentals provider** | `average_volume`, `shares_outstanding`, `float_shares` | `auto_scanner.py:206` | פעם אחת לטיקר לסריקה |
| **קאש מקומי** | `data/market_cap_cache.json` — נופל-אחורה כשאין fundamentals | `auto_scanner.py:117-134` | טעינה/שמירה בכל ריצה |
| **timeline_live (Sheets)** | הסוכן קורא ממנו את הסריקה האחרונה של היום | `agent/orchestrator.py:341-374` | כל דקה |
| **SPY/IWM (Alpaca) + ^VIX (yfinance)** | משטר-שוק | `agent/market_context/market_context_v1.py:6-8` | 08:30 ואז שעתי |
| **SEC EDGAR + Finnhub** | חדשות מהותיות | `agent/news_detective/news_detective_v1.py:5-8` | **כבוי** (`config.py:364`) |
| **Alpaca `get_asset_info`** | shortability. עמלת-השאלה נרשמת NULL — ל-Alpaca אין שדה כזה | `agent/perception/borrow_collector.py:6-13` | יומי, EOD |

⚠️ נקודת-כשל יחידה: FINVIZ. אין fallback לסקרינר — אם הוא נופל, הסקאנר יוצא בשקט (`auto_scanner.py:368-370`).

### B.2 — שרשרת ההחלטה מקצה לקצה

**שלב 1 — סריקה (`auto_scan.yml` → `auto_scanner.py`, כל דקה)**
```
run_scan()                                  auto_scanner.py:355
 ├─ is_market_hours()                       auto_scanner.py:360   ← יוצא אם מחוץ לשעות
 ├─ fetch_finviz()                          auto_scanner.py:340
 ├─ לכל טיקר: analyze_ticker()              auto_scanner.py:149
 │    ├─ get_market_cap_smart()             utils.py:313
 │    ├─ RSI/ATR (ta) → calculate_atrx      formulas.py:109 · validate_atrx:121
 │    ├─ calculate_runup / gap / rel_vol / typical_price_dist / float_pct
 │    ├─ calculate_mxv()                    formulas.py:85
 │    └─ calculate_score(metrics)           formulas.py:584
 ├─ מיון לפי Score יורד                     auto_scanner.py:429
 ├─ כתיבה ל-timeline_live (28 עמודות)      auto_scanner.py:442-478
 ├─ אם is_snapshot_time() (≈דקה לפני נעילה, DST-aware)   auto_scanner.py:77-89
 │    ├─ daily_snapshots (Score מרוקן)      auto_scanner.py:487-500
 │    ├─ portfolio: Score>=70 → שורה חדשה   auto_scanner.py:503-525
 │    └─ _save_daily_summary()              auto_scanner.py:571
 ├─ update_portfolio_live()                 auto_scanner.py:625
 ├─ update_ticker_follow_up()               auto_scanner.py:768
 ├─ update_live_trades()                    auto_scanner.py:999
 └─ אם minute%5==0: sync_score_tracker()    auto_scanner.py:1151
```

**שלב 2 — הסוכן (`agent_minute.yml` → `agent/orchestrator.py`, כל דקה)**
```
run()                                       agent/orchestrator.py:518
 ├─ is_market_hours(now)                    :104   (08:30–15:00, ו-utils.is_trading_day לחגים)
 ├─ check_emergency_stop()                  :131   (system_events, חלון 24ש')
 ├─ detect_outage(now)                      :382   (>10 דק' פער → אירוע; >30 → מייל)
 ├─ אתחול רכיבים                            :608-670
 ├─ build_account_state(broker)             :179   (קריאה אחת paper_portfolio + אחת decision_log)
 ├─ read_latest_signals()                   :341 → _signal_from_timeline_row():44
 ├─ sentinel.check_system()                 :698   ← HALT לכל הריצה אם BLOCK
 └─ לכל סיגנל:                              :721
      ├─ sentinel.check_signal()            data_sentinel.py:147   (shadow → תמיד ALLOW, :193-198)
      ├─ _maybe_write_news()                :500   (no-op, News כבוי)
      ├─ trader.evaluate → evaluate_signal() decision_logic.py:208
      │     ├─ calculate_agent_score()      score_calculator.py:26 → formulas.calculate_score
      │     ├─ validate_quality()           agent/perception/data_quality.py
      │     ├─ _check_filters()             decision_logic.py:354   ← שער הכניסה
      │     ├─ _observe_explicit_gate()     :157   (צל בלבד)
      │     └─ _observe_mxv_price_gate()    :195   (צל בלבד)
      ├─ decision_logger.log(decision)      agent/logging/decision_logger.py
      └─ אם ENTER: order_manager.execute()  agent/execution/order_manager.py:109
            ├─ _submit_with_retry()         :176   (SimulatedOrder ב-DRY_RUN)
            ├─ _wait_for_fill()             :209
            └─ _write_to_portfolio()        :248 → Status="DRY_RUN_OPEN"
 ├─ flush_skip_summary() / flush_shadow_gate_summary()   :781, :787
 ├─ position_manager.monitor_all()          position_manager.py:144
 │     └─ _process_position()               :204
 │           ├─ DRY_RUN: מחיר>=SL → סגירה   :244
 │           ├─ DRY_RUN: מחיר<=TP → סגירה   :248
 │           └─ אחרת: עדכון CurrentPrice/UnrealizedPnL   :262
 │                 └─ _close_position()     :307 → postmortem_engine.generate()
 └─ eod_close_all() אם is_eod_window()      :802  ← **לעולם לא נכנס** (AGENT_FORCE_EOD_CLOSE=False)
```

**שלב 3 — סגירת יום (16:00–16:45)**
```
agent/orchestrator_eod.py:  reconciler.reconcile() → score_analytics.run_daily() → (שבת) run_weekly()
auto_scanner.py:1312        run_eod()
post_analysis_collector.py:389  run()
   ├─ select_candidates()   :78    ← MxV<=-100 (לא Score) — TASK-200
   ├─ fetch_ohlc_for_days() :205
   ├─ utils.calculate_stats()      utils.py:426  → MaxDrop/TP10/TP15/TP20/SL_Hit_D5/NetPnL_*
   └─ utils.classify_trade()       utils.py:513  → WIN/LOSS/WHIPSAW/NO_TOUCH/PENDING
enrich_post_analysis.py     העשרה
backfill_ohlc.yml (16:45)   מילוי פערים
```

**שתי לולאות-מסחר נפרדות, במכוון:** הסקאנר מריץ *סימולציה* על נייר (portfolio / live_trades / post_analysis, TP/SL=10%, חלון 5 ימים). הסוכן מריץ *פוזיציות* משלו (paper_portfolio, TP/SL=10%, בלי מגבלת-זמן). הן לא מדברות ביניהן חוץ מכך שהסוכן קורא `timeline_live` שהסקאנר כותב.

### B.3 — כל המטריקות

| מטריקה | נוסחה | מוגדרת ב- | מי צורך |
|---|---|---|---|
| MxV | `(mc − price×vol)/mc × 100` | `formulas.py:85` | Score, שער-כניסה (F2), `select_candidates` |
| RunUp | `(price − open)/open × 100` | `formulas.py:97` | Score, F3, ROCKET_GUARD |
| ATRX | `(high − low)/ATR14` (יחס) | `formulas.py:109` + `validate_atrx:121` | Score |
| Gap | `(open − prev_close)/prev_close × 100` | `formulas.py:135` | timeline_live בלבד (הוסר מ-Score v2, `formulas.py:636`) |
| TypicalPriceDist | `(price/((H+L+C)/3) − 1) × 100` | `formulas.py:147` | Score |
| ~~vwap_dist~~ | alias ל-TypicalPriceDist | `formulas.py:168` | deprecated |
| REL_VOL | `vol/avg_vol`, cap 100 | `formulas.py:179` (`REL_VOL_CAP` `config.py:71`) | Score |
| Float% | `float/outstanding × 100` | `formulas.py:194` | תצוגה, מחקר |
| PriceToHigh | `(price − high)/high × 100` | `formulas.py:216` | ROCKET_GUARD (F11) |
| PriceTo52WHigh | `(price − h52)/h52 × 100` | `formulas.py:234` | תצוגה |
| ScanChange% | `(price − prev_close)/prev_close × 100` | `formulas.py:250` | Score |
| DropFromHigh | `(high − price)/high × 100` | `formulas.py:272` | מעקב תוך-יומי |
| MaxDrop | `(min_low − scan)/scan × 100` | `formulas.py:292` | `calculate_stats` — ground truth |
| D1_Gap% | `(D1_open − scan)/scan × 100` | `formulas.py:311` | `calculate_stats` |
| night_return | `−D1_Gap%` (היפוך-סימן, לא נוסחה שנייה) | `formulas.py:330` | post_analysis |
| is_interday_artifact | `\|Δclose\| > 100%` | `formulas.py:342` (סף `config.py:76`) | גלאי split/halt |
| phantom tier | אות-ראשונה כפולה + הסימן המקוצר קיים ביקום | `formulas.py:395`, `441` | ניקוי טיקרים משובשים |
| NetPnL | `gross − borrow×days/365`, slip 1%/צד | `formulas.py:494` | `calculate_stats` |
| PnL% | short: `(entry−exit)/entry×100` | `formulas.py:529` | dashboard |
| Wilson CI | — | `formulas.py:640`, `661` | הצגת WR עם אי-ודאות |
| **Score v2** | 7 רכיבים, סכום משקלים 100 | `formulas.py:584`, משקלים `config.py:40-59` | ראה §B.4 |

**כפילויות SSoT שמצאתי בקוד (§10 מפר):**

1. **`price_to_high` מחושב inline** ב-`auto_scanner.py:265` למרות ש-`calculate_price_to_high` מיובא בשורה 38 ולא נקרא שם. אותה נוסחה בדיוק, שני מקומות.
2. **`price_to_52w_high` מחושב inline** ב-`auto_scanner.py:273` — בעוד ש-`auto_scanner.py:931` **כן** קורא ל-`calculate_price_to_52w_high`. כלומר אותו קובץ עושה את זה בשתי דרכים.
3. **`typical_price` מחושב inline** ב-`auto_scanner.py:255` (`(H+L+C)/3`) במקביל ל-`formulas.calculate_typical_price_dist:160` שמחשב את אותו ביטוי בפנים.
4. **`_is_day_complete` ב-`dashboard.py:1928` מכפיל את `utils.is_day_complete`** — זה TASK-222 הפתוח.
5. **חלון ה-5 ימים קיים ב-3 ייצוגים** — `range(1,6)` ב-`utils.py` (הקלסיפייר האמיתי), `MAX_HOLDING_DAYS` (תצוגה בלבד), `CLASSIFY_DAYS` (גבול-איסוף). זו **הפרדה מכוונת ומתועדת** (`config.py:143-152`), לא באג — שינוי כאן לא ישנה בשקט את ה-WR הרשמי.
6. `calculate_vwap_dist` (`formulas.py:168`) — alias deprecated, עדיין מיובא ב-`auto_scanner.py:33`.

### B.4 — שער הכניסה החי היום

הפונקציה: `_check_filters()` ב-`agent/trader/decision_logic.py:354`.
שני מתגי-קונפיג משנים את ההתנהגות שלה:
- `EXPLICIT_GATE_MODE = "active"` (`config.py:374`) ⇒ `_score_gate_on = False` (`decision_logic.py:309`) ⇒ **פילטר Score כבוי**.
- `ENTRY_GATE_MINIMAL = True` (`config.py:378`) ⇒ `_minimal = True` (`:369`) ⇒ **6 פילטרים כבויים**.

**מה חוסם כניסה בפועל היום (9 פילטרים):**

| # | תנאי | שורה |
|---|---|---|
| F2 | `MxV > −100` → SKIP `MXV_TOO_HIGH` — **זה הנהג היחיד שנשאר מהאיכות של הסיגנל** | `:376` |
| F4b | `price < $3` → `PRICE_TOO_LOW` | `:391` |
| F6 | `quality["is_trustworthy"]` False → `QUALITY_TOO_LOW` | `:419` |
| F6b | `account_state_unavailable` → `ACCOUNT_STATE_UNAVAILABLE` (TASK-244, נכתב 8/3) | `:428` |
| F7 | פוזיציה קיימת בטיקר | `:433` |
| F8a | 5 פוזיציות פתוחות (cold-start concurrent) | `:438` |
| F8b | 10 עסקאות היום (cold-start daily) | `:440` |
| F9 | כניסה חוזרת: מקסימום 1 לטיקר ליום | `:444` |
| F10 | buying power < $1000 | `:449` |

**מה כבוי (מחושב או שקוף, לא חוסם):**

| מה | סטטוס | שורה |
|---|---|---|
| F1 Score >= 50 | **כבוי** — Score עדיין מחושב (`:270`) ונרשם ב-decision_log, אבל לא מכריע | `:372` |
| F3 RunUp >= 0 | כבוי ע"י `_minimal` | `:380` |
| F4 Volume >= 100K | כבוי ע"י `_minimal` | `:384` |
| F4c blacklist (AEHL, TDIC) | כבוי ע"י `_minimal` | `:398` |
| F4d Toxic Profile (RSI>88 ∧ SMA20>250%) | כבוי ע"י `_minimal` | `:408` |
| F5 MarketCap $5M–$2B | כבוי ע"י `_minimal` | `:413` |
| F11 ROCKET_GUARD (RunUp>=50 ∧ PTH>=−10) | כבוי ע"י `_minimal` | `:462` |
| Data Sentinel | shadow — BLOCK הופך ל-ALLOW | `data_sentinel.py:193-198` |
| shadow explicit gate | תיעוד בלבד, אף פעם לא נוגע ב-`d.action` | `decision_logic.py:157-179` |
| shadow MxV+price gate | תיעוד בלבד | `decision_logic.py:195-203` |

**המשמעות מהקוד:** היום כניסה נקבעת כמעט לחלוטין ע"י `MxV <= −100 AND price >= $3`. שאר הפילטרים החיים הם מגבלות-חשיפה (כמה פוזיציות, כמה כסף), לא איכות-סיגנל.

### B.5 — הפילטרים לפי סדר ומה כל אחד חוסם

הסדר בקוד הוא לפי הסתברות-כשל יורדת, ויש בו נקודה מכוונת אחת: **F6b חייב להקדים את F7–F10**. אם `build_account_state` נכשל (429 מ-Sheets), כל השדות של F7–F10 הם ברירות-מחדל ולא מדידות — בלעדיו כולם היו עוברים בבת-אחת. זה בדיוק מה שקרה חי ב-2026-07-22: 43 ENTER על 4 טיקרים (`decision_logic.py:422-430`).

הרשימה המלאה בסדר הריצה: F1 Score → F2 MxV → F3 RunUp → F4 Volume → F4b Price → F4c Blacklist → F4d Toxic → F5 MarketCap → F6 Quality → **F6b AccountState** → F7 Existing → F8 ColdStart → F9 Re-entry → F10 BuyingPower → F11 ROCKET_GUARD.

לפני כל זה, ברמת-הריצה: `is_market_hours` (orchestrator:549), `check_emergency_stop` (:556), `sentinel.check_system` (:698 — HALT לכל הריצה).

### B.6 — הסוכנים

הקוד לא ממספר אותם. המספור (#1–#5) קיים ב-docs. מה שקיים בפועל כמודול רץ:

| # | סוכן | קוד | מתי רץ | כותב ל- | פעיל היום? |
|---|---|---|---|---|---|
| 1 | **The Trader** | `agent/orchestrator.py` + `agent/trader/` + `agent/execution/` | כל דקה 08:00–16:59 (`agent_minute.yml`), בפועל 08:30–15:00 (`is_market_hours`) | `decision_log`, `paper_portfolio`, `postmortems`, `skip_summary`, `shadow_gate_events` | ✅ ב-**DRY_RUN** |
| 2 | **Data Sentinel** | `agent/sentinel/` (7 בדיקות ב-`checks/`) | בתוך כל ריצת Trader | `sentinel_events`, `system_events` | ✅ אבל **shadow** — לא חוסם |
| 3 | **The Critic** | `agent/critic/critic_v1.py` + 3 orchestrators | יומי 17:00 · שבועי שישי 18:00 · חודשי 1 לחודש 01:00 | מייל + `weekly_summary` / `monthly_summary` | ✅ |
| 4 | **News Detective** | `agent/news_detective/news_detective_v1.py` | היה: כל דקה | `news_findings` | ❌ **כבוי** (`config.py:364`, TASK-176) |
| 5 | **Market Context** | `agent/market_context/` | 08:30 ואז :23 בכל שעה | `market_context` | ✅ |

מודולים נוספים שאינם "סוכן" אבל רצים כמוהו:
- `agent/analytics/postmortem_engine.py` — פר-פוזיציה, בסגירה. כותב `postmortems`.
- `agent/analytics/score_analytics.py` — יומי ב-EOD; שבועי בשבת → `pending_suggestions`. **תצפיתי בלבד, אף פעם לא משנה נוסחה** (docstring:6-11).
- `agent/execution/reconciler.py` — EOD, מזהה drift מול Alpaca. תיקון-אוטומטי **כבוי** (`RECONCILE_AUTO_REPAIR=False`, `config.py:317`).
- `agent/perception/borrow_collector.py` — EOD, `borrow_data`.
- **Agent #8 "Routine Checker"** (`docs/AGENT8_CAPABILITIES_MAP.md`) — בקרת-איכות על עבודת-פיתוח לילית, לא סוכן-מסחר, לא רץ בזמן-אמת.

### B.7 — סכמת הנתונים

**9 גיליונות חודשיים** (`sheets_manager.py:38-48`) — קובץ Drive נפרד לכל אחד, תיקייה לחודש:

| טאב | הכותב | תדירות |
|---|---|---|
| `timeline_live` (28 עמ', `sheets_manager.py:51-67`) | `auto_scanner.run_scan()` `:442` | כל דקה, append-only |
| `daily_snapshots` | `auto_scanner` `:487` | פעם ביום, ליד הנעילה |
| `daily_summary` | `_save_daily_summary()` `:571` + `run_eod()` | ביום |
| `post_analysis` | `post_analysis_collector.run()` `:389` | 16:05 |
| `portfolio` | `auto_scanner` `:503` (Score>=70) | ליד הנעילה |
| `portfolio_live` | `update_portfolio_live()` `:625` | כל דקה |
| `score_tracker` | `sync_score_tracker()` `:1151` | כל 5 דקות |
| `live_trades` | `update_live_trades()` `:999` | כל דקה |
| `ticker_follow_up` (30 עמ', `:69-84`) | `update_ticker_follow_up()` `:768` | כל דקה, מעקב 3–5 ימים |

**16 טאבים של הסוכן** (`agent/setup/create_agent_sheets.py:36-53`):
`decision_log` (42 עמ') · `paper_portfolio` · `score_analytics` · `postmortems` · `sentinel_events` · `system_events` · `market_context` · `news_findings` · `pending_suggestions` · `config_history` · `borrow_data` · `borrow_coverage` · `agent_scorecard` · `weekly_summary` · `skip_summary` · `shadow_gate_events`.

מהם **3 CORE** — `paper_portfolio`, `decision_log`, `postmortems` (`config.py:352`). drift בכותרת שלהם **מעלה חריגה ועוצר provisioning**; שאר הטאבים רק מזהירים. זה נכתב אחרי שיבוש 8 שורות ב-`paper_portfolio` ביולי (`config.py:347-352`).

בנוסף, מחוץ לרוטציה: גיליון **Health-Audit** (טאבים History / Latest / Failed) ו-**RH-Summaries**.

**רוטציה:** 1 לחודש 00:01 — `monthly_rotation.py` מפעיל את החודש החדש; 00:05 — `prepare_next_month.py` יוצר מראש את החודש שאחריו. שניהם עושים commit ל-`sheets_config.json` בחזרה לריפו.

### B.8 — מצבי בטיחות והקפאות

| דגל | ערך | איפה מוגדר | איפה נאכף |
|---|---|---|---|
| `AGENT_DRY_RUN` | **True** | `config.py:340` | `alpaca_broker.py:84`, `:156` — אם `AGENT_LIVE_PAPER` False מוחזר `SimulatedOrder` ולא נשלחת פקודה |
| `AGENT_LIVE_PAPER` | **False** | `config.py:342` | `alpaca_broker.py:156` |
| `SCORE_WRITE_FROZEN` | **True** | `config.py:341` | `auto_scanner.py:50-64` — Score נכתב כמחרוזת ריקה; מחושב בזיכרון לצורך מיון |
| `DATA_SENTINEL_ENABLED` | True | `config.py:358` | `data_sentinel.py:110` |
| `SENTINEL_MODE` | **"shadow"** | `config.py:359` | `data_sentinel.py:193-198` — BLOCK→ALLOW |
| `NEWS_DETECTIVE_ENABLED` | **False** | `config.py:364` | `orchestrator.py:509-511` |
| `EXPLICIT_GATE_MODE` | **"active"** | `config.py:374` | `decision_logic.py:309` |
| `ENTRY_GATE_MINIMAL` | **True** | `config.py:378` | `decision_logic.py:369` |
| `MXV_PRICE_GATE_MODE` | "shadow" | `config.py:382` | `decision_logic.py:200` |
| `AGENT_FORCE_EOD_CLOSE` | **False** | `config.py:315` | `orchestrator.py:117-124` — `is_eod_window` תמיד False |
| `RECONCILE_AUTO_REPAIR` | **False** | `config.py:317` | `agent/execution/reconciler.py` |
| `AGENT_COLD_START_*` | 5 מקבילות / 10 ליום | `config.py:325-326` | `decision_logic.py:438-441` |
| Emergency stop | ידני | — | `orchestrator.py:131-172` — שורה `EMERGENCY_STOP_REQUESTED` ב-`system_events` בחלון 24ש' עוצרת את הריצה |
| Sentinel system HALT | — | — | `orchestrator.py:698-715` — עוצר ריצה שלמה ושולח מייל |
| Header-drift guard | — | `config.py:352` | `create_agent_sheets.py:265-336` |
| filename-length guard | — | — | `filename_guard.yml` — נכשל על basename >= 250B (CI נפל ל-16ש' בגלל 333B) |

### B.9 — מה מסומן זמני / מוקפא / כבוי / ממתין-לתאריך

| מה | מצב | שורה |
|---|---|---|
| Score — כתיבה לגיליונות | מוקפא, עידן "scoreless" קדימה-בלבד (ADR-009) | `config.py:341` |
| `CLASSIFY_DAYS = 5` | **FROZEN** — שינוי ישנה את ה-WR הרשמי; אסור להרחיב | `config.py:142-152` |
| `COLLECT_DAYS_FORWARD_FROM = "2026-06-13"` | חתך קדימה-בלבד: שורות לפניו נשארות D1–D5 ולעולם לא נוגעים בהן שוב | `config.py:161` |
| News Detective | כבוי, הפיך | `config.py:364` |
| Sentinel active mode | מוקפא ב-shadow מאז 3/6 — הנגד-עובדה הראתה WR 64% למה שהיה נחסם מול 41% | `config.py:359` |
| `RECONCILE_AUTO_REPAIR` | מותנה בשער שלא נפתח (TASK-106/109) | `config.py:317` |
| `MXV_PRICE_GATE_MODE` | shadow; קידום ל-active הוא TASK-194 | `config.py:382` |
| catch-up ל-cron-drift | **Phase 2 לא ממומש** — יש רק תצפית ומייל | `orchestrator.py:598` |
| `position_sync` | מחזיר `POSITION_SYNC_DEFERRED` | `agent/sentinel/checks/position_sync.py:46` |
| `calculate_vwap_dist` | deprecated, "יוסר ב-#11 step D" | `formulas.py:168-176` |
| Overnight runner | **DISARMED 2026-07-02** אחרי 9 לילות שירה ונעצר לפני execute | `docs/POSTMORTEM_overnight_ARMED_2026-07-02.md` |
| `AGENT_SCORE_VERSION = "v2.6"` | תיוג postmortems | `config.py:345` |
| `AGENT_MIN_SCORE = 50` | היסטורי — השער כבוי מאז ה-flip ב-6/29 | `config.py:296` |

### B.10 — איך נראה יום שלם (Peru)

```
00:01  [1 לחודש] monthly_rotation      — הפעלת החודש החדש
00:05  [1 לחודש] prepare_next_month    — יצירה מראש של החודש הבא
01:00  [1 לחודש] agent_critic_monthly  — מייל סיכום חודשי
06:00  health_audit #1                 — 30 בדיקות → מייל 🔴/🟡/✅
07:00  [כל 3 ימים] warm_oauth_token
08:00  auto_scan + agent_minute מתחילים לרוץ — אך שניהם יוצאים ב-is_market_hours
08:30  🟢 פתיחת NYSE (EDT). הסקאנר והסוכן מתחילים לעבוד באמת
08:30  agent_email_morning             — מייל בוקר
08:30  agent_market_context            — משטר-שוק ראשון
08:07→16:07  backup כל שעה ב-:07       — CSV של post_analysis כ-artifact
09:23–15:23  agent_market_context      — :23 בכל שעה
       ↻ כל דקה: FINVIZ → analyze_ticker → timeline_live → portfolio_live →
                  ticker_follow_up → live_trades
       ↻ כל 5 דקות: score_tracker
       ↻ כל דקה: הסוכן קורא timeline_live, מסנן, נכנס/מדלג, מנטר פוזיציות
14:55  daily_snapshots + portfolio + daily_summary (is_snapshot_time, DST-aware)
15:00  🔴 נעילת NYSE. is_market_hours נסגר — הסקאנר והסוכן יוצאים מיד
15:07  backup
15:30  health_audit #2                 — הוזז מחוץ לשעות המסחר (TASK-58, לחץ quota)
16:00  agent_eod                       — reconcile → score_analytics → self-heal טאבים
16:05  post_analysis_collector         — timeout 45 דק'
16:30  backup #3 + agent_email_daily
16:45  backfill_ohlc                   — timeout 40 דק', מנותק מה-collector (TASK-190)
17:00  agent_critic                    — מייל יומי
18:00  [שישי] agent_critic_weekly
22:00  health_audit #3
```

⚠️ פער מדוד: `agent_minute.yml` ו-`auto_scan.yml` רצים 08:00–16:59 Peru (`13-21 UTC`), אבל ההיגיון הפנימי חוסם מחוץ ל-08:30–15:00. החלון הרחב הוא מכוון — הוא מכסה גם EST וגם EDT (`auto_scan.yml:5`).

⚠️ פער בין קוד לתיעוד: §10 ב-PK אומר health_audit #2 ב-12:00; ה-workflow אומר `30 20 UTC` = 15:30 Peru (`health_audit.yml:11`, עם הערה שזה הוזז ב-TASK-58). הקוד מנצח.

---

## C. מה נעשה עד היום

### C.1 — git log 60 יום אחרונים (2026-06-06 → 2026-08-05): **384 commits** ב-origin/main

**נושא 1 — מלחמת ה-429 מול Google Sheets (יוני סוף → יולי תחילת).**
זה היה הנושא הגדול. הרצף: TASK-58 (health_audit ל-SA ייעודי, `c9dc68a`+`4ba854b`) → TASK-214 audit (`7e44fcc`, "de-dup הוא לא התיקון") → TASK-215 (SA ייעודי ל-auto_scan, `ec46b4d`+`54f6e9f`) → TASK-136 (position_manager חולק קאש, `3456d8c`) → TASK-192 (batch-merge לכתיבות portfolio, `0490ab2`) → **TASK-176: כיבוי News Detective מהנתיב-הדקתי** (`5f0b288`, "מסיר 46/91 מה-429"). מה השתנה מהותית: השורש אותר כ-flood-קריאות של news+sentinel ולא כ-service-account משותף — `069aaf5` מתקן במפורש טענה קודמת. נמדד 24.7→1.3 אירועי 429 (~95% ירידה, `5e0d74d`).

**נושא 2 — פירוק ה-Score משער-הכניסה (6/24 → 6/29).**
TASK-128 בשלושה צעדים: הפיכת שער-ה-Score לניתן-לדילוג בשרשרת אחת (`31c5b5e`) → observer בצל (`8e6e7b4`) → התמדה ל-`shadow_gate_events` + ADR-009 (`96c0f8c`). ואז ב-6/29 **ה-flip**: `7f6b965` — `EXPLICIT_GATE_MODE=active`, MxV הופך לנהג החי. מיד אחריו `6b5586d` — `ENTRY_GATE_MINIMAL`, כיבוי 6 פילטרים והידוק re-entry מ-3 ל-1. מה השתנה מהותית: המערכת עברה מ"Score מכריע" ל"MxV+מחיר מכריעים", בלי צבירת-shadow של שבועיים — החלטת בעלים מודעת תחת DRY_RUN (`config.py:372-373`).

**נושא 3 — באגי DST (6/29 → 7/05).**
דפוס אחד חוזר ארבע פעמים: קוד שהניח 15:00 Peru כנעילה, נכון רק בקיץ. `a0d63fe` (`is_market_hours`) → `fe2f226` (`is_day_complete`) → `da13c10` (`is_snapshot_time`) → `5aee2cb` (MinToClose + snapshot + health-check). הקרונים הורחבו ל-`13-21 UTC`. מה השתנה מהותית: באג-נובמבר לטנטי נסגר לפני שהתפוצץ.

**נושא 4 — יושרת-דאטה ב-post_analysis (6/27 → 6/29).**
`96de9f0` — יקום-האיסוף עבר מ-`Score>=60` ל-`MxV<=-100` (TASK-200; הכרחי כי Score קפוא). `4a2a999`+`9a5d4fc` — שומר-שפיות ל-Float% מול נתוני-ספק זבל. `1bee4fc` — עמודת `night_return`. `32384bf` — סגירת דליפת interday-artifact.

**נושא 5 — שיבוש עמודות ב-paper_portfolio (7/01).**
TASK-217 בארבעה צעדים באותו יום: הקשחת כתיבת-כניסה ל-by-name (`dd46470`) → helpers טהורים לתיקון (`7c6f079`) → מיגרציה חיה של 2026-07 ותיקון 8 שורות (`0c441b7`) → פונקציות header-guard (`ad95806`). ואז TASK-219 (`66c984c`) — guard סלקטיבי, CORE_TABS מעלים חריגה.

**נושא 6 — provisioning ורוטציה (7/29).**
`7d9c896` תיקן את הקצאת אוגוסט לפני הרוטציה של 1/8; `dd38543` יצר את ספטמבר מראש; `411e892` תיקן טענה שגויה לגבי ספטמבר ב-PK.

**נושא 7 — טיקרים רפאים (7/29 → 8/03).**
`60612f4` מדד את ההיקף. `21d1766` — השורש: finviz מרנדרת אות-placeholder של לוגו בתא הטיקר, ולכן AMIX הגיע כ-AAMIX. התיקון קורא את הטיקר מתכונת-DOM ולא מטקסט-התא. `4148a9f` נעל בבדיקה. `f1cf01a` (8/03) הוסיף סיווג דו-שכבתי CONFIRMED/SUSPECT.

**נושא 8 — כשל-סגור על account state (8/03).**
`f1cf01a` — "fail closed on unreadable account state". זה F6b. באותו commit גם "void HYP-002".

**נושא 9 — הרצת-לילה אוטונומית (6/18 → 7/02).**
נבנתה ומוזגה (`1421777`), הוקשחה סבב אחרי סבב מול סקירה יריבה (`1c15b44`, `ff93c20`, `8f68ec6`), אוישה (`471c974`) — ואז **בוטלה**. `93e56cf` הוא הפוסטמורטם: הרצה שלטענת התיעוד היתה מנוטרלת ירתה 9 לילות; השורש — `unload` אינו `disable`, ה-plist נטען מחדש בכל login. `674b0b3` תיקן 6 טענות-DISARMED שגויות.

**נושא 10 — ניקוי-בקלוג ותיעוד (8/03).**
`07d50c0` (MASTER_TASK_LIST ל-65 תיקים) → `b6745e0` (65→56) → `72d357d` (56→53).

### C.2 — Changelog ה-PK

**212 רשומות, מ-v2.11 ועד v4.12 הנוכחית** (שורות 21–876, 855 שורות טקסט).

⚠️ **לא הדבקתי כאן את הגוף המלא.** שתי סיבות, שתיהן מפורשות: (א) RULE #14 בפרויקט אוסר להדפיס את גוף ה-PK לפלט; (ב) 855 שורות עברית יטביעו את הדוח. מה שכן נמצא כאן: **אינדקס מלא של כל 212 הגרסאות** לפי מספר ותאריך — כלומר אפשר לאתר כל רשומה בשנייה. הפקודה לקריאת הגוף המלא, אם תרצה: `sed -n '21,876p' docs/RidingHigh_Pro_PK_v2.md`.

תדירות: 212 bumps ב-~11 שבועות ≈ 2.8 ליום-עבודה. הצפיפות אינה אחידה — 6/29 לבדו נשא 8 גרסאות (3.72→3.79), 7/01 נשא 8 (3.91→3.99). זה עצמו עובדה על קצב-העבודה: ימים של flip-קונפיג מייצרים bump לכל צעד.

**האינדקס המלא (חדש→ישן):**
```
v4.12 08-03 · v4.11 08-03 · v4.10 07-29 · v4.09 07-29 · v4.08 07-29 · v4.07 07-05
v4.06 07-04 · v4.05 07-04 · v4.04 07-04 · v4.03 07-03 · v4.02 07-03 · v4.01 07-02
v4.00 07-02 · v3.99 07-01 · v3.98 07-01 · v3.97 07-01 · v3.96 07-01 · v3.95 07-01
v3.94 07-01 · v3.93 07-01 · v3.92 07-01 · v3.91 07-01 · v3.90 06-30 · v3.89 06-30
v3.88 06-30 · v3.87 06-30 · v3.86 06-30 · v3.85 06-30 · v3.84 06-30 · v3.83 06-30
v3.82 06-30 · v3.81 06-30 · v3.80 06-30 · v3.79 06-29 · v3.78 06-29 · v3.77 06-29
v3.76 06-29 · v3.75 06-29 · v3.74 06-29 · v3.73 06-29 · v3.72 06-29 · v3.71 06-28
v3.70 06-28 · v3.69 06-28 · v3.68 06-28 · v3.67 06-27 · v3.66 06-27 · v3.65 06-27
v3.64 06-27 · v3.63 06-27 · v3.62 06-27 · v3.61 06-25 · v3.60→3.54 06-24 (7)
v3.53→3.48 06-23 (6) · v3.47→3.45 06-22 (3) · v3.44→3.39 06-21 (6)
v3.38 06-19 · v3.37 06-19 · v3.36 06-18 · v3.35 06-18 · v3.34 06-18 · v3.33 06-17
v3.32→3.29 06-16 (4) · v3.28 06-15 · v3.27 06-15 · v3.26→3.20 06-14 (7)
v3.19→3.14 06-13 (6) · v3.13→3.07 06-12 (7) · v3.06→3.02 06-11 (5)
v3.01→2.96 06-10 (6) · v2.95→2.91 06-09 (5) · v2.90→2.87 06-08 (4)
v2.86→2.84 06-07 (3) · v2.83 06-05 · v2.82→2.75 06-04 (8) · v2.74→2.64 06-03 (11)
v2.63→2.58 06-02 (6) · v2.57→2.55 06-01 (3) · v2.54→2.49 05-30/31 (5)
v2.48 05-29 · v2.47→2.42 05-28 (6) · v2.41 05-27 · v2.39→2.37 05-26 (3)
v2.36→2.34 05-25 (3) · v2.33 05-24 · v2.32 05-24 · v2.31→2.27 05-23 (5)
v2.26→2.19 05-19 (8) · v2.18→2.16 05-18 (3) · v2.15 05-17 · v2.14 05-17
v2.13 05-16 · v2.12 05-16 · v2.11 05-04
```
(שים לב: v2.52 ו-v2.40 חסרות ברצף.)

### C.3 — 53 תיקים פתוחים — כותרות בלבד

**In Progress (3):**
```
[HIGH]   TASK-186  Build overnight autonomous bug-fix runner
[MEDIUM] TASK-128  Gate כניסה מבוסס-מדדים בא shadow mode
         TASK-217  Fix paper_portfolio column misalignment (entry-write TPPrice/SLPrice vs header)
```

**To Do — HIGH (5):**
```
TASK-179  Validate crossover-short on hold-out (n>=150 events, worst-case costs)
TASK-244  Re-entry guard did not block repeat ENTERs on open positions
TASK-248  requirements.txt pins finvizfinance 0.14.6 which cannot parse finviz today
TASK-249  Collector reprocesses the whole month every night
TASK-250  Unit tests read live Sheets, seven of them
```

**To Do — MEDIUM (28):**
```
TASK-9    P2.2 — Sentinel Analytics module
TASK-10   P2.3 — Filter 12 ticker_reputation
TASK-39   AUDIT.4 — Email consolidation
TASK-54   PreToolUse Phase 2 — enforce RELEVANT skill, not just any
TASK-101  התקנת security-guidance plugin + אימות אי-התנגשות עם skill-gate hook
TASK-126  חילוץ SKIPs היסטוריים מלוגי GitHub Actions לפני פקיעת retention
TASK-176  News Detective demotion — EOD-only or disable pending value proof
TASK-194  ADR-009 post-flip monitoring: track active-mode entries vs Score-gated baseline
TASK-215  Dedicated SA for auto_scan (mirror TASK-58) — real fix for market-hours 429
TASK-216  Structural: mid-month agent-tab misses pre-provisioned next month (no backfill)
TASK-222  dashboard.py:1928 _is_day_complete duplicates utils.is_day_complete
TASK-224  qty guard: quantity<1 => SKIP with dedicated skip_reason
TASK-225  Hold-window research: D1-D25 optimal holding analysis
TASK-226  Active alert on scanner-writes=0 during market hours (unify with TASK-166)
TASK-229  HYP-004-draft: late-entry (>=15:30 ET) forward research
TASK-230  Data-gap audit + enrichment for peak-signature research
TASK-243  Harden root resolution and rotation guards
TASK-245  Scan volume halved starting 2026-07-15, same date as ticker corruption
TASK-246  Clean up 83 stuck DRY_RUN_OPEN positions in 2026-07 paper_portfolio
TASK-251  August live_trades points at its own file, every other month aliases score_tracker
TASK-252  Three missing health checks: symbol sanity, position over HOLD, row count
TASK-253  timeline_live duplicate rows from overlapping scanner runs
```

**To Do — LOW (6):**
```
TASK-109  enable RECONCILE_AUTO_REPAIR after flag-only proves accurate
TASK-145  Investigate agent_critic_monthly 21.9pct failure rate
TASK-153  Review and adopt DROPSLAB_PK_DRAFT as docs/DropsLab_PK.md
TASK-208  Decouple Score from scanner ranking + portfolio selection (auto_scanner)
TASK-209  Retire calculate_score or demote to logged diagnostic (~15 consumers)
TASK-254  score_analytics reports n=0 while July closed sixty positions
```

**To Do — ללא עדיפות (16):**
```
TASK-49   NCT recon mismatch — decision_log vs paper_portfolio
TASK-65   פער postmortems: פוזיציות סגורות ללא postmortem
TASK-66   SENTINEL counterfactual הפוך — הנחסמות הן המנצחות
TASK-71   ניתוח 'הצד השני' — edge חדש משני הצדדים
TASK-73   הרחבת CRITIC במודול ניתוח-עומק
TASK-74   השלמת תוצאות ל-946 מניות חסרות
TASK-82   הוספת 5 מדדי-שורט מקצועיים חסרים
TASK-83   DropsLab: הרחבת drops_post מ-5 ל-15 ימי מעקב
TASK-88   מייל חודשי: גרפים
TASK-92   דיון: צמצום תיעוד-דקה ב-timeline_live
TASK-202  fix: collector cross-month backfill
TASK-205  Display D6-D25 forward journey in dashboard
TASK-206  add fundamental fields
TASK-218  agent_minute 429: sentinel worksheet-handle cache
TASK-219  TASK-217 Task4 wiring: provisioning fail-loud on header drift
TASK-240  Audit data reliability 2026-07-05 to 2026-07-28
TASK-241  Review agent and trade behaviour 2026-07-05 to 2026-07-28
```

---

## D. מה אני לא מבין — הרשימה החשובה

זו הרשימה שביקשת לא לרכך. כל פריט: מה לא ברור, ואיזו קריאה תפתור אותו.

**D1. למה `score_analytics` מדווח n=0 בעוד יולי סגר 60 פוזיציות (TASK-254) — ואיך זה מתיישב עם 83 פוזיציות תקועות ב-`DRY_RUN_OPEN` (TASK-246).**
אלה שתי טענות שנשמעות סותרות על אותו טאב באותו חודש. לא הבנתי אם 60 נסגרו ו-83 נתקעו, או ששני התיקים מודדים דברים חופפים. **קריאה שתפתור:** `agent/analytics/score_analytics.py:1-540` במלואו + הגוף של TASK-246 ו-TASK-254 + שאילתת-קריאה על `paper_portfolio` של 2026-07 (חסום היום — השוק פתוח).

**D2. מה בדיוק שבר את נפח-הסריקה ב-15/07 (TASK-245).**
התיק אומר "הנפח נחצה באותו תאריך שבו התחיל שיבוש-הטיקרים". אם זה אותו שורש — התיקון של TASK-238 (`21d1766`, 29/7) היה אמור להחזיר את הנפח, ואני לא יודע אם החזיר. אם זה **לא** אותו שורש, יש כאן גורם שני שלא זוהה. **קריאה שתפתור:** הגוף של TASK-245 + ספירת שורות `timeline_live` לפני/אחרי 15/07 ואחרי 29/07.

**D3. מה בעצם חוסם כניסות היום, בפועל, במספרים.**
קראתי את שער-הכניסה בקוד וידעתי מה *יכול* לחסום. אני לא יודע איך זה מתחלק בפועל — כמה SKIP-ים על MxV, כמה על PRICE_TOO_LOW, כמה על ACCOUNT_STATE_UNAVAILABLE. בלי זה אין לי מושג אם הפילטר המינימלי מייצר 3 כניסות ביום או 30. **קריאה שתפתור:** טאב `skip_summary` של השבועיים האחרונים (חסום היום).

**D4. האם TASK-244 סגור או פתוח.**
הקומיט `f1cf01a` מ-8/03 כתוב "fail closed on unreadable account state" ופילטר F6b קיים בקוד (`decision_logic.py:428`). ובכל זאת TASK-244 עדיין רשום **HIGH / To Do**. או שהתיקון לא נסגר בבקלוג, או שיש AC נוסף שלא מולא. **קריאה שתפתור:** `backlog task 244 --plain`.

**D5. `requirements.txt` מצמיד finvizfinance 0.14.6 שלא מסוגל לפרסר את finviz היום (TASK-248) — אבל הסקאנר רץ.**
`utils.SanitizedOverview` הוא proxy שעוקף את הבעיה (`utils.py:871-918`), אבל אני לא הבנתי אם הוא עוקף אותה *לגמרי* או רק את שיבוש-הטיקר. אם רק את השיבוש, ייתכן ששדות אחרים חוזרים שבורים בשקט. **קריאה שתפתור:** `utils.py:839-925` במלואו + `backlog task 248 --plain`.

**D6. `is_snapshot_time` פותח חלון של 10 דקות סביב הנעילה, וה-cron רץ כל דקה.**
`auto_scanner.py:87-89` — החלון הוא close−5 עד close+5. משמע יש עד ~5 הזדמנויות לפני הנעילה שבהן `daily_snapshots` נכתב. הקוד ב-`:495-499` דורס את שורות היום, אז זה כנראה idempotent — אבל `portfolio` ב-`:503-525` מוסיף לפי `PositionKey` ייחודי, ו-`_save_daily_summary` נקרא בכל אחת מהפעמים. לא הבנתי אם זה בזבוז-quota בלבד או משהו גרוע יותר. **קריאה שתפתור:** `auto_scanner.py:486-530` + `_save_daily_summary` `:571-624` בעיון, מול TASK-253 (שורות כפולות ב-timeline_live).

**D7. `_read_decision` בתוך `orchestrator.py:629-642` קורא `ws.get_all_records()` בלי קאש.**
זה בתוך callback שמופעל לכל postmortem. בעולם שבו הרגו את News Detective כי הוא עשה 46 קריאות/ריצה — זה נראה כמו מקור-429 שלא נספר. אבל אולי הוא נקרא נדיר. לא יודע. **קריאה שתפתור:** `agent/analytics/postmortem_engine.py:1-407` — לראות מתי בדיוק `decision_reader` נקרא.

**D8. איפה עובר הגבול בין הסימולציה של הסקאנר לפוזיציות של הסוכן.**
שתי מערכות מקבילות עם TP/SL זהים על אותם טיקרים, כותבות לטאבים נפרדים, ואף אחת לא יודעת על השנייה. איזו מהן היא "התוצאה" שאתה מודד? ה-WR הרשמי (`utils.classify_trade`) מחושב על `post_analysis` — כלומר על **הסימולציה**, לא על פוזיציות-הסוכן. אם כך, מה תפקיד `paper_portfolio` בהערכת-הביצועים. **קריאה שתפתור:** PK §20 "Trade Simulation" (`:1881-1990`) + §A9 Agent Execution.

**D9. `EXPLICIT_GATE_MODE=active` נכתב 6/29 עם הערה "flipped without >=2wk shadow-accumulation".**
TASK-194 (ניטור פוסט-flip) עדיין MEDIUM/To Do אחרי 5 שבועות. אני לא יודע אם מישהו מדד מאז מה ה-flip עשה. **קריאה שתפתור:** `backlog task 194 --plain` + `docs/HYPOTHESES.md` (318 שורות) — במיוחד HYP-002 שנפסלה ב-8/03.

**D10. `health_audit.py` הוא 2,079 שורות — הקובץ השני בגודלו — ולא קראתי ממנו שורה.**
ה-PK מדבר על "30 בדיקות בריאות". לא יודע מה הן, מה חומרתן, ומה קורה כשהן נכשלות. TASK-252 מבקש להוסיף שלוש עוד. **קריאה שתפתור:** `health_audit.py` במלואו + PK §23.

**D11. `dashboard.py` הוא 5,330 שורות ולא קראתי ממנו כמעט כלום.**
לפי ה-ADR זה מכוון (ADR-008: קובץ יחיד, לא Streamlit pages). אבל בפועל `agent/dashboard/` מכיל 5 קבצי-עמוד נוספים (1,632 שורות) — כלומר ההחלטה כבר לא מוחזקת במלואה. לא יודע מה מוצג ומאיזה מקור. **קריאה שתפתור:** `dashboard.py:1301-1836` (העמודים הראשיים) + `agent/dashboard/_data_loaders.py`.

**D12. האם `research/` באמת מחוץ ל-git.**
היא רשומה ב-.gitignore אבל `git check-ignore` החזיר exit 1. זו סתירה שלא פתרתי. אם התיקייה כבר tracked, ה-.gitignore לא חל עליה וכל 24 תיקיות-המחקר **כן** בגיט. **קריאה שתפתור:** `git ls-files research/ | head` — פקודה אחת, לא הרצתי אותה כי לא הייתה בהיקף.

**D13. `TASK-251` — אוגוסט מצביע על קובץ live_trades משלו בעוד כל חודש אחר עושה alias ל-score_tracker.**
אם זה נכון, אז `live_trades` ו-`score_tracker` הם **אותו קובץ** בכל החודשים חוץ מאוגוסט. זה משנה איך קוראים היסטוריה. לא הבנתי אם זה באג באוגוסט או באג בכל השאר. **קריאה שתפתור:** `sheets_config.json` + `backlog task 251 --plain`.

**D14. מה קורה כשהסוכן מפעיל ENTER על טיקר שכבר `DRY_RUN_OPEN` — 83 פעמים.**
F7 (`existing_position`) אמור לחסום. F9 (re-entry=1) אמור לחסום. ובכל זאת יש 83 תקועות. אם השורש הוא 429 (כפי ש-`f1cf01a` טוען), אז F6b סוגר את זה קדימה — אבל 83 השורות הקיימות עדיין שם ועדיין נספרות כ-OPEN ב-`build_account_state:241`, כלומר הן **אוכלות את מגבלת ה-5 המקבילות**. אם זה נכון, הסוכן לא יכול להיכנס לשום דבר עכשיו. **זו ההשערה הכי מטרידה שיצאתי איתה, והיא לא מאומתת.** **קריאה שתפתור:** `paper_portfolio` של 2026-08 — כמה שורות OPEN (חסום היום, השוק פתוח).

---

## E. אימות

```
git status --porcelain
?? docs/auto-dancer/queue/QUEUE_2026-07-04.md
?? docs/auto-dancer/queue/QUEUE_2026-07-05.md

git diff --stat
(ריק — אפס שינויים בקבצים מעקבים)
```

לא נגעתי בקוד, לא הרצתי pytest, לא נגעתי ב-Sheets/Drive/FINVIZ, לא commit, לא push, לא שיניתי סטטוס של תיק.
הפעולה היחידה שאינה קריאה: `mkdir -p reports` (התיקייה ריקה).
