#!/bin/bash
#
# check_hooks_mirror.sh — SSoT guard: the repo copy of each Claude Code hook
# must be byte-identical to the installed copy under ~/.claude/hooks.
#
# Fails (exit 1) when any mirrored file differs, is missing from the repo, or is
# not executable.
#
# Why (2026-08-10): the repo has mirrored these hooks since May under
# scripts/claude_hooks/. Measured that morning: the mirror of
# pretooluse_skill_gate.sh was 50 lines dated 2026-05-28 while the installed
# hook was 258 lines dated 2026-08-10 — 181 differing lines, roughly two and a
# half months of drift. TASK-111 ("Consolidate hook mirrors") is marked Done,
# which is exactly the point: a one-off consolidation describes a moment, not a
# state. Nothing re-checked it, so it drifted again the same week and nobody
# could see it. A mirror that silently lags is worse than no mirror, because it
# reads as a backup and restores a hook generations out of date.
#
# ⚠️ SCOPE, stated so it is not mistaken for coverage: only the two files in
# FILES below are compared. skill_gate_allowlist.txt is NOT mirrored and NOT
# checked — it changes the gate's behaviour and is a known blind spot, left open
# deliberately (owner decision pending), not overlooked.
#
# ⚠️ THIS IS A LOCAL CHECK, NOT A CI CHECK. It compares the repo against the
# developer's installed hooks. A GitHub Actions runner has no ~/.claude/hooks,
# so there is nothing there to compare and the check would be meaningless — it
# skips cleanly instead of pretending to pass. It is wired into
# scripts/skill_gate_selftest.sh (case 19), which session_startup_check.sh
# reports on line 7, so every session open sees it.
#
# Overrides exist for the failure-mode test only:
#   HOOKS_MIRROR_DIR   HOOKS_LIVE_DIR
set -u

REPO_ROOT=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)
MIRROR_DIR="${HOOKS_MIRROR_DIR:-$REPO_ROOT/scripts/claude_hooks}"
LIVE_DIR="${HOOKS_LIVE_DIR:-$HOME/.claude/hooks}"
FILES="pretooluse_skill_gate.sh skill_enforcement_hook.sh"

if [ ! -d "$LIVE_DIR" ]; then
  echo "⏭️  hooks-mirror guard: SKIP — no installed hooks dir at $LIVE_DIR (CI or fresh clone)."
  exit 0
fi

violations=""
checked=0
for f in $FILES; do
  live="$LIVE_DIR/$f"
  mirror="$MIRROR_DIR/$f"
  [ -r "$live" ] || { violations="$violations\n  • $f — installed copy missing at $live"; continue; }
  checked=$((checked + 1))
  if [ ! -r "$mirror" ]; then
    violations="$violations\n  • $f — NOT mirrored in the repo ($mirror)"
    continue
  fi
  if ! cmp -s "$live" "$mirror"; then
    n=$(diff "$mirror" "$live" 2>/dev/null | grep -c '^[<>]')
    violations="$violations\n  • $f — DRIFTED: $n differing lines (mirror $(wc -l < "$mirror" | tr -d ' ')L vs installed $(wc -l < "$live" | tr -d ' ')L)"
    continue
  fi
  [ -x "$mirror" ] || violations="$violations\n  • $f — mirrored but not executable"
done

if [ -n "$violations" ]; then
  printf '\n❌ hooks-mirror guard: the repo copy no longer matches the installed hook:\n' >&2
  printf '%b\n' "$violations" >&2
  printf '\nThe mirror is what a fresh clone or a rebuilt machine restores. A stale\n' >&2
  printf 'mirror reads as a backup and restores an obsolete gate.\n' >&2
  printf 'Resync:  cp -p ~/.claude/hooks/<file> scripts/claude_hooks/<file>\n' >&2
  printf 'then review the diff and commit it with the hook change, not after.\n\n' >&2
  exit 1
fi

echo "✅ hooks-mirror guard: $checked/$checked mirrored hooks are byte-identical to the installed copies."
exit 0
