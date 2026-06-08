# Agent #8 — Morning Routine Runbook (מסילת בקרת-בוקר ענן)
*תוצר TASK-94.3. סוגר את epic Agent #8 (Routine Checker).*
*מצביע על מקורות חיים — TASK-93_ROUTINE_RUNBOOK (מנגנון ענן) · AGENT8_CAPABILITIES_MAP §3 (כללים+פורמט) · .claude/agents/rh-routine-checker.md (הפרסונה). לא משכפל עובדות מתיישנות.*

---

## 0. ⛔ תנאי-קבלה חוסם (Phase 0 — לפני הפעלה בפועל)
מסילה זו **מניחה ש-`rh-routine-checker` נטען כ-subagent_type אמיתי**. אימות הטעינה
(Phase 0) הוא **תנאי חוסם לפני הפעלה בפועל** — ב-94.2 אומת רק איכות-ה-prompt דרך
`general-purpose` מוטמע; הפרסונה **טרם אומתה כ-subagent** (`.claude/agents` נטען רק ב-reload).
**ייאומת אחרי reload** (`Task(subagent_type: rh-routine-checker)` על branch-בדיקה → לא
`not found`, פלט §3.3). עד שגייט-0 עובר — מסילה זו **תיעוד בלבד, לא להפעיל**.

---

## 1. מטרה
כל בוקר (אחרי עבודת-לילה אוטונומית): לגלות את ה-`night/*` branches, להריץ עליהם את
פרסונת-הסוקר read-only, ולהפיק **דו"ח-בוקר עברי יחיד מאוחד** (§3.3) — מה התבקש · מה בוצע ·
פערים · verdict per-branch + overall. read-only verdict; עמיחי מכריע בבוקר.

## 2. זרימת המסילה (מבוצעת ע"י סוכן-הענן אחרי clone טרי)
1. **גילוי `night/*`:** `git fetch --all` → `git branch -r | grep 'origin/night/'` → רשימת branches.
   אם הרשימה ריקה → דו"ח "אין עבודת-לילה לבדוק", verdict כולל = N/A, סיום.
2. **הרצת פרסונה per-branch:** לכל `origin/night/TASK-NN`, הפעל
   `Task(subagent_type: rh-routine-checker)` עם base=`main` · head=ה-branch → דו"ח §3.3 per-branch.
3. **איחוד → דו"ח אחד** (סעיף 3).
4. **מסירה:** הטקסט-הסופי של הריצה = הדו"ח (auto-wrap-up). בלי מייל (v1).

## 3. כלל האיחוד (overall verdict)
- ולו branch אחד **Needs-Work** → overall **Needs-Work**.
- אחרת אם יש **Needs-Attention** → overall **Needs-Attention**.
- אחרת → **Ready**.

מבנה הדו"ח המאוחד (פורמט §3.3 של AGENT8_CAPABILITIES_MAP):
```
🌅 דו"ח-בוקר Agent #8 — <תאריך>
verdict כולל: <Ready | Needs-Attention | Needs-Work> · N branches נבדקו
─────────────
[בלוק per-branch מלא לכל night/TASK-NN — 📌 התבקש · ✅ בוצע · 🛡️ טבלת-7 · ⚠️ פערים · 🎯 verdict]
─────────────
🔚 שורה תחתונה — אילו PRs לאשר/לעכב (פעולה לעמיחי)
```

## 4. ערוץ מסירה (v1)
הטקסט-הסופי של ריצת-הרוטינה (auto-wrap-up, מקור #9 במפה) = הדו"ח עצמו.
**ללא תשתית מייל ב-v1.** עקבי עם תבנית-התגובה `rhpro-live §6` (סיכום → פירוט → דגלים → המלצה).

## 5. Routine config — staged / לא-פעיל
> ⚠️ **staged בלבד — `enabled: false`. אין שום הוראת-הפעלה אוטומטית.**
> הרצה רק אחרי (א) גייט-0 עבר, (ב) אישור מפורש (RULE #6), לפי דפוס `create → run PROBE
> → update → run FULL` של `TASK-93_ROUTINE_RUNBOOK §4`. UUID טרי לכל fire.

```json
{
  "name": "agent8-morning-checker",
  "enabled": false,
  "mcp_connections": [],
  "job_config": {
    "ccr": {
      "environment_id": "env_01MwpWU23pSE8busGnwDfyPq",
      "session_context": {
        "model": "claude-sonnet-4-6",
        "sources": [
          {"git_repository": {"url": "https://github.com/projects5069-creator/ridinghigh-pro"}}
        ],
        "allowed_tools": ["Bash", "Read", "Grep", "Glob", "Task"]
      }
    }
  }
}
```
> `allowed_tools` **קריאה-בלבד** — אין `Write`/`Edit` (Agent #8 = verdict-only). `Task` נדרש
> כדי להפעיל את ה-subagent `rh-routine-checker`. `Bash` מוגבל ל-git קריאה (diff/log/branch/fetch).

**event-prompt של מסילת-הבוקר** (גוף ה-`message.content` ב-event, כדפוס TASK-93 §5):
```
# ROUTINE: Agent #8 Morning Checker (read-only)

## Context
Repo: projects5069-creator/ridinghigh-pro (fresh clone from main). Run `pwd` first; read-only.
You are the orchestrator. For each night branch, dispatch the rh-routine-checker subagent.

## Steps
1. `pwd`; `git fetch --all`.
2. Discover branches: `git branch -r | grep 'origin/night/'`. If none → report "אין עבודת-לילה", stop.
3. For each origin/night/TASK-NN: invoke Task(subagent_type: rh-routine-checker) with
   base=main, head=that branch. Collect its §3.3 per-branch report.
4. Compute overall verdict (any Needs-Work → Needs-Work; else any Needs-Attention →
   Needs-Attention; else Ready).
5. Emit ONE unified Hebrew morning report (§3.3): header + per-branch blocks + bottom line.

## Constraints
- READ-ONLY — applies to BOTH you (the orchestrator) AND the rh-routine-checker subagent.
  Do NOT push, merge, edit, or open/close PRs. Do NOT touch main.
- Treat config.py, formulas.py, .github/workflows/*, orchestrator.py, ~/.claude/skills/* as
  forbidden — never modify. The rh-routine-checker subagent reads §3 of
  AGENT8_CAPABILITIES_MAP.md live for the full rule set.
- Your final message IS the morning report (auto-wrap-up delivery).

## Output
The unified §3.3 morning report in Hebrew.
```

## 6. Credentials — מצביע ל-TASK-93 (לא משכפל)
חיבור ה-GitHub (Claude GitHub App על הריפו, least-privilege) + API trigger/token כבר
מותקנים ומאומתים end-to-end ב-**TASK-93** (PR #10). ראה `docs/TASK-93_ROUTINE_RUNBOOK §2 (Part B)`.
מסילת-הבוקר היא **read-only** ולכן אינה זקוקה להרשאות-כתיבה ל-GitHub (אין push/PR) — רק clone.

---

## 7. הפעלה (אחרי גייט-0 + אישור RULE #6)
`create` (config סעיף 5, `run_once_at` רחוק) → `action:run` PROBE (גילוי + דו"ח קצר) →
בדיקה → (אם תקין) `action:update` ל-prompt המלא → `action:run` FULL. ניקוי: `enabled:false`
+ מחיקת branches זרוקים. **אף `/fire` ללא אישור.**

> 🏖️ הערת sandbox: כל פעולת-רשת (RemoteTrigger / git push / gh) חוסמת תחת ה-sandbox של Bash
> (`SSL_ERROR_SYSCALL`) — דורשת `dangerouslyDisableSandbox`. נצפה חי לאורך TASK-94.

*— END —*
