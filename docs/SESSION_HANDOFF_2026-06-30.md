# SESSION HANDOFF — 2026-06-30

*מצביע על מקורות חיים (PK v-live, Backlog). קרא את ה-PK החי לפני פעולה.*

## נדחף ל-main היום (8 commits, ahead 0, HEAD=c19e246)
- **fix-יולי** (c19e246): 2 טאבים חסרים (shadow_gate_events + borrow_coverage) נוצרו ב-2026-07. יולי 25/25. deadline 1/7 נענה.
- **TASK-215 step-1+2** (ec46b4d + 54f6e9f): SA נפרד ל-auto_scan (`ridinghigh-auto-scan@`). קוד+yml+infra נדחפו. **no-op עד שה-secret `GOOGLE_CREDENTIALS_JSON_AS` למעלה.**
- **TASK-58 → Done** (b7b25e6): SA נפרד ל-health_audit + TASK-213 נפתח.
- **TASK-214 → Done**: audit auto_scan (de-dup נדחה; SA-נפרד הוא הפתרון).
- backlog notes: 126/208/215/65/128.

## 🔴 מעקב מחר בבוקר (08:30 פרו)
- **קודם כול — לוודא ש-secret `GOOGLE_CREDENTIALS_JSON_AS` הועלה ל-GitHub.** לא אומת בסשן הזה. אם לא → 215 no-op, auto_scan עדיין על ה-SA המשותף.
- **אם ה-secret למעלה:** ריצת auto_scan ראשונה עם AS SA — success? אין 429-קריסה? באמת עוברת ל-AS SA (לא fallback)?
- **מדידת דליפת-pp:** האם 215 מוריד ENTER-בלי-pp (GVH/SDOT היום)? זה הניסוי החי.
- Rollback אם צריך: `git revert ec46b4d 54f6e9f`.

## שרשרת חקירה שנסגרה היום (מאומת חי — נתון+קוד+system_events)
- **ENTER-בלי-pp** (GVH 08:54 + SDOT 09:27): ENTER מלא, cap נשלל (ColdStartConcurrentLeft>0), אך אפס שורת paper_portfolio.
- **Root-cause:** כתיבת-pp נכשלה תחת 429-storm → `safe_append_row` מיצה 3 retries (backoff 2/4/8s) → False → reconciler flag `RECONCILE_MISSING_PORTFOLIO_ROW` @16:00.
- **Owner = TASK-105 (DONE, PR#4 dc3ddbf)** — ה-write כבר מוקשח (retry+dedup+surface). **לא באג פתוח**; הכשל = retry-exhaustion תחת 429, by-design.
- **השארית:** TASK-109 (auto-repair, flag OFF) + TASK-215 (מפחית 429 במקור). GVH/SDOT = 2 true-positives ל-track-record של 109.
- **"מחר יכנסו מניות?"** כן, רובן (5/7 נפתחו היום, כולן נסגרו TP/SL באותו בוקר). חלק עלול ליפול על 429 — 215 אמור להקל.

## פתוחים + דדליינים
- **TASK-213** (deadline 2026-07-06): מדידת ירידת-429 בפועל פוסט-58/215.
- **TASK-126**: resume 6/04→6/30 + DR-backup ל-historical_skips.csv (16MB, local-only) לפני ~9/8.
- **TASK-109**: הפעלת RECONCILE_AUTO_REPAIR — להחליט אחרי מדידת-215/track-record.
- **TASK-216** (נפתח היום): root-cause מבני — טאב אמצע-חודש מחמיץ חודש-מוכן.
- **TASK-65**: ייתכן 2 באגים מוזגים (write-failure=105-domain מול _read_decision→{}=MetricsAtEntry).

## מצב-מערכת (קרא PK החי v-live לאישור)
- EXPLICIT_GATE_MODE=active (MxV≤−100 גייט ראשי, Score diagnostic, flip 29/6).
- 3 SAs: מסחרי + _HA (health_audit, פעיל) + _AS (auto_scan, ממתין ל-secret).
- SENTINEL=shadow, DRY_RUN, ENTRY_GATE_MINIMAL=True, SCORE_WRITE_FROZEN=True.
- 53 קבצי PK .bak מקומיים (~12MB, untracked) — מועמדים לניקוי, לא דחוף.

## הערה: PK ב-Project Knowledge (claude.ai) הציג v2.31. הריפו נקי ומסונכרן (origin=local=v3.89). לרענן/להסיר את ה-snapshot ב-Project Knowledge בצד המשתמש — הריפו לא צריך שינוי.
