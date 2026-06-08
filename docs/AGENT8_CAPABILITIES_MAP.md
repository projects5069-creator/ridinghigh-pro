# Agent #8 — Routine Checker: מפת יכולות (קלט לבנייה)
*תוצר TASK-95. מזין את TASK-94 (בניית Agent #8).*
*נכתב 2026-06-07. repo-scoped בלבד — אפס קוד/Sheets/ענן/FINVIZ/news.*

---

## 1. מטרה — מה Agent #8 עושה

**Agent #8 = "Routine Checker".** בקרת איכות על **עבודת-פיתוח אוטונומית שנעשתה בלילה** ע"י רוטינות ענן (אחרי TASK-93). מפיק **דו"ח-בוקר עברי יחיד** לעמיחי:
- מה התבקש · מה בוצע בפועל · אילו פערים/דילמות עלו · ציון/verdict איכות.

**תפקיד: דיווח-בלבד (read-only).** מסמן verdict (Ready / Needs-Attention / Needs-Work) ומסביר — **אינו חוסם merge ואינו עורך**. עמיחי מכריע בבוקר.

**מה Agent #8 *אינו*:** הוא **לא** The Critic. The Critic = סיכומי **מסחר** (יומי/שבועי/חודשי, ויזואליזציה). Agent #8 = בקרת **עבודת-פיתוח/קוד**. שני סוכנים נפרדים.

**זמן ריצה מקובל:** 10–30 דק', עמיחי ממתין. הפעלה: אוטומטית כל בוקר אחרי רוטינות-לילה, או ידנית (כשאין ריצת לילה).

---

## 2. טבלת 9 המקורות

עמודת "זמין?" = 3-מצבים (✅ מאומת-חי · ⚠️ חלקי · ❌ reference-only) × 2-סביבות:
**S** = סשן אינטראקטיבי (CC נוכחי) · **R** = cloud-routine (ההקשר ש-#8 ירוץ בו, headless).
האימות נעשה חי (2026-06-07) מול רשימת הסקילים בסשן, רשימת `subagent_type` ב-Agent tool, וכלים deferred.

| # | מקור | מה עושה | זמין? (S / R) | לאמץ ל-#8? |
|---|------|---------|---------------|------------|
| 1 | **Code Review** (auto-PR) | סקירת diff מקבילה, זיהוי באגים, דירוג חומרה, סיכום+הערות inline | **S:✅** (`/code-review` ברשימת הסקילים) · **R:❓** לא אומת ל-headless · ⚠️ "auto-on-PR / Max plan / ultra בענן" = **השערה לא-מאומתת** (אי-אפשר לאמת tier) | כן — מנוע סקירת diff (משני) |
| 2 | **custom `code-reviewer`** subagent | פרסונת-סוקר מוגדרת (frontmatter+system-prompt) ב-`.claude/agents/` | **S:⚠️ · R:⚠️** — **אין** subagent_type מובנה `code-reviewer` (קיימים: claude/Explore/general-purpose/Plan/claude-code-guide/statusline-setup); הפיצ'ר קיים דרך `.claude/agents/` + תבנית superpowers `requesting-code-review`. דורש הגדרה | כן — פרסונת הסוקר של #8 |
| 3 | **HAMY** (9 reviewers) | 9 סוקרים מקבילים → verdict: Ready-to-Merge / Needs-Attention / Needs-Work | **❌ · ❌** — reference-only, אין התקנה מקומית | דפוס בלבד — אימוץ ה-verdict-pattern |
| 4 | **/simplify** | 3 סוקרים (כפילות/איכות/פישוט) מאוחדים לדו"ח | **S:✅** (`/simplify` ברשימת הסקילים) · **R:❓** לא אומת ל-headless | משני — בדיקת איכות משלימה |
| 5 | **VoltAgent** (awesome-claude-code-subagents) | ספריית 100+ סוכנים מוכנים כולל code-reviewer | **❌ · ❌** — reference-only, לא מותקן | מקור-השראה — לייבא פרסונה אם צריך |
| 6 | **/loop** | הרצה חוזרת במרווח (סקירת-בוקר / commits) | **S:✅** (`/loop` ברשימת הסקילים) · **R:↔️** מוחלף ב-cron/RemoteTrigger (לא /loop) | חלקי — חיווט טריגר (לא ב-routine) |
| 7 | **/goal** | לולאה עד תנאי-סיום; בדיקת Haiku בכל סבב | **S:⚠️ · R:⚠️** — **אינו סקיל מקומי**; מצב-ריצה harness המתועד ב-`RUN_MODE_DECISION.md`/`NIGHT_RUN_TEMPLATE.md` בלבד. לא אומת חי כסקיל | חלקי — מצב-ריצה, לא רכיב |
| 8 | **Dispatch / RemoteTrigger** | רוטינת-ענן: `create→run→update→run`, push+PR אוטונומי | **S:✅ · R:✅** — RemoteTrigger = deferred tool נוכח · `/schedule` ברשימת הסקילים · **TASK-93 הוכיח end-to-end (PR #10)** | כן — **backbone** הביצוע של #8 |
| 9 | **auto wrap-up** | סיכום-סוף-ריצה שה-CC מפיק אוטומטית | **S:⚠️ · R:⚠️** — אין סקיל ייעודי; תוצר-לוואי: context auto-summary + הטקסט-הסופי של ריצה (TASK-93 runbook) + ריטואל Session Close (מופעל-בכוונה) | כן — הטקסט-הסופי = דו"ח-הבוקר |

**סיכום זמינות (מול נרטיב "7/9 חי" שב-handoff — מתוקן לפי אימות-חי):**
- ✅ מאומת-חי בסשן: **4** (#1, #4, #6, #8)
- ⚠️ חלקי / לא-סקיל: **3** (#2, #7, #9)
- ❌ reference-only: **2** (#3, #5)
- ב-routine (headless): רק **#8** מאומת ✅; השאר ❓/⚠️ — זמינות headless טרם נבדקה.

---

## 3. ליבת Agent #8 — בדיקות מודעות-לחוקי-RidingHigh *(סגור, TASK-94 v1)*

כלי 1–9 הם סוקרי-קוד גנריים. **ליבת #8 (first-class)** היא מה שאף כלי מהמדף לא מכסה: בדיקות מודעות לחוקי-הבטיחות של ריצת-לילה. v1 = **ליבה-בלבד (מסלול ב — פרסונת-סוקר ב-prompt)**; סקירה גנרית (`/code-review`+`/simplify`) נדחתה ל-v2 כשכבת-משני, מותנית באימות headless (TASK משני לא-חוסם).

---

### 3.1 — auto-safe paths (רשימה שאוכפת ליבה א)

| רשימה | נתיבים | תגובת #8 |
|---|---|---|
| 🔴 **אסור** | `config.py` · `formulas.py` · `~/.claude/skills/*` · `.github/workflows/*` · `orchestrator.py` | נגיעה → **CRITICAL** (Needs-Work) |
| 🟢 **ירוק (safe)** | `docs/` · `tests/` · `backlog/` · `research/` · `scripts/` (לא-core) | מותר ללא דגל |
| 🟡 **אפור** | `dashboard.py` · `utils.py` · `auto_scanner.py` | **WARNING** (Needs-Attention), לא חוסם |

**הרחבה מעבר ל-`RUN_MODE_DECISION.md §7.2` המקורי:** `.github/workflows/*` + `orchestrator.py` נוספו לרשימה ה-🔴 (CI יכול להריץ מסחר חי; orchestrator = ליבת-מסחר). **חוק ברזל:** ההרחבה נכתבה גם ב-`RUN_MODE_DECISION.md §7.2` וב-`NIGHT_RUN_TEMPLATE.md` — לא רק בלוגיקת #8 — כדי למנוע drift בין מה ש-#8 אוכף למה שהמסמך מגדיר.

---

### 3.2 — ניסוח הבדיקות ל-7 כללי הבטיחות (read-only verdict, לא enforcer)

| כלל (§7) | בדיקת #8 | סוג | רמה |
|---|---|---|---|
| 1 — אין push/merge ל-main | main HEAD לא זז · קיים `night/*` · PR פתוח לא-merged | git state | **קשיח ✅** |
| 2 — נתיבים אסורים | `git diff --name-only main..branch` ∩ 🔴 = ∅ | diff | **קשיח ✅** |
| 6 — תקרת לילה (3 משימות, branch לכל) | ספירת `night/*` בחלון ≤ 3 · משימה=branch ייחודי | git state | **קשיח ✅** |
| 3 — Group A (אין IO חיצוני) | grep בקוד-שנוסף ל-finviz/gspread/news/requests | static | best-effort ⚠️ |
| 4 — /goal עם תנאי מדיד | קריאת prompt/config הרוטינה — תנאי-סיום קונקרטי | routine metadata | best-effort ⚠️ |
| 5 — ספי עצירה (3/20) | קריאת wrap-up/log — האם נעצר בזמן | run log | best-effort ⚠️ |
| 7 — תקופת מבחן בפיקוח | דגל policy — שורת-תזכורת | meta | תזכורת ↔️ |

**חוקי-דיווח:** קשיח (1/2/6) = מ-git, ודאי. best-effort (3/4/5) = כשחסר prompt/log, #8 מדווח עם הסתייגות מפורשת **"לא-ודאי — חסר metadata"** ולא קובע verdict שלילי על-בסיסם. כלל 7 = שורת-תזכורת בלבד. #8 לעולם **לא חוסם merge ולא עורך** — verdict בלבד.

---

### 3.3 — פורמט דו"ח-הבוקר העברי (מאוחד רב-ענפי)

```
🌅 דו"ח-בוקר Agent #8 — <תאריך>
verdict כולל: Ready / Needs-Attention / Needs-Work · N branches נבדקו
─────────────
לכל branch (night/TASK-NN):
  📌 מה התבקש  — config הרוטינה / גוף ה-TASK
  ✅ מה בוצע   — commits · קבצים · סיכום diff
  🛡️ 7-כללי בטיחות — טבלת pass/flag (§3.2)
  ⚠️ פערים/דילמות
  🎯 verdict ל-branch
─────────────
🔚 שורה תחתונה — אילו PRs לאשר/לעכב (פעולה לעמיחי)
```

**granularity:** verdict לכל branch בנפרד **+** verdict כולל ללילה.
**ערוץ מסירה v1:** הטקסט-הסופי של ריצת #8 (auto-wrap-up, מקור #9) = הדו"ח עצמו. ללא תשתית מייל ב-v1. עקבי עם תבנית-התגובה `rhpro-live §6` (סיכום → פירוט → דגלים → המלצה).

---

### 3.4 — דגלים ל-scope הבנייה (TASK-94)
1. עדכון `RUN_MODE_DECISION.md §7.2` + `NIGHT_RUN_TEMPLATE.md` עם הנתיבים האסורים החדשים (Anti-Drift) — **בוצע ב-94a**.
2. גישה ל-routine metadata (prompt/log) דרך `RemoteTrigger`/session-context — תנאי ל-best-effort של כללים 3/4/5 (94c).

---

## 4. המלצה ל-TASK-94 — מאילו מקורות לבנות את #8

**בנה את #8 מ:**
- **🏗️ Backbone (✅ מאומת R):** RemoteTrigger / `/schedule` — הרצת-ענן רב-ענפית (TASK-93-proven, PR #10). מאתר את branch-ים של הלילה.
- **🔍 מנוע סקירה — נדחה ל-v2 (לא ב-v1):** `/code-review` (diff) + `/simplify` (איכות) = שכבת ה"משני". v1 = ליבה-בלבד (מסלול ב, ראה §3). הסתמכות עליהם מותנית באימות זמינות headless ב-routine — נרשם כ-TASK משני לא-חוסם, ירד מהנתיב הקריטי.
- **🎭 פרסונת-סוקר (⚠️ לבנות):** custom `code-reviewer` ב-`.claude/agents/` עם system-prompt **מודע-לחוקי-RidingHigh** — כאן נכנסת ליבה א+ב.
- **📋 דו"ח-בוקר (⚠️):** auto-wrap-up — הטקסט-הסופי = הדו"ח העברי המאוחד (ליבה ג).
- **⚙️ טריגר (⚠️):** `/goal`+auto-mode (מצב-ריצה, בכפוף לאימות זמינות ב-routine).

**דפוסים להשאלה (❌ reference):**
- **HAMY** → verdict-pattern (Ready / Needs-Attention / Needs-Work) — כבר אומץ ב-#8.
- **VoltAgent** → לייבא פרסונת code-reviewer אם צריך בסיס.

**הפער שנשאר לבנות ידנית:** ליבה א+ב+ג — אין כלי מהמדף שיודע את חוקי RidingHigh. זה ה-system-prompt של פרסונת-הסוקר + לוגיקת-החיווט.

**תלות:** TASK-93 (creds ענן) לביצוע מלא headless.

---

*— END —*
