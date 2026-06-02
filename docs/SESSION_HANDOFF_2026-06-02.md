# Session Handoff — 2026-06-02 (Tuesday)

## TL;DR
Closed the entire monthly-email / rotation thread. The monthly Critic email now
works end-to-end (May's 115-trade summary was sent + its monthly_summary row
written), and rotation now has double protection against the silent-provisioning
gap that broke June.

## TASKs closed (6)
- TASK-60 ✅ monthly Critic email read the wrong month's paper_portfolio (bug B).
  Fixed review_completed_trades(month=) routing; verified end-to-end (115 May trades).
- TASK-97 ✅ RH-Summaries host failed in CI (sheet ID only in gitignored dotfile).
  env-var fallback + Secret + workflow env. Verified locally: May row written.
- TASK-98 ✅ merged into TASK-91 (Bug A, same root).
- TASK-99 ✅ build_weekly_row missed cross-month exits. Reads all months the
  Mon-Fri window spans, deduped by position_id.
- TASK-100 ✅ documented/won't-fix-now: cross-month position edge does not occur
  (EOD-close prevents overnight holds; 0 occurrences in live data). Canonical
  rule recorded for future overnight-hold scenario.
- TASK-91 ✅ atomic rotation. scope-1 (create_agent_sheets verify-at-source,
  exit!=0 if <13 sheets), scope-2 (health_audit check_28 loud guard), scope-4
  (11->13 strings). scope-3 (_ensure_month self-heal) = won't-do (high risk,
  low value given the guard).

## Commits (5, all pushed clean)
816d135 (TASK-60) -> b9a5dcd (TASK-97) -> 5f1067a (TASK-91 scope-2) ->
d33b963 (TASK-99) -> bb5ecb9 (TASK-91 scope-1+4). PK v2.57 -> v2.62.

## Rotation now defended twice
- Loud at source: create_agent_sheets exits non-zero on incomplete provisioning,
  so prepare_next_month never commits a 9-sheet config.
- Caught within hours: health_audit check_28 (AS1) CRITICAL+email if the active
  month lacks any of the 13 agent sheets.

## Lessons (critical)
- .rh-run.sh RUNAWAY: scripts re-invoked many times at the harness level (not the
  wrapper, not config — the wrapper is clean, single eval). A read-only script is
  safe; a side-effecting one is NOT. Cost today: 25 duplicate May emails from a
  workflow_dispatch loop. RULE: side-effect scripts (dispatch/push/write) run as a
  SINGLE direct foreground call with a dedup guard; never background; never route
  side-effects through the wrapper.
- Script-based anchor auto-detection failed twice (alias _td, candidate mismatch).
  For complex/rotation code, prefer a direct Edit on a verified anchor over a
  guess-and-replace script.
- The awk open-count is inflated by cross-refs in task titles (e.g. "TASK-91" text
  inside TASK-98's body). Use a real manual count, not the awk one-liner.

## Open for next time
- TASK-61: date-gated, verify weekly_summary after the first post-rotation Friday
  weekly run (2026-06-06).
- TASK-48: In Progress; the monthly/weekly core shipped today, daily render +
  follow-ups (TASK-88/89/90) remain.
- CI verification on 1/7: scheduled monthly run should write both the email and
  the monthly_summary row in the cloud (logic already proven locally).
- Older Backlog: TASK-9/10/11/15/26/33/... and others remain untouched.

## State at close
DRY_RUN, Sentinel active (note: TASK-66 contra-factual still open — active mode
blocks winners; decide before LIVE). HEAD synced. PK v2.62.
