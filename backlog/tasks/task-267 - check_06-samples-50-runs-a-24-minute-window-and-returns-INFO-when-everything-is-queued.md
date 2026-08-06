---
id: TASK-267
title: >-
  check_06 samples 50 runs, a 24-minute window, and returns INFO when everything
  is queued
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
labels: []
dependencies: []
priority: medium
ordinal: 265000
---


## Description

Two separate defects in `check_06` (`health_audit.py:587-659`), both found on
2026-08-06 while GitHub Actions was in a major outage. During that outage
`check_06` reported **INFO**.

### Defect 1 — the 24-hour window is really 24 minutes

```python
:639  url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=50"
:646  cutoff = utcnow() - timedelta(hours=24)
```

The 24-hour filter at `:646` is misleading. The API already returned only the
**50 newest** runs at `:639`. At two runs per minute that is about 25 minutes of
history. `check_06` has never looked at 24 hours.

Consequence, measured on 1,000 real runs from 2026-08-05:

```
whole day:  completed=1000  success=740  cancelled=260  ->  74.0%
rolling 50-run window across the day:
   PASSED 181 · WARNING 280 · would-be CRITICAL 490     (52% of windows)
   worst 38% at 18:42Z · best 100% at 13:27Z
```

Yet at the times `health_audit` actually runs (11:00 / 20:30 / 03:00 UTC) the
verdict was **PASSED 100% (50/50)** — because the 24-minute window at 20:30Z
spans 20:05-20:29Z, entirely after the close, where every run exits in 30-40s
and succeeds. **The check systematically samples the quietest moment of the day.**

### Defect 2 — blind when nothing completes

```python
:598  completed = [r for r in recent_runs if r["status"] == "completed"]
:602  if not completed: return CheckResult(..., INFO, f"{n} runs, none completed yet")
```

`queued` runs are filtered out at `:598` and contribute to neither bucket. When
every recent run is queued — exactly what a total outage looks like — `completed`
is empty and the check returns **INFO**. Simulated against the live API during
the outage:

```
fetched: 50   recent(24h): 50   status: {queued: 50}   completed: 0
>>> VERDICT: INFO — "50 runs, none completed yet"
```

374 runs stuck, zero executing, no output for 40 minutes, and the health check
says INFO. **"Nothing has completed" is the strongest possible outage signal and
it is currently the quietest severity.**

### Related — how `cancelled` is counted

`cancelled` enters the denominator (`:598`) but neither `successes` (`:599`) nor
`failures` (`:600`). `_failing_workflows_recovered` (`:570-584`) builds its set
from `conclusion == "failure"` only, so with zero failures it returns `False` at
`:578` and no downgrade applies. **A cancelled run is punished like a failure but
does not qualify for the relief a failure gets.** With TASK-266 producing 188
cancellations a day this is not hypothetical.

## Acceptance Criteria

- [ ] #1 Widen the sample so the window is genuinely time-based, not count-based.
- [ ] #2 `queued`-only must not be INFO. Deep queue plus zero completions is the
      signal, not the absence of one.
- [ ] #3 Decide explicitly how `cancelled` is counted, and record the reason.
- [ ] #4 Re-run the rolling-window simulation on real data after the change and
      confirm the verdict at 20:30Z is no longer 100% by construction.

Evidence: `reports/2026-08-06_1406_queue_recon.md` §4
