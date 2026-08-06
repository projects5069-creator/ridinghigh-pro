---
id: TASK-218
title: 'agent_minute 429: sentinel worksheet-handle cache (remaining 45/91)'
status: Done
assignee: []
created_date: '2026-07-02 04:42'
updated_date: '2026-08-06 18:45'
labels: []
dependencies: []
ordinal: 224000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After TASK-176 removed news_detective (46/91), agent.sentinel still calls get_worksheet('sentinel_events') per BLOCK/WARN event (~45/91 429 on the dedicated _AM SA). Cache the worksheet handle once/run. Connects to TASK-213 (429 measurement) + TASK-217 (paper_portfolio). MARKET-SAFE code.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
CLOSED 2026-08-06 — commit 1df9cba.

WHAT THE TICKET ASKED FOR, verbatim: "Cache the worksheet handle once/run." That is
exactly what was done. No event batching, no flush, and nothing outside
agent/sentinel/data_sentinel.py.

WHY THAT IS THE RIGHT SCOPE — the failure measured on 2026-08-05 was:

    APIError: [429]: Quota exceeded for quota metric 'Read requests' and limit
    'Read requests per minute per user'

READ requests. The call that failed is sm.get_worksheet("sentinel_events"), not
sm.safe_append_row — and safe_append_row already carries its own retry
(sheets_manager.py:389) while the lookup carried none. 55 of 60 events were lost in one
sampled run; sentinel_events took 13,092 events over three days. So the lookup was both
the measured failure and the unprotected one.

THE IMPLEMENTATION:
  data_sentinel.py  _sentinel_ws_cache        module-level handle
                    _get_sentinel_ws(sm)      fetch-once, caches only a real handle
                    reset_sentinel_ws_cache() explicit reset

A FAILED OR EMPTY LOOKUP IS NEVER CACHED. This is the part that matters. Today every
event re-looks-up and therefore self-heals after a transient 429. Caching a dead handle
would have converted one quota blip at the start of a run into a total loss for the rest
of it — strictly worse than the behaviour it replaces. Both paths are covered:
get_worksheet raising, and get_worksheet returning None.

CACHE LIFETIME. Module-level means one per PROCESS, and a runner starts a fresh process
per run (python -m agent.orchestrator), so process lifetime IS run lifetime and nothing
leaks between runs. Same shape as _sentinel_instance in this same file (:294-302) and as
sheets_manager._read_counts / reset_read_counts (:428, :441).

RESET IS EXPLICIT, NOT AUTOMATIC — stated plainly. There is no per-run lifecycle hook in
this module to hang it on, and the only caller that could invoke one is orchestrator.py,
which is a protected path (RUN_MODE_DECISION.md:40-43) and was deliberately not touched.
Production does not need the reset; the suite does. Verified by grep that no long-lived
process imports this module today — only orchestrator.py and the checks/ files, all
per-run.

VERIFICATION: five unit tests, mock only, three consecutive identical runs (5 passed,
0.09s). Full suite 731 -> 736 passed, zero failures, zero new failures.

⚠️ NOT MEASURED IN PRODUCTION. The expected saving is ~60 READ calls per run down to 1.
That is arithmetic from the code, not an observation. The real number needs a trading day
with this deployed, alongside the SMA20 batch that landed in fcdb0aa.
<!-- SECTION:NOTES:END -->
