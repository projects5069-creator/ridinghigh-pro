# SESSION HANDOFF — 2026-06-29 (Monday) — entry-gate revolution: Score OFF + minimal MxV-gate (LIVE, DRY_RUN)

> ⚠️ This supersedes the earlier 2026-06-29 morning handoff (HEAD 94714b5). The morning plan
> ("flip is always TASK-194, time-blocked ~2026-07-27, never auto") was **overridden in the
> afternoon by an explicit owner decision**: the live entry logic was flipped TODAY.

## State
- **HEAD:** `3ae1363` (main, clean, `0 0` vs origin — all pushed)
- **OPEN tasks:** 45 (In Progress: TASK-128 shadow-gate; TASK-186 overnight-runner [disarmed])
- **PK:** v3.79 (bumped 3.76→3.79 across the day) · **Mode:** DRY_RUN (no real money)
- **LIVE entry flags (changed today, all reversible):**
  - `EXPLICIT_GATE_MODE = "active"` ← was "shadow": **Score gate (Filter 1) OFF**
  - `ENTRY_GATE_MINIMAL = True`: **6 filters OFF** (RunUp/Volume/Blacklist/Toxic/MarketCap/ROCKET)
  - `AGENT_MAX_REENTRIES_PER_TICKER = 1` ← was 3
  - `AGENT_DRY_RUN = True` · `SENTINEL_MODE = "shadow"` · `MXV_PRICE_GATE_MODE = "shadow"`
- **Live entry gate NOW = `MxV<=-100` ∧ `price>=$3` ∧ data-quality ∧ exposure-safety** (existing/cold-start/reentry/buying-power). Everything else off.
- **Market:** closed (~16:00 Peru / evening).

## ⭐⭐ READ FIRST next session — LIVE-VERIFY THE FLIP (the only thing that matters tomorrow)
At market open (DST-aware now: ~08:30 Peru summer), the FIRST `agent_minute` run is the
first-ever run of the new gate. **Read `decision_log` and confirm:**
1. ENTERs now appear that were previously `SCORE_TOO_LOW` (low Score, MxV<=-100, price>=$3).
2. Entry volume is sane — NOT a flood of illiquid/extreme-cap names (Volume + MarketCap are OFF, so watch REL_VOL / liquidity of the new entries).
3. `shadow_gate_events` finally gets its first row (tab was provisioned today; was 0 rows).
- **If the new population looks bad → staged revert (one config value each):**
  - `ENTRY_GATE_MINIMAL = False` (restores the 6 filters), and/or
  - `EXPLICIT_GATE_MODE = "shadow"` (restores the Score gate).

## Done today
- **TASK-207 → Done** (`a5b87a2`/`78245e7`/`aebcb4a`/`384ed7d`) — agent-sheet provisioning gap: self-heal step in `agent_eod` runs `create_agent_sheets --month current` (idempotent) + commit/push sheets_config; **verified live** (workflow_dispatch created `shadow_gate_events`, 8 cols). + dry-run config-skip fidelity.
- **TASK-208-B → Done** (`5a127ad`) — `borrow_collector.get_scanned_universe` selects by `MxV<=-100` not frozen Score (daily_snapshots.Score was blank in scoreless era → empty universe → live TASK-172 coverage gap). 208-A (auto_scanner ranking, cosmetic) stays open under TASK-208.
- **TASK-194 → stage-1 + stage-2 flip EXECUTED** (`1f451c2` wire, `7f6b965` flip): `evaluate_signal` honors `EXPLICIT_GATE_MODE`; flipped shadow→active. **Owner decision, AHEAD of the ≥2-week shadow precondition** (0 shadow rows at flip time) — safe because DRY_RUN + reversible. AC 5/6 (#4 = post-flip monitoring, open by design). S2=208 / S3=209 spun out.
- **TASK-210 → Done** (`6b5586d`) — minimal entry gate: `ENTRY_GATE_MINIMAL` wraps 6 filters; reentry 3→1; 7 default-dependent tests pinned `minimal=False`.
- **TASK-212 → Done** (`16045d3`) — dashboard Timeline Archive: combined `$price / mxv` cells (Score off), green styler MxV<=-100, width 120px. **Verified visually (screenshots).**
- **DST fix** (`a0d63fe`) — `is_market_hours` was Peru-hardcoded (summer-only) → now derives the window from ET (`America/New_York`), correct in both seasons; crons `auto_scan` 13-19→13-21, `agent_minute` 13-20→13-21. TDD 5/5.
- **TASK-206 → foundation only (stays To Do)** (`936948e`/`0a372f0`) — provider `get_fundamentals` exposes 8 fields + `raw` .info catch-all; collector-write / FINVIZ-Custom still open.

## Open / next
- **TASK-128** (In Progress) — AC#3 (shadow_gate_events row written) verifiable tomorrow after first run; but post-flip the Score-divergence (WouldAllow) zeroes by design (live==explicit).
- **TASK-194 AC#4** — ongoing post-flip monitoring (not "done"; it's a watch item).
- **New today:** TASK-208 (S2 scanner-ranking), TASK-209 (S3 retire calculate_score), TASK-211 (is_day_complete DST latent ~Nov), TASK-212 (dashboard, Done).
- **TASK-206 next:** collector-write of the 8 fields + raw_fundamentals_json + FINVIZ-Custom.

## Notes
- DRY_RUN throughout — zero real money. Every entry-logic change is reversible via a single config value.
- TDD on every code change (RED→GREEN). Full suite: **2 pre-existing failures only** (`test_write_real_decision_to_sheet` integration-Sheets, verified on clean tree; `test_filename_length_guard` stale premise — no files ≥200B).
- The thesis shift: re-validation deflated the protective filters (Toxic/ROCKET added May-2026, not in the 2yr method; ROCKET blocked 12 wins vs 7 losses) and Score is non-predictive (AUC 0.531). The edge lives in MxV + price. The minimal gate maximizes the MxV-driven entry population for forward measurement.
- Latent (not fixed): `is_day_complete` same DST bug (TASK-211); auto_scan ~14:05 stop earlier today never root-caused (likely Actions throttle — needs `gh run list`).
