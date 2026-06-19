# SESSION HANDOFF — 2026-06-19

מסכם 18/6 (עקירת-Score + יום-discovery) + 19/6 (תיעוד HYP-002 ב-ReboundPro, סגירת-יום).

---

## עקירת Score (forward-only, ADR-009)
- **Stage 0** writer-integrity (`bebd901`) + **Stage 1** freeze (`5c83eca`) — **DONE** (TASK-127.1 + TASK-127.2 נסגרו 19/6).
- scoreless-DATA-era פעיל: `SCORE_WRITE_FROZEN=True`. PK **v3.36**.
- **Stage 2** (driver-removal: Filter1/config/`calculate_score`) + **Stage 3** (viewer-hardening) — **PENDING**, חסומים על TASK-141.
- **TASK-141** = חקירת gate-חלופי, תלוית-recompute נקי.

## TASK-183 — false alarm מאומת (CLOSED)
- feed בריא מאז TASK-144; `drops_post` lag = **D5 מבני**; 698 = יום-אמת (broad down-day).
- **אימות-חי 19/6:** scan_date **6/10 = 94 שורות** ב-drops_post → feed בריא, D5-lag מבני **מאומת 100%**.
- **TASK-185 פתוח** (D5-freshness alert — code, טרם החל).
- 698-weight → robustness ל-TASK-179 (tracking).

## HYP-002 — long-rebound thesis (החדש הגדול)
- **יום-discovery שלם (18/6):** crossover-short התברר **מנופח+לא-סחיר** (−17.75% היה small-n+selection; short = HTB borrow) → **פיבוט ל-LONG mean-reversion** מבוסס.
- **signal:** composite `distress(pct_from_52w_high) + rsi_14` (volume+reversal נזנחו כרעש; leave-one-out).
- **regime-gate:** VIX≥~20 → long פעיל (+5%/74%up); VIX<18 → מת. מנגנון: liquidity-provision (NY Fed sr513).
- **עמידות:** OOS temporal+random · gradient מונוטוני · 2 regime-proxies עצמאיים · מנגנון מתועד.
- **סטטוס:** מבוסס-in-sample (n=3988 DropsLab), **verdict=Refine, טרם-forward**.
- **= ה-Phase-0 החסר של ReboundPro** (לא מערכת שלישית). **תועד ב-ReboundPro** (`d7b122e`, נדחף): `docs/HYP-002_long_rebound_thesis.md` + `docs/HYPOTHESES.md` + drift-fix BuildSpec + TASK-A/B/C.

## NEXT (כשעמיחי חוזר)
- **TASK-C (ReboundPro):** שאלת-דאטה — DropsLab n=3988 מול ReboundPro ~77, **drop-def parity**. ה-blocker לאינטגרציה.
- אחרי TASK-C: **פרומפט-חיבור HYP-002→ReboundPro** (composite→`scoring.py`, VIX→`market_context.py`, cost→`costs.py`; paper-only, לא deploy).
- **RidingHigh:** Stage 2 חסום על TASK-141.

## מצב-backlog (RH)
- פתוח (To Do): **62** (היה 64; נסגרו 127.1+127.2).
- נסגרו היום: TASK-127.1, TASK-127.2. כבר-Done: TASK-183.
- פתוחים-מרכזיים: 141 (חוסם Stage 2/3) · 185 (D5-freshness) · 179 (validate crossover — כעת מוקטן-עדיפות לטובת HYP-002/ReboundPro).

## הערה — מיקום-העבודה
רוב עבודת-היום (HYP-002) **ב-ReboundPro** (committed+pushed `d7b122e`). RH נשאר נקי-short — אין שינוי-קוד RH היום (רק סגירת-tasks + handoff זה). PK RH ללא-שינוי (לא נגענו בנוסחאות/workflows).
