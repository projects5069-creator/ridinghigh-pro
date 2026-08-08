---
id: TASK-268
title: 'detect_outage runs inside an agent run, so it dies with the system it guards'
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
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
