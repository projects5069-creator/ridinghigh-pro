# INVESTIGATION 2026-06-23 — אודיט edge + data-pipeline (read-only)

> **סטטוס:** חקירה read-only בלבד. אפס שינוי קוד / commit / push / sheet-write.
> **מתודולוגיה:** 8 שלבים נעולים (עברו ביקורת ב-4 ממדים, 10 כשלים תוקנו) —
> ראה `~/.claude/plans/cd-ridinghighpro-tingly-stallman.md`.
> **ריפו:** `projects5069-creator/ridinghigh-pro` · HEAD `1da6f2c` · PK v3.51 (אומת, אין בלבול-תיוג).
> **מקורות-נתונים:** CSV snapshots מקומיים בלבד — **post_analysis snapshot 2026-06-11**,
> **full-dump snapshot 2026-05-22**. אין live-sheet read. כל KPI נושא את תאריך-ה-snapshot שלו.

---

## שלב 0 — עיגון מקור-אמת
- PK חי by-mtime: `docs/RidingHigh_Pro_PK_v2.md` (3801 שורות, v3.51, changelog עד 2026-06-23).
- היררכיית מקור-אמת שנקבעה: **קוד חי > sheet חי > PK**. כל סתירה = ממצא (שלב 2).
- מפת-מערכת: ליבת-קוד `formulas.py` (Score/PnL SSoT) · `utils.py` (calculate_stats/classify_trade SSoT) ·
  `config.py` (קבועים) · `health_audit.py` (30 checks) · `.github/workflows/*.yml` (17 workflows) ·
  Sheets לפי `sheets_config.json` (9–23 tabs/חודש).

## שלב 1 — CHARTER (נעול לפני מבט בנתונים)
- **ה-edge במשפט אחד:** מניות שעלו בחדות ("pump") על נפח גבוה נוטות mean-revert; Score מורכב
  (MxV/RunUp/ATRX/RSI/VWAP/ScanChange/REL_VOL) אמור לזהות מועמדי-short עם TP10 hit-rate ≥65% בחלון 5 ימים,
  short ב-TP=−10%/SL=+10%.
- **ספי הכרעה (מתוך PK §7, נעולים מראש):**
  - **Deploy (Phase 2):** real DRY_RUN WR **≥60%** על 30 יום · ≥100 רשומות v2 · ≥30 ימי-מסחר ·
    correlation-analysis מסקנתי · 18/18 (כיום 30/30) health-checks.
  - **Refine:** ליבה תקפה אך WR בטווח 51.4–60% / n<100 / CI רחב.
  - **Abandon (לטענת ה-Score):** Score↔outcome ≈ 0 ו-net-of-cost שלילי.
- **מודל עלויות (נעול):** borrow ≈ **6.85%** (500%/yr × 5/365, HOLD_DAYS=5) + slippage **2%/side**;
  הכרעה על **net**, לא gross. אזהרה מ-charter: ל-`borrow_data` אין BorrowFeePct אמין (flags בלבד) →
  ה-6.85% הוא הנחה worst-case, לא נמדד פר-טיקר.
- **breakeven WR (PK):** 51.4%.

---

## שלב 2 — drift קוד↔PK (scan: systematic-debugging)
**ורדיקט: PASS כמעט-מלא. אפס drift בלוגיקת-מסחר. 2 פערים קוסמטיים בלבד.**

| פריט | PK | קוד (file:line) | ורדיקט |
|---|---|---|---|
| SCORE_WEIGHTS_V2 | 25/25/20/10/10/5/5 | `config.py:40-49` זהה | ✅ PASS |
| SCORE_CAPS_V2 | 200/30/5/–/8/60/15 | `config.py:52-59` זהה, RSI נעדר | ✅ PASS |
| ספי-action (DISPLAY60/ENTRY70/CRIT85/HIGH60/MED40) | — | `config.py:90,106,96,93,99` זהים | ✅ PASS |
| נוסחת RSI overbought-only (90→10/85→7/80→4/else 0; 50-70=0) | — | `formulas.py:496-505` זהה | ✅ PASS |
| נוסחת Score (weight×clamp_to_cap) | — | `formulas.py:482-520` זהה | ✅ PASS |
| `SCORE_WRITE_FROZEN` | True (ADR-009) | `config.py:341 = True` | ✅ PASS |
| §10 SSoT: Score/classify_trade/calculate_stats | מקום יחיד | `formulas.py:469` / `utils.py:500` / `utils.py:413` — אין כפילות חיה | ✅ PASS |

**פערים (LOW — קוסמטי, לא לוגיקת-מסחר):**
- `dashboard.py:89` — `score >= 50` hardcoded (אין קבוע תואם ב-config; styling בלבד).
- `dashboard.py:105` — `score >= 40` hardcoded למרות ש-`MEDIUM_SCORE=40` קיים אך לא מיובא ל-dashboard.
- dead-code `normalize_mxv`/`normalize_atrx` (`formulas.py:441,452`, imported `dashboard.py:59-60`, אפס call-site)
  — **כבר מתועד ב-PK §19 כ-unused** → לא drift.

## שלב 3 — Lineage (scan: data-quality-checker)
- **Score:** `auto_scanner.py:468/478/490` → metrics → `formulas.calculate_score` (`formulas.py:469`) →
  post_analysis/score_tracker (כתוב עם `score_version`, `post_analysis_collector.py:60`).
- **TP10_Hit:** `utils.py:487` בתוך `calculate_stats` — `min(D1..D5_Low) ≤ ScanPrice×(1−TP_FRAC)`; trigger רק כש-5 ימים settled.
- **MaxDrop%:** `formulas.py:295` `(min_low−scan)/scan×100`.
- **classify_trade:** `utils.py:500` → WIN/LOSS/WHIPSAW/NO_TOUCH/PENDING (first-touch D1→D5).
- **NetPnL_*:** `formulas.py:379` `calculate_net_pnl` — diagnostic-only; ה-WR הרשמי מחושב on-the-fly בדשבורד על D1_Open.
- **נקודות-כשל-שקטות שמופו:** scan כותב 0 שורות · write אבד ב-429 (`sheets_manager.py:367-394`) · NaN pre-market ·
  שורת PENDING שלא מתקדמת לעולם · reverse-split שלא נתפס כ-artifact.

## שלב 4 — איכות נתונים (snapshot 2026-06-11)
| קובץ | שורות | TP10_Hit fill | Score range | duplicates | artifacts |
|---|---|---|---|---|---|
| post_analysis_2026-04 | 154 | 100% | [8.94, 99.63] | 0 | אין |
| post_analysis_2026-05 | 78 | 100% | [60.51, 100] | 0 | 2× RunUp>600% (split: SKK, TDIC) |
| post_analysis_2026-06 | 57 | 94.7% (3 NaN = PENDING) | [60.38, 100] | 0 | 2× RunUp>300% + **1× MaxDrop% = +106.8%** (data-error/split) |

- Completeness מצוין בקבצים שהתבייתו; ה-3 NaN ביוני = PENDING תקין (לא settled).
- **artifact חי שדולף:** MaxDrop% = +106.8% הוא בלתי-אפשרי פיזית לשורט (ירידה לא יכולה להיות חיובית) →
  שורת legacy שלא סומנה `InterdayArtifact` ודולפת ל-aggregates (תואם TASK-182 column-dependent leak).

## ⛔ RECONCILIATION-GATE (scan: data-quality-checker + systematic-debugging)
**ורדיקט: PASS עם CAVEAT חוסם-חלקי.**
- full-dump 2026-05-22: post_analysis(55) · score_tracker(1419, time-series) · portfolio_live(48) · **paper_portfolio(89)** · timeline_live(261,593).
- `portfolio_live ⊆ post_analysis` ✅ (48 ≤ 55). score_tracker many-to-many ✅ (לוג סריקות, לא 1:1).
- **`decision_log` לא קיים מקומית** → reconciliation decision_log↔paper_portfolio **CANNOT-VERIFY**. ⚠️
  כל ורדיקט שתלוי ב-decision_log חייב אימות-חי לפני שיוכרע (לא נכלל באודיט הזה).

## שלב 5 — ציד הטיות (scan: signal-postmortem + backtest-expert)
| הטיה | ורדיקט | ראיה |
|---|---|---|
| look-ahead | **SUSPECT** | ScanPrice≠fill: \|Δ\| mean **23.2%** (n=80, snapshot 05-22) — entry-fill מפוזר מאוד; ה-outcome עצמו (D1-D5 forward) תקין לחלון-5-ימים |
| survivorship | **PASS + UPPER-BOUND** | 62/289 (21.4%) שורות SUSPICIOUS/BROKEN; 3 עם MaxDrop%<−95% (חשד halt/delist). מניות שנמחקו ייתכן חסרות → **כל edge-number הוא חסם-עליון** |
| overfitting | **UNKNOWN** | 7 params / 89 decided = 0.079 (סביר), אך **אין תיעוד tuning-set** — לא הוכח ש-MIN_SCORE=70 לא כויל על אותו sample |

## שלב 6 — תוקף סטטיסטי (paper_portfolio, snapshot 2026-05-22, n=89)
| מטריקה | ערך | מסקנה |
|---|---|---|
| n decided (excl 10 BE) | 79 | **<100 = מתחת ל-basic** (backtest-expert) |
| Win-rate | **49.37%** (39/79) | תואם PK 49.4% במדויק |
| Wilson 95% CI | **[34.0%, 54.2%]** (רוחב 20pp) | כולל 50% וכולל 51.4% → **לא ניתן להבדיל ממטבע**; **לא** כולל 60% → נכשל ב-Phase-2 gate |
| mean PnL% (gross) | −0.552% | median = 0.00% |
| net-of-cost PnL% | **−4.62%** (אחרי ~4.07% slip+borrow) | **שלילי — ה-edge לא שורד עלויות** |
| TP בפועל / SL בפועל | **+15.8% / −16.6%** (במקום ±10%) | אישור: execution אסימטרי, drag |
| **Score ↔ PnL%** | Pearson **−0.006** (p=0.90), Spearman −0.039 | **Score לא חוזה PnL** |
| Score ↔ MaxDrop% | r = **−0.235** (p<0.0001, n=289) | Score **כן** עוקב אחרי עוצמת-הצניחה הגולמית (לשורט: drop גדול=טוב) |
| TP10_Hit (post_analysis) | **83.5%** (n=285) | **UPPER-BOUND** (survivorship + 21% suspicious) |

**מסקנת-הליבה המתוקנת (ADR-002, מדויקת יותר מ"Score לא עובד"):** ה-signal הגולמי קיים —
Score מתואם שלילית עם MaxDrop% (r≈−0.23), כלומר ציונים גבוהים *כן* מקבלים צניחות גדולות יותר.
**אבל ה-edge הזה לא ניתן-לכידה (non-capturable)** כי ה-execution הורס אותו: entry-slippage |Δ|≈23%,
TP מתממש ב-+15.8% ו-SL ב-−16.6% (אסימטריה). לכן Score↔PnL≈0 ו-net-PnL שלילי. **הבעיה היא
execution/entry-timing, לא היעדר signal.** multiplicity: גם תחת Bonferroni (8 השוואות, p<0.006) —
אף תוצאה לא מובהקת (p>0.21).

## שלב 7 — תשתית ואמינות (scan: systematic-debugging)
- **30 health-checks** claimed = 30 actual registered (`health_audit.py:1995-2040`). 3 advisory-only (08/29/30 — לעולם לא exit-1) ✅.
- **GAPs בכיסוי silent-failure:**
  - ❌ **אין PENDING-stall detector** — check_30 דוגם רק שורות settled; שורה שלא מתקדמת לעולם לא נתפסת (HIGH — מכווץ n בשקט).
  - ❌ **אין quota-usage cap check** ב-main (`quota_health.py` קיים אך shadow/לא-מחווט) — 429 write-loss נצפה חלקית בלבד.
  - ✅ מכוסים: scan-0-rows (check_04/05), NaN pre-market (check_23), score-drift (check_30), column-drift (check_08).
- **Cron:** 17 workflows, כולם UTC, Peru ב-runtime (`now_peru`). auto_scan + agent_minute = ~390–420 ריצות/יום.
- 🔴 **GitHub Actions minutes:** אומדן **18.9k–35.7k דק'/חודש מול 3,000 חינמי = חריגה ×6–×12** (סיכון עלות/אמינות → scans שלא ירוצו = פערי-נתונים שקטים).
- backoff מעריכי קיים (`sheets_manager.py:367-394`, 2/4/8s, max 3–4) אך **אין circuit-breaker**.
- **determinism:** אין `freeze_time`; holidays hardcoded 2026 בלבד → טסטים יחזירו false-PASS ב-2027 (DRIFT-risk).

---

## שלב 8 — סינתזה, דירוג ו-roadmap

### טבלת ממצאים מדורגת (severity = פוטנציאל לנתונים-שגויים-בשקט)
| # | ממצא | סוג | חומרה | מקור |
|---|---|---|---|---|
| F1 | **net-of-cost PnL שלילי (−4.62%) + WR 49.4% < breakeven 51.4%** | שאלת-מחקר/edge | 🔴 קריטי | שלב 6, paper_portfolio 05-22 |
| F2 | **Score↔PnL≈0; ה-signal לא ניתן-לכידה בגלל execution** (entry \|Δ\|23%, TP/SL ±16%) | שאלת-מחקר | 🔴 קריטי | שלב 5+6 |
| F3 | אין PENDING-stall detector → n מתכווץ בשקט | באג-נתונים | 🟠 גבוה | שלב 7 |
| F4 | MaxDrop%=+106.8% legacy artifact דולף ל-aggregates | באג-נתונים | 🟠 גבוה | שלב 4 (TASK-182) |
| F5 | decision_log↔paper_portfolio לא ניתן-לאימות מקומית | פער-אימות | 🟠 גבוה | gate |
| F6 | GitHub Actions minutes חריגה ×6–×12 → סיכון scans חסרים | תשתית | 🟠 גבוה | שלב 7 |
| F7 | אין quota-usage check ב-main; אין circuit-breaker | תשתית | 🟡 בינוני | שלב 7 |
| F8 | n=79 < 100 (מתחת ל-basic); CI רוחב 20pp | תוקף-סטטיסטי | 🟡 בינוני | שלב 6 |
| F9 | overfitting UNKNOWN — אין תיעוד tuning-set | מתודולוגיה | 🟡 בינוני | שלב 5 |
| F10 | determinism: אין freeze_time, holidays 2026-only | בדיקות | 🟡 בינוני | שלב 7 |
| F11 | dashboard.py:89/105 hardcoded 50/40; dead-code normalize_* | פער-תיעוד/קוסמטי | ⚪ נמוך | שלב 2 |

> כל מספר לעיל מצביע על ראיה משלבים 2–7. כל edge-claim נושא n + תווית UPPER-BOUND היכן שרלוונטי.

### הכרעה מול ה-charter
- **טענת "Score חוזה reversion" → ABANDON.** Score↔PnL r≈0 (p=0.90), net-of-cost שלילי.
  זה כבר מבוצע ע"י הצוות (ADR-009, `SCORE_WRITE_FROZEN=True`). האודיט **מאשר** את ההחלטה.
- **טענת "short-the-pump filter ניתן-למסחר" → REFINE / INSUFFICIENT-DATA.** ה-signal הגולמי קיים
  (Score↔MaxDrop% r≈−0.23) אך נהרס ב-execution; net שלילי על snapshot זה; n<100; CI רחב. לא להפריך, לא לפרוס.
- **קידום Phase-2 → BLOCKED (נכון).** WR 49.4%, CI לא כולל 60%. המערכת **לא** מוכנה — וזה תועד נכון ב-PK.

### roadmap מתועדף (כל פריט עם הצעד-הבא; **לא בוצע — דורש אישור לפני שינוי קוד**)
1. **F2 (execution edge)** — חקירת entry-timing: האם short ב-D1_Close (כמו HYP-001/TASK-178) במקום ScanPrice
   מצמצם את ה-\|Δ\|23%? זו ההשערה הכי מבטיחה. צעד: לכמת net-PnL תחת entry=D1_Close על אותו sample.
2. **F3 (PENDING-stall)** — health-check חדש שמדגל שורה שלא הפכה settled תוך N ימים. צעד: TASK + TDD על `health_audit`.
3. **F4 (artifact leak)** — backfill `InterdayArtifact` לשורות legacy (תלוי TASK-182). צעד: לאמת אם 182 כבר כיסה את שורת ה-+106.8%.
4. **F5 (reconciliation)** — אימות-חי decision_log↔paper_portfolio (pull חי). צעד: סשן read-only עם creds.
5. **F6/F7 (תשתית)** — throttle/jitter ל-auto_scan + חיווט quota_health ל-main + circuit-breaker. צעד: TASK תשתית.
6. **F8 (n)** — להמשיך צבירת Phase-1 forward-only עד n≥100 (ואז 200) לפני כל הכרעת-edge.
7. **F10 (determinism)** — `freeze_time` + הרחבת holidays 2027+. צעד: TASK בדיקות.
8. **F11 (קוסמטי)** — לייבא `MEDIUM_SCORE` ל-dashboard, להחליף 50/40 hardcoded. צעד: patch זעיר.

### 📊 סיכום (תבנית rhpro-live §6)
- **KPI ראשי:** ה-edge **לא שורד net-of-cost** (−4.62%) ו-WR (49.4%) מתחת ל-breakeven — המערכת נכון **לא** מקודמת ל-Phase-2.
- **הממצא המרכזי:** ה-signal קיים אך **non-capturable** בגלל execution — לא היעדר-signal. זו פתיחה למחקר entry-timing.
- **דגל ראשי:** F3 (PENDING-stall) + F4 (artifact leak) = שני נתיבי נתונים-שגויים-בשקט שצריך לסגור.
- **הצעד הבא היחיד:** לכמת net-PnL תחת entry=D1_Close (F2) — ההשערה היחידה עם פוטנציאל להפוך את ה-edge.
