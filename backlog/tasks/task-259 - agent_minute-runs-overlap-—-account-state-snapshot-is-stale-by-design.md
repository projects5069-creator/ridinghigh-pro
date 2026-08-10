---
id: TASK-259
title: agent_minute runs overlap — account state snapshot is stale by design
status: To Do
assignee: []
created_date: '2026-08-05 20:34'
updated_date: '2026-08-08 23:05'
labels:
  - bug
  - agent
  - concurrency
  - hyp-002
  - measured
dependencies: []
priority: high
ordinal: 257000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-05: agent_minute has a 60s cron but a median run duration of 292s, so 92.5 percent of consecutive run pairs overlap. build_account_state snapshots once per run before the signal loop, so a later run can decide against a world that predates an earlier run's ENTER. Produced two re-entry cap breaches on 2026-08-05 (DFNS, SHPH). Different root from TASK-244. Full evidence in Implementation Notes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-08-05 from 400 agent_minute runs of that day. Full evidence:
reports/2026-08-05_1515_reentry_breach.md.

THE MEASUREMENT
  gh run list --workflow=agent_minute.yml, all 400 runs dated 2026-08-05:
    duration s: min=34  p25=136  median=292  p75=321  max=370
    runs longer than 60s: 366 of 400 (91.5 percent)
    consecutive pairs where run N+1 STARTS before run N ENDS: 369 of 399 (92.5 percent)
The cron is every minute. The median run takes 292 seconds. Overlap is the normal state,
not an exception.

THE MECHANISM
build_account_state is called ONCE at the start of a run (agent/orchestrator.py:608-670),
before the signal loop at :721, and the resulting snapshot serves every signal in that
run. When runs overlap, a later run's snapshot can predate an earlier run's decision.
Filters 7 through 10 in decision_logic._check_filters then evaluate a world that has
already changed. This is a time-of-check to time-of-use gap BETWEEN PROCESSES: there is
no lock and no mechanism preventing two concurrent runs from deciding on the same ticker.

WHAT IT PRODUCED ON 2026-08-05
Two breaches of the re-entry cap (the frozen config allows at most 1 entry per ticker per
day):
  DFNS  ENTER 09:32:29 and 09:32:54   (25 seconds apart)
  SHPH  ENTER 11:40:39 and 11:43:55   (3 min 16 s apart)
In both pairs ColdStartConcurrentLeft and ColdStartDailyLeft are IDENTICAL between the two
entries (DFNS 5/7 and 5/7; SHPH 5/5 and 5/5). Had the first entry been visible they would
have decremented. The snapshot predates the event.

DFNS is conclusive. Three runs were active at the instant of ENTER #1, started at
09:30:08, 09:31:02 and 09:32:03. ALL THREE started before ENTER #1 was decided at
09:32:29. Whichever of them decided ENTER #2, its account snapshot could not contain the
first decision. DFNS position #1 opened 09:32:31 and closed 10:45:06 while position #2
opened 09:32:55 — 72 minutes of genuine simultaneous exposure on one ticker, not the
open-then-reenter case documented in TASK-107.

DIFFERENT ROOT FROM TASK-244. On 2026-07-22 build_account_state failed under a Sheets 429
and returned defaults. On 2026-08-05 there was no 429 and no ACCOUNT_STATE_UNAVAILABLE
anywhere in the day, while REENTRY_LIMIT fired 269 times and EXISTING_POSITION 48 times.
The reads succeeded; the guards ran; the input was simply older than the event. F6b
(decision_logic.py:428) closes the 429 path and does not touch this one.

CONSEQUENCE FOR HYP-002. The run re-registered on 2026-08-03 states that another breach of
the re-entry cap voids it (docs/HYPOTHESES.md section F). Two breaches are already in the
sample at n=17 of 150.

SHPH IS PARTLY A SECOND BUG. The first SHPH ENTER, DecisionID
DEC-2026-08-05-SHPH-114039-09, produced NO paper_portfolio row at all. Only the second
wrote one. Even a fresh snapshot would not have found it in the paper_portfolio source.
That belongs to the TASK-105 / TASK-106 / TASK-198 class.

NOT ESTABLISHED, do not assume:
  - 396 of the 400 runs are workflow_dispatch and only 4 are schedule. What triggers them
    was not investigated.
  - Whether the same overlap explains the timeline_live duplicates in TASK-253 (931
    duplicate (ScanTime, Ticker) pairs over three days). auto_scan.yml was not examined.
  - Which specific run made each decision. Three candidates for DFNS, five for SHPH; run
    logs were not opened.
  - Why only one run appeared in skip_summary during the 11:36-11:48 window while five
    were active.

No fix is proposed here by design.

SCOPE NARROWED 2026-08-06.

PART B AS ORIGINALLY FRAMED — batching sentinel events into one append per run — WAS NOT
DONE AND WILL NOT BE DONE IN THAT FORM. Two reasons, both established by measurement:

1. It requires orchestrator.py. Accumulate-then-flush already exists twice in this repo
   and in BOTH cases the flush is called from the orchestrator:
       agent/orchestrator.py:794  decision_logger.flush_skip_summary()        (TASK-125)
       agent/orchestrator.py:800  decision_logger.flush_shadow_gate_summary() (TASK-128)
   There is no alternative anchor: check_system runs at the START of the run, and run()
   has five `return summary` exits (:566 :573 :688 :728 :856) of which four precede the
   existing flushes — so even the existing pattern loses rows on an early exit.
   orchestrator.py is a protected path (RUN_MODE_DECISION.md:40-43).

2. It targets the wrong axis. The 429 measured on 2026-08-05 was on 'Read requests', so
   the failing call was get_worksheet, not the append. safe_append_row already retries
   (sheets_manager.py:389). Batching would have addressed a write-quota problem that was
   never observed as a failure.

WHAT WAS DONE INSTEAD: TASK-218, closed 2026-08-06 (commit 1df9cba) — the worksheet handle
is looked up once per run instead of once per event, inside data_sentinel.py only, with no
flush and no orchestrator change. That removes ~60 READ calls per run, which is the axis
that actually failed.

WHAT REMAINS IN THIS TICKET. One thing: MEASURE THE RUN DURATION IN PRODUCTION now that
two fixes have landed —
    fcdb0aa  SMA20 batched into one Alpaca request  (merged, in main)
    1df9cba  sentinel_events handle cached per run   (this session)
Baseline to beat, measured 2026-08-05 on 487 runs: median 203s, 79 percent of consecutive
pairs overlapping.

WHY IT MATTERS: the concurrency YAML for agent_minute and auto_scan is still sitting
uncommitted in the working tree, and whether it is still needed depends on this number.
The arithmetic says 203 - 106 (SMA20) - 45 (sentinel loop) = 52s, under the 60s cron — but
BOTH subtrahends are upper-bound estimates. The 106s was never reproduced outside Actions
(9.05s serially from a laptop, a factor of 12 unexplained), and the 45s is the whole signal
loop, not only the sentinel writes. The measurement decides; the arithmetic does not.

⚠️ Do not deploy concurrency before that measurement. Its known side effect is unresolved:
check_06/D3 is expected to flip to CRITICAL because a concurrency-cancelled run is
status=completed with conclusion=cancelled, which enters the denominator at
health_audit.py:596-605 but not the numerator. Documented in
reports/2026-08-05_1926_task259_concurrency.md section 6.3.

────────────────────────────────────────────────────────────────────────────────
UPDATE 2026-08-06 — a third option exists, and two claims above are now WRONG.

1. THERE IS A THIRD OPTION: `queue: max`. GitHub's workflow-syntax documentation,
   read today, describes it as allowing "multiple runs to queue instead of being
   canceled — up to 100 pending runs to wait in order." Every analysis in this
   ticket assumed the only choice was cancel-the-pending-run. It was not. A real
   queue of up to 100 changes the cost side of this decision completely: the
   scans would be delayed rather than dropped, and the "effective interval of
   4.5 minutes" framing does not apply to it at all.
   ⚠️ NOT verified as available on this plan. Verify before designing around it.

2. THE SEMANTICS ARE NOW SOURCED, NOT ASSUMED. Same doc, verbatim: "any existing
   pending job or workflow in the same concurrency group will be canceled and the
   new queued job or workflow will take its place." So with N runs waiting, N-1
   are cancelled and the newest survives. This confirms what was assumed here —
   but it is now a citation rather than a guess.

3. ⚠️ THE check_06 WARNING ABOVE IS OVERSTATED. It was computed from the DAILY
   aggregate (about 26 percent success). But check_06 does not see a day: it
   fetches per_page=50 at health_audit.py:639, which at two runs per minute is a
   24-minute window, and health_audit fires at 11:00 / 20:30 / 03:00 UTC. Run
   against 1,000 real runs from 2026-08-05, the verdict at the two evening times
   is PASSED 100 percent (50/50) — the window lands entirely after the close,
   where runs exit in 30-40s and concurrency would never supersede anything.
   The 06:00 check could not be computed (pagination capped at 1,000 runs) and no
   claim is made about it.
   The CRITICAL flip is therefore much less likely than stated above. Still not
   certain: two days of data, health_audit was never actually run. See TASK-267,
   which covers the underlying counting defects in check_06 itself.

4. ⚠️ THE 203s BASELINE IS CONTAMINATED. On 2026-08-05, 188 of 487 agent_minute
   runs (38.6 percent) were cut off by the 5-minute timeout at timeout-minutes: 5.
   A truncated run cannot report a duration longer than its truncation, so the
   median is biased downward by an unknown amount. See TASK-266. The production
   measurement this ticket is waiting for must be taken on a day without that
   truncation, or the comparison is meaningless.

5. ⚠️ DO NOT DEPLOY WHILE GITHUB IS BROKEN. GitHub Actions entered a major outage
   at 2026-08-06T15:22:49Z (impact: critical; "jobs may remain queued for an
   extended period"). Deploying concurrency during a provider outage mixes two
   variables and makes every subsequent measurement uninterpretable. The queue of
   374 runs seen today is the outage, NOT saturation — in_progress was 0 across
   four consecutive measurements, and saturation looks like in_progress equal to
   the cap, not zero.

Evidence: reports/2026-08-06_1406_queue_recon.md
────────────────────────────────────────────────────────────────────────────────
<!-- SECTION:NOTES:END -->

--- השאלה הפתוחה 2026-08-08 (מתוכנית-העבודה) — לא הוכרע ---
גוש ה-`concurrency` כתוב בעץ-העבודה בשני ה-yml ואינו מוקומט. חלון-המדידה
נפתח 10/8, ופריסה **בתוכו** מכניסה משתנה חדש לאמצע הניסוי.

**השאלה: מתי (ואם) לפרוס את ה-concurrency?**
1. א. **לפרוס לפני שני** — החפיפה (92.5%) נעצרת מהיום הראשון; המחיר: ריצות
      מבוטלות יגדלו (ריצה שממתינה נזרקת), והמדגם ייאסף תחת משטר-ריצות שונה
      מזה שנמדד עד היום. חייב לנחות יחד עם הכרעת-266 (שתיהן משנות את אותו
      משטר — עדיף שינוי אחד מתועד משניים נפרדים).
   ב. **לא לפרוס בכלל בחלון** — המדגם נאסף תחת המשטר המוכר; המחיר: סיכון
      פריצת-re-entry נוסף (שתיים כבר קרו ב-5/8), ופריצה פוסלת את HYP-002.
   ג. לפרוס באמצע החלון — ⚠️ הגרוע משניהם: חצי-מדגם בכל משטר. מובא רק כדי
      לסמן אותו כפסול.
   ⚠️ אין ברירת-מחדל. **לא הוכרע.**

2. מה מודדים לפני ההכרעה? ה-baseline הקיים (חציון 203ש) מזוהם — נמדד ביום
   שבו 38.6% מהריצות נקטעו ע"י ה-timeout (ראו TASK-266). מדידה נקייה דורשת
   שהכרעת-266 תיפול קודם. ⇒ **תלות-סדר: 266 לפני 259.**

--- סקירת-קוד 2026-08-08 על הדיף הלא-מקומט — שני ממצאים, לא הכרעה ---

הדיף שיושב בעץ-העבודה (‏`concurrency` בשני ה-yml) נסקר ע"י סוכן `reviewer`.
פסיקה: FLAG, שני ממצאים. שניהם **נרשמים כאן כקלט להכרעה של עמיחי בסעיף
הקודם — הם אינם מכריעים אותה ואינם משנים את הדיף.**

**ממצא 1 — הדיף פורס בלי המדידה שהתיק דורש.**
אחרי צמצום-ההיקף מ-6/8 נותרה בתיק דרישה אחת: למדוד מחדש את משך-הריצה
בפרודקשן. התיק כותב במפורש ⚠️ *"Do not deploy concurrency before that
measurement"*. הדיף מבצע את הפריסה, והמדידה טרם נלקחה. בנוסף,
השאלה-הפתוחה מ-8/8 ("מתי ואם לפרוס") לא הוכרעה, ואין לה ברירת-מחדל.
⇒ קומיט של הדיף הזה כמות-שהוא סותר את התיק — אלא אם ההכרעה בסעיף הקודם
תיפול על 1א ותירשם.

**ממצא 2 — ההערה בקוד סותרת את הסמנטיקה שהתיק עצמו מצטט.**
בשני ה-yml נכתב:
    `# One run at a time. A queued run is dropped if another is already running`
לפי התיעוד שהתיק מביא בציטוט (סעיף UPDATE 2026-08-06, פריט 2), עם
`cancel-in-progress: false` מתרחש **ההפך**: *"any existing pending job or
workflow in the same concurrency group will be canceled and the new queued
job or workflow will take its place"* — כלומר הממתינה **הקיימת** מבוטלת
והחדשה תופסת את מקומה; מתוך N ממתינות שורדת החדשה ביותר.
⇒ ההערה, אם תיפרס כלשונה, תטעה מי שיחקור בעתיד למה סריקות נעלמו. תיקון
ההערה אינו תלוי בהכרעת-הפריסה ואפשר להפריד אותו ממנה.

סייג: זו דעת-סוכן על הדיף, לא מדידה. ממצא 2 בר-אימות מול התיעוד המצוטט
בתיק; ממצא 1 הוא קריאת-דרישה, והפירוש שלה נתון לעמיחי.

--- 2026-08-08: מדידת-שני של TASK-266 נותנת גם את הנתון של 259 ---

‏TASK-266 הוכרעה 8/8 (אופציה ג׳: לא נוגעים בתקרה, מודדים בשני 10/8). שער-הקבלה
שלה מודד **ארבעה** דברים, ושניים מהם הם בדיוק מה שהתיק הזה ממתין לו:
אחוז-מבוטלות · **חציון ו-p90 של משך-job** · ‏429 אמיתיים · **חפיפת-ריצות בפועל**.

⇒ **שתי המשימות, מדידה אחת.** אין צורך במדידה נפרדת ל-259.

**ואם חציון-שני < 60ש עם סיגנלים אמיתיים — שאלת-הפריסה של 259 מתייתרת מאליה.**
‏cron הוא דקתי; ריצה שמסתיימת בתוך הדקה אינה חופפת לבאה אחריה, ולכן
ה-TOCTOU בין-התהליכים שהתיק הזה מתאר פשוט לא מתרחש. אין מה לפרוס.

הנתונים שכבר יש, ולמה הם עדיין לא מספיקים:
```
8/5  (יום התיק, לפני התיקונים, בסערת-429)   חפיפה 92.5%   חציון 292ש/203ש
8/7  (אחרי fcdb0aa + 1df9cba)                חפיפה 10.2%   חציון 48ש · p90 56ש
```
⚠️ ‏8/7 אינו ראיה מספקת: זהו יום ה-FINVIZ השבור, ובלוגים חוזר
`No signals to process this minute` — הריצות קצרות גם משום שלא הייתה
עבודת-סיגנלים. **שני הוא היום הראשון עם סיגנלים אמיתיים אחרי התיקונים.**

⇒ **אל תכריע את שאלת-הפריסה לפני שהמספר של שני קיים.** אם החפיפה אכן קרסה
מ-92.5% ל-‏~10%, אופציה ב׳ ("לא לפרוס בכלל בחלון") מקבלת בסיס מדוד ולא רק
העדפה — והדיף שיושב בעץ-העבודה עשוי להתייתר לגמרי.

‏baseline מזוהם שנשאר לתיקון (מ-Implementation Notes, פריט 4 של UPDATE 2026-08-06):
"median 203s on 487 runs" — נמדד ביום שבו 38.6% מהריצות נקטעו. **יתוקן במספר
הישר של שני**, לפי AC#3 של 266.

════════════════════════════════════════════════════════════════════════════════
## 2026-08-10 — baseline-שני האמיתי + הפרכת שתי הנחות (append)

**המספרים של היום** (365 ריצות, job-level): חציון 58ש בבוקר → 101ש אחה"צ ·
p90 עד 152ש · max 316ש · חפיפת-זוגות 53%→95% · שיא-מקביליות 5 · 1 מבוטלת.
(מחליף את "median 203s" המזוהם ואת "48ש/10.2%" של 8/7 חסר-הסיגנלים.)

**ופריצה חיה של התקרה, יום 1 של החלון:** JWEL ×2 + DKI ×2 בהפרש 1-2ש, משתי
ריצות שהתחילו job באותה שנייה (13:31:13Z) — run 31392859358 (נוצרה 13:26:02,
המתינה 311ש בתור) ו-31393286602 (נוצרה 13:31:02). Score זהה = אותה שורת-סיגנל
= כפילות-אכיפה. TASK-301.

⚠️ **"חציון<60ש ⇒ הפריסה מתייתרת" הופרך:** השורש היום היה עיכוב-תור
(מחסור-runners של GitHub), לא משך-ריצה. גם ביום שכל הריצות קצרות, שתי ריצות
יכולות להתחיל באותה שנייה. המדד להכרעה = זוגות התחלות-צמודות (<15ש), הנמדד
יומית ע"י scripts/detect_duplicate_entries_v1.py.

מחיר-הפריסה נמדד (סימולציה על נתוני-היום): 137/365 נזרקות (חסם עליון) ·
כיסוי-דקות 359→228 · אף ריצת-ENTER לא נזרקת · הכפילות נמנעת ע"י סידור.
ההערה בגוש ה-yml תוקנה 10/8 מול התיעוד הרשמי (הישנה תיארה את ההיפך).
הכרעת-פריסה: ממתינה 3-4 ימים לנתוני הגלאי (הכרעת עמיחי 10/8).

## 2026-08-10 ערב — gate266 FAIL: ה-baseline הישר של סוף-יום

last-60 של הסשן: median=314s (חיתוך-timeout, לא משך-אמת) · חפיפה 98.3% ·
44/431 מבוטלות · 145 שורות-429 ב-5 ריצות. סופת-429 של אחה"צ החזירה את
משטר-8/5. המספר "1 מבוטלת" מה-append הקודם נמדד באמצע-היום — מתוקן.
⇒ שאלת-הפריסה אינה מתייתרת; היא מוכרעת על נתוני הגלאי + הנתונים האלה.
