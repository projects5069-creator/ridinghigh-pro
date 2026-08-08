---
id: TASK-269
title: Delayed runs write current prices under a stale signal timestamp
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
labels: []
dependencies: []
priority: medium
ordinal: 267000
---


## Description

Data contamination observed on 2026-08-06, caused by the GitHub Actions outage
but **not prevented by anything in our code**. It would recur on any day with
severe runner delay.

Concrete case, run `31120743074`:

```
created  : 2026-08-06T16:42:02Z     <- the minute the run represents
checkout : 2026-08-06T18:36:22Z     <- when a runner was finally allocated
first log: 2026-08-06T18:37:08Z
finished : 2026-08-06T18:37:51Z  (success)
```

**A queue wait of 1h54m.** The run then fetched live market data at 18:37 and
processed it as the 16:42 signal set. It reported success. Nothing in the run
noticed that its own idea of "now" was two hours behind the wall clock.

This is not one run. 154 `agent_minute` and 148 `auto_scan` runs were queued at
the time of measurement, and everything that eventually drains carries the same
defect proportional to its wait.

## Also visible in that same log

```
18:37:08 [WARNING] agent.orchestrator: check_emergency_stop: fetch failed
         (APIError: [429]: Quota exceeded for quota metric 'Read requests' ...)
```

The read-quota 429 is still live. TASK-218's handle cache (`1df9cba`) is in
PR #36 and not merged, so this is expected — recorded here only as corroboration
that the run really was executing at 18:37.

## Acceptance Criteria

- [ ] #1 Decide the policy: should a run whose start is more than N minutes after
      its scheduled minute do its work at all, or exit early and log a skip?
- [ ] #2 If it should exit: where does the check go, and what is N? The run has
      access to its own scheduled time via `GITHUB_EVENT` / the API.
      ⚠️ `orchestrator.py` is a protected path; needs explicit approval.
- [ ] #3 Quantify the damage already done — how many rows written on 2026-08-06
      carry a timestamp materially older than the data in them.
      ⚠️ Read-only against Sheets, outside market hours.

Evidence: `reports/2026-08-06_1406_queue_recon.md` §7ב

--- מדיניות הוכרעה 2026-08-08 (מרשם TASK_REGISTER §5/§8) ---
**ההכרעה: ריצה שמתחילה יותר משעה אחרי המועד המתוזמן שלה — מדלגת ואינה
מבצעת עבודה.** היא רושמת אירוע ומסתיימת בהצלחה, ולא מעבדת דאטה חיה תחת
חותמת-זמן ישנה.
הראיה שהובילה לכך היא בגוף התיק: ריצה 31120743074 נוצרה 16:42:02Z, עשתה
checkout ב-18:36:22Z, **משכה מחירים חיים ב-18:37 ועיבדה אותם כסט-הסיגנלים
של 16:42** — ודיווחה success.
מה שנשאר לביצוע: (1) מימוש הדילוג + רישום האירוע — ⚠️ `orchestrator.py`
נתיב מוגן, דורש אישור מפורש; (2) AC#3 — כימות הנזק שכבר נגרם ב-6/8
(כמה שורות נושאות חותמת ישנה משמעותית מהדאטה שבהן), קריאה-בלבד מחוץ
לשעות-מסחר. הסף (שעה) ננעל כאן ואינו פתוח לכיול-בדיעבד.
