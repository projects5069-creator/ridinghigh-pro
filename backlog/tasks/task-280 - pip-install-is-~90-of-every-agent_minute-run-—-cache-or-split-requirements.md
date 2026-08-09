---
id: TASK-280
title: pip install is ~90% of every agent_minute run — cache or split requirements
status: To Do
assignee: []
created_date: '2026-08-08 23:07'
labels:
  - perf
  - ci
  - actions
dependencies: []
priority: medium
ordinal: 278000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-08 during the TASK-266 recon: on a healthy day the agent_minute job median is 48s, and roughly 45 of those seconds are a full pip install of requirements.txt from scratch, every minute. The actual trading work is 2-5s (log line: Sheets API reads this run (cache misses): total=4). The install pulls streamlit, plotly, altair and pyarrow into an agent run that renders no UI. Caching pip or splitting requirements into agent vs dashboard should take a run from ~50s to ~10s. This is the real source of slowness — not the 5-minute timeout, which TASK-266 decided on 2026-08-08 to leave alone. It also shrinks run overlap directly, which is the mechanism behind TASK-259.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
⚠️ **TIMING CONSTRAINT — DO NOT TOUCH BEFORE 2026-09-04.**
`.github/workflows/` is a protected path, and this changes the run regime in the
middle of the measurement window (10/8 → 4/9). A run that suddenly takes 10s
instead of 50s is a new variable in the experiment. This is a post-4/9 candidate.
The `window_guard.sh` hook does NOT cover workflow files — the discipline here is
human.

## THE MEASUREMENT (2026-08-08, from real logs)

A healthy run, 8/7 median (~48s):
```
~45s   checkout + pip install -r requirements.txt, from scratch, every minute
       "Successfully installed … alpaca-py … altair … pandas … plotly …
        pyarrow-24.0.0 … streamlit-1.61.1 … yfinance …"   (80+ packages)
~2-5s  the actual work:
       "Account state: 1 open positions, 0 ENTER today"
       "No signals to process this minute"
       "Position monitor: {'updated': 1, …}"
       "Sheets API reads this run (cache misses): total=4"
```

So ~90% of every agent run is dependency installation, and a large share of it is
the dashboard stack (`streamlit`, `plotly`, `altair`, `pyarrow`) which the agent
never imports.

## WHY IT MATTERS BEYOND SPEED

Shorter runs shrink overlap directly. Overlap is the mechanism behind TASK-259
(stale `build_account_state` snapshot across concurrent runs, two re-entry
breaches on 2026-08-05). Measured overlap: 92.5% on 8/5 (median 292s) versus
10.2% on 8/7 (median 48s). Taking the median to ~10s would make overlap
structurally impossible on a 60s cron — which is a cleaner fix than deploying
`concurrency`, the option still open in TASK-259.

## TWO APPROACHES — not decided

1. **Cache pip.** `actions/setup-python` with `cache: pip`, or `actions/cache`
   keyed on `hashFiles('requirements.txt')`. Smallest diff, keeps one
   requirements file. Cache restore is not free — measure it, do not assume.
2. **Split requirements.** `requirements-agent.txt` (no streamlit/plotly/altair)
   for agent_minute + auto_scan; the full file stays for the dashboard.
   Bigger diff, touches more workflows, but removes the work instead of caching
   it. ⚠️ Risk: a missed transitive import fails the agent at runtime, in
   production, on a 60s cron.

⚠️ Not established: how much of the 45s is download versus install/compile, and
therefore how much a warm cache actually saves. Measure before choosing.

## Acceptance Criteria

- [ ] #1 Measure the current install cost in isolation: from a run log, the wall
      time from the start of the pip step to its end, on 5 runs of one trading
      day. Record median.
- [ ] #2 After the change, on a full trading day, `agent_minute` job median
      duration is **≤ 20s** (from the TASK-266 gate script, section 2), with
      **0 failures** attributable to a missing dependency across the whole day
      (`gh run list --workflow=agent_minute.yml --created <DAY> --json conclusion`
      shows no `failure`).
- [ ] #3 The agent still does its work: on that same day, at least one run logs
      `Run complete: signals=…` with `errors=0`, and `Sheets API reads this run`
      is present — proving the run reached the end, not that it merely started fast.

Gate command (same harness as TASK-266's gate, reused deliberately):
```bash
bash gate266.sh <DAY>     # section 2 gives median/p90; section 1 gives conclusions
```

Evidence: `~/rhpro_audit_run/TASK266_RECON.md`, `~/rhpro_audit_run/TASK266_DECISION.md`
<!-- SECTION:NOTES:END -->
