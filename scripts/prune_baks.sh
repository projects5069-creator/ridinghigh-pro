#!/usr/bin/env bash
# prune_baks.sh — keep the N most-recent *.bak_<timestamp> backups per source
# file and remove older ones. Stops the .bak treadmill (TASK-114; TASK-30/50/86
# kept deleting baks manually and they regenerated).
#
# SAFE BY DEFAULT: dry-run unless --apply is given. Never deletes git-tracked
# files (only untracked *.bak_* backups, which are gitignored anyway).
#
# Usage:
#   scripts/prune_baks.sh                 # dry-run, N=3, repo root
#   scripts/prune_baks.sh --apply         # actually delete, keep 3 newest
#   scripts/prune_baks.sh -n 5 --apply    # keep 5 newest per source
#   scripts/prune_baks.sh /some/dir       # operate on another root
set -euo pipefail

N=3
APPLY=0
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n) N="${2:?-n needs a value}"; shift 2;;
    --apply) APPLY=1; shift;;
    --dry-run) APPLY=0; shift;;
    -h|--help) sed -n '2,14p' "$0"; exit 0;;
    *) ROOT="$1"; shift;;
  esac
done

deleted=0; kept=0; skipped=0
prev_key=""; c=0

# Stream "<source-key>\t<timestamp>\t<path>", sorted by key then timestamp desc,
# so all backups of one source are consecutive, newest first. A running counter
# per key (reset on key change) avoids associative arrays (works on bash 3.2).
# key = path with the .bak_<ts> suffix removed.
while IFS=$'\t' read -r key ts path; do
  if [[ "$key" != "$prev_key" ]]; then prev_key="$key"; c=0; fi
  c=$((c + 1))
  if (( c <= N )); then
    kept=$((kept + 1)); continue
  fi
  rel="${path#"$ROOT"/}"
  if git -C "$ROOT" ls-files --error-unmatch -- "$rel" >/dev/null 2>&1; then
    echo "SKIP (git-tracked, never delete): $rel"; skipped=$((skipped + 1)); continue
  fi
  if (( APPLY )); then rm -f -- "$path"; echo "DELETED: $rel"
  else echo "WOULD-DELETE: $rel"; fi
  deleted=$((deleted + 1))
done < <(
  find "$ROOT" -path '*/.git' -prune -o -type f -name '*.bak_*' -print |
  while IFS= read -r f; do
    printf '%s\t%s\t%s\n' "${f%.bak_*}" "${f##*.bak_}" "$f"
  done |
  sort -t$'\t' -k1,1 -k2,2r
)

mode=$([[ $APPLY -eq 1 ]] && echo APPLY || echo DRY-RUN)
echo "---"
echo "TASK-114 prune_baks · N=$N · mode=$mode · root=$ROOT"
echo "kept=$kept · $([[ $APPLY -eq 1 ]] && echo deleted || echo would_delete)=$deleted · skipped_tracked=$skipped"
