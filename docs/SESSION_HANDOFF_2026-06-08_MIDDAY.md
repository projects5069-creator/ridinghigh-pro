# HANDOFF-ביניים — 2026-06-08, לקראת reload (TASK-94.3 Phase 0)

> פתק-מעבר בלבד — **לא** סגירת-יום. בלי PK bump, בלי handoff סוף-יום.

## למה reload
`.claude/agents/rh-routine-checker.md` נוצר היום באמצע הסשן — נטען לרישום `subagent_type`
רק אחרי reload. Phase 0 (אימות הטעינה) דורש סשן טרי.

## מצב epic TASK-94
- **94.1 ✅ Done** (PR #11) — §3 סגור + §7.2 הורחב ל-5 נתיבים + PK 2.87.
- **94.2 ✅ Done** (PR #12) — פרסונת `rh-routine-checker` (system-prompt read-only מקודד §3,
  dry-run אומת A→Needs-Work / Clean-B→Ready).
- **94.3 ⬜ To Do** — Phase 1 (runbook) מוזג (PR #13). נשאר Phase 0 + Phase 2.

## מה לעשות בסשן החדש (אחרי reload)
**Phase 0 (חוסם):** הרץ `Task(subagent_type: rh-routine-checker)` על branch-בדיקה זרוק →
ודא שלא מחזיר `not found` ושהפלט בפורמט §3.3.
- אם עובד → **Phase 2:** אימות-ענן staged (`RemoteTrigger` PROBE, `run_once_at` רחוק),
  **גייט RULE #6** — אף `create/run` בלי אישור מפורש של עמיחי. דפוס TASK-93.
- אם `not found` → חקור מיקום/הגדרת `.claude/agents` — 94.3 חסום עד שהטעינה עובדת.
- כל פעולת-רשת דורשת **sandbox מושבת** (נצפה כל היום).

## מקורות חיים (לקריאה בסשן החדש)
- `docs/AGENT8_MORNING_RUNBOOK.md` — מסילת-הבוקר (Phase 1).
- `docs/AGENT8_CAPABILITIES_MAP.md §3` — auto-safe paths + 7 כללים + פורמט §3.3.
- `.claude/agents/rh-routine-checker.md` — הפרסונה.
- `docs/TASK-93_ROUTINE_RUNBOOK.md` — מנגנון הענן (create→run→update→run).
- AC #1 של TASK-94.3 — ה-reload caveat.

## מצב git
main `077be17`, ahead 0, נקי. כל תוצרי Agent #8 חיים ב-main.
המשך: **TASK-94.3 Phase 0 → Phase 2 → סגירת epic.**

*— END (פתק-ביניים) —*
