# NIGHT_RUN — 2026-06-08 · TASK-114 (.bak auto-prune) · שלב 2a

> **מצב:** ATTENDED (ping-pong) — ה-`/goal` הגיע לסשן האינטראקטיבי, **לא** auto-mode עיוור. עמיחי ער וצופה (כלל-בטיחות #7). מבחן 2a של חיבור דור-שני (TASK-121).

## משימה
**TASK-114** — מנגנון prune אוטומטי לקבצי `.bak`: שמור N=3 אחרונים לכל basename, מחק ישנים. עוצר את ה-treadmill (TASK-30/50/86 מחקו ידנית והם נוצרו מחדש).

## goal (תנאי-סיום מדיד)
`until scripts/prune_baks.sh exists, is executable, and keeps ≤3 .bak per basename (verified on fixture), committed on branch night/TASK-114`

> הערה: התנאי המקורי "until git status clean" לא ישים — קבצי `.bak_*` הם gitignored, ולכן מחיקתם לא מפיקה diff. התוצר ה-tracked = **הסקריפט עצמו**; מחיקת ה-baks היא side-effect.

## מה בוצע
- נוצר `scripts/prune_baks.sh` (🟢, tracked) — N=3 default, **dry-run כברירת-מחדל** (`--apply` למחיקה), מדלג על git-tracked, תואם bash 3.2.
- **אומת על fixture:** 5 baks ל-foo → נשמרו 3 החדשים, נמחקו 2 הישנים; 2 baks ל-bar → נשמרו. לוגיקת keep-N נכונה.
- **dry-run על הריפו:** 7 baks, ≤2 לכל basename → 0 למחיקה (שום basename חורג מ-3). prune מסופק; לא הורץ `--apply` (no-op).

## כללי-בטיחות (RUN_MODE_DECISION §7 / NIGHT_RUN_TEMPLATE)
- **branch:** `night/TASK-114` (G1) · **base:** `main` · **no merge, no push ל-main** (G3).
- **נתיבים:** `scripts/` (🟢 non-core) + `docs/` (🟢). אפס נגיעה ב-🔴.
- **תקרת לילה (#6):** branch יחיד.
- **קבוצה A (#3):** אין IO חיצוני (אין finviz/gspread/news/requests) — מניפולציית קבצים מקומית בלבד.

## Run Log
- mode: attended (ping-pong, **לא** auto-mode) · /goal: `until scripts/prune_baks.sh exists, executable, keeps ≤3 per basename (verified), committed on night/TASK-114`
- steps: (1) branch night/TASK-114; (2) כתיבת scripts/prune_baks.sh; (3) תיקון bash-3.2 (declare -A → running counter); (4) אימות fixture 5→3 + dry-run ריפו; (5) כתיבת NIGHT_RUN; (6) commit + push + PR.
- stop-counters: consecutive_blocks=0 · total_blocks=0 · stopped_reason=goal-met
- result: goal met — scripts/prune_baks.sh נוצר ואומת; branch night/TASK-114; PR נפתח (DO NOT merge).

## verdict צפוי מ-Agent #8
**Ready** — diff scripts/+docs (🟢), אפס נתיב 🔴, branch יחיד. **כלל-5 = ✅** (Run Log קיים, stopped_reason=goal-met, counters=0 < ספים) — הפעם לא "לא-ודאי".
