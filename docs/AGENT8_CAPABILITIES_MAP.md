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

## 3. 🔓 הפער הייחודי של עמיחי *(פתוח לדיון)*

כלי 1–9 הם סוקרי-קוד גנריים. **ליבת Agent #8 (first-class)** היא דווקא מה שאף כלי מהמדף לא מכסה — בדיקות מודעות-לחוקי-RidingHigh. סקירת-הקוד הגנרית היא המשנית.

**ליבה א — ציות ל-7 כללי הבטיחות (`RUN_MODE_DECISION.md` §7):**
- נגעה הרוטינה ב**נתיב אסור**? (`config.py`, `formulas.py`, `~/.claude/skills/*`)
- היה **push ל-main / merge**? (אסור בלילה — branch+PR בלבד)
- חרגה מ**תקרת הלילה** (3 משימות, branch לכל אחת)?
- נשארה **Group-A** (repo-scoped, בלי FINVIZ/news/Sheets)?

**ליבה ב — Drift ספציפי-למערכת:**
- חוזה **Anti-Drift** — אם נגעה בנוסחאות/workflows/config: עודכן PK (bump+changelog)?
- **PROJECT_STATE.md** עקבי מול מה שבוצע?

**ליבה ג — פער "התבקש מול בוצע":**
- דו"ח עברי **מאוחד רב-ענפי** — מה התבקש בכל branch-לילה מול מה שבוצע בפועל (לא סקירת-diff נקודתית per-PR).

**משני — סקירת-קוד גנרית:** איכות/באגים/כפילות (מ-`/code-review`, `/simplify`).

> **🔓 דורש החלטות עמיחי לפני בנייה:** הרשימה המדויקת של auto-safe paths · ניסוח הבדיקות לכל כלל-בטיחות · פורמט דו"ח-הבוקר. סעיף זה ייסגר ב-TASK-94 עם agent-builder.

---

## 4. המלצה ל-TASK-94 — מאילו מקורות לבנות את #8

**בנה את #8 מ:**
- **🏗️ Backbone (✅ מאומת R):** RemoteTrigger / `/schedule` — הרצת-ענן רב-ענפית (TASK-93-proven, PR #10). מאתר את branch-ים של הלילה.
- **🔍 מנוע סקירה (⚠️ זמינות headless טרם אומתה):** `/code-review` (diff) + `/simplify` (איכות) — שכבת ה"משני". **אזהרה:** שניהם S:✅·R:❓ בטבלה; #8 רץ headless ב-routine — חובה לאמת זמינותם ב-routine לפני הסתמכות.
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
