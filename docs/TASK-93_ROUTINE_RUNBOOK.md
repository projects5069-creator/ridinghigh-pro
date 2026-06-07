# TASK-93 — Cloud Routine GitHub Connectivity Runbook

*מטרה: לאפשר ל-Cloud Routine (סוכן claude.ai מרוחק, /schedule) לדחוף branch ולפתוח PR
על `projects5069-creator/ridinghigh-pro` לבד = end-to-end אמיתי.*

> סטטוס: **תכנון + staged**. אף routine לא נוצר/נורה בענן. ההרצה בפועל מחייבת אישור מפורש.

---

## 1. Context — שני הבלוקרים (מאומתים חי מול config הפיילוט)

פיילוט 1/6 (`trig_01YN8VnZ4KTBbMrxT1DDAi1D`, TASK-77, run-once, fired 2026-06-02)
ביצע נכון אך **לא דחף/פתח PR**. `RemoteTrigger {action:list}` חשף את שורש שני הכשלים:

| # | בלוקר | ראיה ב-config הפיילוט | תיקון |
|---|-------|----------------------|-------|
| B1 | **אין GitHub auth** | `mcp_connections` = רק `Google-Drive`; אין token/SSH → push נכשל | התקנת **Claude GitHub App** על הריפו (Part B) |
| B2 | **אין `sources` רשום** | `session_context` מכיל רק `allowed_tools` + `autofix_on_pr_create` — **אין שדה `sources`** → signing service מחזיר **400 missing source** | רישום `sources` ב-config (Part A) |

**שורש:** ה-routine נוצר דרך `http_api` בלי השדה `sources` (שקיים במבנה ה-create הרשמי),
וללא חיבור GitHub ברמת-חשבון. שני התיקונים בלתי-תלויים — צריך את **שניהם**.

---

## 2. Part B — חיבור ידני בממשק claude.ai

> זהו החלק שעמיחי מבצע ידנית. לא ניתן לאוטומציה מה-CLI ולא לאימות מהזיכרון.

### Part B1 — התקנת Claude GitHub App
1. התקן את **Claude GitHub App** על `projects5069-creator/ridinghigh-pro`.
2. הרשאות write נדרשות: **Contents** + **Pull requests**.
3. **least-privilege:** הגבל את ה-App ל-**repo היחיד הזה** — לא "All repositories", לא org/admin.

⚠️ **אזהרת באג #57009:** חיבור **OAuth-בלבד** (בלי התקנת App) הוא נתיב רעוע ומחזיר **403**
ב-push. הקריטריון הקובע (AC1) הוא **התקנת ה-App**, לא חיבור OAuth.

### Part B2 — API trigger + bearer token
1. הקם **API trigger persistent** על ה-routine.
2. הפק **bearer token** עבורו.
3. ה-token מאפשר קריאת **`/fire`** שיורה את ה-routine ומחזירה **session URL**.

> ℹ️ **`/fire` = שכבת foundation ל-Agent #8, נפרד ממנגנון הטסט (`action:run`).** הטסט של TASK-93
> רץ על `action:run` המתועד (§4); B2 כאן מתעד את `/fire` לשימוש עתידי, לא נדרש לטסט הזה.

> ⚠️ **לא מאומת מ-skill `schedule`** (per עמיחי / claude.ai UI): המבנה המדויק של ה-API
> trigger, אופן הפקת ה-token (UI בלבד או פעולת-API), ו-endpoint ה-`/fire` — **אינם
> מתועדים בסקיל**. הסקיל מתעד רק `list/get/create/update/run` + שדה `api_token_hint`
> ב-trigger object, בלי דרך מתועדת ליצור/לצרוך אותו. **לאמת בממשק לפני שימוש — לא להמציא.**

---

## 3. Part A — Routine config עם `sources` (בשליטת הסוכן)

מבנה ה-create הרשמי (מתוך skill `schedule`) כולל את השדה שחסר בפיילוט:

```json
"session_context": {
  "sources": [{"git_repository": {"url": "https://github.com/projects5069-creator/ridinghigh-pro"}}],
  "...": "..."
}
```

זה מבטל את "400 missing source" (B2). ה-JSON המלא — בסעיף 5 (Staged config).

---

## 4. אימות — טסט דו-שלבי דרך `action:run` (הרצף המתועד בסקיל)

```text
1. RemoteTrigger create — routine עם sources (Part A) + trigger=run_once_at
     רחוק בעתיד (כדי שלא יירה אוטומטית); event=prompt ה-PROBE        # פעם אחת
2. RemoteTrigger action:run — ירי PROBE ידני (push branch claude/* בלבד)
     ✓ branch claude/task-93-conn-test נדחף, ללא 403, בלי PR, main לא נגוע
3. RemoteTrigger action:update — job_config עם event=prompt ה-FULL
4. RemoteTrigger action:run — ירי FULL (פותח PR)
     ✓ PR נפתח מ-claude/* מול main, ללא merge
5. קריאת תוצאה: PR מ-`gh pr list` / claude.ai UI
     (הסקיל לא מתעד שדה-תגובה ל-run עם PR URL — קוראים מ-gh/UI)
6. ניקוי: סגור PR + מחק branch claude/* (אין יתום)
```

> רצף מתועד: `create → run → update → run`. `run` עם body-override של ה-prompt קיים תיאורטית
> (body אופציונלי) אך **לא מאומת בסקיל** — לכן משתמשים ב-`update` בין שני ה-ירי.

קריטריון מעבר: PROBE דוחף branch **ללא 403** → FULL פותח **PR** מ-claude/* מול main, הכל ללא `git push` מקומי.

---

## 5. Staged prompts — PROBE + FULL (NOT fired)

> ⚠️ שני ה-prompts **מוכנים בלבד**. לא נוצר routine, לא נורה `/fire`.
> הרצה רק אחרי (א) Part B1+B2 מותקנים, (ב) אישור מפורש מעמיחי.
> רצף: create routine (עם `sources`) → `/fire` PROBE → `/fire` FULL.
> כל prompt משנה רק `docs/.routine_conn_test`. PROBE = push בלבד; FULL = פותח PR, **DO NOT merge**.

**גוף ה-event ל-PROBE** (push branch claude/* בלבד, ללא PR):
```json
{
  "data": {
    "uuid": "6b23e9fa-61b2-4fa8-b8d3-d0f564d4ddcd",
    "session_id": "",
    "type": "user",
    "parent_tool_use_id": null,
    "message": {
      "role": "user",
      "content": "# ROUTINE: TASK-93 connectivity PROBE (push only)\n\n## Context\nRepo: projects5069-creator/ridinghigh-pro (fresh clone from main). Run `pwd` first; only read/write inside this repo.\nGoal: prove the routine can PUSH a branch end-to-end. Push only — DO NOT open a PR.\n\n## Steps\n1. `pwd`.\n2. Create branch `claude/task-93-conn-test`.\n3. Create file `docs/.routine_conn_test` with a single line: `TASK-93 connectivity test`.\n4. `git add docs/.routine_conn_test` and commit.\n5. Push the branch `claude/task-93-conn-test` only.\n6. Report the branch name and the push result.\n\n## Constraints\n- DO NOT open a PR. DO NOT push to main. Change ONLY docs/.routine_conn_test.\n\n## Output\nReport branch name + push result (success / 403 / other error)."
    }
  }
}
```

**גוף ה-event ל-FULL** (פותח PR מ-claude/* מול main):
```json
{
  "data": {
    "uuid": "e13f3acc-11f3-4c37-bd05-7f992ba0d704",
    "session_id": "",
    "type": "user",
    "parent_tool_use_id": null,
    "message": {
      "role": "user",
      "content": "# ROUTINE: TASK-93 routine connectivity test\n\n## Context\nRepo: projects5069-creator/ridinghigh-pro (fresh clone from main). Run `pwd` first; only read/write inside this repo.\nGoal: prove the routine can push a branch and open a PR end-to-end. This is a connectivity test only.\n\n## Steps\n1. `pwd`.\n2. Create a trivial file `docs/.routine_conn_test` containing a single line: `TASK-93 connectivity test`.\n3. Commit on branch `claude/task-93-conn-test`.\n4. Open a PR against `main` titled \"TASK-93 routine connectivity test\".\n\n## Constraints\n- DO NOT merge. DO NOT push to main. Stop after the PR is open.\n- Change ONLY docs/.routine_conn_test. Touch nothing else.\n\n## Output\nReport the PR URL."
    }
  }
}
```

**Routine create body** (פעם אחת, לפני ה-fires) — מבנה מאומת מ-skill `schedule`:
```json
{
  "name": "TASK-93-conn-test",
  "enabled": true,
  "mcp_connections": [],
  "job_config": {
    "ccr": {
      "environment_id": "env_01MwpWU23pSE8busGnwDfyPq",
      "session_context": {
        "model": "claude-sonnet-4-6",
        "sources": [
          {"git_repository": {"url": "https://github.com/projects5069-creator/ridinghigh-pro"}}
        ],
        "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
      }
    }
  }
}
```

> UUIDs טריים: PROBE `6b23e9fa-…`, FULL `e13f3acc-…`. לחדש UUID לכל fire/create חדש.
> ⚠️ אופן הצמדת prompt ל-`/fire` והפעלתו — per Part B2 (לא מתועד בסקיל, לאמת בממשק).

---

## 6. הערות

- **Least-privilege מובנה (AC4ב):** מעבר להגבלת ה-App לריפו יחיד, ה-push בענן מוגבל ל-working
  branch ע"י proxy התשתית — ברירת מחדל מובנית, לא ניתן לדחוף ישירות ל-main.
- **תקרת ריצות ל-`action:run` — לא מתועד בסקיל, לאמת.** (הסקיל מתעד תקרות רק ל-cron: מינימום אינטרוול שעה, `*/30` נדחה — לא רלוונטי ל-action:run ידני.)
- **ניקוי חובה:** TASK-93 נסגר Done רק אחרי שה-test PR נצפה פתוח **ואז נוקה** — אין branch/PR יתום.

---

*נכתב במסגרת TASK-93. מצביע על מקורות חיים (config הפיילוט, skill schedule) — לא משכפל עובדות מתיישנות.*
