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

# Test-only override, אותו דפוס בדיוק כמו window_guard.sh שורה 35 —
# מנגנון אחד בשני המקומות, לא שניים שונים.
TODAY="${WINDOW_GUARD_DATE:-$(date +%F)}"
if [ "$TODAY" \< "$WIN_START" ]; then
  echo "4. חלון-המדידה  : טרם נפתח (נפתח $WIN_START) · היום $TODAY"
elif [ "$TODAY" \> "$WIN_END" ]; then
  echo "4. חלון-המדידה  : נסגר ($WIN_END) · היום $TODAY"
else
  # יום-מסחר N מתוך 20: ספירת ימי-חול מ-WIN_START ועד היום, כולל.
  # אין חגי-בורסה בתוך 10/8..4/9 (Labor Day הוא 7/9, אחרי הסגירה).
  DAYN=$(/usr/bin/python3 - "$WIN_START" "$TODAY" <<'PYEOF'
import sys, datetime as dt
a=dt.date.fromisoformat(sys.argv[1]); b=dt.date.fromisoformat(sys.argv[2])
n=0; d=a
while d<=b:
    if d.weekday()<5: n+=1
    d+=dt.timedelta(days=1)
print(n)
PYEOF
)
  echo "4. חלון-המדידה  : ⚠️ פתוח — יום $DAYN מתוך 20 ($WIN_START..$WIN_END) · היום $TODAY — order_manager.py ו-decision_logic.py קפואים"
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

# 7 (2026-08-10) — שורה 3 מדווחת רק אם מתג-האכיפה קיים; ב-10/8 נמדד ששער דלוק
# יכול לדווח ירוק ולא לבדוק דבר. הבקרה היחידה שמבדילה היא הרצת ה-selftest,
# וספירת החסימות בפועל: שער שלא ירה מעולם ושער שבור נראים זהה בלעדיה.
SELF=$(cd "$HOME/RidingHighPro" && bash scripts/skill_gate_selftest.sh -q 2>/dev/null | head -1)
LOG="$HOME/ClaudeWork/_machine/skill_gate/blocks.log"
TDAY=$(date +%Y-%m-%d); YDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d yesterday +%Y-%m-%d)
BLK=$(grep -c -e "^$TDAY" -e "^$YDAY" "$LOG" 2>/dev/null | tr -d ' ')
echo "7. ${SELF:-שער-סקילים: לא זמין} · חסימות מאתמול: ${BLK:-0}"

# 8 (2026-08-10) — כפילויות-כניסה. ב-10/8, יום 1 של חלון-המדידה, JWEL ו-DKI
# נכנסו פעמיים כל אחד בהפרש שנייה, משתי ריצות שהתחילו job באותה שנייה. איש לא
# היה יודע אלמלא חיפשנו. הגלאי אינו מונע — הוא מוודא שלא נגלה את זה ב-7/9.
# קורא דוח מוכן בלבד (הסריקה עולה מאות שליפות-לוג ואינה שייכת לפתיחת-סשן):
#   uv run python3 scripts/detect_duplicate_entries_v1.py --date <יום>
DUPDIR="$HOME/ClaudeWork/RidingHighPro/audit/duplicates"
LASTSUM=$(ls -1 "$DUPDIR"/*.summary 2>/dev/null | sort | tail -1)
if [ -n "$LASTSUM" ] && [ -r "$LASTSUM" ]; then
  DUPDATE=$(basename "$LASTSUM" .summary)
  DUPLINE=$(head -1 "$LASTSUM")
  case "$DUPLINE" in
    STATUS=CLEAN*) MARK="✅" ;;
    *)             MARK="❌" ;;
  esac
  echo "8. כפילויות-כניסה: $MARK $DUPDATE — $DUPLINE"
else
  echo "8. כפילויות-כניסה: ⚠️ אין דוח — הגלאי טרם רץ (scripts/detect_duplicate_entries_v1.py)"
fi

# 9-11 (2026-08-10) — חוב-המשימות. נמדד באותו יום: 87 תיקים פתוחים, 61 נפתחו
# בשבוע מול 28 שנסגרו, 48% בלי קריטריון-סגירה, ושלושה תיקים חדשים שכפלו
# קיימים. בקלוג שאיש לא רואה גדל פי-2.4 מקצב-הסגירה שלו.
RHDIR="$HOME/RidingHighPro"

# 9 · טריות ה-DIGEST — קובץ בן יומיים מתאר בקלוג אחר
DG="$RHDIR/docs/OPEN_TASKS_DIGEST.md"
if [ -r "$DG" ]; then
  AGE_H=$(( ( $(date +%s) - $(stat -f %m "$DG" 2>/dev/null || stat -c %Y "$DG") ) / 3600 ))
  CNT=$(grep -cE '^TASK-[0-9]+ \| ' "$DG" 2>/dev/null | tr -d ' ')
  if [ "$AGE_H" -lt 24 ]; then
    echo "9. תקציר-המשימות: ✅ $CNT תיקים · גיל ${AGE_H}ש"
  else
    echo "9. תקציר-המשימות: ❌ ישן (${AGE_H}ש) — הרץ scripts/generate_open_tasks_digest.sh"
  fi
else
  echo "9. תקציר-המשימות: ❌ אינו קיים — הרץ scripts/generate_open_tasks_digest.sh"
fi

# 10 · תיקים חדשים בלי תנאי-סגירה (לא רטרואקטיבי — רק של היום)
echo "10. $(bash "$RHDIR/scripts/check_task_gate.sh" -q 2>/dev/null || true)"

# 11 · כמה תיקים נפתחו אתמול — התקציב, במבט לאחור
YD=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d yesterday +%Y-%m-%d)
echo "11. $(bash "$RHDIR/scripts/check_task_budget.sh" -q --date "$YD" 2>/dev/null || true)"
