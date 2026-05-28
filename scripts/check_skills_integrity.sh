#!/usr/bin/env bash
# RidingHigh Pro — Skills Integrity Guard
# Runs at session open. Catches the 26/5 bug (superpowers renamed to .bak, skills invisible).

FAIL=0
WARN=0
PLUGIN_JSON=~/.claude/plugins/installed_plugins.json

echo "🛡️  Skills Integrity Guard"
echo "==========================================="

# 1) plugin manifest
[[ -f "$PLUGIN_JSON" ]] || { echo "❌ FAIL: plugin manifest missing"; ((FAIL++)); }

# 2) required plugins
for plugin in superpowers modern-python git-cleanup ask-questions-if-underspecified; do
  if grep -q "\"$plugin@" "$PLUGIN_JSON" 2>/dev/null; then
    echo "✅ plugin: $plugin"
  else
    echo "❌ FAIL: plugin not installed: $plugin"
    ((FAIL++))
  fi
done

# 3) superpowers sub-skills (version-agnostic glob)
for skill in systematic-debugging brainstorming writing-plans verification-before-completion test-driven-development using-superpowers; do
  p=$(ls -d ~/.claude/plugins/cache/superpowers-marketplace/superpowers/*/skills/$skill/SKILL.md 2>/dev/null | head -1)
  if [[ -n "$p" && -f "$p" ]]; then
    echo "✅ superpowers/$skill ($(wc -l < "$p") lines)"
  else
    echo "❌ FAIL: superpowers/$skill not resolvable"
    ((FAIL++))
  fi
done

# 4) RH-dedicated skills
for skill in rhpro-live rhpro-session backtest-expert data-quality-checker position-sizer signal-postmortem trader-memory-core time-check; do
  if [[ -f ~/.claude/skills/$skill/SKILL.md ]]; then
    echo "✅ rh: $skill"
  else
    echo "❌ FAIL: rh skill missing: $skill"
    ((FAIL++))
  fi
done

# 5) anthropic-skills bundle
for skill in docx pdf pptx xlsx skill-creator frontend-design; do
  if [[ -f ~/.claude/skills/anthropic-skills/skills/$skill/SKILL.md ]]; then
    echo "✅ anthropic: $skill"
  else
    echo "⚠️  WARN: anthropic/$skill missing"
    ((WARN++))
  fi
done

# 6) zero superpowers duplicates in ~/.claude/skills/
DUPES=$(find ~/.claude/skills -maxdepth 1 -type d -name 'superpowers*' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$DUPES" -eq 0 ]]; then
  echo "✅ no superpowers duplicates in ~/.claude/skills/"
else
  echo "❌ FAIL: $DUPES superpowers copy/copies in skills/ (should be 0 — lives in plugins/cache/)"
  ((FAIL++))
fi

# 7) zero .bak directories (Claude Code skips them silently — this is the 26/5 bug)
BAKS=$(find ~/.claude/skills -maxdepth 1 -type d -name '*.bak*' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$BAKS" -eq 0 ]]; then
  echo "✅ no .bak directories in ~/.claude/skills/"
else
  echo "⚠️  WARN: $BAKS .bak director(ies) — Claude Code does not load them"
  ((WARN++))
fi

echo "==========================================="
if [[ $FAIL -gt 0 ]]; then
  echo "❌ SKILLS INTEGRITY: $FAIL FAIL / $WARN WARN"
  exit 1
elif [[ $WARN -gt 0 ]]; then
  echo "⚠️  SKILLS INTEGRITY: PASS with $WARN warning(s)"
  exit 0
else
  echo "✅ SKILLS INTEGRITY: PASS (all checks)"
  exit 0
fi
