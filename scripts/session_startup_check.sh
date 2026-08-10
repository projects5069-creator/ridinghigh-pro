#!/usr/bin/env bash
# RidingHigh Pro — Session Startup Check
#
# Six facts a session must know before it touches anything. Created 2026-08-09
# after two near-misses: the measurement-window guard was registered only in the
# project settings, so a session opened from the home directory silently had no
# guard; and the skill gate's enforce switch is a file whose state nobody could
# see. Both were invisible until someone went looking. This makes them the
# first thing printed.
#
# Read-only. Never exits non-zero — it reports, it does not block.

WIN_START="2026-08-10"; WIN_END="2026-09-04"
GUARD="$HOME/RidingHighPro/.claude/hooks/window_guard.sh"
GLOBAL="$HOME/.claude/settings.json"
PROJECT="$HOME/RidingHighPro/.claude/settings.json"
ENFORCE="$HOME/.claude/hooks/.skill_gate_enforce"

has_guard() {  # $1 = settings file; matches the basename so ~/… and ${CLAUDE_PROJECT_DIR}/… both count
  [ -r "$1" ] || { echo "no (אין קובץ)"; return; }
  grep -q "window_guard.sh" "$1" && echo "כן" || echo "לא"
}

echo "═══ Session Startup Check · $(TZ='America/Lima' date '+%Y-%m-%d %H:%M %Z') ═══"
echo "1. שומר-החלון ב-settings הגלובלי : $(has_guard "$GLOBAL")   ($GLOBAL)"
echo "2. שומר-החלון ב-settings הפרויקט : $(has_guard "$PROJECT")   (נטען רק בסשן מ-~/RidingHighPro)"

if [ -e "$HOME/RidingHighPro/.claude/hooks/WINDOW_GUARD_OFF" ] || [ "${WINDOW_GUARD_OFF:-0}" = "1" ]; then
  echo "   ⚠️ שומר-החלון מנוטרל כרגע ע\"י מתג-חירום"
fi

if [ -f "$ENFORCE" ]; then
  echo "3. אכיפת-סקילים : דלוקה · כיבוי: rm $ENFORCE"
else
  echo "3. אכיפת-סקילים : כבויה · הדלקה: touch $ENFORCE"
fi

TODAY=$(date +%F)
if [ "$TODAY" \< "$WIN_START" ]; then
  echo "4. חלון-המדידה  : טרם נפתח (נפתח $WIN_START) · היום $TODAY"
elif [ "$TODAY" \> "$WIN_END" ]; then
  echo "4. חלון-המדידה  : נסגר ($WIN_END) · היום $TODAY"
else
  echo "4. חלון-המדידה  : ⚠️ פתוח ($WIN_START..$WIN_END) · היום $TODAY — order_manager.py ו-decision_logic.py קפואים"
fi

PK=$(ls -1t "$HOME/RidingHighPro"/docs/*PK*.md 2>/dev/null | head -1)
if [ -n "$PK" ]; then
  V=$(grep -m1 -oE '\| \*\*Document version\*\* \| [0-9.]+' "$PK" | grep -oE '[0-9.]+$')
  echo "5. PK חי        : v${V:-?} · $PK"
else
  echo "5. PK חי        : ❌ לא נמצא"
fi

N=$(cd "$HOME/RidingHighPro" && backlog task list --plain 2>/dev/null \
     | awk '/:$/{h=$0} /TASK-/{if(h!~/Done|Archived|Cancelled/)c++} END{print c+0}')
echo "6. משימות פתוחות: $N"
