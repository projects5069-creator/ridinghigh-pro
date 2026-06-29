# SESSION HANDOFF — 2026-06-29 (Monday) — MxV-shadow master-plan execution day

## State
- **HEAD:** `94714b5` (main, clean, `0 0` vs origin — all commits pushed)
- **OPEN tasks:** 42 (In Progress: TASK-128 shadow-gate; TASK-186 overnight-runner [disarmed per memory]; rest To Do)
- **PK:** v3.75 (bumped across the day; reflects 200/201/203/204/128-C1/128-C2-A) · **Mode:** DRY_RUN · **Sentinel:** shadow · **EXPLICIT_GATE_MODE / MXV_PRICE_GATE_MODE:** shadow
- **Market:** closed (late-night, ~01:00 Peru).

## Done today (MxV-shadow master plan)
- **TASK-201 → Done** — guard `calculate_float_pct` against garbage provider floatShares (forward-only). (`4a2a999`)
- **TASK-200 → Done** — collector candidate selection `Score>=60` → `MxV<=-100` (`select_candidates`); June backfill verified. Cross-month limitation → **TASK-202 opened**. (`5985763`)
- **TASK-203 → Done** — guard Float% at collector copy-path (`clamp_float_pct`, (0,100] else NULL) + retro-cleanup of 12 May+June rows. (`9a5d4fc`/`1884e0b`)
- **TASK-204 → Done** — `night_return` column = −D1_Gap% (SSoT-derived, no second calculator); MxV_at_entry skipped (redundant); backfill 357 values. (`1bee4fc`/`6d9c340`)
- **TASK-128 → code C1+C2-A committed (stays In Progress):**
  - C1 (`52dafbb`) — isolated MxV+price shadow observer: would-enter = `MxV<=-100 AND price>=$3` ONLY; `_check_filters`/`d.action` byte-identical (proven isolation from the live gate).
  - C2-A (`94714b5`) — `shadow_gate_events` per-run summary now counts MxV+price would-enter (header 6→8); FIELD_MAPPING/decision_log untouched. C2-B (per-decision flag) skipped — redundant vs post_analysis.

## Infra bug discovered (NOT from C2-A — pre-existing)
- `shadow_gate_events` was **never provisioned/registered** in sheets_config (for any month) → `flush_shadow_gate_summary` — **including the existing Score-divergence shadow** — has been silently no-op'ing since it was added (catches the exception → returns 0). **Zero damage** (silent no-op, no bad write). This blocks live-verification of TASK-128 AC#3.

## ⭐ Next chat
- **Provision `shadow_gate_events`** (create sheet + register in sheets_config, monthly rotation) → activates TASK-128 AC#3 AND fixes the silently-failing Score-divergence shadow → live-verify (flush test row, read back 8 values) → **close TASK-128 Done**. A separate gated op (creates a new Sheet file) — needs explicit go.
- After: **T-E** (TASK-206 fundamentals), **T-D** (TASK-205 25-day horizon), **T-F** (TASK-202 cross-month backfill, optional), **T-G** (TASK-194 Score-flip-to-active — time-blocked ~2026-07-27, never auto).

## Notes
- DRY_RUN · shadow · zero real trades. The flip to active is always TASK-194, time-blocked on multi-regime verification (~2026-07-27), never automatic.
- TDD throughout (RED→GREEN); test suite green (271 passed; sole failure = pre-existing `test_write_real_decision_to_sheet` integration, confirmed on a clean tree).
- Zero touch to `_check_filters` / `d.action` (live-gate isolation, life-critical constraint).
