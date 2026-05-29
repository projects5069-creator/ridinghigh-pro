# TASK AUDIT — RidingHigh Pro

**תאריך:** 2026-05-26 (יום שלישי, Peru / ET=EDT — אומת עם `date`)
**סוג:** דוח אנליטי בלבד — **לא** עדכון של רשימות קיימות, **לא** יצירת קוד, **לא** יצירת tasks חדשים ב-Backlog.
**מקורות שנקראו:**
- `docs/MASTER_TASK_LIST.md` (15 שלבים, ~65 משימות — אסטרטגיית מסחר/פילטרים)
- `backlog task list --plain` + 20 קבצי משימות פתוחות מ-`backlog/tasks/` (47 משימות, 20 To Do / 27 Done — תשתית/agents/תחזוקה)
- `NEXT_SESSION.md`, `docs/WORK_ALLOCATION.md`, `docs/WORK_LOG.md`, `PROJECT_STATE.md`

> ⚠️ דוח זה **לא מחליף** את `MASTER_TASK_LIST.md` ולא את ה-Backlog. הוא ניתוח-על שמאחד את שתי המערכות לתעדוף אחד.

---

## TL;DR — 5 ה-DO NOW

| # | משימה | מערכת | קטגוריה | למה עכשיו |
|---|-------|-------|---------|-----------|
| 1 | **SENT.2 / TASK-28** — Verify scan_freshness 26/5 | Backlog (HIGH) | Analysis | רגיש-זמן: היום הוא יום המסחר הראשון אחרי תיקון ה-lex-compare. חלון האימות פתוח **עכשיו**. |
| 2 | **DEV.1 / TASK-33** — Agent #6 Devil's Advocate | Backlog (MED) | Development | data-independent, ללא חוסמים, "הצעד הבא" המחושב ב-NEXT_SESSION, סוגר פער תקציב Development. |
| 3 | **Wait.3 / TASK-37** — Live Write Verification | Backlog (MED) | Maintenance | **שוחרר** — החוסם שלו (P1.4/TASK-6) הושלם. מאמת שכתיבות חיות (ENTER/EOD) נוחתות נכון. הקובץ עדיין מתויג BLOCKED בטעות. |
| 4 | **Stage 5** — score_analytics Workflow | Master | Development | הפריט הראשון שנותר ב"שבועיים ראשונים" של Master (0.4+2 כבר הושלמו). גיליון `score_analytics` כרגע **ריק** (PROJECT_STATE). |
| 5 | **DEV.2 / TASK-34** — Agent #7 Risk Sentinel | Backlog (MED) | Development | data-independent, שומר על סיכון תיק (ריכוזיות/חשיפה/קורלציה), משלים תקציב Development. |

*(5 השורות מוצגות גם ב-terminal בסוף הריצה.)*

---

## מתודולוגיה

**4 buckets** לפי בקשת המשתמש:
- 🔴 **DO NOW** — השבוע (25–31/5), עד 5
- 🟠 **DO SOON** — 2–4 שבועות, עד 8
- 🟡 **DO LATER** — חודש+, עד 6
- ⚪ **BLOCKED** — חסום על data / זמן / תלות

**כללי שיוך (לפי הוראת המשתמש):**
- משימה שחוסמת משימות אחרות → DO NOW (או מסומנת מפורשות כ-blocker).
- quick win (effort S × value High) → DO NOW.

**הסתייגויות (לפי חוקי המשימה):**
- דירוגי **effort (S/M/L)** ו-**value (L/M/H)** הם **הערכה אנליטית שלי**, לא נתון מתוך המסמכים — אלא היכן שקובץ המשימה נתן אומדן מפורש (AUDIT.11=1h, AUDIT.12=30min).
- כשלא יכולתי לאמת חסימה כתבתי **"possibly blocked"**.
- מה שלא ראיתי בנתונים נשאר **TBD** (ראו נספח "Data gaps") — לא ניחשתי.
- משימות מנוסחות-עמום קיבלו **שני פירושים** (ראו נספח).

---

## 🔴 DO NOW (השבוע — עד 5)

### 1. SENT.2 / TASK-28 — Verify scan_freshness on 26/5
- **מערכת:** Backlog · **עדיפות:** HIGH · **קטגוריה:** Analysis · **effort:** S · **value:** H
- **מה:** למשוך `system_events` ל-26/5 EOD, לספור BLOCK events מול סך הסיגנלים, לאמת שיעור BLOCK < 5%.
- **למה DO NOW:** רגיש-זמן. 26/5 הוא יום המסחר הראשון אחרי תיקוני ה-lex-compare (commits 5cc658b + 2ef7ceb). זהו אימות regression למקור ההתפוצצות של 21–22/5. workflow ה-End of Day כבר רץ היום (PROJECT_STATE: "Agent — End of Day 2026-05-26 21:00 UTC ✅") → הנתונים אמורים להיות זמינים.
- **חוסם/נחסם:** אין. עצמאי.
- **Data gap:** שיעור ה-BLOCK בפועל ל-26/5 **לא נמשך** בדוח זה (אימות = החלק שצריך להריץ). אם > 5% → לחזור לחקירה (SENT.1).

### 2. DEV.1 / TASK-33 — Build Agent #6: Devil's Advocate
- **מערכת:** Backlog · **עדיפות:** MEDIUM · **קטגוריה:** Development · **effort:** M–L · **value:** M–H
- **מה:** סוכן data-independent — לכל החלטת ENTER מייצר נימוק-נגד (למה לא לשורט), מתעד.
- **למה DO NOW:** (א) "הצעד הבא" המחושב ב-NEXT_SESSION.md לפי Rule §3; (ב) data-independent → אפשר לבנות עכשיו; (ג) WORK_LOG מראה D_pct ≈ 0–18% < 20% → כלל התקציב דורש Development.
- **חוסם/נחסם:** אין.

### 3. Wait.3 / TASK-37 — Live Write Verification
- **מערכת:** Backlog · **עדיפות:** MEDIUM · **קטגוריה:** Maintenance/verify · **effort:** M · **value:** H
- **מה:** בדיקת end-to-end שכתיבות חיות (ENTER, עדכון פוזיציה, סגירת EOD) נוחתות נכון ב-Sheets.
- **למה DO NOW:** **שוחרר** — קובץ המשימה אומר "depends on P1.4", ו-P1.4/TASK-6 הושלם (Done ב-Backlog; WORK_LOG 25/5: "P1.4 unblocked it"). value גבוה — תקינות נתיב-הכסף.
- **דגל:** קובץ המשימה עדיין כתוב "BLOCKED" — תיוג מיושן (ראו תובנה #5).

### 4. Stage 5 — score_analytics Workflow
- **מערכת:** Master · **קטגוריה:** Development · **effort:** M · **value:** M
- **מה:** 5.1 workflow `agent_score_analytics.yml`; 5.2 cron 21:30 UTC Mon–Fri; 5.3 שבת 23:00 UTC weekly; 5.4 verification.
- **למה DO NOW:** ב-Master זהו הפריט הראשון שנותר ב"שבועיים ראשונים" (הרצף היה 0.4→2→5; 0.4 ו-2 כבר מסומנים [x]). גיליון `score_analytics` כרגע **0 שורות / ⚠️ empty** (PROJECT_STATE) → פער נראה-לעין. עצמאי יחסית.

### 5. DEV.2 / TASK-34 — Build Agent #7: Risk Sentinel
- **מערכת:** Backlog · **עדיפות:** MEDIUM · **קטגוריה:** Development · **effort:** M–L · **value:** H
- **מה:** סוכן data-independent — ניטור סיכון ברמת התיק (ריכוזיות, חשיפה כוללת, קורלציה בין פוזיציות פתוחות), חוסם ENTER חדש בחריגת סף.
- **למה DO NOW:** data-independent + ערך-בטיחות + משלים תקציב Development.
- **דגל:** קיים קונפליקט מספור-סוכנים (ראו תובנה #7) — לאמת מי #6 ומי #7 לפני בנייה.

---

## 🟠 DO SOON (2–4 שבועות — עד 8)

| # | משימה | מערכת | קטגוריה | effort/value | הערה |
|---|-------|-------|---------|--------------|------|
| 1 | **Stage 3 — Full Metrics Logging** | Master | Dev | L / H | **BLOCKER** של Stage 4, 6, 14. להעלות ל-DO NOW אם Stage 4 הופך דחוף. בסיס נתונים ל-SKIPs שלא נכתבים היום. |
| 2 | **P2.2 / TASK-9 — Sentinel Analytics** | Backlog (MED) | Dev/Analysis | M / M–H | תנאי-קדם למעבר Sentinel shadow→active. |
| 3 | **AUDIT.3 / TASK-38 — Health checks for support agents** | Backlog (MED) | Maintenance | S–M / H | תפס באג אמיתי (5 ימי שתיקה של Critic/MktCtx/News, 24/5). quick win חזק — שקול קידום ל-DO NOW. |
| 4 | **AUDIT.7 / TASK-42 — SPY benchmark** | Backlog (MED) | Dev | S / M | quick win: Market Context כבר אוסף spy_close/open — רק אינטגרציה ב-entry+exit. |
| 5 | **P2.3 / TASK-10 — Filter 12 ticker_reputation** | Backlog (MED) | Dev | M / M | פילטר חדש ל-Trader, דילוג על whipsaws כרוניים (סגנון HCWB). |
| 6 | **AUDIT.4 / TASK-39 — Email consolidation** | Backlog (MED) | Maintenance | M / M | 6 מיילים/יום → סיכום יומי אחד + התראות-שגיאה בלבד (signal/noise). |
| 7 | **TD.8 — health_audit market-calendar awareness** | Master | Maintenance | S / M | תיקון false-positive שאירע 26/5. quick win. |
| 8 | **N2 / TASK-30 — מחיקה סלקטיבית של .bak_** | Backlog (LOW) | Maintenance | S / L | מתוזמן ~2026-05-30 (חלון בטיחות שבוע מ-P2.5). חופף ל-Master TD.3. |

---

## 🟡 DO LATER (חודש+ — עד 6)

| # | משימה | מערכת | קטגוריה | הערה |
|---|-------|-------|---------|------|
| 1 | **Stage 4 — Watch Threshold 15%** | Master | Dev | תלוי ב-Stage 3 (scanner_metrics_log מקבל 15–25%). |
| 2 | **Stage 6 — Minute Tracker** | Master | Dev | BLOCKER של Stage 14 (Entry Timing Score). |
| 3 | **Stage 8 — Position Sizing דינמי** | Master | Dev | חודש 3 בתכנון Master. |
| 4 | **Stage 9 — Time-based Exits** | Master | Dev | חודש 3 בתכנון Master. |
| 5 | **P2.4 / TASK-11 — Cross-month aggregation** | Backlog (MED) | Dev | Phase 1 משתרע על מספר חודשים; כל חודש מסולו היום. |
| 6 | **אשכול ניקיון LOW (tech-debt batch)** | Backlog | Maintenance | AUDIT.5 (מחיקת dummy_allow.py), AUDIT.6/TD.5 (filter order), AUDIT.8 (page logging), AUDIT.10/TD.4 (קבצים מיושנים — שים לב RAG capacity 32%), AUDIT.11 (classify dedup ~1h), AUDIT.12 (portfolio sheet ~30min). |

**אופק ארוך (חודשים 4+, מעבר ל-cap של 6) — מ-Master, לא נעלמים:** Stage 10 Anti-Squeeze · Stage 11 SEC EDGAR · Stage 12 Sector Heat · Stage 13 DropsLab Bridge · Stage 14 Entry Timing Score · Stage 15 Infra & Quality (כולל dashboard.py refactor 5,193 שורות).

---

## ⚪ BLOCKED

| משימה | מערכת | סוג חסימה | צפי שחרור | הערה |
|-------|-------|-----------|-----------|------|
| **Wait.1 / TASK-26** (≡ Master TD.6, TD.7) — WHIPSAW+NO_TOUCH + win-rate | Backlog (MED) | data-gated | **end-May 2026 (≈31/5, השבוע)** | n=62, צריך n>91. **possibly unblocking this week** — לאמת n נוכחי. |
| **P3.3 / TASK-15** — Wire Market Context | Backlog (MED) | data-gated | ~2026-06-23 | אפס שונות regime (100% NEUTRAL+LOW), 19h stale, 18/89 trades joinable. צריך backtest עם שונות. |
| **Wait.2 / TASK-27** — DropsLab integration #N25 | Backlog (LOW) | תלות + data | TBD | תלוי בצבירת data של DropsLab + תיקון Stage 13.1. |
| **Stage 7 — L3/L4/L5 Active** | Master | time-gated | "אחרי 30 ימי נתונים מ-L6" | 7.4 (L3 Toxic Profile) **כבר הושלם** (commit 14452a2). 7.1/7.2/7.3/7.5 חסומים. **possibly** ~סוף יוני — תאריך התחלת L6 המדויק לא נראה לי (Data gap). |

**Strategic (לא משימות — דיון, לפי Master):** STRAT.1 "Real WR 49.4% — מה זה אומר?" · STRAT.2 "Phase 2 gate (WR≥60%) — איך לסגור פער?". לא משויכות ל-bucket לבקשת המקור; דורשות החלטה, לא ביצוע.

---

## תובנות (Insights)

1. **שתי מערכות task מקבילות, בעלות scope כמעט-זר.** `MASTER_TASK_LIST.md` = אסטרטגיית מסחר/פילטרים (L3–L6, scanner metrics, sizing, exits…). `Backlog` = תשתית/agents/תחזוקה (Devil's Advocate, Risk Sentinel, bug-fixes, audits). הן כמעט לא נחתכות — חוץ מסעיף ה-Tech Debt.

2. **סעיף "Tech Debt" ב-Master מכפיל משימות Backlog:**
   - `TD.5` ≡ `AUDIT.6 / TASK-41` (filter order distribution) — אפילו כתוב "TASK-41" מפורשות.
   - `TD.6` + `TD.7` ≈ `Wait.1 / TASK-26` (WHIPSAW/NO_TOUCH + win-rate n>91).
   - `TD.3` ≈ `N2 / TASK-30` (+P2.5) — ניקוי .bak.
   - `TD.4` ≈ `AUDIT.10 / TASK-45` — ניקוי קבצים מיושנים/research dirs.
   → סיכון double-tracking. המלצה: לבחור מקור-אמת קנוני אחד או לקשר צולב (לא בוצע — דוח קריאה בלבד).

3. **קונפליקט "הצעד הבא" בין מסמכים:** NEXT_SESSION (23/5) → DEV.1 · Master (26/5) → "Stage 0.4 + Stage 2" (**שניהם כבר [x] done**) · WORK_LOG (25/5) → SENT.2/Wait.3/DEV. ההתכנסות: Development + ה-SENT.2 הרגיש-זמן. ה-footer של Master מיושן.

4. **סתירה פנימית ב-Master:** Stage 2 מסומן כולו `[x]` אך הכותרת אומרת "(NEXT)" וסדר העדיפויות אומר "Stage 0.4 → Stage 2". גם Stage 0.4 מסומן `[x]` (הושלם 26/5) אך מופיע כצעד הבא. → footer עדיפויות לא עודכן אחרי השלמת השלבים.

5. **Wait.3 / TASK-37 מתויג BLOCKED בטעות.** החוסם שלו (P1.4/TASK-6) Done. WORK_LOG כבר ציין "P1.4 unblocked it", אך גוף קובץ המשימה לא עודכן. → לסווג מחדש כ-actionable.

6. **גיליונות ריקים = פיצ'רים שלא נבנו** (PROJECT_STATE): `score_analytics`=0 (Stage 5), `borrow_data`=0 (Stage 10 short-interest), `pending_suggestions`=0, `config_history`=0. שימושי כ-cross-check לסטטוס roadmap.

7. **קונפליקט מספור-סוכנים.** Backlog: Agent **#6 = Devil's Advocate** (DEV.1), **#7 = Risk Sentinel** (DEV.2). זיכרון roadmap שמור (`project_agent_roadmap`) אומר "#6 Risk Sentinel next". סתירה — **לא הנחתי מי נכון**; דגל לאיחוד לפני בנייה.

8. **אחוז השלמה לא בר-השוואה בין המערכות:** Master 26% (17/65) מול Backlog 57% (27/47) — מודדים scope שונה. אין מספר "% done" יחיד משמעותי.

9. **אות התקציב עקבי ל-Development** (D_pct ≈ 0–18% < 20% לאורך הלוגים) → מתיישב עם פריטי ה-Development ב-DO NOW. A_pct נמוך גם → SENT.2 (ו-Wait.1 כשישוחרר) מכסים Analysis.

10. **שני פריטים מנוסחים-עמום (שני פירושים):**
    - *Stage 0.4 "בדיקת DropsLab":* (א) הושלם 26/5 וה-footer פשוט מיושן; (ב) קיימת בדיקת-המשך מתוכננת ל-DropsLab שטרם בוצעה. לא הכרעתי.
    - *Stage 2 "(NEXT)":* (א) תיוג מיושן והשלב גמור; (ב) יש עבודת-המשך ל-blacklist שלא נרשמה כתת-משימה. לא הכרעתי.

---

## נספח A — Data gaps (מה לא יכולתי לאמת)

- **SENT.2:** שיעור ה-BLOCK בפועל ל-26/5 לא נמשך (קריאת sheet נדרשת; מחוץ ל-scope של דוח קריאה-בלבד).
- **Wait.1:** ספירת ה-trades הנוכחית (n) — האם כבר ≥91? לא נראה לי. לכן BLOCKED מסומן "possibly unblocking this week".
- **Stage 7:** תאריך תחילת L6 המדויק → אי-אפשר לחשב במדויק את תאריך שחרור ה-30-יום.
- **דירוגי effort/value:** הערכה שלי, פרט ל-AUDIT.11 (~1h) ו-AUDIT.12 (~30min) שצוינו בקבצים.
- **הערת זיכרון מיושן (לא פעלתי לפיה):** `project_sentinel_shadow_status` אומר "system_events empty by design", אך PROJECT_STATE מראה 9,183 שורות + SENT.1 נסגר 24/5. הזיכרון משקף מצב ישן.

## נספח B — מיפוי מהיר ID → מערכת

- **Master stages:** 0–15 + TD.1–8 + STRAT.1–2.
- **Backlog open (To Do, 20):** TASK-28(SENT.2,HIGH) · TASK-9/10/11/15/26/33/34/37/38/39/42(MED) · TASK-27/30/40/41/43/45/46/47(LOW).
- **Backlog done (27):** TASK-1..8,12..14,16..25,29,31,32,35,36,44.

---

*נוצר 2026-05-26 ע"י Claude. אנליזה בלבד — לא עודכנו MASTER_TASK_LIST.md / Backlog / קוד.*
*Skills: ask-questions-if-underspecified (להבהרת scope) + verification-before-completion (טרם סיום).*
