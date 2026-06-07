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

## 2. Part B — חיבור GitHub (ידני, בממשק claude.ai)

> זהו החלק שעמיחי מבצע ידנית. לא ניתן לאוטומציה מה-CLI ולא לאימות מהזיכרון.

1. התקן את **Claude GitHub App** על `projects5069-creator/ridinghigh-pro`.
2. הרשאות write נדרשות: **Contents** + **Pull requests**.
3. **least-privilege:** הגבל את ה-App ל-**repo היחיד הזה** — לא "All repositories", לא org/admin.

⚠️ **אזהרת באג #57009:** חיבור **OAuth-בלבד** (בלי התקנת App) הוא נתיב רעוע ומחזיר **403**
ב-push. הקריטריון הקובע (AC1) הוא **התקנת ה-App**, לא חיבור OAuth.

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

## 4. אימות (אחרי ש-Part B מותקן ו-Part A מוכן)

```text
1. /schedule → list           # ודא שה-routine קיים עם sources רשום
2. Run-once (RemoteTrigger run / או run_once_at עתידי)
3. בדוק session: last_fired_at מתעדכן, אין שגיאת 400/403
4. ודא PR: branch claude/* נפתח מול main, מוחזר PR URL — בלי push ידני
5. ניקוי: סגור PR + מחק branch claude/* (אין יתום)
```

קריטריון מעבר: **PR URL חוזר אוטומטית** + branch קיים בענן ללא שום `git push` מקומי.

---

## 5. Staged config — TASK-93-conn-test (NOT yet fired)

> ⚠️ זהו גוף ה-`RemoteTrigger {action:create}` **המוכן בלבד**. לא נוצר ולא נורה.
> הרצה רק אחרי (א) Part B מותקן, (ב) אישור מפורש מעמיחי.
> ה-prompt עושה שינוי טריוויאלי (`docs/.routine_conn_test`) ופותח PR — **DO NOT merge**.

```json
{
  "name": "TASK-93-conn-test",
  "run_once_at": "<RFC3339-UTC-future — לקבוע בזמן ההרצה דרך date -u>",
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
      },
      "events": [
        {"data": {
          "uuid": "e13f3acc-11f3-4c37-bd05-7f992ba0d704",
          "session_id": "",
          "type": "user",
          "parent_tool_use_id": null,
          "message": {
            "role": "user",
            "content": "# ROUTINE: TASK-93 routine connectivity test\n\n## Context\nRepo: projects5069-creator/ridinghigh-pro (fresh clone from main). Run `pwd` first; only read/write inside this repo.\nGoal: prove the routine can push a branch and open a PR end-to-end. This is a connectivity test only.\n\n## Steps\n1. `pwd`.\n2. Create a trivial file `docs/.routine_conn_test` containing a single line: `TASK-93 connectivity test`.\n3. Commit on branch `claude/task-93-conn-test`.\n4. Open a PR against `main` titled \"TASK-93 routine connectivity test\".\n\n## Constraints\n- DO NOT merge. DO NOT push to main. Stop after the PR is open.\n- Change ONLY docs/.routine_conn_test. Touch nothing else.\n\n## Output\nReport the PR URL."
          }
        }}
      ]
    }
  }
}
```

> UUID נוצר טרי (`e13f3acc-...`). אם תעבור יותר מ-run אחד — יש לחדש UUID לכל create.

---

## 6. הערות

- **Least-privilege מובנה (AC4ב):** מעבר להגבלת ה-App לריפו יחיד, ה-push בענן מוגבל ל-working
  branch ע"י proxy התשתית — ברירת מחדל מובנית, לא ניתן לדחוף ישירות ל-main.
- **תקרת ריצות:** ריצות **run-once** פטורות מתקרת ה-~15 routines/יום (זו תקרת recurring).
- **ניקוי חובה:** TASK-93 נסגר Done רק אחרי שה-test PR נצפה פתוח **ואז נוקה** — אין branch/PR יתום.

---

*נכתב במסגרת TASK-93. מצביע על מקורות חיים (config הפיילוט, skill schedule) — לא משכפל עובדות מתיישנות.*
