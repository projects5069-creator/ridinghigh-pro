#!/bin/bash
#
# check_no_tool_mentions.sh — SSoT guard for RULE #15 (CLAUDE.md).
#
# Fails (exit 1) if a PR body carries a tool mention. The four patterns:
#     Generated with .*Claude Code
#     Co-Authored-By: Claude
#     claude.com/claude-code
#     claude.ai/code
#
# Why (2026-08-08): the written rule covered COMMIT MESSAGES only
# (.claude/skills/rh-task/SKILL.md), so all five commits that day were clean
# while PR #40, #41 and #42 each carried the attribution line. The gap was in
# the wording, not in the execution — and a wording gap is invisible until
# someone reads it. CI is the only place that reads it every time.
#
# ⚠️ WHAT THIS DOES NOT CATCH — read before trusting it:
#   1. Comments on PRs and on issues. `pull_request` does not fire for them;
#      catching those needs `issue_comment` / `issues` triggers, not added here.
#   2. A manual merge that bypasses CI, or a merge forced while the check is red.
#   3. Any NEW phrasing of the same idea that does not match the four patterns
#      above. This is a string check, not a meaning check.
#   4. Issue bodies. Same trigger limitation as (1).
#   5. Commit messages when the checkout has no history to compare against —
#      see the COMMITS section below, which says so out loud rather than
#      quietly reporting success.
#
# INPUT, in precedence order. Every path prints which one was used.
#   1. a file path argument      -> that file is the body      (local testing)
#   2. $PR_BODY                  -> that string is the body    (workflow env)
#   3. $GITHUB_EVENT_PATH        -> jq .pull_request.body      (the real CI path)
#   4. none of the above         -> VISIBLE SKIP, exit 0       (e.g. push events)
#
# ⚠️ Reading $GITHUB_EVENT_PATH is deliberate. Passing the body through
# `env: PR_BODY: ${{ github.event.pull_request.body }}` assumes the expression
# interpolates as expected, and that assumption cannot be tested off-runner.
# The event file is plain JSON on disk, so a synthetic payload reproduces the
# real path exactly — which is how the self-test below verifies it.
#
#   check_no_tool_mentions.sh                 # CI: env or event file
#   check_no_tool_mentions.sh <file>          # check one file
#   check_no_tool_mentions.sh --self-test     # two-way control, no arguments
#
# The self-test is built in rather than sitting in fixture files so the control
# stays runnable forever, by anyone, with no setup.

set -u

# The patterns are assembled from parts on purpose: written literally, this
# script would match itself, and a repo-wide grep for the offending string
# would point here instead of at a real violation.
C="Claude"
PATTERNS=(
  "Generated with .*${C} Code"
  "Co-Authored-By: ${C}"
  "claude\.com/claude-code"
  "claude\.ai/code"
)

scan () {   # scan <label> <text> ; returns 1 if any pattern hit
    local label="$1" text="$2" hit=0
    for p in "${PATTERNS[@]}"; do
        local n
        n=$(printf '%s' "$text" | grep -acE "$p" || true)
        if [ "${n:-0}" -gt 0 ]; then
            echo "    ❌ $label matches: $p   ($n line(s))"
            printf '%s' "$text" | grep -aE "$p" | head -3 | sed 's/^/       > /'
            hit=1
        fi
    done
    return $hit
}

if [ "${1:-}" = "--self-test" ]; then
    echo "══ check_no_tool_mentions.sh · self-test ══"
    d=$(mktemp -d)
    # dirty fixture: one file per pattern, so a failure names WHICH pattern broke
    printf 'a real body\n\n%s Generated with [%s Code](https://claude.com/claude-code)\n' '🤖' "$C" > "$d/dirty_generated.txt"
    printf 'a real body\n\nCo-Authored-By: %s <noreply@anthropic.com>\n' "$C" > "$d/dirty_coauthored.txt"
    printf 'see https://claude.com/claude-code for details\n' > "$d/dirty_dotcom.txt"
    printf 'see https://claude.ai/code for details\n'        > "$d/dirty_dotai.txt"
    printf 'A normal PR body.\n\nEvidence: reports/x.md\n'   > "$d/clean.txt"
    # synthetic GitHub event payloads — this is what proves the CI path works
    printf '{"pull_request":{"number":99,"body":"body with %s Generated with [%s Code](https://claude.com/claude-code)"}}\n' '🤖' "$C" > "$d/event_dirty.json"
    printf '{"pull_request":{"number":99,"body":"a clean body"}}\n' > "$d/event_clean.json"
    printf '{"pusher":{"name":"someone"}}\n' > "$d/event_push.json"

    fails=0
    t () {  # t <expect-exit> <label> <command...>
        local want="$1" label="$2"; shift 2
        "$@" >/dev/null 2>&1; local got=$?
        if [ "$got" -eq "$want" ]; then echo "  ✅ $label (exit $got)"
        else echo "  ❌ $label — expected exit $want, got $got"; fails=$((fails+1)); fi
    }
    S="$0"
    t 1 "dirty file · generated-with"        bash "$S" "$d/dirty_generated.txt"
    t 1 "dirty file · co-authored"           bash "$S" "$d/dirty_coauthored.txt"
    t 1 "dirty file · claude.com link"       bash "$S" "$d/dirty_dotcom.txt"
    t 1 "dirty file · claude.ai link"        bash "$S" "$d/dirty_dotai.txt"
    t 0 "clean file"                         bash "$S" "$d/clean.txt"
    t 1 "dirty PR_BODY env"                  env PR_BODY="x Co-Authored-By: $C y" bash "$S"
    t 0 "clean PR_BODY env"                  env PR_BODY="a clean body" bash "$S"
    t 1 "dirty event payload (the CI path)"  env -u PR_BODY GITHUB_EVENT_PATH="$d/event_dirty.json" bash "$S"
    t 0 "clean event payload (the CI path)"  env -u PR_BODY GITHUB_EVENT_PATH="$d/event_clean.json" bash "$S"
    t 0 "push event — no PR context, skips"  env -u PR_BODY GITHUB_EVENT_PATH="$d/event_push.json" bash "$S"
    t 0 "no input at all — skips"            env -u PR_BODY -u GITHUB_EVENT_PATH bash "$S"
    rm -rf "$d"
    echo
    [ "$fails" -eq 0 ] && { echo "SELF-TEST PASS — 11/11"; exit 0; }
    echo "SELF-TEST FAIL — $fails case(s)"; exit 1
fi

echo "══ tool-mention guard (RULE #15) ══"

BODY=""
SRC=""
# LABEL names what was actually checked, and is derived from the input source
# rather than hardcoded. An earlier version always said "PR body", which was
# wrong when the input was a file holding a commit message — a message that
# misdescribes what it examined is the same defect class this guard exists for.
LABEL=""
if [ "$#" -gt 0 ] && [ -n "${1:-}" ]; then
    [ -f "$1" ] || { echo "  ❌ no such file: $1"; exit 1; }
    BODY=$(cat "$1"); SRC="file: $1"; LABEL="input file"
elif [ -n "${PR_BODY:-}" ]; then
    BODY="$PR_BODY"; SRC="env PR_BODY"; LABEL="PR body (env)"
elif [ -n "${GITHUB_EVENT_PATH:-}" ] && [ -f "${GITHUB_EVENT_PATH}" ]; then
    if command -v jq >/dev/null 2>&1; then
        BODY=$(jq -r '.pull_request.body // empty' "$GITHUB_EVENT_PATH" 2>/dev/null || true)
        SRC="event payload: $GITHUB_EVENT_PATH (.pull_request.body)"
        LABEL="PR body (event payload)"
    else
        # fail closed: an unverifiable check must not report success
        echo "  ❌ jq not found — cannot read the event payload, and this guard"
        echo "     will not claim a pass it did not perform."
        exit 1
    fi
fi

if [ -z "$BODY" ]; then
    # ⚠️ Loud, never silent. A push event legitimately has no PR body; a silent
    # exit 0 here would read as "checked and clean" on every push forever.
    echo "  ⏭  SKIPPED — no PR body available${SRC:+ ($SRC was empty)}."
    echo "     Expected on a push event, which carries no pull_request context."
    echo "     Nothing was checked. This is not a pass."
    exit 0
fi

echo "  source: $SRC"
echo "  checked: $LABEL — $(printf '%s' "$BODY" | wc -l | tr -d ' ') line(s), $(printf '%s' "$BODY" | wc -c | tr -d ' ') bytes"

rc=0
scan "$LABEL" "$BODY" || rc=1

# ── COMMITS — best effort, and it says so when it cannot look ──────────────
# actions/checkout defaults to depth 1, so there is usually no base to diff
# against. Reporting "commits clean" from an empty range would be exactly the
# empty-check trap this repo has hit before.
RANGE=""
if [ -n "${GITHUB_BASE_REF:-}" ] && git rev-parse --verify -q "origin/${GITHUB_BASE_REF}" >/dev/null 2>&1; then
    RANGE="origin/${GITHUB_BASE_REF}..HEAD"
fi
if [ -n "$RANGE" ]; then
    n=$(git rev-list --count "$RANGE" 2>/dev/null || echo 0)
    echo "  commits in $RANGE: $n"
    if [ "${n:-0}" -gt 0 ]; then
        scan "commit message" "$(git log --format='%B' "$RANGE")" || rc=1
    fi
else
    echo "  ⏭  commit messages NOT checked — no base ref to compare against"
    echo "     (shallow checkout). What WAS checked: the $LABEL above."
fi

echo
if [ "$rc" -ne 0 ]; then
    echo "❌ tool-mention guard: a tool attribution reached a public artifact." >&2
    echo "   RULE #15 (CLAUDE.md): commit messages, PR bodies, PR comments and" >&2
    echo "   issue text carry no tool mention. Edit the PR body and re-run." >&2
    echo "     gh pr edit <N> --body-file <clean file>" >&2
    exit 1
fi
echo "✅ tool-mention guard: no tool attribution found."
exit 0
