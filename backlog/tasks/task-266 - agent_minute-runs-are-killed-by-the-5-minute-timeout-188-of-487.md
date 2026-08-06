---
id: TASK-266
title: 'agent_minute runs are killed by the 5-minute timeout, 188 of 487'
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
labels: []
dependencies: []
priority: medium
ordinal: 264000
---


## Description

Found while measuring something else (queue recon, 2026-08-06). Not caused by
the outage — it predates it and is a normal-day condition.

Sampled 60 runs from the busiest hour of 2026-08-05 (19:00-20:00Z) and read
`started_at`/`completed_at` at the **job** level, which is the only API that
exposes the real execution moment:

```
n=60   job duration: median 315s · max 317s · min 36s
conclusions: cancelled=58, success=2
```

`agent_minute.yml:16` sets `timeout-minutes: 5` (=300s). 315s is 300s plus
runner overhead. These are not manual cancellations — they are the timeout
cutting the job off mid-work.

Full count across two days:

```
2026-08-05  agent_minute  cancelled 188  success 299   ->  38.6% cancelled
2026-08-05  auto_scan     cancelled  72  success 414   ->  14.8% cancelled
```

## Why it matters beyond the runs themselves

1. **Nearly two in five agent runs did not finish their work.** Whatever the
   orchestrator was doing at 300s — monitoring positions, writing decisions —
   stopped there.
2. **It silently poisons the baseline.** The "median 203s" figure that TASK-259
   is built on was measured on a day where 38.6% of runs were being cut at 300s.
   A truncated run cannot report a duration longer than the truncation.
3. **It feeds `check_06`.** `cancelled` lands in the denominator but not the
   numerator, and does not trigger the RECOVERING gate — see TASK-267.

## Acceptance Criteria

- [ ] #1 Determine what the run is doing when it hits 300s — is the timeout too
      tight, or is the run genuinely stuck?
- [ ] #2 Decide: raise `timeout-minutes`, or fix what makes the run slow.
      ⚠️ `.github/workflows/` is a protected path; the change needs explicit approval.
- [ ] #3 Re-measure the `agent_minute` duration baseline on a day with no
      timeout truncation, and correct TASK-259 with the honest number.

Evidence: `reports/2026-08-06_1406_queue_recon.md` §3ב
