---
id: TASK-268
title: 'detect_outage runs inside an agent run, so it dies with the system it guards'
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
updated_date: '2026-08-09 00:35'
labels: []
dependencies: []
priority: medium
ordinal: 266000
---


## Description

`detect_outage` (`agent/orchestrator.py:395-445`) is the only minute-resolution
outage detector in the system. Its logic is sound: read the newest `ScanTime`
from `timeline_live`, compare to now, raise above `gap_min > 10` (`:437`), mail
above 30 (`:566-600`).

Its **placement** defeats it. It is called at `orchestrator.py:577`, inside
`run()`. It only executes when an agent run executes. On 2026-08-06 no agent run
executed for hours, so nothing called it.

Verified directly against the logs of the last four completed runs:

```
31119866242  outage-mentions: 0
31120630280  outage-mentions: 0
31120684892  outage-mentions: 0
31120743074  outage-mentions: 0
```

**A detector that runs inside the thing it monitors cannot report that thing
stopping.** This is a structural property, not a bug in the logic — the logic
never ran.

## The mitigation already landed, and it is not a fix

`scripts/watchdog/watchdog_v1.gs` (commit 4406a92, deployment TASK-265) covers
the same failure from outside, on Google infrastructure. But it watches GitHub
Actions throughput, not `timeline_live` freshness. **They are different signals**:
the watchdog cannot see a run that executes and writes nothing.

## Acceptance Criteria

- [ ] #1 Decide whether `detect_outage` keeps its current role at all, given the
      external watchdog now covers total-stoppage from outside.
- [ ] #2 If it stays: give it a caller that does not depend on the agent running.
      ⚠️ `orchestrator.py` is a protected path; any change needs explicit approval.
- [ ] #3 Whatever is decided, record it — the current arrangement looks like
      coverage and is not.

Evidence: `reports/2026-08-06_1439_watchdog_design.md` §2

--- סומן למחיקה-מותנית 2026-08-08 (מרשם TASK_REGISTER §5) ---
**ההכרעה: `detect_outage` ימחק — אבל רק אחרי שהתקנת ה-watchdog החיצוני
(TASK-265) תאומת בפועל.** הנימוק המבני עומד כפי שנכתב בגוף: גלאי שרץ בתוך
`run()` (`orchestrator.py:577`) אינו יכול לדווח על כך שהריצות פסקו — ב-6/8
לא רצה אף ריצה, ולכן איש לא קרא לו (4 לוגים עם אפס outage-mentions).
⚠️ **הסדר קריטי ואסור להפוך אותו:** כל עוד ה-watchdog לא מותקן (ALERT_TO
עדיין placeholder ב-`scripts/watchdog/watchdog_v1.gs:24`), מחיקת
`detect_outage` תשאיר את המערכת **בלי שום גלאי-נפילות** — גרוע מהמצב הנוכחי.
**תלוי-265. אין לגעת לפני שלושת האימותים של 265 עוברים.**

--- עדכון 2026-08-08: החוסם ירד **חלקית** — ההתקנה בוצעה, האימות טרם ---

**מה השתנה:** עמיחי התקין את ה-watchdog ב-Apps Script על **RH-Summaries**
וקבע טריגר `rhWatchdogRun` · Time-based · Head · Owned by Me. ‏`rhWatchdogRun`
רץ ידנית (19:27:47→19:28:01, Execution completed), הטאב `watchdog_log` נוצר,
והשורה הראשונה נושאת `Queued=1` ⇒ ‏UrlFetchApp אושר וקריאת GitHub API עובדת.
‏`rhWatchdogTestAlert` רץ אף הוא (19:28:20→19:28:21).

⇒ **התנאי שכתוב כאן במפורש — "כל עוד ה-watchdog לא מותקן (`ALERT_TO` עדיין
placeholder)" — כבר אינו התיאור הנכון של המצב.** ה-watchdog מותקן ורשום.

⚠️ **אבל החוסם לא ירד במלואו, ואסור לקרוא את העדכון הזה כאישור-מחיקה.**
הסעיף למעלה מתנה את המחיקה ב**שלושת האימותים**, ואף אחד מהם עדיין לא נסגר:

```
AC#1  ≥3 שורות רצופות ב-watchdog_log מטריגר שירה מעצמו, בשעות-מסחר
      ❌ פתוח — אבל רק חציו. הטריגר **יורה מעצמו**: ארבע שורות אוטומטיות
         רצופות ב-00:30:27 · 00:35:28 · 00:40:27 · 00:45 (5:00 ו-4:59),
         אחרי הידנית ב-00:27:47. מה שחסר: שהן ייפלו **בשעות-מסחר** —
         כולן OUTSIDE_WINDOW כי זו שבת. אפשרי רק בשני 10/8, 14:45-19:45Z.
         שער: ~/rhpro_audit_run/audit_gate/gate265_watchdog.py
AC#2  מייל-הבדיקה התקבל בפועל
      ✅ נסגר 8/8 — נחת ב-projects5069@gmail.com ב-19:28, נושא
         "RH WATCHDOG: GitHub Actions pipeline is not producing".
AC#3  ALERT_TO המותקן אינו ה-placeholder
      ✅ נסגר 8/8, נגזר מ-AC#2 — @example.com שמור ב-RFC 2606 ואינו מקבל
         דואר, ולכן הקבלה בתיבה היא ההוכחה שהכתובת נערכה.
```

**ההבחנה שקובעת כאן:** טריגר **רשום** אינו טריגר ש**יורה** — וכאן כבר הוכח
שהוא יורה. מה שטרם הוכח הוא ש-`decide_()` עושה את **עבודת-הספירה** כשהחלון
פתוח (‏`Recent15`/`Prior60` מתמלאים). מחיקת `detect_outage` לפני כן תשאיר את
המערכת בלי גלאי אם ה-watchdog יורה אך אינו מודד — בדיוק מחלקת-הכשל
"נראה מותקן ואינו מחובר".

⇒ **הסדר נשמר: אין לגעת ב-`detect_outage`.** ‏`agent/orchestrator.py:395-445`
ו-`:577` ללא שינוי. השער הוא `watchdog_log` בשני, לא ההתקנה של שבת.
⚠️ ‏AC#1 של התיק הזה ("האם `detect_outage` שומר על תפקידו בכלל") **לא הוכרע
כאן** — זו הכרעת עמיחי, ולא נגעתי בה.

## הכרעת עמיחי 2026-08-10 — לא למחוק
detect_outage נשאר. הנימוק כתוב בגוף התיק עצמו: השומר החיצוני והגלאי הפנימי מודדים
**אותות שונים** — "the watchdog cannot see a run that executes and writes nothing".
זה בדיוק תרחיש 27/5 (387 ריצות ירוקות, אפס שורות נרשמו), והוא חזר ב-10/8 בערב
(145 שורות שגיאת-מכסה בחמש ריצות שנדגמו). מחיקה הייתה מסירה את הכיסוי היחיד לתרחיש.
התנאי המתלה (אימות ה-watchdog) נפתח ב-10/8 — אך ההכרעה היא לא למחוק בכל זאת.
agent/orchestrator.py:395-445 ו-:577 ללא שינוי; הקובץ קפוא עד 4/9 ממילא.
