#!/usr/bin/env bash
#
# check_task_gate.sh — every NEW ticket must say when it is allowed to close.
#
# WHY (2026-08-10): 42 of 87 open tickets (48%) carry no measurable closing
# criterion, and two that did close — TASK-223 and TASK-111 — regressed within
# weeks because "the action was performed" was the whole bar. A ticket without
# a closing condition cannot be finished, only abandoned.
#
# The required field is a line that begins:   ייסגר כאשר:
# Free text after it; the point is that someone had to write the condition down
# before the ticket entered the backlog.
#
# ⚠️ DELIBERATELY NOT RETROACTIVE. The 42 existing gate-less tickets are
# reported as a debt figure and never as a failure — a rule applied backwards
# turns into 42 red lines nobody can clear, and then the whole check gets
# ignored. Only tickets created TODAY (or --date) are enforced.
#
# usage: check_task_gate.sh [--date YYYY-MM-DD] [-q]
# exit 0 = every new ticket has the field · 1 = at least one is missing
set -u
REPO="${RH_REPO_DIR:-$HOME/RidingHighPro}"
DATE=$(date +%Y-%m-%d); QUIET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --date) DATE="$2"; shift 2 ;;
    -q) QUIET=1; shift ;;
    *) shift ;;
  esac
done

cd "$REPO" || exit 0
missing=""; total=0; debt=0
for f in backlog/tasks/*.md; do
  case "$f" in *.bak*) continue ;; esac
  st=$(grep -m1 '^status:' "$f" | sed 's/status: *//')
  case "$st" in Done|Archived|Cancelled) continue ;; esac
  grep -q "ייסגר כאשר:" "$f" || debt=$((debt + 1))
  grep -q "^created_date: '\?$DATE" "$f" || continue
  total=$((total + 1))
  if ! grep -q "ייסגר כאשר:" "$f"; then
    id=$(grep -m1 '^id:' "$f" | sed 's/id: *//')
    missing="$missing $id"
  fi
done

n=$(printf '%s' "$missing" | wc -w | tr -d ' ')
if [ "$QUIET" -eq 1 ]; then
  if [ "$n" -eq 0 ]; then
    echo "שער-קבלה בתיקים חדשים: ✅ $total/$total ($DATE) · חוב היסטורי: $debt"
  else
    echo "שער-קבלה בתיקים חדשים: ❌ $n מתוך $total חסרים ($DATE) · חוב היסטורי: $debt"
  fi
  [ "$n" -eq 0 ] && exit 0 || exit 1
fi

echo "════ check_task_gate · תיקים שנוצרו $DATE ════"
echo "  נבדקו: $total · חסרי-שדה: $n"
echo "  חוב היסטורי (כל הפתוחים ללא השדה, לא נאכף): $debt"
if [ "$n" -ne 0 ]; then
  echo
  echo "❌ חסר \"ייסגר כאשר:\" ב:$missing"
  echo
  echo "הוסף לגוף כל אחד שורה שמתחילה ב-\"ייסגר כאשר: \" ואחריה התנאי המדיד"
  echo "שבו התיק נסגר. תיק בלי תנאי-סגירה לא נסגר — הוא ננטש."
  exit 1
fi
echo "✅ כל תיק שנוצר $DATE נושא תנאי-סגירה."
exit 0
