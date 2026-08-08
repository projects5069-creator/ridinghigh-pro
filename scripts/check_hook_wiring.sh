#!/bin/bash
#
# check_hook_wiring.sh — SSoT guard: every Claude Code hook must actually be reachable.
#
# Fails (exit 1) if any hook `command` in a tracked .claude/settings*.json resolves
# to a path that is missing, not executable, or outside the repo.
#
# Why (2026-08-08): the measurement-window guard was committed with its command
# written as an ABSOLUTE path into one developer's home directory. A clone on any
# other machine got the guard script plus a settings.json pointing at a path that
# does not exist there. That is worse than no guard, because the guard is
# DELIBERATELY fail-open (TASK-53 lesson: a hook once locked all Claude Code work),
# so a broken path does not raise — it silently stops guarding.
#
# Measured that day: with the hook pointed at a nonexistent script, a real Edit on
# the frozen agent/execution/order_manager.py went through, and no error surfaced
# in the tool result. Fail-open + broken wiring = total silence. CI is the only
# place that can be loud about it, because a hook cannot report its own absence.
#
# ⚠️ WHAT THIS DOES NOT CATCH — read before trusting it:
#   1. A hook that breaks only ON THE TARGET MACHINE. This runs on the CI runner
#      against the repo tree. An interpreter missing locally, a machine-specific
#      env var, a $PATH difference, an OS difference, or a file made non-executable
#      after checkout are all invisible here.
#   2. A hook whose script exists and runs but does the WRONG thing. This checks
#      reachability, not behaviour.
#   3. Anything in .claude/settings.local.json — untracked by design, so CI never
#      sees it.
#   4. Hooks whose command is a bare PATH executable (e.g. "node"). Those are
#      reported as SKIPPED, never silently passed.
#
# Modes:
#   check_hook_wiring.sh <file> [<file> ...]   # check exactly the given settings files
#   check_hook_wiring.sh                       # no args -> .claude/settings.json only,
#                                              #   the file Claude Code auto-loads for
#                                              #   the project. Other tracked settings
#                                              #   files are LISTED as out of scope.
#
# Every hook inspected prints one line. There is no silent skip.

set -eu

ROOT=$(git rev-parse --show-toplevel)

# jq, not python3: the local modern-python shim intercepts bare `python3` and
# refuses it ("Use `uv run python3` instead"), which made an early version of this
# guard fail on EVERY input — including good input — for a reason that had nothing
# to do with hook wiring. jq is already a hard dependency of window_guard.sh and is
# preinstalled on ubuntu-latest.
# This guard fails CLOSED: no jq means we cannot verify, and an unverifiable guard
# must not report success (window_guard.sh fails OPEN on purpose; this is the
# opposite role).
if ! command -v jq >/dev/null 2>&1; then
    printf '\n❌ hook-wiring guard: jq not found — cannot verify hook wiring.\n' >&2
    printf 'This guard fails closed on purpose: an unverifiable check must not pass.\n\n' >&2
    exit 1
fi

# Scope: by default ONLY .claude/settings.json — the file Claude Code auto-loads
# for the project. Other tracked settings files are TEMPLATES for other launchers
# and would produce false failures here. Verified 2026-08-08:
# .claude/settings.night.json writes "${REPO}/..." and is never loaded as-is;
# scripts/overnight/rh-overnight.sh:161 resolves it before use
#   sed "s#\${REPO}#$REPO#g" "$NIGHT_SETTINGS" > "$resolved_settings"
# so flagging it would be wrong. They are LISTED as out of scope below, never
# silently dropped — pass a path explicitly to check it.
if [ "$#" -gt 0 ]; then
    FILES="$*"
    OTHERS=""
else
    FILES=$(git ls-files '.claude/settings.json' || true)
    OTHERS=$(git ls-files '.claude/settings*.json' | grep -v '^\.claude/settings\.json$' || true)
fi

if [ -z "$FILES" ]; then
    printf '\n❌ hook-wiring guard: .claude/settings.json is not tracked.\n' >&2
    printf 'The window guard is wired through that file; if it is not tracked, a clone\n' >&2
    printf 'gets the guard script and no wiring at all — a guard that looks installed\n' >&2
    printf 'and never runs.\n\n' >&2
    exit 1
fi

printf 'hook-wiring guard — repo root: %s\n' "$ROOT"

violations=""
for f in $FILES; do
    printf '\n  %s\n' "$f"
    if [ ! -f "$f" ]; then
        violations="${violations}  ${f}: file not found\n"
        printf '    ❌ file not found\n'
        continue
    fi

    # One line per hook: HOOK <event> <matcher> <form> <raw-command>
    if ! lines=$(jq -r '
        (.hooks // {}) | to_entries[] as $e
        | ($e.value // [])[] as $g
        | ($g.hooks // [])[]
        | select(.type == "command")
        | ["HOOK", $e.key, ($g.matcher // "*"),
           (if has("args") then "exec" else "shell" end),
           (.command // "")]
        | @tsv
    ' "$f" 2>&1); then
        violations="${violations}  ${f}: not valid JSON / unreadable: ${lines}\n"
        printf '    ❌ not valid JSON or unreadable: %s\n' "$lines"
        continue
    fi

    if [ -z "$lines" ]; then
        printf '    (no command hooks declared)\n'
        continue
    fi

    while IFS=$'\t' read -r kind a b c d; do
        [ "$kind" = "HOOK" ] || continue
        event="$a"; matcher="$b"; form="$c"; raw="$d"

        label="$event/$matcher [$form]"

        # Shell form may carry arguments; the executable is the first token.
        exe="$raw"
        [ "$form" = "shell" ] && exe=${exe%% *}
        exe=${exe%\"}; exe=${exe#\"}

        # A hardcoded absolute path is a violation BY CONSTRUCTION, never mind
        # whether it happens to exist on the machine running this check. On the
        # author's Mac /Users/<name>/RidingHighPro/... sits inside the repo root
        # and an earlier version of this guard passed it — the exact defect it was
        # written to catch. Portability is a property of how the path is WRITTEN.
        case "$exe" in
            *'${CLAUDE_PROJECT_DIR}'*|*'$CLAUDE_PROJECT_DIR'*) : ;;
            /*)
                violations="${violations}  ${f}: ${label}\n      command  : ${raw}\n      reason   : hardcoded ABSOLUTE path — a clone on another machine gets a dead hook.\n                 Use \${CLAUDE_PROJECT_DIR}/... instead.\n"
                printf '    ❌ %s -> %s  HARDCODED ABSOLUTE PATH\n' "$label" "$exe"
                continue
                ;;
        esac

        # Substitute the documented project-root placeholder.
        # Source: https://code.claude.com/docs/en/hooks — "${CLAUDE_PROJECT_DIR}: the project root".
        resolved=${exe//\$\{CLAUDE_PROJECT_DIR\}/$ROOT}
        resolved=${resolved//\$CLAUDE_PROJECT_DIR/$ROOT}

        case "$resolved" in
            */*) : ;;
            *)
                printf '    ⏭  %s -> %s  SKIPPED (bare PATH executable, not verifiable here)\n' "$label" "$resolved"
                continue
                ;;
        esac

        # A repo-relative path is fine; anchor it to the repo root.
        case "$resolved" in
            /*) : ;;
            *) resolved="$ROOT/$resolved" ;;
        esac

        # "${CLAUDE_PROJECT_DIR}/../x.sh" starts with the repo root as a STRING while
        # pointing outside it. Reject traversal before the prefix test.
        case "$resolved" in
            */../*|*/..)
                violations="${violations}  ${f}: ${label}\n      command  : ${raw}\n      resolved : ${resolved}\n      reason   : path traversal (..) escapes the repo\n"
                printf '    ❌ %s -> %s  PATH TRAVERSAL\n' "$label" "$resolved"
                continue
                ;;
        esac

        case "$resolved" in
            "$ROOT"/*) : ;;
            *)
                violations="${violations}  ${f}: ${label}\n      command  : ${raw}\n      resolved : ${resolved}\n      reason   : resolves OUTSIDE the repo — a clone elsewhere gets a dead hook\n"
                printf '    ❌ %s -> %s  OUTSIDE THE REPO\n' "$label" "$resolved"
                continue
                ;;
        esac

        if [ ! -f "$resolved" ]; then
            violations="${violations}  ${f}: ${label}\n      command  : ${raw}\n      resolved : ${resolved}\n      reason   : file does not exist in the repo\n"
            printf '    ❌ %s -> %s  MISSING\n' "$label" "$resolved"
            continue
        fi

        if [ ! -x "$resolved" ]; then
            violations="${violations}  ${f}: ${label}\n      command  : ${raw}\n      resolved : ${resolved}\n      reason   : exists but is not executable (chmod +x)\n"
            printf '    ❌ %s -> %s  NOT EXECUTABLE\n' "$label" "$resolved"
            continue
        fi

        printf '    ✅ %s -> %s\n' "$label" "${resolved#$ROOT/}"
    done <<EOF
$lines
EOF
done

if [ -n "$OTHERS" ]; then
    printf '\n  out of scope (templates resolved by their own launcher, not auto-loaded):\n'
    for o in $OTHERS; do printf '    ⏭  %s\n' "$o"; done
fi

if [ -n "$violations" ]; then
    printf '\n❌ hook-wiring guard: a declared hook is not reachable from a fresh clone:\n\n' >&2
    printf '%b' "$violations" >&2
    printf '\nThe window guard is fail-open by design (TASK-53), so a broken path does not\n' >&2
    printf 'raise — it silently stops guarding. Write the command as\n' >&2
    printf '  "${CLAUDE_PROJECT_DIR}/.claude/hooks/<script>.sh"  with  "args": []\n' >&2
    printf 'and keep the script tracked and executable.\n' >&2
    printf 'Docs: https://code.claude.com/docs/en/hooks\n\n' >&2
    exit 1
fi

printf '\n✅ hook-wiring guard: every declared hook resolves inside the repo and is executable.\n'
exit 0
