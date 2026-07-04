# SESSION HANDOFF — 2026-07-04 (שבת)

**קריאה חובה לסשן הבא:** קרא קודם `rhpro-live` (עובדות-מערכת חיות) + `docs/SESSION_PROTOCOL.md`.
ה-handoff **מצביע**, לא משכפל — כל מספר מול המקור החי.

**Session end:** 2026-07-04 ~08:46 Peru (America/Lima) / 09:46 ET · שבת (שוק סגור)
**HEAD:** `975ac7c` · origin/main **in sync** (ahead 0 / behind 0) · working tree clean
**OPEN tasks (live `backlog task list`):** **50**
**Global state:** DRY_RUN · gate = **active + minimal** (flip 6/29) · Sentinel = shadow · PK **v4.04→v4.05**
**HYP-002:** קפוא עד ההכרעה (~2026-07-27 checkpoint / n≥150 post-flip / 45 ימי-מסחר, המוקדם). n post-flip = **25/150** → הקצב מוביל להכרעה קרובה ל-45-הימים (סוף-אוגוסט). checkpoint 27/7 = על n חלקי.

---

## א. מה נעשה היום (3-4/7) — docs+backlog בלבד, אפס שינוי קוד/gate

| נושא | תוצר | commit |
|------|------|--------|
| חקירת E2E S1-S5 (P0-P9 + X1-X6) | דו"ח `plans/stateless-seeking-sifakis.md` + סל-ב docs | `19832a7` |
| מחקר-מדדים + post-flip + תזמון-כניסה | PK v4.03 research-log + TASK-229/230 | `7922dee` |
| candle-recon verdict (IEX blocked-by-data) | PK v4.04 + TASK-230 שלבי-דאטה | `975ac7c` |

**ידע-מחקר מרכזי (הכל raw/exploratory — אפס קיבוע לפני 27/7):**
- **MxV מחזיק לבד** — base-WR בתוך MxV≤−100 = 87.8% [83-91] n=270 (TP10_Hit, מדגם-מחקר); ceiling → אף booster לא מפריד מעבר-CI. מדידת-boosters עתידית = עומק/catastrophe, לא WR.
- **ScanChange% = מתאם-העומק החזק** (Spearman −0.365 מול MaxDrop) אך חופף-MxV → דגל-סיכון בלבד, לא gate.
- **late-entry (≥15:30 ET)** הראתה edge יחסי raw (sim R1: WR 57.1 מול 46.9; כל ה-PnL שלילי על יקום-survivorship 176/4,425 — השוואה-יחסית בלבד). אנטומיית-שיא: הופעה→שיא median 29 דק', שיא→−3% median 6 דק', **אין חתימת-שיא מדדית**.
- **חתימת-נרות חסומה-דאטה** — feed=IEX (paper-plan) נותן median 28/390 נרות ליום למיקרו-קאפ. IBKR/SIP הם השער לבדיקה אמיתית.

## ב. פתוחות מדורגות — תעדוף למחר/הבא

**דחוף:**
- **TASK-213** [HIGH] — אימות ירידת-429 של TASK-58, **דדליין קשיח 2026-07-06** — לא לדחות.
- **TASK-223** [HIGH] — DST time-sweep (is_snapshot_time לא-DST-aware, auto_scanner:76-78) — **דדליין לפני 2026-11-01** (מעבר EST).

**נתיב-חי (דורש go מפורש למימוש-קוד):**
- **TASK-224** [MED] — qty<1 ⇒ SKIP עם skip_reason ייעודי (הכרעת-notional).

**דאטת-נרות (דורש go):**
- **TASK-230** שלבים: 4א volume-per-scan מ-FINVIZ (feed-independent) · 4ב yfinance-1m forward-collection · **4ג IBKR-recon** (השער ל-backfill היסטורי; SIP רק-אם-4ג-נכשל).

**חסום עד סיום HYP-002 (~27/7):**
- **TASK-225** hold-window D1-D25 · **TASK-229** HYP-004 late-entry forward research (רישום ל-HYPOTHESES רק בהחלטה נפרדת אחרי verdict).

**אשכול-Score (נדחה כמכלול, LOW):** TASK-208 (ranking ×3 אתרים) · TASK-209 (retire calculate_score + dead-imports + health_audit 07/12) · TASK-222 (dup _is_day_complete). **TASK-194** = ניטור post-flip בלבד.

## ג. IBKR — לשאול לפני 4ג
לעמיחי חשבון-IBKR. שלב-4ג (recon) דורש לוודא ש-**Gateway/TWS מותקן ורץ** על ה-Mac (IBKR API הוא session-based, לא REST) — **לשאול לפני** שמתחילים recon.

## ד. הערות-דיוק (drift שתוקן / פתוח)
- §0.3 בחוזה-הגלובלי המודבק מזכיר "Backlog.md" — **שגוי**: הבקלוג = `backlog` CLI + `docs/BACKLOG_DETAILED.md`.
- "2 eod_borrow failures" (רשומות-PK ישנות) — תוקן ב-v4.02: בפועל 2 טסטי-integration (אחד תלוי-סדר → TASK-228; CI מדלג `-m "not integration"`).

## ה. Process
- אפס נגיעה ב-TP/SL/HOLD/reentry עד verdict-HYP-002 (void + re-registration).
- כל ממצא-חקירה → TASK, לא fix אגבי. מימוש בנתיב-חי (agent/execution/gate) = go מפורש.
- §15 SESSION_PROTOCOL: build-from-files, Anti-Drift על PK בכל close.

**חתימה:** נכתב 2026-07-04, סגירת-סשן (Fable 5). HEAD `975ac7c`, tree clean, OPEN=50.
