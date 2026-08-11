---
id: TASK-194
title: >-
  ADR-009 post-flip monitoring: track active-mode entries vs Score-gated
  baseline (flip executed 6/29)
status: To Do
assignee: []
created_date: '2026-06-24 16:10'
updated_date: '2026-07-04 01:50'
labels:
  - agent
  - score
dependencies: []
priority: medium
ordinal: 200000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ADR-009 Stage 2 driver-removal — the LIVE flip deferred by the 141+174 ruling (Option B, shadow-first). BLOCKED until >=2 weeks of multi-regime shadow_gate_events data (TASK-128) show the SCORE_TOO_LOW->would-ALLOW divergence is benign. Then either flip EXPLICIT_GATE_MODE to active, OR remove Filter 1 Score gate (decision_logic.py:277 d.score<AGENT_MIN_SCORE) + Score ranking (auto_scanner.py:578/1338 idxmax / TRADE_ENTRY_MIN_SCORE>=70) + retire calculate_score. Two-shape tolerant history reads (ADR-009 over-principle). Linked: TASK-128 (shadow owner) + ADR-009. Decision-gates 141/174/127 already Done (decision recorded). TDD + ping-pong when unblocked.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 decision_logic live path (evaluate_signal) honors EXPLICIT_GATE_MODE: shadow=Score gates byte-identical, active=Filter 1 skipped + filters 2-11 decide (TDD)
- [x] #2 flip AND revert = single EXPLICIT_GATE_MODE config value; zero code change to toggle
- [x] #3 stage-1 lands flag=shadow -> zero live-behavior change verified (shadow test byte-identical)
- [ ] #4 flip executed 2026-06-29 ahead of shadow-accumulation (owner decision, DRY_RUN/reversible); monitoring now POST-flip: track active-mode entries + outcomes vs prior Score-gated; revert=EXPLICIT_GATE_MODE shadow
- [x] #5 zero touch to scanner-ranking (S2) and calculate_score retire (S3) - separate tasks (208/209)
- [x] #6 PK + ADR-009 updated with decision + reversible-flag mechanism
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
E2E-AUDIT S5 (3/7) — הכותרת הקודמת ('flip after shadow proves benign') הייתה stale: ה-flip בוצע 6/29 (owner-decision, PK v3.77, ללא חלון-shadow — 0 שורות shadow_gate_events באותו רגע). ה-scope החי הנותר = AC#4 בלבד: ניטור post-flip של כניסות-active מול baseline Score-gated + revert-בערך-קונפיג. גבולות: הסרת-ranking = TASK-208 (AC#5) · retire calculate_score = TASK-209. קצב-ההכרעה צמוד ל-stopping-rule של HYP-002 (n>=150 post-flip או 45 ימי-מסחר; checkpoint 2026-07-27 = החלטת-promote נפרדת, HYPOTHESES.md:202-204).
<!-- SECTION:NOTES:END -->

## HYP-002 VOIDED 2026-08-03

The run this task monitors was voided. n reached 173 against a threshold of 150 while 86 of those entries sat on phantom tickers and 54 breached the frozen reentry cap. Re-registered from 2026-08-03 with no carry forward. Whatever this task tracks starts again from that date.

--- השאלה הפתוחה 2026-08-08 (מתוכנית-העבודה) — לא הוכרע ---
AC#4 (הניטור) הוא הפריט היחיד שנותר פתוח, והבסיס שלו נמחק: הריצה שהוא עקב
אחריה בוטלה ב-3/8. ‏`docs/MEASUREMENT_HORIZON.md` נעל מאז חלון חדש
(10/8→4/9, ‏n_ENTER≥100, הכרעה 7/9).

**השאלה: מה בדיוק AC#4 מודד עכשיו?**
1. א. **לנסח מחדש מול האופק הנעול** — הניטור הופך ל"אוסף כניסות-active
      ותוצאותיהן בחלון, מול baseline היסטורי Score-gated"; זו עבודת-הגדרה
      (docs), אפס קוד.
   ב. לסגור את AC#4 ולתת ל-MEASUREMENT_HORIZON לרשת אותו במלואו — התיק
      נסגר, אבל אז אין תיק-בעלים לניטור עצמו.
   ג. להשאיר כמות-שהוא — ⚠️ פסול בפועל: מודד תקופה שכבר לא קיימת.
   ⚠️ אין ברירת-מחדל. **לא הוכרע.**

2. מה ה-baseline להשוואה? ‏Score-gated היסטורי — אבל עמודת ה-Score ריקה
   מיולי (SCORE_WRITE_FROZEN), כך שההשוואה אינה טריוויאלית. **פתוח.**

⚠️ אם אף אחת מהאפשרויות לא נבחרת לפני 10/8: החלון ייאסף ולא יהיה מוגדר
מי קורא אותו ב-7/9.

## ממצא 2026-08-10 — שתי האפשרויות שהוצגו נפסלו, שתיהן
נקרא `docs/MEASUREMENT_HORIZON.md` במלואו (170 שורות, חמישה סעיפים, אף אחד אינו ריק).
§1 מגדיר את השאלה הנמדדת: **"האם ששת מדדי-הכניסה של המועמדים שנדחו מבדילים אותם
מאלה שנכנסו"** — כלומר נדחים מול נכנסים.
AC#4 של התיק הזה מודד **נכנסים במשטר החדש מול baseline היסטורי Score-gated**.
אלה שתי שאלות שונות על אותה תקופה.
⇒ אפשרות א' ("לנסח מחדש מול החלון") אינה עובדת — החלון אינו מכיל את השאלה.
⇒ אפשרות ב' ("לסגור ולתת לחלון לרשת") אינה עובדת — **אין מה לרשת**.
מדידות תומכות: grep על `קורא`/`reader`/`baseline`/`השוואה` במסמך מחזיר **0** לכל אחד.
⏳ **פתוח.** ההכרעה האמיתית: לנסח ל-194 שאלה חדשה ומדידה, או להצהיר שהניטור נזנח במודע.
