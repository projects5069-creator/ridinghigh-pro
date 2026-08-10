#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# skill_gate_selftest.sh — permanent RED/GREEN control for the PreToolUse
# skill gate (~/.claude/hooks/pretooluse_skill_gate.sh).
#
# WHY THIS EXISTS
# On 2026-08-10 the gate was measured to be lit, reporting green, and checking
# nothing: a Bash command that merely PRINTED a SKILL.md path satisfied it, and
# any command prefixed `echo hi;` skipped both phases entirely. The gate was
# fixed the same day. A fix with no regression test decays back — this file is
# the test. It runs entirely on synthetic input and touches no live state.
#
# USAGE   bash scripts/skill_gate_selftest.sh [-q]
#         exit 0 only when every case matches; 1 otherwise.
#         -q prints just the one-line verdict (used by session_startup_check).
# ─────────────────────────────────────────────────────────────────────────────
GATE="${SKILL_GATE_PATH:-$HOME/.claude/hooks/pretooluse_skill_gate.sh}"
SETTINGS="${SKILL_GATE_SETTINGS:-$HOME/.claude/settings.json}"
QUIET=0; [ "${1:-}" = "-q" ] && QUIET=1

[ -r "$GATE" ] || { echo "שער-סקילים: SKIP — ההוק אינו מותקן ($GATE)"; exit 0; }
command -v jq >/dev/null 2>&1 || { echo "שער-סקילים: SKIP — jq חסר"; exit 0; }

D=$(mktemp -d /tmp/skillgate_selftest.XXXXXX)
ST="$D/state"                       # never /tmp/cc-task-type — no live state touched
# The gate logs every block. Synthetic blocks must not enter the operational
# count that session_startup_check reports, or the counter counts this test.
export SKILL_GATE_LOGDIR="$D/log"
trap 'rm -rf "$D"' EXIT

SK="$HOME/.claude/skills"
PL="$HOME/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills"
DECL="systematic-debugging,verification-before-completion,rhpro-session,rhpro-live"
GATED_CMD="git diff --stat"         # deliberately NOT on the allowlist

# ── synthetic transcripts ────────────────────────────────────────────────────
cat > "$D/pos_skill.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"a1","name":"Skill","input":{"skill":"superpowers:systematic-debugging"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"a2","name":"Skill","input":{"skill":"superpowers:verification-before-completion"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"a3","name":"Skill","input":{"skill":"rhpro-session"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"a4","name":"Skill","input":{"skill":"rhpro-live"}}]}}
EOF
cat > "$D/pos_read.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"b1","name":"Read","input":{"file_path":"$PL/systematic-debugging/SKILL.md"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"b2","name":"Read","input":{"file_path":"$PL/verification-before-completion/SKILL.md"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"b3","name":"Read","input":{"file_path":"$SK/rhpro-session/SKILL.md"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"b4","name":"Read","input":{"file_path":"$SK/rhpro-live/SKILL.md"}}]}}
EOF
# a Bash call that only PRINTS the paths; line 1 satisfies Phase-1 with an
# UNDECLARED skill, which is the real-world shape of the 2026-08-10 hole.
cat > "$D/neg_print.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"c0","name":"Skill","input":{"skill":"time-check"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"c1","name":"Bash","input":{"command":"wc -l $PL/systematic-debugging/SKILL.md $PL/verification-before-completion/SKILL.md $SK/rhpro-session/SKILL.md $SK/rhpro-live/SKILL.md"}}]}}
EOF
# free text naming the paths, on the same line as an unrelated Read
cat > "$D/neg_mixed.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"d0","name":"Skill","input":{"skill":"time-check"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"I consulted skills/systematic-debugging/SKILL.md, skills/verification-before-completion/SKILL.md, skills/rhpro-session/SKILL.md and skills/rhpro-live/SKILL.md"},{"type":"tool_use","id":"d1","name":"Read","input":{"file_path":"/tmp/unrelated.txt"}}]}}
EOF
cat > "$D/neg_text.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"e0","name":"Skill","input":{"skill":"time-check"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"loaded skills/systematic-debugging/SKILL.md skills/rhpro-live/SKILL.md"}]}}
EOF
cat > "$D/neg_partial.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"f1","name":"Skill","input":{"skill":"superpowers:systematic-debugging"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"f2","name":"Skill","input":{"skill":"superpowers:verification-before-completion"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"f3","name":"Skill","input":{"skill":"rhpro-session"}}]}}
EOF
: > "$D/empty.jsonl"
cat > "$D/p1_fake.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"g1","name":"Read","input":{"file_path":"/tmp/SKILL.md"}}]}}
EOF
cat > "$D/p1_real.jsonl" <<EOF
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"h1","name":"Read","input":{"file_path":"$SK/time-check/SKILL.md"}}]}}
EOF
# FLAT serialisation — the headless/overnight shape. Regression guard: the
# 2026-08-10 fix originally handled only the nested form and broke
# tests/overnight/test_skill_gate_satisfied.sh (measured exit=1).
cat > "$D/flat.jsonl" <<'EOF'
{"type":"tool_use","name":"Skill","input":{"skill":"superpowers:systematic-debugging"}}
EOF
# TURN boundary — the skill is loaded in a PREVIOUS promptId group.
cat > "$D/turn_prev.jsonl" <<'EOF'
{"promptId":"AAAAAAAA-0000-0000-0000-000000000001","type":"user","message":{"role":"user","content":"previous prompt"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Skill","input":{"skill":"rhpro-live"}}]}}
{"promptId":"BBBBBBBB-0000-0000-0000-000000000002","type":"user","message":{"role":"user","content":"current prompt"}}
{"promptId":"BBBBBBBB-0000-0000-0000-000000000002","type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"x"}]}}
EOF
# same, but the load happens INSIDE the current group
cat > "$D/turn_curr.jsonl" <<'EOF'
{"promptId":"AAAAAAAA-0000-0000-0000-000000000001","type":"user","message":{"role":"user","content":"previous prompt"}}
{"promptId":"BBBBBBBB-0000-0000-0000-000000000002","type":"user","message":{"role":"user","content":"current prompt"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Skill","input":{"skill":"rhpro-live"}}]}}
EOF

# ── runner ───────────────────────────────────────────────────────────────────
PASS=0; FAIL=0; FAILED_CASES=""
run() {  # name transcript command state expected [tool]
  name="$1"; tr="$2"; cmd="$3"; st="$4"; exp="$5"; tool="${6:-Bash}"
  printf "%s\n" "$st" > "$ST"
  if [ -n "$cmd" ]; then
    input=$(jq -n --arg t "$tr" --arg c "$cmd" --arg n "$tool" \
            '{transcript_path:$t, tool_name:$n, tool_input:{command:$c}}')
  else
    input=$(jq -n --arg t "$tr" --arg n "$tool" \
            '{transcript_path:$t, tool_name:$n, tool_input:{file_path:"x.py"}}')
  fi
  printf '%s' "$input" | SKILL_GATE_STATE="$ST" bash "$GATE" >/dev/null 2>&1
  rc=$?
  if [ "$rc" = "$exp" ]; then
    PASS=$((PASS+1)); [ "$QUIET" -eq 0 ] && printf "  ✅ %-20s exit=%s\n" "$name" "$rc"
  else
    FAIL=$((FAIL+1)); FAILED_CASES="$FAILED_CASES $name"
    [ "$QUIET" -eq 0 ] && printf "  ❌ %-20s exit=%s  צפוי=%s\n" "$name" "$rc" "$exp"
  fi
}
assert() {  # name  condition-already-evaluated($?)  -> pass/fail
  if [ "$2" -eq 0 ]; then
    PASS=$((PASS+1)); [ "$QUIET" -eq 0 ] && printf "  ✅ %-20s\n" "$1"
  else
    FAIL=$((FAIL+1)); FAILED_CASES="$FAILED_CASES $1"
    [ "$QUIET" -eq 0 ] && printf "  ❌ %-20s\n" "$1"
  fi
}

DS="declared:$DECL:0"
NS="none:none:0"
[ "$QUIET" -eq 0 ] && echo "── Phase-2 · סקילים מוצהרים ──"
run "POS-skill-calls"  "$D/pos_skill.jsonl"   "$GATED_CMD" "$DS" 0
run "POS-read-skillmd" "$D/pos_read.jsonl"    "$GATED_CMD" "$DS" 0
run "NEG-print-paths"  "$D/neg_print.jsonl"   "$GATED_CMD" "$DS" 2
run "NEG-mixed-line"   "$D/neg_mixed.jsonl"   "$GATED_CMD" "$DS" 2
run "NEG-free-text"    "$D/neg_text.jsonl"    "$GATED_CMD" "$DS" 2
run "NEG-partial-3of4" "$D/neg_partial.jsonl" "$GATED_CMD" "$DS" 2
[ "$QUIET" -eq 0 ] && echo "── Phase-1 · סקיל כלשהו ──"
run "P1-fake-skillmd"  "$D/p1_fake.jsonl"     "$GATED_CMD" "$NS" 2
run "P1-real-skillmd"  "$D/p1_real.jsonl"     "$GATED_CMD" "$NS" 0
run "P1-empty"         "$D/empty.jsonl"       "$GATED_CMD" "$NS" 2
run "FLAT-serialise"   "$D/flat.jsonl"        "$GATED_CMD" "$NS" 0
[ "$QUIET" -eq 0 ] && echo "── allowlist ──"
run "ALLOW-simple-pwd" "$D/empty.jsonl"       "pwd"               "$DS" 0
run "ALLOW-compound"   "$D/empty.jsonl"       "echo hi; whoami"   "$DS" 2
run "ALLOW-pipe"       "$D/empty.jsonl"       "ls | wc -l"        "$DS" 2
run "ALLOW-redirect"   "$D/empty.jsonl"       "echo x > /tmp/zz9" "$DS" 2
[ "$QUIET" -eq 0 ] && echo "── גבול-התור ──"
run "TURN-previous"    "$D/turn_prev.jsonl"   "$GATED_CMD" "declared:rhpro-live:0" 2
run "TURN-current"     "$D/turn_curr.jsonl"   "$GATED_CMD" "declared:rhpro-live:0" 0
[ "$QUIET" -eq 0 ] && echo "── כלי ללא .command (Edit/MultiEdit) ──"
run "NOCMD-payload"    "$D/empty.jsonl"       ""           "$DS" 2 "MultiEdit"
[ "$QUIET" -eq 0 ] && echo "── חיווט ──"
jq -e '.hooks.PreToolUse[] | select(.hooks[0].command | test("pretooluse_skill_gate"))
       | .matcher | test("MultiEdit")' "$SETTINGS" >/dev/null 2>&1
assert "MATCHER-MultiEdit" $?
# 19 — the repo mirror of the hooks must match what is installed. Measured
# 2026-08-10: 181 differing lines after TASK-111 closed as Done. A one-off
# consolidation describes a moment; only a check describes a state.
SELF_DIR=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
bash "$SELF_DIR/check_hooks_mirror.sh" >/dev/null 2>&1
assert "HOOKS-MIRROR" $?

TOTAL=$((PASS+FAIL))
echo "שער-סקילים: $PASS/$TOTAL"
[ "$FAIL" -ne 0 ] && echo "נכשלו:$FAILED_CASES"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
