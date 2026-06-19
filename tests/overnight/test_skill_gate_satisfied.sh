#!/usr/bin/env bash
# Keystone verification — the user-level skill-gate hook (~/.claude/hooks/pretooluse_skill_gate.sh)
# loads via ~/.claude/settings.json and CANNOT be unregistered by the night --settings. It blocks
# Edit/Write/Bash until a Read(*SKILL.md) or Skill(*) tool_use exists in the transcript.
#
# execute_task.md makes the model invoke the systematic-debugging Skill as its FIRST action, which
# writes a satisfying transcript line. This test proves, against the ACTUAL gate hook with REAL
# transcript serialization, that: (a) such a line makes a headless Edit ALLOWED; (b) without it the
# Edit is BLOCKED (the stall we are preventing). If the hook isn't installed, the test is a no-op.
GATE="$HOME/.claude/hooks/pretooluse_skill_gate.sh"
[ -r "$GATE" ] || { echo "SKIP: skill-gate hook not installed — nothing to verify"; exit 0; }

fail=0
tmp="$(mktemp -d)"; sat="$tmp/sat.jsonl"; unsat="$tmp/unsat.jsonl"
# Real serialization (verified from a live transcript): name:Skill + "skill":"..."
printf '%s\n' '{"type":"tool_use","name":"Skill","input":{"skill":"superpowers:systematic-debugging"}}' > "$sat"
printf '%s\n' '{"type":"tool_use","name":"Bash","input":{"command":"ls"}}'                              > "$unsat"

printf '{"transcript_path":"%s","tool_name":"Edit","tool_input":{"file_path":"x.py"}}' "$sat" | bash "$GATE" >/dev/null 2>&1
[ "$?" -eq 0 ] && echo "  ✓ skill loaded → headless Edit ALLOWED (no stall)" || { echo "  ✗ should allow when a skill is loaded"; fail=1; }

printf '{"transcript_path":"%s","tool_name":"Edit","tool_input":{"file_path":"x.py"}}' "$unsat" | bash "$GATE" >/dev/null 2>&1
[ "$?" -eq 2 ] && echo "  ✓ no skill → Edit BLOCKED (the stall execute_task.md prevents)" || { echo "  ✗ expected a block when no skill is loaded"; fail=1; }

rm -rf "$tmp"
[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit "$fail"
