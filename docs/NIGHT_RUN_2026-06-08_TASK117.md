# Night Run — 2026-06-08 (TASK-117, supervised /goal)

Task: **TASK-117** — post-commit hook עמיד: tracked source + installer wiring.
Branch: `night/TASK-117` off clean `main` (`7ac62a6`, == origin). Iron rules
applied: recon-first, explicit-path `git add`, no merge to main, verify-before-done.

Skills loaded (step 0): `writing-plans`
(`~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/writing-plans/SKILL.md`).

---

## TASK-117 — post-commit hook עמיד (tracked source + installer)
**Status: ✅ PR READY (no merge — עמיחי approves diff in the morning)**

### Recon
- TASK-116 fixed `.git/hooks/post-commit` locally (`python3` → `uv run python3`)
  but the hook lives under `.git/hooks/` which is **not version-controlled**, so
  the fix does not survive a clone. There was no tracked source and no installer
  for post-commit.
- The live hook header still read *"Installed by setup_project_state.sh"* — a
  **dead reference**: that installer is a ghost (never tracked, not on disk).
- Precedent already exists for the tracked-source + installer pattern: TASK-85
  created `scripts/git_hooks/pre-commit` + `scripts/git_hooks/install.sh`
  (mirrors the hook convention, does **NOT** set `core.hooksPath`).

### What changed (1 new file, 1 modified)
- **`scripts/git_hooks/post-commit`** (new, tracked, mode 100755) — copy of the
  live TASK-116-fixed hook (`uv run python3 generate_project_state.py`), with the
  header's dead `setup_project_state.sh` reference replaced by
  *"Installed by scripts/git_hooks/install.sh"* + a TASK-117 provenance note.
- **`scripts/git_hooks/install.sh`** (modified) — the single pre-commit `cp` block
  generalized to a `for hook in pre-commit post-commit` loop that installs **both**
  hooks into `.git/hooks/`. Header comment updated (no longer implies post-commit
  is "the existing local hook"; now both are tracked + installed here). The
  Claude-hooks deploy block is unchanged. `core.hooksPath` deliberately left unset.

### Why this satisfies the task
- The TASK-116 fix is now **clone-survivable**: `git clone` → run
  `scripts/git_hooks/install.sh` → post-commit (uv-based) is installed.
- The dead `setup_project_state.sh` reference is gone from the tracked hook.

### Verification (all green)
- `bash -n scripts/git_hooks/post-commit` → OK.
- `bash -n scripts/git_hooks/install.sh` → OK.
- Ran `scripts/git_hooks/install.sh` → printed `Installed pre-commit hook` **and**
  `Installed post-commit hook`.
- `diff scripts/git_hooks/post-commit .git/hooks/post-commit` → IDENTICAL.
- `git ls-files -s scripts/git_hooks/post-commit` → `100755` (exec bit tracked).

### ⚠️ Activation note (in PR)
`.git/hooks/` is not version-controlled — after merge, run
`scripts/git_hooks/install.sh` to (re)install both hooks. Already run locally for
verification, so the live post-commit now matches the tracked source.

---

## Run Log
- mode: supervised /goal (session-scoped Stop hook) · /goal: *until scripts/git_hooks/post-commit is tracked, install.sh wires it, the dead setup_project_state.sh ref is removed, NIGHT_RUN written with a ## Run Log, branch night/TASK-117 pushed, and a PR opened without merge*
- steps:
  1. Loaded `writing-plans` skill (RULE #11 gate satisfied).
  2. Recon: surveyed `scripts/git_hooks/`, found pre-commit + install.sh tracked, no post-commit; located dead `setup_project_state.sh` refs; read live `.git/hooks/post-commit` (TASK-116 fix) + NIGHT_RUN template/precedent.
  3. `git checkout -b night/TASK-117` off clean `main` (7ac62a6 == origin).
  4. Wrote `scripts/git_hooks/post-commit` (tracked, header dead-ref removed).
  5. Edited `scripts/git_hooks/install.sh` → pre-commit+post-commit install loop.
  6. Verified: `bash -n` both, ran installer, `diff` IDENTICAL, exec bit 100755.
  7. Wrote this NIGHT_RUN doc with `## Run Log`.
  8. `git add` explicit paths + commit (SKIP_PROJECT_STATE=1) → push branch → open PR (no merge).
- stop-counters: consecutive_blocks=0 · total_blocks=0 · stopped_reason=goal-met
- result: goal met — branch `night/TASK-117` pushed, PR opened (no merge). עמיחי reviews diff and merges manually.
