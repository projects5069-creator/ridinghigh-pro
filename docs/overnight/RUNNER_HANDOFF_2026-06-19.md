# Overnight Runner — Handoff (2026-06-19)

Branch: `feature/overnight-runner` (14 build commits; NOT merged, NOT auto-merge).
Status: **built, hardened, live-validated; schedule DELIBERATELY OFF.**

## (a) The 0/22 finding — and what it means
Wide live triage (`--triage-only`, MAX_CANDIDATES=25) classified **22 distinct To-Do backlog
tasks → auto_safe = 0/22.** Every one is CORE_UNSAFE (agent/**, formulas.py, config.py,
health_audit.py, dashboard.py, post_analysis_collector.py, utils.classify_trade_row), reads
Google Sheets / Alpaca data, or is exploratory/unbounded research. The strict filter is
**correct** (each verdict cites a real gate). **Meaning:** RidingHigh's current backlog is almost
entirely core trading logic + research, so the runner has **near-zero addressable surface here**.
Arming it tonight would burn ~25 classifier calls for 0 PRs. → schedule stays OFF until non-core
(auto-safe) work accumulates.

## (b) The runner's real value (despite 0/22 here)
1. **Reusable TEMPLATE** — drop `scripts/overnight/` + `.claude/hooks|settings.night.json` into any
   repo that *does* have auto-safe work (bug fixes outside its core).
2. **`--triage-only` as a standalone day-close tool** — classifies the backlog (auto-safe vs
   needs-human, with reasons) without executing anything. Useful as-is for RidingHigh triage.
3. **Safety net** — if a rare trivial non-core task appears (a test, a doc, an isolated helper),
   the runner can clear it overnight into a reviewed draft PR.

## (c) Branch disposition
`feature/overnight-runner` carries the **complete** runner (code + tests + hooks + plists +
install runbook). Ready to **merge** OR **hold as dormant infrastructure** — עמיחי's call.
**Do NOT auto-merge.**

## §11 gate results (this session)
- Gate 4 (auth, shell) ✅ — `--check-auth` → OK (token + no-API + clean env).
- Gate 5 (live dry-run triage) ✅ — full pipeline from the worktree; also caught 3 real issues
  (night-window daytime-abort, guard_base_ready clean-tree, bare-python3 PATH-shim bug → fixed).
- Secret/core-hook live-refuse ✅ — `_sheet_id` read denied ("denied by your permission settings");
  `Edit formulas.py` denied by the block_core_unsafe hook ("CORE_UNSAFE file is off-limits…").
- **Deferred:** ONE supervised auto-safe task (no real candidate exists — 0/22); circuit-breaker
  live; gate-6 launchd-context `--check-auth` (one-shot LaunchAgent, runbook in SCHEDULE_INSTALL.md).
- **Schedule arm:** NOT done. Never armed. Stays last, stays OFF.

## Reviews / quality
3 adversarial reviews (all findings closed); 25 pytest + 6 bash tests green; every commit
explicit-path + `git show --stat` verified. PK: no Anti-Drift trigger (no trading-system change);
live PK lives on `main` — bump there (or on merge), not on this stale branch copy.
