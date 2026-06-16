# TASK AUDIT — 2026-06-15

**Scope:** READ-ONLY מיפוי + תעדוף של כל המשימות הפתוחות. אפס שינוי קוד/backlog/Sheets. באגים שהתגלו → מתועדים כאן בלבד, **לא תוקנו**. אין marking Done/Cancelled, אין יצירת tasks.

**מצב מאומת חי:** PK **v3.27** · **DRY_RUN** · Sentinel=**shadow** · RidingHighPro + DropsLab נקיים+מסונכרנים · **OPEN = 66**.

**הערת-תיאום ספירה:** ספירה תמימה `grep TASK- | grep -v Done` מחזירה ~185/73 כי היא **לא מכבדת section headers** (שורת `[HIGH] TASK-144 - ...` תחת section "Done" לא מכילה את המילה "Done"). הסמכותי = **66**, מ-awk one-liner שמכבד את ה-headers:
`backlog task list --plain | awk '/:[[:space:]]*$/{h=$0} /TASK-/{if(h!~/Done|Archived|Cancelled/)c++} END{print c}'`

---

## 🔴 §0 — הממצא בעל ה-leverage הגבוה ביותר (באג load-bearing — לתיעוד בלבד)

**`_coerce_bool` מבטל בשקט את הוצאת-הארטיפקטים שכל aggregate נקי תלוי בה.**

- `_coerce_bool` (`cross_month_loaders.py:131`) מחזיר `True` רק עבור `{"true","1","yes"}`.
- ה-collector (`post_analysis_collector.py:557/573`) כותב Python `bool`, אבל ה-dry-run של TASK-182 (2026-06-15) גילה תאים חיים מסודרים כ-**numeric `1.0`/`0.0`** (value_counts: `1.0:1, 0.0:13, NaN:128, "":51`).
- `str(1.0).lower() = "1.0"` ∉ הסט → **כל artifact שה-collector סימן כ-`1.0` נקרא כ-"לא-artifact"** ע"י `exclude_interday_artifacts`.
- **תוצאה:** TASK-180 AC#2 (recompute נקי 49.5%→47.2%) **לא יושג גם אחרי backfill** — ה-exclude מחמיץ את ה-artifacts שה-collector סימן.
- **מועמד-תיקון (לא לבצע — תיעוד בלבד):** numeric-coercion בסט ב-`cross_month_loaders.py:131` (למשל union של `pd.to_numeric(...)==1` עם סט-המחרוזות). שייך ל-**TASK-182**, חייב לנחות **לפני** כל טענת "aggregate נקי".
- **חומרה:** חור data-integrity חמור יותר מהארטיפקטים עצמם — תוצאות "נקיות" יהיו שקריות בשקט.

---

## §1 — סיכום מקובץ (כל 66; טבלת-נספח מלאה ב-§A)

**DATA-INTEGRITY (ליבה):**
- **180** parent split/halt detector — RH-half בקוד + AC#3 wiring live-verified; AC#2 recompute חסום על 182; DropsLab-half **שוחרר ע"י 144**. *partial.*
- **182** backfill InterdayArtifact — פונקציה טהורה Done (`5434861`); dry-run חשף scope אמיתי **179/3-חודשים** (לא 51) + פורמט numeric + **באג §0**. *partial.*
- **173** port detector→DropsLab; **148/90** DropsLab contamination (d1 +124% / CTNT +28567%) — שלושתן תחת 180, שוחררו ע"י 144.
- **149** סיווג 19 NO_DATA (delisting=survivorship/short-wins) · **132** סימון 14 תקועות (SBLX+13 holiday) · **168** delisting auto-detector (phase-2 של 149).
- **137** RSI/ATR ב-ticker_follow_up = SMA לא Wilder → D1-D3 לא-השוואתי ל-D0 (DRY §10).
- **167** SCHEMA.json contract+drift · **166** daily lineage sentinel · **63/65** snapshot 2/104 + 9 postmortems חסרים · **49** NCT recon DL≠PP.

**CROSSOVER CHAIN (אסטרטגי — ה-signal היחיד, HYP-001 −17.75% 5d n=62):**
- **172** borrow coverage (code+TDD done, AC#3 live-verify pending) · **177** D6-D15 window (AC#1/2 done, AC#3 pending — חשד auto-grow gap) → **178** pre-register/lock → **179** validate (n≥150 ≈ 4-5 חודשים, calendar-gated).

**DECISION-GATES (שיפוט אנושי, לא ביצוע):** **141** החלף Filter1 · **174** Score-as-ranking מת (AUC 0.531) · **127** Score decouple · **92** timeline minute-logging · **159** _generate_lessons dead code · **66** SENTINEL counterfactual (blocked=winners; חוסם active-mode).

**DEADLINE (כפוי-לוח):** **135** orchestrator holiday-blind (רץ בשוק-סגור Independence Day שישי 3-4/7) · **143** dup RH-2026-07 sheet (לפני רוטציית 1/7; orphan נוקה, root-guard pending).

**QUOTA/HEALTH:** **136** חתוך כתיבות agent_minute (429/דקה) · **176/67** News Detective demotion (אין WIN/LOSS) · **58** SA נפרד ל-health_audit · **38** health-checks סוכני-תמיכה · **145** critic_monthly 21.9% (כנראה רעש manual-test).

**RESEARCH (P2/exploratory — רובן חסומות על n או על 74):** 62 · 68/69/72/75 (נעולות עד n) · 71/74 (946 תוצאות חסרות) · 73 · 82 · 83 · 88/89 · 126 · 170 (unify 15+42+70) · 169.

**INFRA/AGENT/DOCS/CLEANUP:** 9/10/11 · 33/34 (Agent#6/#7 — FREEZE) · 39 · 54 · 96 · 101 · 109 · 113 · 128 · 151 (merges 129) · 153 · 154 · 158 · 181 · 183 · 87 · 46.

---

## §2 — מועמדות סגירה/מיזוג (המלצה, לא ביצוע)

| פעולה | משימות | נימוק |
|---|---|---|
| מיזוג תחת parent **180** | 90, 148, 173, 182 | כבר "tracked under 180"; detector אחד לשני המערכות. 182 נשאר sub-task (נושא את ה-live-write + באג §0). |
| מיזוג **129 → 151** | 129 | 151 "extends 129+138" (RSI dead-config / PK drift). |
| מיזוג **15+42+70 → 170** | 15, 42, 70 | 170 = market-regime unify; 42 "NOT standalone". |
| סגירה/צמצום **181** | 181 | אם prune-script (114) מכסה `*.bak_*` → מיותר. אחרת צמצם ל"ודא .gitignore glob". |
| **168** = phase-2 של 149 | 168 | "completes 149" — לא peer. |
| **176/67** = החיתוך הקונקרטי בתוך **136** | 176, 67 | News Detective demotion = החיתוך הראשון ב-quota audit. |
| בחינת-הקפאה **33/34** | 33, 34 | Agent#6/#7 — FREEZE על סוכנים חדשים (27/5); Agent#8 קיבל קדימות; Risk-Sentinel נבנה+הוסר. maybe-obsolete. |

---

## §3 — מפת-דרכים בשכבות (data-integrity-first)

- **L0 — ליבת-אמת-נתונים:** באג §0 `_coerce_bool` → **182** (scope+write-back) → **180** (recompute נקי + DropsLab-half) → **137** (Wilder).
- **L1 — survivorship/ספירה:** **149** → **132** → **168**; **167** + **166** (guardrails); 63/65/49.
- **L2 — deadlines:** **135** (לפני 3-4/7) · **143** (לפני 1/7).
- **L3 — crossover research:** **172**+**177** live-verify → **178** lock → **179** (accrue, n≥150).
- **L4 — gates+quota+nice-to-haves:** 141/127/174/92/159/66 (אחרי recompute נקי) · 136(+176/67)/58/38/145 · cleanup/infra · exploratory (חסומות).

```
144 ✅ ── unblocks ──> 173/148/90/182(DropsLab-half)
§0 coerce-fix ── gates ──> 182 write-back ── gates ──> 180-AC2 recompute נקי
180 (absorbs 90/148/173/182) ──> substrate שכל research/gates עומדים עליו
149 ── ties ──> 132, 168
172 + 177 (live-verify) ──> 178 (lock) ──> 179 (validate, n≥150 calendar-gated)
135, 143 ── calendar-forced, independent ──> hard dates 7/3, 7/1
```

---

## §4 — Top-8 קריטיות-לליבה (עם sketch)

1. **באג §0 `_coerce_bool` (בתוך 182)** — מבטל בשקט את ה-exclusion. *sketch:* numeric-coercion ב-`:131` → RED/GREEN עם `"1.0"` → re-run dry-run.
2. **182 backfill** — חוסם 180-AC2. *sketch:* החלט scope (June-51 קודם, all-179+column-add דחה) → B-targeted cell-update (אין helper — להוסיף) → dry-run → live post-market.
3. **180 parent** — PHASE-0 item 1. *sketch:* 182+coerce-fix → recompute נקי 49.5→47.2 → port DropsLab (173/148/90).
4. **137 Wilder** (`auto_scanner.py:865-886`) — D1-D3 לא-השוואתי. *sketch:* route דרך ta/formulas (§10) → אמת schema → ping-pong.
5. **135 holiday-blind (DEADLINE)** (`orchestrator.py:~104`) — רץ בשוק-סגור 3-4/7. *sketch:* `utils.is_trading_day` → test מול 3/7 → ping-pong לפני הדדליין.
6. **143 dup sheet (DEADLINE)** — סיכון כתיבה-לגיליון-שגוי לפני 1/7. *sketch:* ודא config→live → trash orphan → post-rotation dup-check.
7. **172+177 live-verify** — code-done, רק AC#3 (ריצת EOD חיה) חוסם את כל שרשרת HYP-001. *sketch:* ריצת collector חיה post-market אחת → ודא borrow_coverage+D6-D25 (auto-grow gap!) → Done → שחרר 178.
8. **178 pre-register** — נועל את ה-signal היחיד לפני peeking. *sketch:* ודא 172/177 → HYPOTHESES.md entry (entry/exit/universe/fitness net-after-borrow+slip2x + hold-out) → lock → 179 accrue.

---

## §5 — 3 הפעולות הראשונות לסשן הבא

1. **באג §0 + השלמת 182** (off-market רובו): numeric-coercion (TDD) → B-targeted cell-update + dry-run June-51; **live-write דחה ל-post-market**.
2. **180 recompute נקי (49.5→47.2)** + התחלת DropsLab-half (173/148/90) — pure-compute, אפס live-write, משוחרר ע"י 144.
3. **135 holiday-blind** — קטן, מבודד, calendar-forced; ping-pong עכשיו שלא יחליק לשבוע-הדדליין.

**הערת-רצף (RULE #6):** 172/177 live-verify + 182 live-write + 143 — כולם דורשים ריצת EOD חיה / כתיבת-Sheets → **לאגד לחלון post-market אחד**.

---

## §6 — עקרונות מ-web research (מיושמים)

- **WSJF (Cost-of-Delay ÷ effort)** — L0 data-integrity = risk-reduction עם CoD אפקטיבית-אינסופי (מונע שכל תוצאה תהיה שקרית); 135/143 = max time-criticality; 179 = job-size ענק → "accrue, don't push".
- **High-impact/low-effort first; blocking-debt = דחוף כמו feature** — באג §0 (2 שורות, חוסם את כל ה-substrate) = quick-win קנוני; 137 = blocking-debt.
- **MoSCoW** — Must=L0+L2 · Should=L1+crossover-infra · Could=gates+quota · Won't-now=research נעול.
- **Fail-blocked-loudly + auto-close-stale** — §2 הורגת כפילויות; 178/179 חייבות להישאר חסומות עד 180+182 (לא להתחיל על דאטה מלוכלך).
- **Dependency-first topological sort** — L0→L4 = מיון טופולוגי של §1; 144 קודם שחרר את אשכול-L0.

מקורות: WSJF (ProductSchool/Highberg/6Sigma) · tech-debt-vs-feature (Metamindz/CTO-Magazine/kodus) · backlog-with-AI-agents (Backlog.md/Backlog.so).

---

## §A — נספח: טבלת 66 המשימות הפתוחות המלאה

| TASK | requires | state | blocked-on / blocks | relevance | category |
|---|---|---|---|---|---|
| 135 | orchestrator is_market_hours holiday-aware (align utils.is_trading_day) | not-started | blocks: market-correctness / **DEADLINE 7/3-4** | still-valid | agent(deadline) |
| 136 | cut non-essential agent_minute Sheets I/O (News Detective first) | not-started | blocks: 429 reduction | still-valid | agent/quota |
| 141 | [GATE] replace Filter1 w/ explicit vol+price+float | not-started | depends 174 | still-valid | decision-gate |
| 145 | investigate critic_monthly 21.9% fail | not-started | watch 7/1 sched run | maybe-obsolete (manual-test noise) | agent |
| 172 | borrow coverage→scanned-universe + report | code-done, **AC#3 live-verify pending** | blocks 178/179 | still-valid | pipeline |
| 173 | port split/halt detector to DropsLab | not-started (DropsLab) | depends 144✅; under 180 | still-valid | data-integrity |
| 174 | [GATE] Score-as-ranking demote/drop (AUC 0.531) | not-started | depends 127/141 | still-valid | decision-gate |
| 177 | extend outcome window D6-D15 | code-done AC#1/2, **AC#3 live-verify pending** | blocks 178/179 | still-valid (auto-grow gap risk) | pipeline |
| 178 | pre-register HYP-001 crossover-short | not-started | blocked 172+177; blocks 179 | still-valid | research |
| 179 | validate crossover hold-out n≥150 | not-started | blocked 178 + n≥150 (~4-5mo) | still-valid | research |
| 180 | split/halt detector parent (unify 90/148/173) | partial (RH code; AC#2 blocked on 182; DropsLab-half unblocked 144) | blocks research/gates | still-valid | data-integrity |
| 9 | Sentinel Analytics module | not-started | pre-active | still-valid | infra |
| 10 | Filter 12 ticker_reputation | not-started | depends 127/141 | still-valid | pipeline |
| 11 | cross-month aggregation (dashboard) | not-started | blocks multi-month analysis | still-valid | infra |
| 33 | Agent #6 Devils Advocate | not-started | roadmap | maybe-obsolete (FREEZE/Agent#8 priority) | agent |
| 34 | Agent #7 Risk Sentinel | not-started | roadmap | maybe-obsolete (built+reverted; FREEZE) | agent |
| 38 | health checks for support agents | not-started | pre-active transition | still-valid | agent |
| 39 | email consolidation 6→1 daily | not-started | comms hygiene | still-valid | infra |
| 54 | skill-gate phase-2 (enforce RELEVANT skill) | partial (v3.3 guidance) | kill-switch risk | still-valid | infra |
| 58 | separate service account for health_audit | partial (read-reduction verified) | measure peak first | still-valid | infra |
| 62 | broad email per-trade analysis (MxV/ATRX/Gap…) | not-started | partial-blocked n>91 | still-valid | research |
| 87 | fix mxv sentinel values polluting avg | not-started | blocks email Section C | still-valid | formula |
| 96 | check_06 downgrade clustered fails →WARNING | not-started (design-ready) | — | still-valid | infra |
| 101 | install security-guidance plugin + vet hook | not-started | gated on auto-mode readiness | still-valid | infra |
| 126 | scrape historical [SKIP] logs (90d retention) | not-started | read-only one-off | still-valid | research |
| 127 | Score decouple decision (Filter1 review) | not-started | feeds 174 | still-valid | decision-gate |
| 128 | entry-gate shadow-mode (price band, D1 re-anchor) | not-started | depends 174 | still-valid | pipeline |
| 132 | mark 14 stuck PENDING (SBLX+13 holiday) | not-started | depends 130✅/182 | still-valid | data-integrity |
| 137 | route ticker_follow_up RSI/ATR through ta/formulas (Wilder) | not-started | DRY §10 | still-valid | formula |
| 143 | resolve dup RH-2026-07 sheet | partial (orphan cleaned, root-guard pending) | **DEADLINE 7/1** | still-valid | infra(deadline) |
| 148 | DropsLab d1 +124% contamination port | not-started | depends 144✅; under 180 | still-valid | data-integrity |
| 149 | classify 19 NO_DATA (delisting/survivorship) | not-started | ties 132/168 | still-valid | data-integrity |
| 154 | evaluate private-repo migration (minutes/scrub) | not-started | depends 146✅ | still-valid | infra |
| 159 | _generate_lessons dead code: wire or remove | not-started | policy decision first | still-valid | decision-gate |
| 166 | daily lineage sentinel (random-row recompute) | not-started | guardrail | still-valid | data-integrity |
| 167 | SCHEMA.json contract for all sheets + drift | not-started | guardrail (cf 150) | still-valid | data-integrity |
| 168 | delisting auto-detector | not-started | phase-2 of 149 | still-valid | data-integrity |
| 169 | Wilson 95% CI beside percentages | not-started | honesty (extends 26) | still-valid | docs |
| 170 | market-regime cluster (unify 15+42+70) | not-started | market_context ready | still-valid | research |
| 176 | News Detective demotion (EOD/disable) | not-started | inside 136; depends 67 | still-valid | agent |
| 46 | Portfolio Tracker classify_trade dedup | not-started | code-quality (intentional differ) | still-valid (LOW) | infra |
| 109 | enable RECONCILE_AUTO_REPAIR | not-started | depends 106/108 track record | still-valid (LOW) | pipeline |
| 113 | literal raw-read verify timeline_live 4→2 | not-started | cache already effective | maybe-obsolete (LOW) | pipeline |
| 151 | PK batch drift (workflows 19→15, RSI dead, dead config) | not-started | merges 129 | still-valid | docs |
| 153 | adopt DROPSLAB_PK_DRAFT as docs/DropsLab_PK.md | not-started | depends 156✅ | still-valid | docs |
| 181 | cleanup stale .bak files | not-started | maybe-redundant (prune-script 114) | maybe-obsolete | cleanup |
| 49 | NCT recon mismatch decision_log vs paper_portfolio | not-started | reverse of 106 | still-valid | data-integrity |
| 63 | post_analysis_snapshot.json 2 vs ~104 rows | not-started | blocks 62 | still-valid | data-integrity |
| 65 | 9 closed positions w/o postmortem (104 vs 95) | not-started | from 62 | still-valid | data-integrity |
| 66 | SENTINEL counterfactual (blocked trades = winners 64% vs 41%) | not-started | blocks active-mode | still-valid | research/decision |
| 67 | News Detective no WIN/LOSS discrimination | not-started | feeds 136/176 | still-valid | agent/research |
| 68 | RSI divergence vs raw RSI | not-started | from 62; locked | still-valid | research |
| 69 | calibration inversion (ScanChange/REL_VOL vs MxV/RunUp) | not-started | LOCKED until n grows | still-valid | research |
| 71 | 'other-side' analysis (all documented, not just 104) | not-started | blocked 74 | still-valid | research |
| 72 | extended metrics scan (SMA20/Gap/DaysSinceIPO…) | not-started | from 62 | still-valid | research |
| 73 | automate CRITIC deep-analysis (62 methodology) | not-started | builds on 48✅ | still-valid | research |
| 74 | backfill 946 missing outcomes (post_analysis 54/~1000) | not-started | blocks 71/72 | still-valid | research/pipeline |
| 75 | DaysSinceIPO candidate metric (r=+0.261) | not-started | from 62 | still-valid | research |
| 82 | add 5 pro short-metrics (utilization, days-to-cover…) | not-started | data sources missing | still-valid | research |
| 83 | DropsLab drops_post D6-D15 tracking | not-started | parallel 177 | still-valid | research |
| 88 | monthly email graphs (equity curve + metric bars) | not-started | email enhance | still-valid | docs |
| 89 | monthly email anomaly detection | not-started | email enhance | still-valid | research |
| 90 | DropsLab reverse-split recovery cleanup (CTNT +28567%) | not-started | under 180; depends 144✅ | still-valid | data-integrity |
| 92 | [discussion] reduce/disable timeline_live minute-logging | not-started | GATE; ties 136 | still-valid | decision-gate |
| 182 | backfill InterdayArtifact on legacy rows | partial (pure fn done 5434861; write-back+scope+§0 bug pending) | blocks 180-AC2 | still-valid (scope refined 179/3mo) | data-integrity |
| 183 | DropsLab drops_post freshness alert (stall >2d) | not-started | created today | still-valid | monitoring |

**סה"כ: 66 שורות** (11 HIGH · 31 MEDIUM · 6 LOW · 18 ללא-priority).

---

*— END TASK_AUDIT_2026-06-15 —*
