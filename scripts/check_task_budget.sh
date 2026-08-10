#!/usr/bin/env bash
#
# check_task_budget.sh — three new tickets a day, and the fourth needs a word.
#
# WHY (2026-08-10): 61 tickets opened in seven days against 28 closed, +42 over
# thirty days. The backlog is growing 2.4× faster than it drains, and every
# ticket opened without a decision to work on it is a promise nobody made.
#
# ⚠️ WARNS, NEVER BLOCKS. A day like 2026-08-10 — nine tickets from one deep
# investigation — is legitimate; what is not legitimate is it happening
# quietly. The point is that the fourth ticket costs a sentence out loud, not
# that it is forbidden. A hard block here would just be routed around.
#
# usage: check_task_budget.sh [--date YYYY-MM-DD] [--limit N] [-q]
# exit 0 = at or under budget · 1 = over (warning, caller decides)
set -u
REPO="${RH_REPO_DIR:-$HOME/RidingHighPro}"
DATE=$(date +%Y-%m-%d); LIMIT=3; QUIET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --date) DATE="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    -q) QUIET=1; shift ;;
    *) shift ;;
  esac
done

cd "$REPO" || exit 0
ids=""
n=0
for f in backlog/tasks/*.md; do
  case "$f" in *.bak*) continue ;; esac
  grep -q "^created_date: '\?$DATE" "$f" || continue
  n=$((n + 1))
  ids="$ids $(grep -m1 '^id:' "$f" | sed 's/id: *//')"
done

if [ "$QUIET" -eq 1 ]; then
  if [ "$n" -le "$LIMIT" ]; then
    echo "תקציב-תיקים $DATE: ✅ $n/$LIMIT"
  else
    echo "תקציב-תיקים $DATE: ⚠️ $n נפתחו (תקרה $LIMIT) — דורש אישור מפורש"
  fi
  [ "$n" -le "$LIMIT" ] && exit 0 || exit 1
fi

echo "════ תקציב-תיקים · $DATE ════"
echo "  נפתחו: $n · תקרה: $LIMIT"
echo "  התיקים:$ids"
if [ "$n" -gt "$LIMIT" ]; then
  echo
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║ ⚠️  נפתחו $n תיקים היום. מעל $LIMIT דורש אישור מפורש של עמיחי.        ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo
  echo "  זו אזהרה, לא חסימה. יום עמוס הוא לגיטימי — אבל הוא עובר דרך"
  echo "  שאלה מפורשת ולא בשקט. לפני התיק הבא: האם הוא נפרד מהקיימים"
  echo "  (scripts/check_task_duplicate.sh) והאם יש לו תנאי-סגירה?"
  exit 1
fi
echo "✅ בתוך התקציב."
exit 0
