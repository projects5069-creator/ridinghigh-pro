#!/usr/bin/env bash
# PreToolUse secret-block hook for the overnight runner.
# The reliable replacement for the unreliable .claudeignore: a deterministic gate
# that HARD-DENIES any tool call targeting a secret file, regardless of what the
# model "decides". FAIL-CLOSED — if we cannot parse the input or jq is missing on a
# file-touching tool, we DENY. (Contrast the skill-gate hook, which fails open.)

input="$(cat)"

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}
allow() { printf '{}\n'; exit 0; }

tool="$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || echo "__ERR__")"

# Only gate tools that can read/inspect/execute on files; everything else passes.
case "$tool" in
  Read|Grep|Glob|Bash|Edit|Write) ;;
  __ERR__) deny "secret-guard: jq missing or input unparseable (fail-closed)" ;;
  *) allow ;;
esac

# Collect candidate targets from the common tool_input fields.
target="$(printf '%s' "$input" | jq -r '
  [.tool_input.file_path, .tool_input.command, .tool_input.pattern, .tool_input.path,
   .tool_input.old_string, .tool_input.content]
  | map(select(. != null)) | join(" ")' 2>/dev/null || echo "__ERR__")"

if [ "$target" = "__ERR__" ]; then
  deny "secret-guard: unparseable tool input (fail-closed)"
fi

# Env-dump via Bash would expose any secret living in an env var (the file regex can't see
# env). Deny env/set/export/printenv/declare/compgen dumps + python os.environ reads. A
# legit `env VAR=x cmd` (env followed by a NAME=, not a pipe/terminator) is still allowed.
if [ "$tool" = "Bash" ]; then
  envdump_re='printenv|(^|[;&|[:space:]])env[[:space:]]*($|[|;&>])|(^|[;&|[:space:]])set[[:space:]]*($|[|;&>])|export[[:space:]]+-p|declare[[:space:]]+-[xp]|compgen[[:space:]]+-e|os\.environ'
  if printf '%s' "$target" | grep -Eq "$envdump_re"; then
    deny "secret-guard: environment dump blocked"
  fi
fi

# Secret file patterns + the runner's own auth tokens (deny any command that references them,
# e.g. `echo $CLAUDE_CODE_OAUTH_TOKEN > leak`), credential stores (aws/ssh/gcloud/netrc/keys).
secret_re='(^|[^[:alnum:]])\.env([^[:alnum:]]|$)|google_credentials|oauth_credentials|oauth_client|oauth_token|_sheet_id|secrets\.toml|\.credentials\.json|\.aws/|\.ssh/|id_rsa|id_ed25519|\.netrc|gcloud|credentials\.db|kubeconfig|\.pem([^[:alnum:]]|$)|\.p12([^[:alnum:]]|$)|CLAUDE_CODE_OAUTH_TOKEN|GH_TOKEN|GITHUB_TOKEN|ANTHROPIC_API_KEY'

if printf '%s' "$target" | grep -Eq "$secret_re"; then
  deny "secret file access blocked by overnight runner"
fi

allow
