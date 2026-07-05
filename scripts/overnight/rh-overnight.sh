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
MAX_CANDIDATES="${MAX_CANDIDATES:-25}"   # hard cap on classifier calls/night (bounds token spend; samples the distribution)
MAX_TURNS="${MAX_TURNS:-40}"
MAX_ROUNDS="${MAX_ROUNDS:-5}"           # Auto Dancer §6: retry the P→C→E→C→V round up to this many times before PARK
TOKEN_CEILING="${TOKEN_CEILING:-600000}"
WALL_CLOCK_MIN="${WALL_CLOCK_MIN:-180}"
NIGHT_END_HOUR="${NIGHT_END_HOUR:-5}"   # abort if Lima hour >= 5 (deferred-run guard)
EXEC_MODEL="${EXEC_MODEL:-sonnet}"
CLASSIFY_MODEL="${CLASSIFY_MODEL:-sonnet}"
PLAN_MODEL="${PLAN_MODEL:-opus}"        # RPI role models (Auto Dancer M2): plan/critic/verify default to opus
CRITIC_MODEL="${CRITIC_MODEL:-opus}"
VERIFY_MODEL="${VERIFY_MODEL:-opus}"
KEYCHAIN_SERVICE="${KEYCHAIN_SERVICE:-rh-overnight-oauth}"
BASE_BRANCH="${RH_BASE_BRANCH:-main}"   # branch tasks/reports base off; override for isolated §11 runs
PYBIN="${RH_PYBIN:-/usr/bin/python3}"   # stdlib-only runner scripts; bypasses the modern-python PATH shim

# launchd hands us a minimal PATH (/usr/bin:/bin:/usr/sbin:/sbin). The external tools this
# runner needs live OUTSIDE it: claude → ~/.npm-global/bin, gh → ~/bin, node → /usr/local/bin
# (git is already in the base PATH). Without this the smoke check + `gh pr create` die with
# exit 127 "command not found" — exactly the 2026-06-20 abort. Prepend BEFORE any tool call;
# runs at top level so it also applies to `claude` subprocesses (which shell out to gh).
RH_TOOL_DIRS="${RH_TOOL_DIRS:-$HOME/.npm-global/bin:$HOME/bin:/opt/homebrew/bin:/usr/local/bin}"
export PATH="$RH_TOOL_DIRS:$PATH"

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

guard_base_ready() {            # replaces "cwd==main": pass only if tree is clean AND BASE_BRANCH is a real ref
  git diff --quiet && git diff --cached --quiet || { echo "ABORT: working tree not clean"; return 1; }
  git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1 || { echo "ABORT: base branch '$BASE_BRANCH' not found"; return 1; }
}

is_triage_only() { [ "${TRIAGE_ONLY:-0}" = "1" ]; }   # --triage-only: stop after triage; no execute/PR/publish
cap_reached()    { [ "${1:-0}" -ge "$MAX_CANDIDATES" ]; }   # true once we've classified MAX_CANDIDATES tasks

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

# Classify ONE task body → verdict JSON. FAIL-CLOSED: any classify failure (non-zero claude,
# empty/invalid output) → auto_safe=false, so the task is NEVER auto-executed; the caller
# routes it to needs_human. Guarded (|| v="") so one failure can't abort the run under set -e
# (the 2026-06-20 exit-1: candidate 52/59 killed the whole sweep). claude's stderr is preserved
# to a per-task .classify.err instead of /dev/null'd.
classify_verdict() {
  local body="$1" wt="$2" settings="$3" errlog="$4"
  local v=""
  v="$(printf '%s' "$body" | ( cd "$wt" && claude -p --model "$CLASSIFY_MODEL" \
        --settings "$settings" --permission-mode dontAsk \
        --append-system-prompt "$(cat "$REPO/scripts/overnight/classify_task.md")" \
        --output-format json \
        --json-schema '{"type":"object","properties":{"auto_safe":{"type":"boolean"},"touches_core":{"type":"array","items":{"type":"string"}},"reads_data":{"type":"boolean"},"reason":{"type":"string"}},"required":["auto_safe","reason"]}' \
        2>>"$errlog" ) | jq -r '.structured_output // empty')" || v=""
  if ! printf '%s' "$v" | jq -e 'type=="object"' >/dev/null 2>&1; then
    v="$(jq -n --arg e "${errlog##*/}" '{auto_safe:false,reason:("classify failed — see "+$e)}')"
  fi
  printf '%s\n' "$v"
}

# Run ONE role prompt (plan/critic/execute/verify) in a worktree; extract its result JSON
# to out_json; echo the tokens it spent (incl. cache) on stdout. FAIL-CLOSED: any claude
# failure or empty result → out_json={"status":"error",...} and 0 tokens (never aborts set -e).
# Pure I/O helper — sourced so tests can drive it; the caller composes the prompt file.
run_stage() {
  local prompt_file="$1" model="$2" worktree="$3" settings="$4" out_json="$5" raw_json="$6"
  ( cd "$worktree" && claude -p --model "$model" --settings "$settings" \
        --permission-mode dontAsk --max-turns "$MAX_TURNS" --output-format json 2>/dev/null ) \
      < "$prompt_file" > "$raw_json" || true
  jq -r '.result // empty' "$raw_json" 2>/dev/null | sed -n '/{/,/}/p' > "$out_json" || true
  if [ ! -s "$out_json" ]; then
    printf '%s\n' '{"status":"error","reason":"stage failed"}' > "$out_json"
    echo 0; return 0
  fi
  jq -r '((.usage.input_tokens//0)+(.usage.output_tokens//0)+(.usage.cache_read_input_tokens//0)+(.usage.cache_creation_input_tokens//0))' "$raw_json" 2>/dev/null || echo 0
}

# Run ONE P→C→E→C→V round for a single task: each stage via run_stage, artifacts → adir.
# Echoes "<chain_status>\t<total_tokens>" on stdout. FAIL-CLOSED / early-stop: a stage that
# errors → "stage_error"; PLAN not 'planned' → its status; a CRITIC 'bounce' → "bounced_plan"
# / "bounced_exec"; VERIFY → "ready" | "rejected". This is ONE round; the retry/PARK loop
# (spec §6, up to 5 rounds) is wired separately (3c-iii). Never commits/pushes — writes artifacts only.
run_rpi_chain() {
  local tid="$1" wt="$2" settings="$3" adir="$4"
  mkdir -p "$adir"
  local roles="$REPO/scripts/overnight"
  local body; body="$(cat "$TASKS_DIR/task-${tid#TASK-} "*.md 2>/dev/null || true)"
  local tmp; tmp="$(mktemp)"
  local total=0 t chain_status="unknown" v

  _emit() { rm -f "$tmp"; printf '%s\t%s\n' "$1" "$total"; }   # finalize: cleanup + emit status<TAB>tokens

  # --- PLAN ---
  printf 'TASK: %s\n\n%s\n\n%s\n' "$tid" "$body" "$(cat "$roles/plan_task.md")" > "$tmp"
  t="$(run_stage "$tmp" "$PLAN_MODEL" "$wt" "$settings" "$adir/plan_result.json" "$adir/plan.raw.json")"
  total=$((total + ${t:-0}))
  v="$(jq -r '.status // "error"' "$adir/plan_result.json" 2>/dev/null || echo error)"
  [ "$v" = "planned" ] || { _emit "$([ "$v" = "error" ] && echo stage_error || echo "$v")"; return 0; }

  # --- CRITIC post-plan ---
  printf 'STAGE: post-plan\nTASK: %s\n\n%s\n' "$tid" "$(cat "$roles/critique_task.md")" > "$tmp"
  t="$(run_stage "$tmp" "$CRITIC_MODEL" "$wt" "$settings" "$adir/critique_plan.json" "$adir/critique_plan.raw.json")"
  total=$((total + ${t:-0}))
  v="$(jq -r '.verdict // "error"' "$adir/critique_plan.json" 2>/dev/null || echo error)"
  [ "$v" = "error" ]  && { _emit stage_error; return 0; }
  [ "$v" = "bounce" ] && { _emit bounced_plan; return 0; }

  # --- EXECUTE ---
  printf 'TASK: %s\n\n%s\n' "$tid" "$(cat "$roles/execute_task.md")" > "$tmp"
  t="$(run_stage "$tmp" "$EXEC_MODEL" "$wt" "$settings" "$adir/execution.json" "$adir/execution.raw.json")"
  total=$((total + ${t:-0}))
  v="$(jq -r '.status // "error"' "$adir/execution.json" 2>/dev/null || echo error)"
  [ "$v" = "error" ] && { _emit stage_error; return 0; }

  # --- CRITIC post-execute ---
  printf 'STAGE: post-execute\nTASK: %s\n\n%s\n' "$tid" "$(cat "$roles/critique_task.md")" > "$tmp"
  t="$(run_stage "$tmp" "$CRITIC_MODEL" "$wt" "$settings" "$adir/critique_exec.json" "$adir/critique_exec.raw.json")"
  total=$((total + ${t:-0}))
  v="$(jq -r '.verdict // "error"' "$adir/critique_exec.json" 2>/dev/null || echo error)"
  [ "$v" = "error" ]  && { _emit stage_error; return 0; }
  [ "$v" = "bounce" ] && { _emit bounced_exec; return 0; }

  # --- VERIFY ---
  printf 'TASK: %s\n\n%s\n' "$tid" "$(cat "$roles/verify_task.md")" > "$tmp"
  t="$(run_stage "$tmp" "$VERIFY_MODEL" "$wt" "$settings" "$adir/verify.json" "$adir/verify.raw.json")"
  total=$((total + ${t:-0}))
  v="$(jq -r '.verdict // "error"' "$adir/verify.json" 2>/dev/null || echo error)"
  case "$v" in
    ready)  _emit ready ;;
    reject) _emit rejected ;;
    *)      _emit stage_error ;;
  esac
  return 0
}

# Signature of a retryable round = status + the reason/issues of every critic/verify artifact.
# Two consecutive rounds with the SAME signature = no progress (marginal-value collapse).
_rpi_sig() {
  local adir="$1" st="$2" s="$2::" a
  for a in critique_plan critique_exec verify; do
    s="$s$(jq -c '{r:(.reason//""),i:(.issues//[])}' "$adir/$a.json" 2>/dev/null || echo '{}')"
  done
  printf '%s' "$s"
}

# Best machine-readable reason from the last gate (verify → critic-exec → critic-plan).
_rpi_last_reason() {
  local adir="$1" a r
  for a in verify critique_exec critique_plan; do
    r="$(jq -r 'if (.reason // "") != "" then .reason else (.issues[0].issue // "") end' "$adir/$a.json" 2>/dev/null || echo "")"
    [ -n "$r" ] && [ "$r" != "null" ] && { printf '%s' "$r"; return 0; }
  done
  printf 'no machine-readable reason — inspect .dancer/ artifacts'
}

# Write parked.json with a concrete written question + evidence paths (spec §6).
# Optional $5 overrides the derived question (e.g. the budget-exceeded message).
_rpi_park() {
  local tid="$1" adir="$2" rounds="$3" stage="$4" q="${5:-}"
  [ -n "$q" ] || q="$(_rpi_last_reason "$adir")"
  jq -n --arg t "$tid" --arg s "$stage" --arg q "$q" --argjson r "$rounds" \
    --arg p1 "$adir/plan_result.json" --arg p2 "$adir/critique_exec.json" --arg p3 "$adir/verify.json" \
    '{task:$t,stage:$s,question:$q,evidence_paths:[$p1,$p2,$p3],rounds:$r}' > "$adir/parked.json" 2>/dev/null || true
}

# Drive one task through up to MAX_ROUNDS P→C→E→C→V rounds (spec §6). ready → task_result.json
# "ready". bounced/rejected → retry, UNLESS the round is a repeat of the previous one (same
# status + same reasons) → marginal-value collapse → PARK now. blocked/needs_human/stage_error
# → stop, not auto-fixable. MAX_ROUNDS exhausted → PARK. Echoes "<status>\t<total_tokens>".
# FAIL-CLOSED: any unknown status or write failure → parked (never a false ready).
run_rpi_task() {
  local tid="$1" wt="$2" settings="$3" adir="$4" budget="${5:-}"
  mkdir -p "$adir"
  # Per-task token budget (spec §7). Empty / non-numeric / 0 → fall back to the night ceiling
  # = no effective per-task cap until we have measured real spend (M5). Checked BETWEEN rounds
  # only — a started round always finishes; we never cut a round mid-flight.
  case "$budget" in ''|*[!0-9]*) budget="$TOKEN_CEILING" ;; esac
  [ "$budget" -gt 0 ] 2>/dev/null || budget="$TOKEN_CEILING"
  local total=0 round=0 prev_sig="" out st toks sig last_status="unknown"
  while [ "$round" -lt "$MAX_ROUNDS" ]; do
    round=$((round + 1))
    # Between-rounds budget gate: only after ≥1 completed round; the finished round's tokens count.
    if [ "$round" -gt 1 ] && [ "$total" -ge "$budget" ]; then
      _rpi_park "$tid" "$adir" "$((round - 1))" budget_exceeded \
        "task exceeded its token budget ($total >= $budget) after $((round - 1)) round(s) — human decision needed (raise budget / split / drop)"
      printf 'parked\t%s\n' "$total"; return 0
    fi
    out="$(run_rpi_chain "$tid" "$wt" "$settings" "$adir")"
    st="${out%%$'\t'*}"; toks="${out##*$'\t'}"
    total=$((total + ${toks:-0})); last_status="$st"
    case "$st" in
      ready)
        jq -n --arg t "$tid" --argjson r "$round" --argjson k "$total" \
          '{task:$t,status:"ready",rounds:$r,tokens:$k}' > "$adir/task_result.json" 2>/dev/null \
          || { _rpi_park "$tid" "$adir" "$round" ready-write-failed; printf 'parked\t%s\n' "$total"; return 0; }
        printf 'ready\t%s\n' "$total"; return 0 ;;
      blocked|needs_human|stage_error)
        jq -n --arg t "$tid" --arg s "$st" --argjson r "$round" --argjson k "$total" \
          '{task:$t,status:$s,rounds:$r,tokens:$k}' > "$adir/task_result.json" 2>/dev/null || true
        printf '%s\t%s\n' "$st" "$total"; return 0 ;;
      bounced_plan|bounced_exec|rejected)
        sig="$(_rpi_sig "$adir" "$st")"
        if [ "$round" -gt 1 ] && [ "$sig" = "$prev_sig" ]; then
          _rpi_park "$tid" "$adir" "$round" "$st"; printf 'parked\t%s\n' "$total"; return 0
        fi
        prev_sig="$sig" ;;
      *)
        _rpi_park "$tid" "$adir" "$round" "$st"; printf 'parked\t%s\n' "$total"; return 0 ;;
    esac
  done
  # exhausted MAX_ROUNDS without a ready → PARK
  _rpi_park "$tid" "$adir" "$round" "$last_status"
  printf 'parked\t%s\n' "$total"
  return 0
}

# Mechanical scope-lock: prove the task's git diff touched ONLY files in the plan's
# allowed_files, and NO CORE_UNSAFE file (belt-and-suspenders beyond block_core_unsafe.sh).
# Returns 0 iff every touched file is allowed AND non-CORE_UNSAFE. FAIL-CLOSED: no
# allowed_files, or any jq/git error → return 1 (never approve without a scope). Touched =
# committed-since-base ∪ staged ∪ unstaged ∪ untracked(non-ignored); .dancer/ is gitignored
# so its artifacts are excluded.
check_scope_lock() {
  local wt="$1" adir="$2"
  local allowed; allowed="$(jq -r '.allowed_files[]?' "$adir/plan_result.json" 2>/dev/null)" || return 1
  [ -n "$allowed" ] || { echo "scope-lock: no allowed_files in plan (fail-closed)" >&2; return 1; }
  local touched
  touched="$( cd "$wt" && {
        git diff --name-only "$BASE_BRANCH"...HEAD 2>/dev/null
        git diff --name-only 2>/dev/null
        git diff --name-only --cached 2>/dev/null
        git ls-files --others --exclude-standard 2>/dev/null
      } | sort -u )" || return 1
  local f verdict
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    printf '%s\n' "$allowed" | grep -Fxq -- "$f" \
      || { echo "SCOPE VIOLATION: $f (not in plan allowed_files)" >&2; return 1; }
    verdict="$("$PYBIN" "$REPO/scripts/overnight/core_unsafe.py" --anchored "$f" 2>/dev/null | awk 'NR==1{print $1}')"
    [ "$verdict" = "UNSAFE" ] && { echo "SCOPE VIOLATION (CORE_UNSAFE): $f" >&2; return 1; }
  done <<< "$touched"
  return 0
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
  if [ "${MANUAL:-0}" = "1" ]; then
    echo "MANUAL run — night-window bypassed"
  else
    guard_night_window   || { echo "ABORT: outside night window ($(now_lima) Lima) — deferred run suppressed"; exit 0; }
  fi

  local token; token="$(read_oauth_token)"
  [ -n "$token" ] || { echo "ABORT: no subscription OAuth token in Keychain ($KEYCHAIN_SERVICE)"; exit 2; }
  export CLAUDE_CODE_OAUTH_TOKEN="$token"   # precedence #5 → subscription billing

  # Smoke auth check (confirms the token authenticates; structural guarantee = no API key + OAuth token present).
  # Discard only stdout (the "ok" JSON); let stderr flow to the run log (main tee's fd2) so a
  # future auth/PATH failure is VISIBLE, not silent — the 2026-06-20 abort hid exit 127 behind 2>&1.
  local smoke_rc=0
  claude -p --output-format json "ok" >/dev/null || smoke_rc=$?
  if [ "$smoke_rc" -ne 0 ]; then
    echo "ABORT: subscription auth smoke check failed (claude exit $smoke_rc)"; exit 2
  fi

  # 1. Pre-flight: clean tree + BASE_BRANCH resolves (so the runner can execute from an
  #    isolated worktree while basing tasks/reports/SHA on BASE_BRANCH = main).
  cd "$REPO"
  guard_base_ready || exit 2
  git fetch --quiet origin || true
  git tag -f "rh-night-base-$stamp" "$BASE_BRANCH" >/dev/null
  local base_sha; base_sha="$(git rev-parse --short "$BASE_BRANCH")"   # BASE_BRANCH tip, not cwd HEAD
  echo "base $base_sha ($BASE_BRANCH)"
  if ! uv run --with-requirements requirements.txt --with pytest python3 -m pytest -m "not integration" -q >/dev/null 2>&1; then
    echo "ABORT: base test suite is RED — refusing to build on a broken base"; exit 0
  fi

  # Resolve ${REPO} in the night settings to ABSOLUTE paths so the secret/core hooks fire
  # correctly when claude runs from a WORKTREE (cwd != main). KEYSTONE: a fresh worktree has
  # no .claude/settings.local.json (gitignored), so its broad Bash allows never load.
  local resolved_settings="$RAW_DIR/settings.night.resolved.json"
  sed "s#\${REPO}#$REPO#g" "$NIGHT_SETTINGS" > "$resolved_settings"

  # 2. Triage: layer-1 (deterministic) → layer-2 (classifier in a clean scan worktree).
  # MANUAL/QUEUE mode (M1): the task SOURCE becomes the human-written queue file; the
  # classifier below still runs as a fail-closed veto over each queued task (spec §3).
  # Non-manual = unchanged auto-discovery (zero regression).
  local queue_file="${QUEUE_FILE:-$REPO/docs/auto-dancer/queue/QUEUE_${stamp}.md}"
  local candidates
  local -A task_budget=()      # tid → per-task token budget (QUEUE mode only; discovery → empty → default)
  if [ "${MANUAL:-0}" = "1" ]; then
    # A MANUAL run requires an explicit human-written queue — never silently fall back
    # to auto-discovery (that would defeat the point of hand-picking the tasks).
    [ -f "$queue_file" ] || { echo "ABORT: MANUAL run requires a queue file: $queue_file"; exit 2; }
    echo "MANUAL/QUEUE mode — task source: $queue_file"
    local queue_tsv; queue_tsv="$("$PYBIN" "$REPO/scripts/overnight/read_queue.py" "$queue_file")"
    candidates="$(printf '%s\n' "$queue_tsv" | cut -f1)"   # ordered ids (queue order = execution order)
    local _qt _qb _qr
    while IFS=$'\t' read -r _qt _qb _qr; do
      [ -n "$_qt" ] && task_budget["$_qt"]="$_qb"
    done <<< "$queue_tsv"
  else
    candidates="$("$PYBIN" "$REPO/scripts/overnight/triage_filter.py" "$TASKS_DIR")"
  fi
  local wt_scan="$REPO/../rh-night-scan-$stamp"
  git worktree add --detach --force "$wt_scan" "$BASE_BRANCH" >/dev/null 2>&1 || true
  # Never orphan the scan worktree again (the 2026-06-20 exit-1 left it behind). No prior EXIT
  # trap exists in this script, so this does not clobber one. Idempotent with the explicit
  # removal below (|| true). Note: by design only the read-only scan worktree is auto-removed;
  # per-task execute worktrees are intentionally kept for inspection unless the task is "done".
  trap 'git worktree remove --force "$wt_scan" 2>/dev/null || true' EXIT
  local queue=() n_needs=0 classified=0
  while read -r tid; do
    [ -n "$tid" ] || continue
    cap_reached "$classified" && { echo "candidate cap ($MAX_CANDIDATES) reached — stop classifying"; break; }
    # production stops once the queue is full; the dry-run keeps sampling to MAX_CANDIDATES to show the distribution
    if ! is_triage_only && [ "${#queue[@]}" -ge "$MAX_TASKS" ]; then break; fi
    classified=$((classified + 1))
    local body; body="$(cat "$TASKS_DIR/task-${tid#TASK-} "*.md 2>/dev/null || true)"
    local verdict; verdict="$(classify_verdict "$body" "$wt_scan" "$resolved_settings" "$RAW_DIR/${tid}.classify.err")"
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

  # Gate-5 dry-run: stop here. No per-task worktrees, no model execution, no PRs, no publish.
  if is_triage_only; then
    echo "TRIAGE-ONLY: pre-flight + triage complete; queue + needs_human JSON emitted in $RAW_DIR. Stopping (no execute, no PRs)."
    return 0
  fi

  # 3. Execute loop — each task in its OWN fresh worktree (KEYSTONE isolation), driven through
  #    the full P→C→E→C→V RPI chain (run_rpi_task, up to MAX_ROUNDS); circuit breaker between
  #    tasks. The ORCHESTRATOR — never the model — makes the LOCAL commit, and ONLY on a
  #    verified `ready` that also passes the mechanical scope-lock (spec §8). Never push,
  #    never gh pr, never touch main. Every worktree is kept for the morning review.
  local spent=0 ran=0 start_epoch; start_epoch="$(date +%s)"
  for tid in "${queue[@]:-}"; do
    [ -n "${tid:-}" ] || continue
    over_ceiling "$spent" "$TOKEN_CEILING" && { echo "ceiling hit ($spent) — stop"; break; }
    local elapsed_min=$(( ($(date +%s) - start_epoch) / 60 ))
    [ "$elapsed_min" -ge "$WALL_CLOCK_MIN" ] && { echo "wall-clock cap hit — stop"; break; }

    local wt="$REPO/../rh-dancer-${tid}"
    git worktree add --force "$wt" -b "auto-dancer/$tid" "$BASE_BRANCH" >/dev/null 2>&1 \
      || git worktree add --force "$wt" "auto-dancer/$tid" >/dev/null 2>&1 || { echo "  worktree add failed for $tid"; continue; }
    local adir="$wt/.dancer"

    # Drive the RPI chain; run_rpi_task echoes "<status>\t<total_tokens>". Per-task budget comes
    # from the queue (QUEUE mode); discovery mode passes empty → run_rpi_task uses the night ceiling.
    local tbud="${task_budget[$tid]:-}"
    local out st toks; out="$(run_rpi_task "$tid" "$wt" "$resolved_settings" "$adir" "$tbud")"
    st="${out%%$'\t'*}"; toks="${out##*$'\t'}"
    spent=$(( spent + ${toks:-0} )); ran=$((ran + 1))
    echo "  $tid → $st; tokens+=$toks (spent $spent)"

    # Surface the per-task result to the morning report (task_result.json, else parked.json).
    if   [ -f "$adir/task_result.json" ]; then cp "$adir/task_result.json" "$RAW_DIR/${tid}.json" 2>/dev/null || true
    elif [ -f "$adir/parked.json" ];      then cp "$adir/parked.json"      "$RAW_DIR/${tid}.json" 2>/dev/null || true
    fi

    # §8 commit boundary: LOCAL commit to the branch ONLY on a verified `ready` that also passes
    # the mechanical scope-lock — done by the orchestrator, never the model. No push, no PR.
    if [ "$st" = "ready" ]; then
      if check_scope_lock "$wt" "$adir"; then
        local dsent; dsent="$(jq -r '.done_sentence // "task"' "$adir/plan_result.json" 2>/dev/null || echo task)"
        ( cd "$wt" && git add -A -- ':!.dancer' && git commit -q -m "auto-dancer($tid): $dsent" ) \
          && echo "  committed locally to auto-dancer/$tid (no push)" \
          || echo "  commit failed for $tid — worktree kept"
      else
        echo "  SCOPE-LOCK FAILED for $tid — no commit; worktree kept for inspection"
        jq -n --arg t "$tid" '{task:$t,status:"scope_violation",reason:"diff touched files outside plan allowed_files (or CORE_UNSAFE)"}' \
          > "$RAW_DIR/${tid}.json" 2>/dev/null || true
      fi
    fi
    # Every outcome (committed `ready`, parked, blocked, rejected, needs_human, stage_error,
    # scope_violation) keeps its worktree for the morning review — nothing is auto-removed here.
    echo "  (worktree kept for inspection: $wt)"
  done

  # 4. Budget + report.
  jq -n --argjson run "$ran" --argjson maxt "$MAX_TASKS" \
        --argjson tok "$spent" --argjson ceil "$TOKEN_CEILING" \
        '{tasks_run:$run,max_tasks:$maxt,tokens:$tok,token_ceiling:$ceil,ceiling_hit:($tok>=$ceil),per_task:{}}' \
        > "$RAW_DIR/_budget.json"
  # Write the report into the gitignored per-night RAW_DIR so the runner's own tree stays
  # clean (else next run's guard_base_ready would abort). It is published to the
  # overnight-reports branch (committed there as docs/overnight/REPORT_*.md) below.
  local report="$RAW_DIR/REPORT_${stamp}.md"
  "$PYBIN" "$REPO/scripts/overnight/build_report.py" "$RAW_DIR" "$stamp" "$base_sha" "$report"

  # 5. Report stays LOCAL — spec §8.2 zero-push. The Auto Dancer never pushes anything: the
  #    morning review is done locally against the per-task branches + this report. (Removed the
  #    old overnight-reports worktree/commit/push; the email workflow that keyed off that push
  #    is dormant by consequence — no code path here references it.)
  echo "== report (local): $report =="
  echo "   read it in the terminal — no push (spec §8.2)"
}

# Run only when executed directly (sourcing exposes guards to tests).
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  case "${1:-}" in
    --check-auth)  check_auth ;;          # §11 gate #3: invoke via launchd to verify Keychain context
    --triage-only) TRIAGE_ONLY=1 main "$@" ;;   # §11 gate-5 dry-run: pre-flight + triage, no execute/PR
    --manual)      MANUAL=1 main "$@" ;;         # M1: manual trigger any hour — night-window bypassed, queue-file source
    *)             main "$@" ;;
  esac
fi
