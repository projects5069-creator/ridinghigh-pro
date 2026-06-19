#!/usr/bin/env bash
# RidingHigh Pro — overnight autonomous bug-fix runner (launchd entrypoint).
#
# Control flow lives HERE (bash), not in the model, so guardrails are deterministic.
# Billed to the Max subscription via a Keychain OAuth token (claude setup-token) —
# NEVER API. Guards: no-API-key, night-window, token+task+wall-clock ceilings.
# main() runs only when executed directly; sourcing exposes the guards for tests.

REPO="${RH_REPO:-/Users/adilevy/RidingHighPro}"
TASKS_DIR="$REPO/backlog/tasks"
RAW_BASE="$REPO/docs/overnight/raw"
RAW_DIR="$RAW_BASE"                      # reassigned per-night inside main()
NIGHT_SETTINGS="$REPO/.claude/settings.night.json"
MAX_TASKS="${MAX_TASKS:-3}"
MAX_TURNS="${MAX_TURNS:-40}"
TOKEN_CEILING="${TOKEN_CEILING:-600000}"
WALL_CLOCK_MIN="${WALL_CLOCK_MIN:-180}"
NIGHT_END_HOUR="${NIGHT_END_HOUR:-5}"   # abort if Lima hour >= 5 (deferred-run guard)
EXEC_MODEL="${EXEC_MODEL:-sonnet}"
CLASSIFY_MODEL="${CLASSIFY_MODEL:-sonnet}"
KEYCHAIN_SERVICE="${KEYCHAIN_SERVICE:-rh-overnight-oauth}"

now_lima() { TZ="America/Lima" date +%H:%M; }
today()    { TZ="America/Lima" date +%Y-%m-%d; }
night_raw_dir() { echo "$RAW_BASE/$1"; }   # per-night subdir → no stale rows in a fresh report

# --- Guards (unit-tested) -------------------------------------------------------
guard_no_api_key() {            # pass (0) only if no API key/token in env
  [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${ANTHROPIC_AUTH_TOKEN:-}" ]
}

guard_night_window() {          # pass (0) only if a VALID Lima clock reads hour in [0, NIGHT_END_HOUR)
  local hhmm="${1:-$(now_lima)}"
  case "$hhmm" in               # require H:MM or HH:MM; anything else => fail-closed (broken clock)
    [0-9]:[0-9][0-9] | [0-9][0-9]:[0-9][0-9]) ;;
    *) return 1 ;;
  esac
  local hour=$((10#${hhmm%%:*}))
  [ "$hour" -ge 0 ] && [ "$hour" -lt "$NIGHT_END_HOUR" ]
}

over_ceiling() {                # true (0) if spent >= ceiling
  [ "${1:-0}" -ge "${2:-0}" ]
}

read_oauth_token() {            # subscription token from macOS Keychain (never on disk)
  security find-generic-password -s "$KEYCHAIN_SERVICE" -w 2>/dev/null
}

# Secret-env families (denylist). The file-focused hooks cannot stop the model from
# reading a secret sitting in an ENV var, so scrub them before launching claude.
SECRET_ENV_RE='^(ALPACA_|FINNHUB_|GOOGLE_|GMAIL_|SMTP_|RH_SUMMARIES_|AWS_|TWILIO_|STRIPE_|SLACK_|AZURE_|GCP_|DB_|DATABASE_|[A-Z0-9_]*_SHEET_ID$|[A-Z0-9_]*_API_KEY$|[A-Z0-9_]*_SECRET|[A-Z0-9_]*_TOKEN|[A-Z0-9_]*_PASSWORD$|[A-Z0-9_]*PASS$|[A-Z0-9_]*_KEY$|[A-Z0-9_]*CREDENTIALS)'
SECRET_ENV_WHITELIST='^(CLAUDE_CODE_OAUTH_TOKEN|GITHUB_TOKEN|GH_TOKEN)$'   # needed for auth + gh

guard_clean_secret_env() {      # unset secret-family env vars; keep the whitelist; assert clean
  local name
  for name in $(env | cut -d= -f1 | grep -E "$SECRET_ENV_RE" 2>/dev/null || true); do
    printf '%s' "$name" | grep -Eq "$SECRET_ENV_WHITELIST" && continue
    unset "$name" 2>/dev/null || true
  done
  # clean iff no secret-family var remains other than the whitelist
  [ -z "$(env | cut -d= -f1 | grep -E "$SECRET_ENV_RE" | grep -Ev "$SECRET_ENV_WHITELIST" || true)" ]
}

# --check-auth: prove the Keychain read + clean env from the ACTUAL launchd context
# (launchd Keychain access differs from an interactive shell). No model call.
check_auth() {
  unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true
  guard_clean_secret_env || { echo "FAIL: secret env present after scrub"; return 1; }
  guard_no_api_key        || { echo "FAIL: an API key is set (would bill API)"; return 1; }
  local t; t="$(read_oauth_token)"
  [ -n "$t" ] || { echo "FAIL: no subscription OAuth token in Keychain ($KEYCHAIN_SERVICE)"; return 1; }
  echo "OK: subscription token present, no API key, secret env clean"; return 0
}

# --- Orchestration (runs only when executed, not sourced) -----------------------
main() {
  set -euo pipefail
  local stamp; stamp="$(today)"
  RAW_DIR="$(night_raw_dir "$stamp")"      # isolate this night's per-task JSON from prior nights
  mkdir -p "$RAW_DIR"
  local log="$RAW_DIR/run_${stamp}.log"
  exec > >(tee -a "$log") 2>&1
  echo "== RH overnight $stamp $(now_lima) Lima =="

  # 0. Auth + time + env guards (FAIL HARD — protect against #37686 silent API billing
  #    and against secrets leaking via env vars the file-hooks can't see).
  unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN || true
  guard_no_api_key       || { echo "ABORT: an API key is set in env — refusing (would bill API)"; exit 2; }
  guard_clean_secret_env || { echo "ABORT: secret env vars present after scrub"; exit 2; }
  guard_night_window     || { echo "ABORT: outside night window ($(now_lima) Lima) — deferred run suppressed"; exit 0; }

  local token; token="$(read_oauth_token)"
  [ -n "$token" ] || { echo "ABORT: no subscription OAuth token in Keychain ($KEYCHAIN_SERVICE)"; exit 2; }
  export CLAUDE_CODE_OAUTH_TOKEN="$token"   # precedence #5 → subscription billing

  # Smoke auth check (confirms the token authenticates; structural guarantee = no API key + OAuth token present).
  claude -p --output-format json "ok" >/dev/null 2>&1 \
    || { echo "ABORT: subscription auth smoke check failed"; exit 2; }

  # 1. Pre-flight: on main, clean tree, base tests green.
  cd "$REPO"
  [ "$(git branch --show-current)" = "main" ] || { echo "ABORT: not on main"; exit 2; }
  git fetch --quiet origin || true
  git tag -f "rh-night-base-$stamp" >/dev/null
  local base_sha; base_sha="$(git rev-parse --short HEAD)"
  echo "base $base_sha"
  if ! uv run --with pytest python3 -m pytest -m "not integration" -q >/dev/null 2>&1; then
    echo "ABORT: base test suite is RED — refusing to build on a broken base"; exit 0
  fi

  # Resolve ${REPO} in the night settings to ABSOLUTE paths so the secret/core hooks fire
  # correctly when claude runs from a WORKTREE (cwd != main). KEYSTONE: a fresh worktree has
  # no .claude/settings.local.json (gitignored), so its broad Bash allows never load.
  local resolved_settings="$RAW_DIR/settings.night.resolved.json"
  sed "s#\${REPO}#$REPO#g" "$NIGHT_SETTINGS" > "$resolved_settings"

  # 2. Triage: layer-1 (deterministic) → layer-2 (classifier in a clean scan worktree).
  local candidates; candidates="$(python3 "$REPO/scripts/overnight/triage_filter.py" "$TASKS_DIR")"
  local wt_scan="$REPO/../rh-night-scan-$stamp"
  git worktree add --detach --force "$wt_scan" main >/dev/null 2>&1 || true
  local queue=() n_needs=0
  while read -r tid; do
    [ -n "$tid" ] || continue
    [ "${#queue[@]}" -ge "$MAX_TASKS" ] && break
    local body; body="$(cat "$TASKS_DIR/task-${tid#TASK-} "*.md 2>/dev/null || true)"
    local verdict; verdict="$(printf '%s' "$body" | ( cd "$wt_scan" && claude -p --model "$CLASSIFY_MODEL" \
        --settings "$resolved_settings" --permission-mode dontAsk \
        --append-system-prompt "$(cat "$REPO/scripts/overnight/classify_task.md")" \
        --output-format json \
        --json-schema '{"type":"object","properties":{"auto_safe":{"type":"boolean"},"touches_core":{"type":"array","items":{"type":"string"}},"reads_data":{"type":"boolean"},"reason":{"type":"string"}},"required":["auto_safe","reason"]}' \
        2>/dev/null ) | jq -r '.structured_output // empty')"
    if [ "$(printf '%s' "$verdict" | jq -r '.auto_safe // false')" = "true" ]; then
      queue+=("$tid")
    else
      # serialize NEEDS-HUMAN so it reaches the morning report (not echo-only)
      jq -n --arg t "$tid" --arg r "$(printf '%s' "$verdict" | jq -r '.reason // "unclassified"')" \
            '{task:$t,status:"needs_human",reason:$r}' > "$RAW_DIR/${tid}.json"
      n_needs=$((n_needs + 1))
    fi
  done <<< "$candidates"
  git worktree remove --force "$wt_scan" 2>/dev/null || true
  echo "queue: ${queue[*]:-none} | needs_human: $n_needs"

  # 3. Execute loop — each task in its OWN fresh worktree (KEYSTONE isolation); circuit
  #    breaker between tasks (tokens incl. cache / count / wall-clock).
  local spent=0 ran=0 start_epoch; start_epoch="$(date +%s)"
  for tid in "${queue[@]:-}"; do
    [ -n "${tid:-}" ] || continue
    over_ceiling "$spent" "$TOKEN_CEILING" && { echo "ceiling hit ($spent) — stop"; break; }
    local elapsed_min=$(( ($(date +%s) - start_epoch) / 60 ))
    [ "$elapsed_min" -ge "$WALL_CLOCK_MIN" ] && { echo "wall-clock cap hit — stop"; break; }

    local wt="$REPO/../rh-night-${tid}"
    git worktree add --force "$wt" -b "rh-night/$tid" main >/dev/null 2>&1 \
      || git worktree add --force "$wt" "rh-night/$tid" >/dev/null 2>&1 || { echo "  worktree add failed for $tid"; continue; }

    local out="$RAW_DIR/${tid}.json"
    printf 'TASK to execute: %s\n\n%s\n' "$tid" "$(cat "$REPO/scripts/overnight/execute_task.md")" \
      | ( cd "$wt" && claude -p --model "$EXEC_MODEL" --settings "$resolved_settings" \
            --permission-mode dontAsk --max-turns "$MAX_TURNS" --output-format json 2>/dev/null ) \
          > "$RAW_DIR/${tid}.raw.json" || true
    # Extract the task's result JSON (model's final message) + FULL token usage (incl. cache).
    jq -r '.result // empty' "$RAW_DIR/${tid}.raw.json" 2>/dev/null \
      | sed -n '/{/,/}/p' > "$out" || true
    local used; used="$(jq -r '((.usage.input_tokens//0)+(.usage.output_tokens//0)+(.usage.cache_read_input_tokens//0)+(.usage.cache_creation_input_tokens//0))' "$RAW_DIR/${tid}.raw.json" 2>/dev/null || echo 0)"
    spent=$(( spent + ${used:-0} )); ran=$((ran + 1))
    echo "  $tid done; tokens+=$used (spent $spent)"
    # DONE → drop the worktree (branch + draft PR persist); else keep it for inspection.
    if [ "$(jq -r '.status // "unknown"' "$out" 2>/dev/null || echo unknown)" = "done" ]; then
      git worktree remove --force "$wt" 2>/dev/null || true
    else
      echo "  (worktree kept for inspection: $wt)"
    fi
  done

  # 4. Budget + report.
  jq -n --argjson run "$ran" --argjson maxt "$MAX_TASKS" \
        --argjson tok "$spent" --argjson ceil "$TOKEN_CEILING" \
        '{tasks_run:$run,max_tasks:$maxt,tokens:$tok,token_ceiling:$ceil,ceiling_hit:($tok>=$ceil),per_task:{}}' \
        > "$RAW_DIR/_budget.json"
  local report="$REPO/docs/overnight/REPORT_${stamp}.md"
  python3 "$REPO/scripts/overnight/build_report.py" "$RAW_DIR" "$stamp" "$base_sha" "$report"

  # 5. Publish report via a DEDICATED worktree — never stash/checkout main's working tree
  #    (so the user's uncommitted files are untouched). main is never pushed.
  local wt_rep="$REPO/../rh-night-report-$stamp"
  git fetch --quiet origin overnight-reports 2>/dev/null || true
  git worktree add --force "$wt_rep" -b overnight-reports >/dev/null 2>&1 \
    || git worktree add --force "$wt_rep" overnight-reports >/dev/null 2>&1 \
    || git worktree add --force --detach "$wt_rep" main >/dev/null 2>&1
  mkdir -p "$wt_rep/docs/overnight"
  cp "$report" "$wt_rep/docs/overnight/"
  ( cd "$wt_rep" && git add "docs/overnight/$(basename "$report")" \
      && git commit -q -m "report: overnight $stamp" \
      && git push -q origin HEAD:overnight-reports ) || echo "WARN: report publish failed"
  git worktree remove --force "$wt_rep" 2>/dev/null || true
  echo "== done: $report =="
}

# Run only when executed directly (sourcing exposes guards to tests).
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  case "${1:-}" in
    --check-auth) check_auth ;;          # §11 gate #3: invoke via launchd to verify Keychain context
    *)            main "$@" ;;
  esac
fi
