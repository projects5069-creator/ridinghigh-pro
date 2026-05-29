# Recovery — PreToolUse Skill Gate lockout

If Claude Code blocks every Bash/Edit/Write call with "🛑 PreToolUse blocked",
the hook may be misbehaving. Recover from a NATIVE terminal (Terminal.app / iTerm
— **NOT** Claude Code itself; its tools are blocked).

---

## Step 1 — Open a NATIVE terminal
Cmd+Space → "Terminal" (or iTerm). Confirm the prompt is your normal shell,
not Claude Code's session.

## Step 2 — FASTEST: kill-switch (reversible)
Paste this one-liner:
```bash
python3 -c "import json,os; p=os.path.expanduser(\"~/.claude/settings.json\"); d=json.load(open(p)); d[\"disableAllHooks\"]=True; json.dump(d,open(p,\"w\"),indent=2); print(\"✅ disableAllHooks=true — file watcher will pick up\")"
```
The Claude Code file watcher reloads automatically. Next tool call is freed.
To re-enable later: same one-liner with `d.pop("disableAllHooks",None)`.

## Step 3 — SURGICAL: remove only PreToolUse (preserves UserPromptSubmit + plugins)
```bash
python3 -c "import json,os; p=os.path.expanduser(\"~/.claude/settings.json\"); d=json.load(open(p)); d.get(\"hooks\",{}).pop(\"PreToolUse\",None); json.dump(d,open(p,\"w\"),indent=2); print(\"✅ PreToolUse removed\")"
```

## Step 4 — FULL rollback to backup
Stage C of the install creates `~/.claude/settings.json.bak_YYYYMMDD_HHMMSS`.
Restore the most recent backup:
```bash
cp ~/.claude/settings.json.bak_$(ls -t ~/.claude/settings.json.bak_* | head -1 | sed "s|.*\.bak_||") ~/.claude/settings.json
```

---

**Doc source:** code.claude.com/docs/en/hooks — *"To temporarily disable all
hooks without removing them, set `disableAllHooks: true` in your settings file."*
