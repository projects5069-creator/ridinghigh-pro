# Session Handoff — 2026-06-20 (Overnight Runner: ARMED → DISARMED)

## מה קרה היום
ריצה מפוקחת ראשונה של ה-overnight runner ב-daylight (NIGHT_END_HOUR=24 inline). חשפה שני דברים שלילה לא-מפוקח היה מסתיר:

1. **באג robustness (exit 1):** classify substitution לא-מוגן ב-rh-overnight.sh תחת set -euo pipefail — כשל classify יחיד מתוך 59 הרג את כל הריצה (מת במועמד #52, TASK-174), השאיר scan worktree יתום, דילג על report.
2. **הפרכת פרמיסה:** "TASK-126 = sole auto-safe (1/59)" — שגוי. ה-classifier החי שפט את כל 59 needs_human, TASK-126 בכללם (נימוק נכון: 100+ gh run view = research, לא bounded helper). אין auto-safe אמיתי בבקלוג.

## תיקונים שנחתו (main, CI ירוק)
- `b33b204` — widen launchd PATH (claude/gh/node) + unmask smoke stderr
- `211981b` — holiday-safe test (Juneteenth red CI)
- `655fbc5` — fail-closed classify_verdict + stderr→.classify.err + scan-worktree trap EXIT

## מצב נוכחי
- **Runner DISARMED** — launchctl unload (מאומת: לא ב-launchctl list; plist על הדיסק → reload-able עם launchctl load).
- **TASK-186** (Build overnight runner) — In Progress, תקוע על execute-proof. ה-execute machine ממופה וקיים (queue→worktree rh-night/$tid→execute_task.md: debug→TDD→review→draft PR @ :51) אך **לא validated end-to-end** — אין auto-safe אמיתי להריץ עליו.
- **TASK-126** — To Do (needs_human, לא Done).

## הוכחת execute — נדחתה ביודעין
synthetic task (clamp) נשקל ונדחה: שורף tokens + residue (PR/branch/report/task-לארכב) בלי רווח אמיתי כשהרנר disarmed ואין auto-safe. recon מלא של מכונת ה-execute שמור ב-plan file (polished-bubbling-lecun.md). אילוץ עיקרי לעתיד: helper synthetic חייב **קובץ לא-core חדש** (utils.py הוא CORE_UNSAFE).

## אם מחזירים בעתיד
ערך הרנר מכאן = template + `--triage-only`, לא auto-exec לילי. הוכחת execute (כשתצוץ סיבה): task ב-קובץ לא-core חדש, MAX_TASKS=1, ריצה מפוקחת — ה-recon כבר עשוי.
