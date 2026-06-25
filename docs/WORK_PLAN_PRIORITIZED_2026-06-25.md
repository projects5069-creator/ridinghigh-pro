# RidingHigh Pro — תוכנית-עבודה מקובעת (2026-06-25)
# סדר נעול: data-integrity לפני F2 (Phase-0 קודם-למחקר). edge_audit verdict: Abandon-Score / Refine-execution.
# הצוואר = execution/entry-timing, לא היעדר-signal. המנוף = F2 (entry=D1_Close).

# RidingHigh Pro — תוכנית-עבודה מתועדפת (PLAN MODE, read-only)
בנוי על: WORK_PLAN_2026-06-25 + 39 גופי-משימות + edge_audit_v1 (הורץ במלואו) + אימות-קוד-חי.
עוגן: HEAD d5efe9d · PK v3.60 · config: DRY_RUN=True · SCORE_FROZEN=True · SENTINEL=shadow · GATE=shadow.
סקיל-gate שנטען בפועל: backtest-expert (אימות ה-edge verdict).

## A. תקציר edge_audit + השלכה על אשכול-62
VERDICT (מאומת מול backtest-expert, snapshot paper_portfolio 05-22, n=79):
- טענת "Score חוזה reversion" => **ABANDON**. Score↔PnL r=-0.006 (p=0.90); net-of-cost -4.62%; כבר בוצע (ADR-009/SCORE_FROZEN). האודיט מאשר.
- טענת "short-the-pump ניתן-למסחר" => **REFINE / INSUFFICIENT-DATA**. signal גולמי קיים (Score↔MaxDrop% r=-0.235) אך נהרס ב-execution; net שלילי; n<100; CI [34,54]pp לא כולל 60. לא להפריך, לא לפרוס.
- קידום Phase-2 => **BLOCKED (נכון)**. WR 49.4% < breakeven 51.4%.
- backtest-expert lens: נכשל ב-Sample-Size (n<100), Execution-Realism (net<0 תחת עלות), Robustness (CI כולל 50%, multiplicity לא-מובהק). תואם "Abandon/Refine" — לא Deploy.

**המסקנה המכרעת:** הצוואר = **EXECUTION/entry-timing, לא היעדר-signal** (entry |Δ|=23%, TP בפועל +15.8% / SL -16.6%).
**השלכה על אשכול-62** (קובע גורל 62/63/65/68/69/71/72/73/74/75):
- מתרומם: מחקר-execution => לכמת net-PnL תחת entry=D1_Close (F2). קושר ל-HYP-001 / TASK-178(Done) / TASK-179(crossover). זה המנוף היחיד שעשוי להפוך edge.
- נשאר תקף: 74 (להגדיל n->100, roadmap F8) · 63/65 (data-integrity, בלתי-תלוי ב-verdict) · 62/73 (מנוע-ניתוח — אך לכוון ל-execution-analysis, לא עוד ציד-מדדי-כניסה).
- יורד/pre-register-only: **68/69/72/75** — ציד מדד-כניסה טוב יותר לא יעזור כל עוד execution הורס (Score↔PnL~0). research-only, נמוך, עד שה-execution-edge יוכח.
- exploratory חסום: 71 (הצד-השני) — חסום על 74.

## B. מסלול VERIFY-FIX (פרמיסות שאומתו מול קוד/דאטה חי)
פורמט: TASK | פרמיסה | מאמץ | תלות | סקיל-לביצוע
- 190 | AC#1-3 FIXED (backfill_ohlc.yml cron 16:45 + timeout 25m; collector backfill הוסר — אומת בקוד). AC#5 = LIVE (ב-6/23 עוד 2 פערים) | זול | ריצה-חיה היום | data-quality-checker
- 182/F4 | FIXED-בקוד (backfill_interday_v1 + collector:589 + exclude:141). שורת +106.8% legacy ב-snapshot 6/11 = LIVE-check אם backfill כוסה | זול | live | data-quality-checker
- 166 | check_30 lineage קיים (1ddf281). חסר: live-verify recompute-drift | זול | פוסט-EOD 16:00+ Peru | data-quality-checker
- 49 | NCT dl=1/pp=2 — CANNOT-VERIFY מקומית (decision_log חסר, gate F5) | בינוני | pull חי | systematic-debugging
- 66 | HOLDS — SENTINEL=shadow אומת; counterfactual WR 64% vs 41% n=36 רגים-יחיד | — | רב-משטרי | signal-postmortem
- 67 | HOLDS — news_detective מחווט per-minute (orchestrator:721); WITH 60% vs WITHOUT 62% | זול | — | signal-postmortem
- 69 | HOLDS-locked — Score↔PnL~0 מאשר שהמשקלים לא חוזים; היפוך טרם נבדק | — | n רב-שבועי | data-quality-checker
- 75 | HOLDS-but-mooted — DaysSinceIPO r=+0.261 מול MaxDrop% (שהוא upper-bound+non-capturable) | — | pre-register | data-quality-checker
- 54 | HOLDS — fail-open KNOWN HOLE אומת ב-CLAUDE.md | בינוני | — | systematic-debugging
- 145 | watch — 30/32 כשלים היו manual-test 2/6; ריצת-תזמון 1/7 תכריע | זול | 1/7 | systematic-debugging
- 63 | snapshot 2/104 שבור (אומת באודיט שלב 4) | זול | — | data-quality-checker
- 65 | 9 postmortems חסרים (רשימה שמית) | זול | — | signal-postmortem
- 74 | פער ~770/1000 מאומת (post_analysis 54-57/~1000) | כבד (Alpaca) | הכרעת-עמיחי | data-quality-checker

## C. מסלול DECIDE (8 הכרעות לעמיחי — שורה+המלצה)
- 186 overnight-runner | קוד+טסטים GREEN, DISARMED 6/20 | המלצה: להשאיר DISARMED עד שיש משימת auto-safe אמיתית (פרמיסת "TASK-126=auto-safe" הופרכה — 0/59 auto-safe). ערך = template + --triage-only.
- 194 Stage-2 flip | להסיר Score gate חי | המלצה: BLOCKED נכון — להמתין ל-128 (>=2 שב' shadow רב-משטרי). לא לפעול עכשיו.
- 176 News-Detective demote | net-negative, quota כבד | המלצה: **demote ל-EOD-only** (67 מאשר אפס discrimination; ch-audit F6 quota חריגה ×6-×12). זול ומפחית עומס.
- 170 market-regime wire | market_context מוכן | המלצה: לחווט כ-shadow-modifier בלבד (לא חי) — עד שיש edge; אחרת מוסיף רעש להחלטה ללא signal מוכח.
- 153 DropsLab_PK adopt | docs draft v0.1 | המלצה: לאמץ — זול, מתעד, anti-drift. אבל cross-repo (DropsLab) — לתאם.
- 154 private-repo migration | F6: Actions ×6-×12 חריגה | המלצה: להעריך ברצינות (עלות/אמינות אמיתית) — לקשור ל-F6.
- 92 timeline_live minute-logging | writer הכי כבד (~390/יום) | המלצה: רמה-א בלבד (להסתיר דף דשבורד) — לא לבטל כתיבה (שובר orchestrator+post_analysis).
- 66 sentinel active? | blocked=winners | המלצה: להישאר shadow עד דאטה רב-משטרי (n=36 רגים-יחיד).

## D. מסלול BUILD (לפי קיבולת, מאמץ-גס)
- זול (<יום): 88 equity-curve PNG · 89 חריגות-מייל · 39 איחוד-6-מיילים · 11 cross-month-agg · 9 sentinel-analytics
- בינוני: 58 SA נפרד ל-health_audit (MEASURE-FIRST: למדוד 429 חי לפני בנייה — אולי מיותר) · 10 Filter-12 reputation (אין AC; דורש metric+סף+מקור) · 101 security-plugin (gated על auto-mode 93/94)
- כבד/cross-repo: 82 5-מדדי-שורט (רובם בתשלום; חינם: VWAP+sigma-bands) · 83 drops_post d6-d15 (DropsLab) · 33 Agent#6 (FREEZE על סוכנים חדשים)

## E. סדר-ביצוע מומלץ
1. **היום (זול+read-only):** 190 AC#5 live-recheck => אם 0 פערים, סגירת Done · 166 live-verify פוסט-EOD.
2. **MEASURE-FIRST:** למדוד 429 חי => מכריע אם 58 נחוץ (לפני בנייה).
3. **המנוף האמיתי (F2):** למדוד net-PnL תחת entry=D1_Close על snapshot קיים — זו ההשערה היחידה שעשויה להפוך edge. read-only, מזין 178/179.
4. **data-integrity זול:** 63 (snapshot) · 65 (postmortems) · 182-legacy-row live-check.
5. **חבילת-הכרעה לעמיחי (C):** 176(demote) + 186(park) + 153/154 + 92 + 170 + 66 + 194 — להגיש יחד.
6. **חסומים (אין פעולה):** 179 (n>=150 ~אמצע-יולי) · 128/194 (>=2 שב' shadow) · 74->71 (הכרעת pull כבד) · 69 (n רב-שבועי) · 109 (RECONCILE_AUTO_REPAIR — חסום עד track-record נקי של 106; follow-up ל-108).
7. **דחה (pre-register-only):** 68/72/75 ב-HYPOTHESES.md — נמוך עד execution-edge מוכח.

## הערות-אזהרה
- כל edge-number = UPPER-BOUND (survivorship: 21% suspicious + delisted חסרים).
- borrow 6.85% = worst-case הנחה, לא נמדד פר-טיקר (BorrowFeePct תמיד NULL).
- F3 PENDING-stall detector + F4 artifact-leak = שני נתיבי נתונים-שגויים-בשקט פתוחים (מכווצים n בשקט).
