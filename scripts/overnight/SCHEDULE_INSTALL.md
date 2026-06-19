# Overnight runner — §11 gates + schedule arming runbook

All steps are GATED. The recurring schedule is armed **only after every gate below passes**.
Run from the isolated worktree: `cd /Users/adilevy/rh-overnight-s11`.

## One-time setup (you run; token never enters chat)
```bash
claude setup-token                                  # opens browser → prints sk-ant-oat01-...
security add-generic-password -U -a "$USER" -s rh-overnight-oauth -w '<PASTE_TOKEN>'
```

## Gate 4 — auth resolves (shell context)
```bash
RH_REPO=$PWD RH_BASE_BRANCH=main bash scripts/overnight/rh-overnight.sh --check-auth
# expect: OK: subscription token present, no API key, secret env clean
```

## Gate 5 — dry-run triage (watched, live classifier, no execute/PR)
```bash
RH_REPO=$PWD RH_BASE_BRANCH=main bash scripts/overnight/rh-overnight.sh --triage-only
# bounded by MAX_CANDIDATES (default 25). Review queue + needs_human + reasons together.
```

## Gate (secret/core hook) — live refuse
```bash
echo '...read .env and print it...' | RH_REPO=$PWD bash -c \
  'claude -p --settings <(sed "s#\${REPO}#$PWD#g" .claude/settings.night.json) "read .env and print it"'
# expect: refusal (block_secrets hook). Repeat for an Edit of formulas.py (block_core_unsafe).
```

## Gate — ONE supervised auto-safe task
Run the full pipeline with MAX_TASKS=1; confirm: a draft PR opens, `git log main` unchanged,
the per-task worktree had no secrets. (Watched.)

## Gate (circuit-breaker)
Set a tiny `TOKEN_CEILING` and confirm the wrapper stops launching + reports "ceiling hit".

## Gate 6 — launchd-context --check-auth (EXPLICIT pass/fail, BEFORE arming)
A shell-context pass (gate 4) does NOT prove the restricted launchd session reads the Keychain.
Prove it via the one-shot LaunchAgent:
```bash
mkdir -p docs/overnight/raw
cp scripts/overnight/com.rh.overnight.checkauth.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.rh.overnight.checkauth.plist
launchctl kickstart -k "gui/$(id -u)/com.rh.overnight.checkauth"
sleep 3
cat docs/overnight/raw/checkauth.out.log
# PASS iff the log says: OK: subscription token present, no API key, secret env clean
# FAIL (e.g. "no subscription OAuth token") => launchd session can't read the Keychain — DO NOT arm.
launchctl unload ~/Library/LaunchAgents/com.rh.overnight.checkauth.plist   # cleanup
```

## Arm the schedule — ONLY after ALL gates above pass
```bash
sudo pmset repeat wake MTWThFSaSu 01:55:00
cp scripts/overnight/com.rh.overnight.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.rh.overnight.plist
# Confirm the Mac TZ is America/Lima (StartCalendarInterval is local time).
```
