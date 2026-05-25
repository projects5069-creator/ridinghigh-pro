---
id: TASK-16
title: 'P3.4 — #N20 cron-drift catch-up logic'
status: Done
assignee: []
created_date: '2026-05-23 19:33'
updated_date: '2026-05-24 20:15'
labels: []
dependencies: []
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When GitHub Actions cron drifts and misses minutes, detect and log it. Phase 1 = observability (done). Phase 2 = catch-up = deferred after data-driven decision.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**Phase 1: DONE (commit 7dae5e5)**
- New function `detect_outage(now)` in agent/orchestrator.py
- Wired into run() as Safety check 3 (after emergency_stop, before Initialize)
- Logs to sentinel_events on gap > 10 min
- Email alert via send_alert() on gap > 30 min (CRITICAL)
- Graceful try/except — never halts the run
- Uses parse_hhmm (same pattern as read_latest_signals, no lex-compare bugs)

**Phase 2: DEFERRED**

Evidence from deep research on 16 trading days (2026-05-01 to 2026-05-22, 4575 gaps):
- 95.28% of gaps are on-time (0-2 min)
- 2.73% slight drift (2-3 min)
- Only 8 severe outages (>10 min) across 16 days = 0.5/day
- Only 1 critical outage (>30 min) — the 22/5 GH Actions incident
- 5 of 8 severe outages clustered on 22/5 alone
- 80% of total data loss (8.21%) is small drift (3-7 min) — Phase 2 threshold of 15 min wouldn't fix it
- Severe loss (>15 min) = only 1.65% of market time

Cost/benefit analysis:
- Phase 2 cost: 1.5-2h implementation + ongoing maintenance + risk (Alpaca bar fetching, score consistency vs FINVIZ snapshots, dedup logic)
- Phase 2 benefit: would have recovered ~103 minutes across 16 days, mostly from the single 22/5 incident
- Phase 1 alone: full observability with zero risk and zero maintenance

**Reopen criteria:**
If outage frequency increases (>2 critical outages per month, OR >5 severe per week), reopen Phase 2 as new task. Until then, Phase 1's observability is sufficient.

Reference: PK v2.33 changelog. Research code in /tmp/p34_deep_research.py.
<!-- SECTION:NOTES:END -->
