# 🔬 SYSTEM REVIEW — RidingHigh Pro — 2026-06-09 (v1)

**סוג:** Read-only deep audit (אפס שינויי קוד, אפס כתיבות ל-Sheets, אפס commits)
**בסיס:** PK v2.91 (working tree, uncommitted) + קריאת קוד מלאה + נתונים חיים (קריאה-בלבד)
**ריפו:** `projects5069-creator/ridinghigh-pro` @ main `c9fdeca` + שינויים לא-מקומטים (ראה §D.1)
**גישת נתונים:** ✅ הייתה (service account מקומי) — כל המספרים בדוח חושבו מהנתונים החיים הערב

---

## A. ארכיטקטורה כפי שהיא היום

```
                       ┌─────────────────────────── GitHub Actions (15 workflows) ───────────────────────────┐
                       │                                                                                      │
  FINVIZ (screener) ───┤  auto_scan.yml          cron */1 13-19 UTC  →  auto_scanner.run_scan()              │
  Alpaca (prices)   ───┤  agent_minute.yml       cron */1 13-20 UTC  →  agent.orchestrator.run()             │
  yfinance (fund.)  ───┤  post_analysis.yml      21:05 UTC           →  auto_scanner --eod + collector v5    │
                       │  health_audit / backup / monthly_rotation / prepare_next_month / warm_oauth          │
                       │  agent_eod / agent_email_morning|daily / agent_critic(+weekly/monthly) / market_ctx  │
                       └──────────────────────────────────────────────────────────────────────────────────────┘
                                          │ כתיבה/קריאה (gspread + retry + 60s cache)
                                          ▼
        Google Sheets — 9 גיליונות/חודש (timeline_live, daily_snapshots, portfolio, post_analysis,
        daily_summary, portfolio_live, ticker_follow_up, live_trades, score_tracker)
        + גיליונות agent (decision_log, paper_portfolio, postmortems, sentinel_events, system_events…)
                                          │
                                          ▼
        dashboard.py (Streamlit, 5,192 שורות, 10 עמודים) — תצוגה + סימולציות
```

**שכבת הסוכן (agent/):** orchestrator (796 שורות) → sentinel (6 בדיקות פר-signal + 3 מערכתיות, mode=shadow) → trader/decision_logic (11 פילטרים) → decision_logger (42 עמודות) → order_manager/position_manager (DRY_RUN) → postmortem_engine + score_analytics. critic/market_context/monitoring = stubs חלקיים.

**מקורות אמת:** `config.py` (משקלים/ספים) · `formulas.py` (חישובים) · `utils.py` (classify_trade) · `sheets_manager.py` (I/O + quota) · PK v2.91 (תיעוד).

**הפרדת ספים מכוונת:** סקאנר נכנס ב-Score≥70 (`config.py:104`), הסוכן ב-Score≥50 (`config.py:267`), post_analysis אוסף מ-Score≥60 (`post_analysis_collector.py:52`) — ראה ממצא D.5.

---

## B. אינוונטר מלא — מטריקות/נוסחאות/ניקוד + VERDICT

### B.1 נוסחאות ליבה (formulas.py — מקור אמת יחיד)

| # | מטריקה | קובץ:שורות | נוסחה | Verdict |
|---|--------|-----------|--------|---------|
| 1 | MxV | formulas.py:84-93 | `((MC − P·V)/MC)·100` | **VALID** מתמטית (גודר None/0); **SUSPECT** כפילטר — ראה E.4 |
| 2 | RunUp | formulas.py:96-105 | `(P−Open)/Open·100` | **VALID** |
| 3 | ATRX | formulas.py:108-117 | `(High−Low)/ATR14` | **VALID** |
| 4 | validate_atrx | formulas.py:120-131 | מאפס אם `ATR<0.5%·P AND ATRX>5` | **VALID** (אבל PK §19 טוען "returns bool" — מחזיר float. drift) |
| 5 | Gap | formulas.py:134-143 | `(Open−PrevClose)/PrevClose·100` | **VALID** (לא בניקוד v2) |
| 6 | TypicalPriceDist | formulas.py:146-164 | `(P/((H+L+C)/3)−1)·100` | **VALID** |
| 7 | calculate_vwap_dist | formulas.py:167-175 | alias deprecated | **SUSPECT** — מיועד למחיקה (#11 step D), עדיין מיובא ב-dashboard.py |
| 8 | REL_VOL | formulas.py:178-190 | `V/AvgV`, cap=100 (`config.py:78`) | **VALID** |
| 9 | Float% | formulas.py:193-204 | `float/outstanding·100` | **VALID** |
| 10 | PriceToHigh | formulas.py:211-226 | `(P−High)/High·100` | **VALID** — אבל מחושב inline במקביל (B.4) |
| 11 | PriceTo52WHigh | formulas.py:229-242 | אנלוגי | **VALID** — אותה בעיה |
| 12 | ScanChange | formulas.py:245-264 | `(P−PrevClose)/PrevClose·100` | **VALID** |
| 13 | DropFromHigh | formulas.py:267-284 | `max(0,(IH−P)/IH·100)` | **VALID** |
| 14 | MaxDrop | formulas.py:287-303 | `(MinLow−ScanP)/ScanP·100` | **VALID** |
| 15 | D1Gap | formulas.py:306-322 | `(D1Open−ScanP)/ScanP·100` | **VALID** — והמנבא החזק ביותר בנתונים (E.3) |
| 16 | PnL% (short) | formulas.py:325-344 | `(entry−exit)/entry·100` | **VALID** |
| 17 | normalize_mxv | formulas.py:352-360 | clip+scale | **BROKEN-as-doc / DEAD** — לא בשימוש בשום מקום; docstring+PK אומרים "0-1", מחזיר 0-100 |
| 18 | normalize_atrx | formulas.py:363-371 | clip+scale | **DEAD** — כנ"ל |

כל 16 הפונקציות החיות גודרות None/0/ZeroDivision ומחזירות float צפוי. `test_formulas.py` (107 בדיקות) מכסה אותן.

### B.2 Score v2 (formulas.py:380-434 + config.py:40-70)

משקלים: MxV=25, RunUp=25, ATRX=20, RSI=10, VWAP=10, ScanChange=5, REL_VOL=5 (סכום 100 ✅).
Caps: MxV=200(|x|), RunUp=30, ATRX=5, VWAP=8, ScanChange=60, REL_VOL=15.
לוגיקה: תרומה לינארית `min(x/cap,1)·weight`; MxV רק שלילי, RunUp/TPD/ScanChange רק חיוביים; **RSI במדרגות** — ≥90→10, ≥85→7, ≥80→4, אחרת 0 (formulas.py:408-417).

**Verdict: SUSPECT (מבני) + BROKEN (תיעוד):**
- **מתמטית תקין** — סכום מקסימלי 100, ללא חריגות, עיגול ל-2 ספרות.
- **`config.SCORE_RSI_PARAMS` (config.py:64-70) הוא קוד מת** — `calculate_score` לא קורא אותו בכלל; המדרגות hardcoded. גם `RSI_HIGH/RSI_LOW` ב-SCORE_CAPS_V2 (config.py:56-57) לא בשימוש. מי שמכוונן את config לא משנה כלום.
- **bare `except: pass` ×7** (formulas.py:398-432) — מפתח חסר/typo במילון metrics מאפס רכיב **בשקט**. למשל קריאה עם `'scan_change'` במקום `'change'` תוריד 5 נקודות בלי שום שגיאה.
- **אמפירית** (E.2): Spearman מול WIN במחקר −0.02; מול PnL אמיתי −0.08; שכבת 80-90 גרועה מ-50-60. ה-Score כרגע לא מנבא.

### B.3 ספים, פילטרים, סימולציה

| פריט | ערך | מקור | Verdict |
|------|-----|------|---------|
| TP/SL | ±10% | config.py:117-120 (ADR-007) | **VALID** עקבי בכל המסלולים |
| חלון | 5 ימי מסחר | config.py:131 | **SUSPECT** — 52/59 טריידים מוכרעים ב-D1 (E.5); D3-D5 מוסיפים רק חשיפת SL |
| classify_trade | WIN/LOSS/WHIPSAW/NO_TOUCH/PENDING | utils.py:483-537 | **VALID** לוגית; שמרני — WIN מוכרע ב-D1 נשאר PENDING עד שכל 5 הימים קיימים (utils.py:517-519), מה שמחריף את בעיית ה-PENDING (E.1) |
| calculate_stats | TP10/15/20, SL_Hit_D5, MaxDrop | utils.py:412-480 | **VALID**; TP15=0.85, TP20=0.80 hardcoded (לא ב-config) |
| 11 פילטרי הסוכן | score≥50, mxv≤−100, runup≥0, vol≥100K, p≥$3, blacklist, toxic(RSI>88∧SMA20>250), MC $5M-2B, quality≥0.5, positions, cold-start, reentry≤3, BP, rocket-guard(RunUp≥50∧PTH≥−10) | decision_logic.py:276-362 + config.py:267-307 | **VALID** קוד; **SUSPECT** כיול — MXV_TOO_HIGH ו-RUNUP_TOO_LOW עם counterfactual הפוך (PK 25/5); p≥$3 נמוך מדי — רצועת $3-5 היא הגרועה (E.4) |
| quality_score | `max(0, 1−flags·0.25)`, סף 0.5 | data_quality.py:125 | **VALID** |
| Sentinel | shadow; 6+3 בדיקות, ספים config.py:333-339 | data_sentinel.py | **VALID** קוד; shadow נכון עד דאטה רב-משטרי (TASK-66) |
| sizing | $1000 קבוע, `floor(1000/P)` | decision_logic.py:129 | **VALID** |
| PnL שורט | `(entry−current)·qty` | position_manager.py:196,273 | **VALID** |

### B.4 הפרות Single-Source-of-Truth (§10) — חישוב באותו שם ביותר ממקום אחד

| מטריקה | מקור-אמת | כפילות | חומרה |
|--------|----------|--------|-------|
| PriceToHigh | formulas.py:211 | **auto_scanner.py:235** inline (למרות import בשורה 37!) + **dashboard.py:382,562** | 🟠 |
| PriceTo52WHigh | formulas.py:229 | **auto_scanner.py:243** + **dashboard.py:388,568** | 🟠 |
| ScanChange | formulas.py:245 | **dashboard.py:301,409,464,593** inline | 🟠 |
| TypicalPriceDist | formulas.py:146 | **auto_scanner.py:906-907** inline (ב-ticker_follow_up) + **post_analysis_collector.py:498** (מסומן בכוונה) | 🟠 |
| **RSI** | ta.RSIIndicator (Wilder) — auto_scanner.py:183, dashboard.py:324 | **auto_scanner.py:880-886** — מימוש ידני `rolling(14).mean()` (SMA-RSI) ב-ticker_follow_up | 🔴 **ערכים שונים מתודולוגית** — RSI של D1-D3 לא בר-השוואה ל-D0 |
| **ATR14** | ta.AverageTrueRange — auto_scanner.py:190 | **auto_scanner.py:865-870** — TR ידני + `rolling(14).mean()` | 🔴 כנ"ל — ATRX ב-follow_up שיטה אחרת |
| is_market_hours | utils.py:145-157 (`<=15:00`, כולל חגים) | **agent/orchestrator.py:104-111** (`<15:00`, weekday בלבד — בלי חגים!) | 🟡 הסוכן ירוץ בחגי בורסה; הסקאנר לא |
| TP15 | — | dashboard.py:2017 — `0.15` hardcoded, לא קיים ב-config | 🟡 |
| ספי תצוגה 40/50 | config.py:97 | dashboard.py:88,103 hardcoded | 🟢 |
| Sheet ID legacy | sheets_manager.py:29 | dashboard.py:964 — אותו ID hardcoded שוב | 🟢 |
| MIN_PRICE=2 | config.py:167 | auto_scanner.py:122 — `price < 2` hardcoded | 🟢 |

---

## C. PK-vs-Code drift (PK v2.91)

1. **RSI בניקוד** — PK §18 (שורות 1580, 1594-1595) מתאר "bell curve, peak 50-70" ו-`RSI_LOW: 50`; בקוד: מדרגות ≥80/85/90 (formulas.py:408-417) ו-`RSI_LOW: 60` (config.py:57). docstring של calculate_score (formulas.py:388) גם הוא אומר bell curve וסותר את הקוד 20 שורות מתחתיו. **זה ה-drift המהותי ביותר.**
2. **SCORE_RSI_PARAMS מוצג כפעיל** (PK §18 + config.py:64-70) — בפועל קוד מת.
3. PK §19: `validate_atrx` "returns bool" (מחזיר float); `normalize_*` "0-1" (0-100, ובכלל לא בשימוש); `price_to_high/52w` "Used by dashboard" — בפועל dashboard והסקאנר מחשבים inline.
4. PK §1 Metadata: "Generated 2026-06-04", "7 workflows", "~13,000 lines" — בפועל 15 קבצי workflow, ~26K שורות (כולל agent). TASK-119 כבר פתוחה על זה.
5. PK §2 TL;DR: "Dashboard 3 pages" — בפועל 10 עמודים; נתוני סטטוס מ-2026-05-02 (תוקנו חלקית ב-Critical Update 25/5, אבל ה-TL;DR עצמו לא עודכן).
6. PK §20: "portfolio_live … every minute" — נכון; אבל score_tracker רץ כל 5 דקות (auto_scanner.py:525), לא מתועד שם.
7. PK §29 סטטיסטיקות מ-2026-05-02 — היום: 276 שורות post_analysis (לא 156), 172 v2 (לא 52). הסעיף מסומן "current" ומטעה.
8. ה-PK המעודכן (2.91) נמצא רק ב-working tree — לא קומט. ראה D.1.

---

## D. פערים, חולשות, קוד מת, סטטוס משימות

### D.1 🔴 עבודת TASK-107 לא מקומטת
`git status`: שינויים ב-`agent/orchestrator.py`, `agent/sentinel/checks/position_sync.py`, `test_position_sync_v1.py`, `.gitignore`, וה-PK (v2.91). ה-backlog מסמן TASK-107 **Done** (עודכן היום 22:35) וה-PK changelog מתאר את התיקון — אבל **main לא מכיל אותו, וה-agent בענן רץ בלי התיקון**. ה-FP של closed-same-day (283 HALTs ב-3/6) עדיין חי בפרודקשן עד commit+push. זהו פער Done-vs-deployed שצריך לסגור ראשון.

### D.2 סטטוס המשימות שנשאלו
- **TASK-107** (position_sync closed-same-day): קוד+טסטים (11/11) קיימים מקומית, מסומן Done — **לא ב-main** (D.1).
- **TASK-108** (reconciler auto-repair): Done, מומש מאחורי דגל `RECONCILE_AUTO_REPAIR=False` (config.py:287). הפעלה = TASK-109, מותנית בתקופת הוכחה של flag-only — **0 ימי הוכחה עד 3/6**; לא נמצא מנגנון שסופר ימי הוכחה אוטומטית — ההוכחה תלויה בקריאת לוגים ידנית.
- **TASK-58 Phase 2**: S1 (timeline_live דרך cache 4→2) ✅ חי ואומת (auto_scanner.py:73-82, PK v2.78: total=4 reads/run). S2 (portfolio 2→1) נדחה במכוון. ה-AC המקורי — service account נפרד ל-health_audit — **לא בוצע**; השאלה הפתוחה "peak משולב agent+scanner+health_audit באותה דקה" לא נמדדה. הסטטוס: To Do, בצדק.

### D.3 קוד מת / זומבי
- `formulas.normalize_mxv/normalize_atrx` (352-371) — אפס callers.
- `config.SCORE_RSI_PARAMS` + `SCORE_CAPS_V2["RSI_HIGH"/"RSI_LOW"]` — נקראים ע"י formulas (import) אך לא בשימוש בחישוב.
- `post_analysis_collector.fetch_timeline_stats` שורות 280-305: `peak_metrics` נבנה במלואו (כולל `_safe()`) ו**לא נצרך** מאז הסרת Score_B-I (Issue #34).
- `calculate_vwap_dist` — deprecated, ממתין ל-#11 step D, עדיין מיובא (auto_scanner.py:32, dashboard).
- `dashboard.py:964` — SHEET_ID legacy "unused but present".
- `agent/critic`, `agent/market_context`, `agent/monitoring` — stubs מוצהרים (Phase 2).
- bare `except:` בנקודות קריטיות: auto_scanner.py:308 (`analyze_ticker` בולע הכל), 379-382; formulas.py ×7 — מסתירים שגיאות דאטה.

### D.4 חולשות pipeline (מאומתות בנתונים)
- **🔴 חורי OHLC חוצי-חודש:** 70 שורות v2 עם ScanDate לפני 2/6 עדיין PENDING בגלל D-days חסרים (דפוסים: D4,D5 / D2-D5 / כל החמישה). הסיבה המבנית: ה-collector קורא מועמדים מ-`daily_snapshots` של החודש הפעיל (post_analysis_collector.py:337-391) — שורה שסרוקה בסוף חודש מאבדת את ההזדמנות להשלמת D4/D5 אחרי הרוטציה, וכשל fetch חד-פעמי לא מנוסה שוב. **41% מדאטת המחקר v2 לא שמישה** עד backfill.
- **🔴 SKIP logging מת אחרי 20/5:** decision_log מאז 26/5 מכיל ENTERs בלבד (אומת: כל השורות מ-26/5 עד היום = ENTER). 16,145 SKIPs נעצרו ב-~20/5. בלי SKIPs אין counterfactual — בדיוק הניתוח שחשף את בעיות MXV/RUNUP ב-25/5 בלתי אפשרי על יוני.
- **🟠 פער כיסוי מחקרי:** הסוכן נכנס מ-Score≥50 (config.py:267) אבל post_analysis אוסף רק Score≥60 (collector:52). רצועת 50-60 — **המנצחת בפועל** (WR 66.7%) — לא קיימת בדאטת המחקר.
- **🟡 EntryTime לא אחיד** ב-paper_portfolio ("8:45" מול "08:45:00") — `parse_hhmm` מטפל, אבל כל ניתוח שעות ישיר נשבר (נצפה בפועל בניתוח). 
- **🟡 cron mismatch:** auto_scan עד 19:59 UTC (14:59 פרו) — דקת הסגירה לא נסרקת; agent_minute עד 20:59. חלון snapshot (14:55-15:05) מכוסה רק בחלקו ע"י הסקאנר.
- **🟡 audit_flag לא נאכף בניתוחים:** 48 SUSPICIOUS + 19 NO_DATA יושבים בדאטה; חלק מהניתוחים בדשבורד לא מסננים לפיו.

---

## E. תוצאות ולידציה על נתונים חיים (קריאה-בלבד, נמשכו 22:40-22:50 פרו)

**דגימה:** post_analysis 276 שורות (104 v1 / 172 v2; אפריל 154, מאי 78, יוני 44) · paper_portfolio 152 · decision_log 16,296.

### E.1 מצב הדאטה
v2 נקי (בלי BROKEN/PRE_SPLIT): 169. סיווג `classify_trade` חי: **110 PENDING / 35 WIN / 14 LOSS / 9 WHIPSAW / 1 NO_TOUCH**. מתוך ה-PENDING — 70 ותיקים שאמורים היו להיסגר (ראה D.4). n אפקטיבי למחקר: **49 בלבד** אחרי חודשיים וחצי.

### E.2 Score מול תוצאה — הממצא המרכזי
| בדיקה | n | תוצאה |
|-------|---|--------|
| מחקר (ScanPrice): Spearman Score↔WIN | 49 | **−0.019 (p=0.90)** — אפס |
| מחקר: Spearman Score↔MaxDrop% | 143 | **−0.327 (p<0.001)** — Score כן מנבא עומק ירידה, אבל לא ניצחון (כי מנבא גם תנודתיות ל-SL) |
| אמיתי (DRY_RUN, join decision_log↔paper_portfolio): Score↔PnL | 134 | **−0.083 (p=0.34)** — אפס/שלילי |
| WR אמיתי לפי שכבה | 50-60: 66.7% (+7.8%) · 60-70: 70.0% (+8.2%) · 70-80: 50.0% (−1.9%) · **80-90: 42.0% (−5.5%)** · 90+: 48.9% (+1.6%) | **היפוך** — השכבות הנמוכות מנצחות |
| WR מחקרי לפי שכבה (n קטן!) | 60-70: 72.7% (22) · 70-80: 88.9% (9) · 80-90: **16.7% (6)** · 90+: 83.3% (12) | אותה צניחה ב-80-90 |

ביצועי DRY_RUN כוללים (138 סגירות TP/SL): **WR 50.7%**, ממוצע +0.68%, חציון +10.0%; win ממוצע +17.47% מול loss ממוצע −16.61% — ה-slippage הא-סימטרי מ-25/5 עדיין קיים אך התאזן מעט (אז: 49.4%, −0.55%).

### E.3 כוח המטריקות (מחקר, Spearman מול MaxDrop%, n=143)
ScanChange **−0.317***, DayRunUp% −0.271**, ATRX −0.251**, RunUp −0.222**, REL_VOL −0.207*, Price_vs_SMA20 −0.200*, TypicalPriceDist −0.189*, Gap −0.181*, MxV +0.154(p=.066, כיוון נכון), RSI −0.148(n.s.), PriceToHigh/52W ≈ 0.
מול WIN בינארי — **אף מטריקה בודדת לא מובהקת** (כולן |r|<0.17) חוץ מ:
- **D1_Gap%: r=−0.59 מול WIN, +0.62 מול MaxDrop (p<0.001)** — המנבא הדומיננטי בפער.
- בנתונים האמיתיים: **Price: +0.249 מול PnL (p=0.004)** — המשתנה המובהק היחיד.

### E.4 פיצולים אקציוניים
- **רצועות מחיר (אמיתי):** $0-3: 41% WR/−4.5% · **$3-5: 39%/−4.7% (הגרוע)** · **$5-10: 67%/+10.3%** · $10+: 59%/+2.4%. הרצפה $3 (config.py:271) נמוכה מדי לפי הדאטה.
- **D1 gap-down (מחקרי, anchored ל-ScanPrice):** gap<0 → **87.5% WR (n=32)**; gap≥0 → **41.2% (n=17)**; gap<−4% → 90.9%. ⚠️ חלקית מכני (הפער עצמו מקרב ל-TP) — דורש בדיקת re-anchor (F.1).
- **ריכוז טיקרים:** PIII 16, QUCY 12, AEHL 9 טריידים — AEHL ברשימה השחורה אבל הצ'רן נמשך באחרים; reentry≤3/יום לא מגביל פני-שבוע.
- **שעות (אמיתי):** אין יותר אפקט "שעה אחרונה" ברור (hour 14: WR 50%, n=20) — הממצא מ-25/5 לא יציב.

### E.5 מבנה זמן
Resolution day: **52/59 מוכרעים ב-D1**, 6 ב-D2, 1 אף-פעם. חלון D1 בלבד היה נותן WR 74.4% מול 71.4% בחלון מלא — **D3-D5 כמעט לא תורמים ניצחונות, רק סיכון**. BestDay (מינימום) מתפזר (D1:20 … D5:17) אבל ההכרעה TP/SL מהירה.

### E.6 אימות מול טענות PK
- "TP10 hit rate 75-80%" — window metric אכן מראה 77.6%; classify אמיתי 71.4% (CI 57.6-82.2) על תיאורטי, ו-50.7% על fills אמיתיים. עקבי עם ה-Reality Check.
- "Score↔TP10 r≈0.05" — מאושש ומוחמר (היפוך שכבות).
- "ScanChange המנבא החזק (r=−0.348)" — מאושש (−0.317), אך D1_Gap חזק ממנו פי 2.

---

## F. Fresh Perspective — 5 כיוונים חדשים (כולם נבדקים בקריאה-בלבד)

**F.1 כניסת D1-open מותנית-gap (לנטוש כניסת-סריקה?)**
*היפותזה:* הכניסה הנכונה היא בפתיחת D1, רק כשיש gap-down (או דווקא gap-up — מחיר כניסה גבוה יותר לשורט). D1_Gap הוא הסיגנל הדומיננטי (|r|≈0.6) והוא ידוע בזמן אמת בפתיחה.
*למה חשוב:* כל הפער תיאורטי-מול-אמיתי (71%→51%) הוא פער כניסה; זה תוקף אותו ישירות.
*בדיקה זולה:* על 49+ השורות הסגורות — לסווג מחדש עם entry=D1_Open ו-TP/SL מעוגנים אליו, בפיצול לפי סימן/גודל ה-gap. הכל קיים ב-post_analysis (D1_Open + D1-D5 OHLC). סקריפט אחד, אפס API.

**F.2 להחליף את "Score" במודל קטן + price-band (ה-Score כאבסטרקציה שגויה)**
*היפותזה:* Score מודד עוצמת-pump, שמנבאת תנודתיות לשני הכיוונים — לכן r≈0 מול ניצחון והיפוך ב-80-90. מודל לוגיסטי על (Price, ScanChange, ATRX, D1_Gap) יפריד טוב יותר מסקלר 0-100.
*למה חשוב:* Price הוא המנבא המובהק היחיד ב-134 טריידים אמיתיים (+0.249) — ואין לו אפילו משקל ב-Score.
*בדיקה זולה:* logistic regression + leave-one-out CV על 134 הסגורים מ-decision_log (כבר ב-/tmp). שעה של עבודה, אפס תשתית.

**F.3 רזולוציית דקות ל-WHIPSAW ול-slippage (הדאטה כבר משולמת)**
*היפותזה:* 9/59 (15%) WHIPSAW ניתנים להכרעה עם נרות דקה של Alpaca (שכבר זמינים בחינם דרך data_provider). אותו מהלך ימדוד slippage אמיתי (למה SL מבוצע ב-−16.6% במקום −10%).
*למה חשוב:* WHIPSAW הוא בדיוק המקרים בהם הכרעת התזמון שווה הכי הרבה; ו-6.6pp slippage לכל SL הוא ההבדל בין edge לאין-edge.
*בדיקה זולה:* `get_intraday_bars` ל-9 ימי-ההכרעה (9 קריאות API, קריאה-בלבד) ולקבוע מי נפגע קודם.

**F.4 קיצור חלון ההחזקה (5 ימים → 2)**
*היפותזה:* כל ה-alpha בחלון D1-D2 (52/59 הכרעות ב-D1). D3-D5 רק חושפים ל-SL ומאריכים PENDING.
*למה חשוב:* חלון קצר = ריבוי מחזורי הון, פחות overnight risk, ופחות תלות ב-backfill של D4/D5 (הבעיה מ-D.4 נעלמת כמעט לגמרי).
*בדיקה זולה:* כבר רצה ראשונית בביקורת הזו (D1-only: 74.4% WR); להריץ גרסה מלאה עם PnL מצטבר + NO_TOUCH-exit-at-D2-close על הדאטה הקיימת.

**F.5 הצד הארוך של אותו סיגנל (short-only משאיר מידע על השולחן)**
*היפותזה:* האוכלוסייה שה-ROCKET_GUARD חוסם (RunUp≥50 ועדיין ליד השיא) והאוכלוסייה שמפסידה לשורט (SL_HIT) הן מועמדות מומנטום-לונג ל-1-2 ימים. ה-PK עצמו מצא ש-MXV>97 SKIPs היו "100% WIN" הפוך.
*למה חשוב:* המערכת כבר אוספת D1-D5 OHLC על כולן — תזת לונג נבדקת באפס איסוף נוסף, ומגדרת את התיק אם תאומת.
*בדיקה זולה:* על SKIPs היסטוריים (יש 16K עד 20/5 עם סיבות!) שיש להם שורת post_analysis — לחשב תשואת לונג היפותטית D1-open→D2-close. קובץ אחד, אפס API.

*הערת cadence:* הסריקה הדקתית מייצרת ~16K שורות SKIP/חודש ו-280K שורות timeline, אבל דאטת המחקר גדלה ב-2-3 שורות/יום. הערך האמיתי של הדקות הוא ב-F.1/F.3 (תזמון) — כרגע הוא כמעט לא מנוצל. אם F.4 מאומת, אפשר לשקול cadence של 5 דקות ולחסוך 80% מה-quota.

---

## G. Roadmap מתועדף (impact ÷ effort)

| # | מהלך | Impact | Effort | הערות |
|---|------|--------|--------|-------|
| 1 | **לקמט ולדחוף את TASK-107** (כבר כתוב+נבדק) | 🔴 פרודקשן עם FP חי | דקות | D.1 — Done-but-not-deployed |
| 2 | **Backfill 70 שורות ה-PENDING הוותיקות** + תיקון ה-collector לסרוק חודשים קודמים (או הרצת backfill_ohlc חודשית) | 🔴 מכפיל את n המחקרי 49→~115 | קטן (סקריפט קיים: backfill_ohlc.py) | D.4 |
| 3 | **להחזיר SKIP logging** (לחקור למה מת ב-20/5 — כנראה quota-protection) | 🔴 בלעדיו אין למידה מ-counterfactual | קטן-בינוני | D.4 |
| 4 | **ניסוי F.1 (D1-open entry) + F.4 (חלון קצר)** — read-only | 🔴 תוקף את פער 71%→51% | קטן | הדאטה כבר ב-/tmp |
| 5 | **יישור RSI: למחוק SCORE_RSI_PARAMS או לחווט אותו; לעדכן PK §18; לאחד RSI/ATR ב-ticker_follow_up ל-ta** | 🟠 מסיר drift מסוכן | קטן | B.2, B.4 |
| 6 | **העלאת AGENT_MIN_SCANPRICE $3→$5 (אחרי אימות על n גדול יותר)** | 🟠 רצועת $3-5 = 39% WR | זעיר (שורת config) | E.4 — לחכות ל-#2 קודם |
| 7 | **מחיקת inline duplicates** (scanner:235,243,906; dashboard:382,388,409,…) + dead code (normalize_*, peak_metrics, vwap_dist) | 🟡 היגיינת §10 | קטן | B.4, D.3 |
| 8 | **F.2 מודל חלופי ל-Score** | 🟠 ארוך-טווח: ההחלטה אם Score v3 או נטישה | בינוני | אחרי #2 (n גדול יותר) |
| 9 | TASK-58: למדוד peak משולב לפני בניית SA נפרד | 🟢 ייתכן מיותר | קטן | D.2 |
| 10 | איחוד is_market_hours (utils ← orchestrator) + תיקון cron 19→20 UTC לסקאנר | 🟢 עקביות | זעיר | B.4 |

**אזהרות כנות:** כל המספרים המחקריים על n=49-143 — רחוק מ-200+ הנדרשים לביטחון; ההיפוך ב-80-90 מחקרי הוא n=6; פיצול ה-D1-gap מוטה מכנית עד בדיקת re-anchor; ניתוח יוני מבוסס 6 ימי מסחר. לא בדקתי את health_audit.py/daily_audit.py לעומק (מחוץ לליבת המטריקות), ולא את 4 ה-agent_critic/email workflows מעבר לסקירת הסוכן.

---
*נוצר ע"י Claude Code, ביקורת קריאה-בלבד, 2026-06-09 ~18:00 פרו. אפס שינויי קוד, אפס כתיבות Sheets, אפס commits.*
