# Overnight Runner + Backlog Auto-Safe Status — 2026-06-19

Persisted record of the overnight-runner build and the verified full-backlog classification.

## 1. Runner / §11 status
**Built, hardened (3 adversarial reviews), live-validated.** On `origin/feature/overnight-runner`
(NOT merged, NOT auto-merge; `main` untouched). Handoff committed (RUNNER_HANDOFF_2026-06-19.md).
**Schedule OFF — never armed** (`launchctl`: 0 `com.rh.overnight` jobs).

Gates passed (this session):
- Gate 4 — `--check-auth` (shell): OK (subscription token, no API key, clean env).
- Gate 5 — live dry-run triage from the worktree: full pipeline; also caught 3 real issues
  (night-window daytime-abort, guard_base_ready clean-tree, bare-python3 PATH-shim → fixed).
- Secret/core-hook live-refuse: `_sheet_id` read → "denied by permission settings"; `Edit
  formulas.py` → block_core_unsafe hook "CORE_UNSAFE file is off-limits".

Open items:
- Execute-path gate on **TASK-126** (the sole auto-safe task; not yet run).
- Merge decision: merge `feature/overnight-runner` OR hold as dormant infra (עמיחי's call).
- Gate-6 launchd-context `--check-auth` (one-shot LaunchAgent, runbook in SCHEDULE_INSTALL.md): NOT yet run.

## 2. Full backlog classification — VERIFIED sweep (59 To-Do tasks)
All 59 classified; every auto_safe candidate re-verified against the real code (the 3 Explore
agents over-accepted 8 → corrected to 1: email/monthly all live in `agent/**`; TASK-101 is a
`/plugin install` op; TASK-132/167 touch live Sheets).

### AUTO_SAFE (1)
- **TASK-126** — Export GitHub-Actions SKIPs → CSV: standalone read-only `gh run` scraper → local
  CSV; touches no core/agent/Sheets/data. (Caveat: full test needs `gh run` API, which the night
  allowlist excludes — runner could still write the scraper + a mocked test + draft PR.)

### BORDERLINE (6) — a human could reasonably hand-approve; each touches a soft boundary
- **TASK-54** — PreToolUse Phase-2 skill-gate: non-core hook, but risky self-tooling (could block all CC actions).
- **TASK-88** — Monthly email graphs: viz-only in spirit, but code lives in `agent/notifications/templates/monthly_brief.py` (`agent/**`).
- **TASK-89** — Monthly email anomaly flags: reporting-only, but in the `agent/**` monthly email path.
- **TASK-132** — Flag 14 stuck PENDING rows: reversible `audit_flag`, but a live post_analysis Sheet write.
- **TASK-153** — Adopt DropsLab_PK as docs: docs-only, but explicitly "review with Amihay" + Anti-Drift contract.
- **TASK-167** — SCHEMA.json + drift check: SCHEMA.json authoring bounded, but the drift-check reads live sheets.

### NEEDS_HUMAN (52) — grouped by cluster
- **`agent/**`:** 9, 33, 39, 67, 73, 136, 159, 176
- **formulas / config / score / weights:** 10, 68, 69, 87, 151, 170, 174
- **health_audit / dashboard / utils.classify_trade_row:** 38, 46, 58
- **post_analysis / cross_month / data_provider / backfill / Alpaca:** 11, 49, 63, 65, 74, 109, 143, 149, 166, 168, 172, 173, 177, 180, 180.1, 182
- **DropsLab data semantics:** 82, 83, 90, 148
- **exploratory / research / decision-gate:** 62, 66, 71, 72, 75, 92, 127, 128, 141, 145, 154, 178, 179
- **plugin-install / not-a-repo-fix:** 101

### Totals
**total open = 59 · auto_safe = 1 · borderline = 6 · clear needs_human = 52.**

**Verdict:** exactly one genuinely auto-safe task (TASK-126) exists. The strict filter is correct,
not over-rejecting — RidingHigh's backlog is ~98% core trading logic / agent subsystem / data /
research. The runner has near-zero addressable surface here; its value is as a reusable template
for other repos, a standalone day-close triage tool (`--triage-only`), and a rare-trivial-task safety net.
