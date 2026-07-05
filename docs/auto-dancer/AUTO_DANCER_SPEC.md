# The Auto Dancer — SPEC v1 (M0)

| שדה | ערך |
|---|---|
| **סטטוס** | טיוטה — ממתין לאישור עמיחי (M0) |
| **תאריך** | 2026-07-04 |
| **בסיס** | recon חי 4/7 (gap-map) + PK v4.06 + בקלוג חי |
| **יחס לקיים** | אבולוציה של תשתית-הרנר `scripts/overnight/` — לא בנייה מאפס |
| **מקור-אמת** | הקוד/PK/בקלוג החיים. מסמך זה = תכנון; בכל סתירה עתידית — הקוד מנצח |

לכל רכיב במסמך מסומן מצב מול הקיים: **[קיים]** / **[להתאים]** / **[חדש]**.
אפס קוד נכתב בשלב M0. שום נגיעה ב-`scripts/overnight/*`, hooks, plists.

---

## 1. מטרה + הגדרת-הצלחה (SLO)

**מטרה:** לולאת-עבודה אוטונומית ("The Auto Dancer") שעמיחי מפעיל ידנית עם תור-משימות
שהכין, והיא עובדת מקצה-לקצה עד גבול-ה-commit. עמיחי עושה review + push בבוקר.

**ריצה מוצלחת (SLO):**
1. **תפוקה:** כל משימה בתור מסתיימת באחד מ-4 מצבים כנים: `READY` (verifier PASS +
   commit-מקומי-לענף) · `PARKED` (שאלה כתובה) · `NEEDS_HUMAN` (וטו-classifier) · `RED`
   (ניסיון שנכשל, ראיות נשמרו). ריצה עם 0 READY אבל parks נקיים = ריצה **תקינה**
   (park ≠ כישלון); שתי ריצות רצופות עם 0 READY → בחינת קריטריון-הסינון של התור.
2. **אפס-נזק:** אפס כתיבה ל-CORE_UNSAFE, אפס קריאת-secrets, אפס כתיבת-Sheets,
   אפס הרצת runner/scanner/collector.
3. **אפס-מגע-main:** working tree של main לא נגוע; **אפס push לכל branch שהוא**
   (כולל `overnight-reports` — ראה §8).
4. **כל תוצר = commit מקומי לענף `auto-dancer/<TASK>` בתוך worktree מבודד בלבד.**
5. **תקציב נשמר:** cap פר-משימה (מהתור) + cap פר-ריצה (§7).

---

## 2. מודל-ההפעלה

- **Trigger ידני בלבד, בכל שעה.** עמיחי מריץ את ה-entrypoint מתי שרוצה, כולל ביום.
  אין launchd, אין cron, אין ירייה מתוזמנת. ה-plists נשארים `.disabled` (מאומת 4/7:
  `launchctl print` → not found; רק `.disabled`+`.bak` ב-LaunchAgents).
- **`guard_night_window` מבוטל ב-trigger ידני** — re-scope מהעיצוב הישן (4/7). הרציונל
  המקורי היה חסימת deferred-run של launchd; בלי launchd אין deferred-run. **[להתאים]**
  (rh-overnight.sh:130 — עוקף במצב ידני; שאר השערים נשארים).
- **שערים שנשארים כמות-שהם [קיים]:** `guard_no_api_key` (חיוב-subscription בלבד) ·
  `guard_clean_secret_env` (סקראב env) · `guard_base_ready` (עץ נקי + base קיים) ·
  **base GREEN** (suite ירוק לפני בנייה; ABORT אם RED) · smoke-auth מה-Keychain.

---

## 3. תור-הכניסה (QUEUE)

**קובץ markdown פר-ריצה:** `docs/auto-dancer/queue/QUEUE_YYYY-MM-DD.md` **[חדש]**

```markdown
# AUTO_DANCER QUEUE 2026-07-05
# סדר-השורות = סדר-הביצוע. שורה = משימה.
- TASK-159 | budget: 120k | note: wire-or-remove בלבד; אם ההכרעה דורשת שיקול-מסחר → PARK
- TASK-228 | budget: 80k  | note: בידוד דליפת-state בטסט; אסור לגעת בקוד production
```

**שדות-שורה:** `TASK-ID` (חייב להתקיים בבקלוג) · `budget:` cap-טוקנים למשימה
(ברירת-מחדל 150k אם הושמט) · `note:` אילוצים/רמזים/גבולות שעמיחי מכתיב ·
אופציונלי `files:` רמז לרשימת-קבצים (ה-PLANNER עדיין מחויב לגזור רשימה מלאה בעצמו).

**סדר-עבודה מפורש:**
1. **עמיחי מסנן בעצמו** כל מועמדת מול קריטריון "מתאימה-לעבודה-עצמאית" **לפני** השליחה:
   תחומה וקונקרטית · בלי כוונת-CORE_UNSAFE · בלי קריאת-דאטה-חי/secrets · ניתנת-לבדיקה
   בטסט. הסינון-האנושי הוא הפתרון לממצא 6/20 (auto-discovery סיווג 59/59 needs_human —
   תור-גילוי-אוטומטי ריק בפועל).
2. **ה-classifier (`classify_task.md`) נשאר שכבת-וטו fail-closed מעל הבחירה שלו — לא
   במקומה. [קיים→להתאים]** וטו → המשימה נרשמת `NEEDS_HUMAN` בדוח + הלולאה ממשיכה.
   הוא לעולם לא מרחיב את התור (תפקיד-ה-discovery של `triage_filter.py` פורש מהזרימה
   הזו; הקובץ נשאר לשימושי triage-only עתידיים).
3. **פתוח ל-M1 (הכרעה):** קובץ-QUEUE לא-committed מלכלך את העץ ומפיל את
   `guard_base_ready`. המלצה: `docs/auto-dancer/queue/` נכנס ל-`.gitignore` (כמו
   `docs/overnight/raw/`); חלופה: עמיחי עושה לו commit בסגירת-היום.

---

## 4. ארבעת התפקידים (RPI)

**משותף:** כל שלב = קריאת `claude -p` **טרייה** (context טרי פר-שלב — מתחת ל-Dumb-Zone),
תחת settings-הלילה (hooks `block_secrets` + `block_core_unsafe` פעילים **[קיים]**),
בתוך ה-worktree של המשימה. artifacts עוברים בין שלבים דרך קבצים (§9), לא דרך שיחה.
המודל לעולם לא מריץ פקודות-git-כותבות (§5 FORBIDDEN-FLOOR).

### 4.1 PLANNER — Opus **[חדש]**
| | |
|---|---|
| קלט | גוף-המשימה + note מהתור + הריפו (קריאה בלבד) |
| פלט | `plan.md`: (א) research-log — **עובדות בלבד** עם ראיות file:line, בלי דעות ובלי החלטות-מימוש מוקדמות; (ב) **רשימת-קבצים-מותרים** מפורשת (כולל קובצי-טסט); (ג) אסטרטגיית-טסטים — איזה טסט-אדום מוכיח את הבאג; (ד) **משפט-"done" חד-משמעי** וניתן-לבדיקה; (ה) הערכת הפיכוּת/סיכון לפי מטריצת-§5 |
| מותר | Read, Grep, Glob, Bash קריאה-בלבד (git log/show, pytest --collect-only) |
| אסור | **כל כתיבת-קוד**; Edit/Write; המלצת-מימוש שאינה נגזרת מעובדה מתועדת |
| מודל | Opus (`PLAN_MODEL=opus`) |

### 4.2 CRITIC — Opus **[חדש]** (מחליף את ה-self-review שבתוך `execute_task.md`)
| | |
|---|---|
| קלט | המשימה + ה-artifact של השלב הנבדק בלבד: אחרי-PLAN → `plan.md`; אחרי-EXECUTE → diff + פלט-טסטים. רץ **בין כל שני שלבים**, לא רק בסוף |
| פלט | `critique-N.json`: `{verdict: pass\|bounce, issues:[{issue, severity, evidence, suggested_fix}]}` |
| ראיית-כלי (חובה) | **חייב להריץ כלי אמת (pytest ממוקד / git diff) ולצרף את הפלט כראיה ב-verdict. verdict בלי ראיית-כלי = fail-closed** — בודק בלי כלים רק מהדהד את היוצר; כלי דטרמיניסטי מונע "לדבר אותו" לאישור |
| כלל | **fail-closed:** לא הצליח לאמת → `bounce` (צעד אחורה עם נימוק), לא pass. סבב חוזר עד 5 סבבים → PARK (§6) |
| מותר | Read, Grep, Glob, Bash קריאה-בלבד |
| אסור | לתקן בעצמו; Edit/Write; "לאשר בהסתייגות" |
| מודל | Opus (`CRITIC_MODEL=opus`) |

### 4.3 EXECUTOR — Sonnet **[קיים→להתאים]** (מ-`execute_task.md` שלבים 1-4; שלבי commit/push/PR נחתכים)
| | |
|---|---|
| קלט | **התוכנית המאושרת בלבד** (`plan.md` + `critique` pass) — לא שיחת-ה-PLANNER |
| פלט | diff בעץ-ה-worktree + תוצאות-טסטים + `execution.json` |
| מותר | לפי-התוכנית בלבד: TDD RED→GREEN · **str_replace בלבד** (לא full-file) · backup מתוארך לפני עריכת-קובץ-קיים · `py_compile` אחרי · pytest ממוקד |
| אסור | git commit/push/add · קובץ מחוץ ל-whitelist · שינוי-התוכנית · שינוי-טסט-כדי-שיעבור (RULE #9) · CORE_UNSAFE (hook **[קיים]**) |
| Scope-lock | רשימת-הקבצים מ-`plan.md` נאכפת **מכנית** — hook/deny-rules פר-משימה שמג'ונרטים מהתוכנית **[חדש, פירוט-מימוש ב-M2]**; בנוסף ל-`block_core_unsafe.sh`+`block_secrets.sh` הקיימים |
| מודל | Sonnet (`EXEC_MODEL=sonnet` **[קיים]**) |

### 4.4 VERIFIER — Opus **[חדש]**
| | |
|---|---|
| קלט | **תיאור-המשימה + `git diff` + פלט-הרצת-הטסטים בלבד — לעולם לא את השיחה.** בידוד = נטרול self-reporting bias והטיית-הסכמה-עם-הקודם |
| פלט | `verify.json`: `{verdict: ready\|reject, checks: {scope_match, tests_green_evidence, core_unsafe_untouched, done_sentence_met}, issues:[{issue, severity, evidence, suggested_fix}]}` |
| ראיית-כלי (חובה) | **חייב להריץ כלי אמת (pytest ממוקד / git diff) ולצרף את הפלט כראיה ב-verdict. verdict בלי ראיית-כלי = fail-closed** — בודק בלי כלים רק מהדהד את המבצע; כלי דטרמיניסטי מונע "לדבר אותו" לאישור |
| תפקיד | השער האחרון פר-משימה: `ready` → ה-orchestrator עושה commit מקומי (§8); `reject` → bounce (נספר ל-stuck-loop §6) |
| מודל | Opus (`VERIFY_MODEL=opus`) |
| הערה | **נפרד מ-Agent #8** (`rh-routine-checker`) — #8 נשאר כלי-הבוקר של עמיחי, ללא שינוי (הוא גם בנוי ל-branch בשם `night/*`; ה-Dancer יוצר `auto-dancer/*` — אי-התאמה מכוונת, שני כלים שונים) |

---

## 5. מטריצת-סמכות-החלטה

**טופולוגיה: pipeline סדרתי — משימה-אחת-בכל-פעם ב-worktree מבודד. אין ריצה מקבילה,
ולכן אין collision על shared-state (מקור-הכשל מספר-1 במערכות רב-סוכן). תואם דפוס
Composio-AO המוכח בפרודקשן.**

שלושה צירים; **AUTO רק אם שלושתם ירוקים** — אחרת PARK + escalate:

| ציר | ירוק כאשר |
|---|---|
| **הפיכוּת** | השינוי כולו בתוך worktree מבודד, עם backup מתוארך, ניתן-לביטול ב-revert פשוט |
| **Scope** | הקובץ ברשימת-המותרים של התוכנית, והמשימה מהתור |
| **ביטחון** | critic/verifier עברו; עוגני-str_replace ייחודיים; אין שיקול-דעת-מסחרי פתוח |

**AUTO (הסוכן מחליט לבד):** עריכה בתוך scope עם טסט אדום→ירוק · הוספת קובץ-טסט חדש
תחת `tests/` (אם בתוכנית) · הרצות py_compile/pytest ממוקדות · קריאת כל קובץ לא-סודי.

**PARK (עוצר ושואל, ממשיך לתור):** עוגן-str_replace לא-ייחודי · scope-creep (התיקון
דורש קובץ מחוץ ל-whitelist) · ביטחון-נמוך / קריאת-שיפוט-מסחרית · **כל נגיעה
ב-CORE_UNSAFE = PARK תמיד ב-v1** (גם אם note-התור רמז אחרת) · סתירה בין התוכנית למציאות.

**FORBIDDEN-FLOOR (לעולם לא אוטומטי — לאף סוכן, בשום מצב; §8 + RULE #6):**
`git commit` / `git push` / `git add` ע"י המודל · הרצת runner/scanner/collector ·
`launchctl` כלשהו · כתיבת-Sheets · קריאת-secrets (hook **[קיים]**) · נגיעה
ב-`~/Library/LaunchAgents` · עריכת `.github/workflows/*`.
ה-commit-המקומי-לענף מבוצע ע"י ה-**orchestrator** (bash דטרמיניסטי) בלבד, ורק אחרי
VERIFIER `ready` — כך שגם "commit" לעולם אינו החלטת-מודל.

**שני מצבי-הכשל שהמטריצה מונעת:** over-automation (סוכן חורג מכשירותו — נחסם ע"י
הצירים + FLOOR) ו-under-automation (קיפאון על משימה 1 = לילה-שרוף — נפתר ב-§6).

---

## 6. סמנטיקת park & continue

- **ping-pong loop פר-משימה:** **עד 5 סבבי `plan↔critic` / `execute↔verify` לפני PARK**
  (3–5 = הטווח המוכח שמסלק 90%+ מהבעיות). תקרת-הטוקנים פר-משימה (§7) עדיין עוצרת קודם
  אם נפגעת. **critical (טסט אדום / חריגת-scope / core-unsafe) → תמיד סבב חוזר; עניין-סגנון
  בלבד → לא שורף סבב.** backstop: `--max-turns` פר-שלב **[קיים]**.
- **PARK ≠ הקפאת-ריצה. stuck = park; התור ממשיך תמיד** למשימה הבאה.
- **רשומת-park:** `parked.json` — `{task, stage, question, evidence_paths[]}`. השאלה
  חייבת להיות **שאלה כתובה וקונקרטית לעמיחי**, לא "לא הצלחתי".
- **PARK ≠ RED בדוח-הבוקר:** `⏸ PARKED` = נדרשת הכרעת-אדם (שאלה ממתינה);
  `❌ RED` = ניסיון-ביצוע שנכשל (טסטים אדומים / max-turns). ההבחנה קיימת כבר
  בקבוצות-הסטטוס של `build_report.py` **[להתאים** — קבוצת PARKED חדשה**]**.
- ברמת-bash הלולאה כבר ממשיכה אחרי כשל **[קיים]**; ה-חדש = סמנטיקת-park + לכידת-השאלה.

---

## 7. שישה קריטריוני-עצירת-משימה → קוד או שער-אדם

לעולם לא "המודל אמר done" — כל קריטריון ממופה למנגנון:

| # | קריטריון | מנגנון | מצב |
|---|---|---|---|
| 1 | goal-met | משפט-ה-"done" מהתוכנית נבדק ע"י **VERIFIER** מול ה-diff — לא הצהרת-המודל-המבצע | **[חדש]** |
| 2 | verification-passed | שער VERIFIER `ready` לפני כל commit | **[חדש]** |
| 3 | budget-reached | פר-ריצה: `TOKEN_CEILING` 600k (כולל cache) + wall-clock 180min **[קיים]**; פר-משימה: `budget:` מהתור (ברירת-מחדל 150k) **[חדש]**; פר-שלב: `--max-turns` **[קיים]** |
| 4 | marginal-value-collapsed | retry-ביצוע שלא שינה את ה-diff / bounce חוזר על אותו נימוק → PARK מיידי (בלי למצות תקציב) | **[חדש]** |
| 5 | stuck-loop | מוני-סבב של §6 (עד 5 סבבי ping-pong) | **[חדש]** (max-turns כ-backstop **[קיים]**) |
| 6 | human-handoff | סטטוסים `needs_human` / `uncertain` **[קיים]** + `parked` **[חדש]** |

---

## 8. גבול-commit

**הזרימה החדשה:** VERIFIER `ready` → ה-orchestrator (bash) עושה **commit מקומי** בתוך
ה-worktree לענף `auto-dancer/<TASK>`. **בלי push, בלי draft-PR — לשום remote.**

**השינוי מול הקיים [להתאים]:**
1. `execute_task.md` שלבים 5-6 (two-stage self-review → `git push` + `gh pr create
   --draft`) **נחתכים** — ה-review עובר ל-CRITIC/VERIFIER החיצוניים, וה-commit
   ל-orchestrator.
2. `rh-overnight.sh` שלב-5 (publish הדוח ב-push לענף `overnight-reports`) **נחתך** —
   הדוח נשאר מקומי ב-RAW_DIR. נגזרת: `overnight_report_email.yml` (שנורה רק על push
   לענף ההוא) לא יורה — ערוץ-המייל יורד ב-v1; ה-review הבוקרי הוא מקומי.
3. ענף שורד גם אחרי הסרת-worktree; worktrees של משימות לא-READY נשמרים לבדיקה
   **[קיים]**.

**בוקר (עמיחי):** קורא את הדוח → פר-משימה `git diff main..auto-dancer/<TASK>` (+
Agent #8 אם רוצה) → מכריע: push+PR / תיקון / זריקה (`worktree remove` + `branch -D`).
**autonomy-floor מובטח מבנית:** CODE_CHANGE מגיע ל-main רק דרך הידיים שלו.

---

## 9. Instrumentation

תיקיית-ריצה: `docs/auto-dancer/raw/YYYY-MM-DD/` (gitignored, כמו `docs/overnight/raw/`
— לאמת ב-M1) **[להתאים]**:

- `run_<stamp>.log` — לוג-ריצה מלא (תבנית ה-tee הקיימת) **[קיים]**
- פר-משימה: `plan.md` · `critique-1..N.json` · `execution.json` · `verify.json` ·
  `parked.json` (אם רלוונטי) · raw JSON פר-שלב + טוקנים פר-שלב **[חדש]**
- **trace-id פר-משימה ופר-שלב (`P→C→E→C→V`) בכל artifact ובלוג — בלי trace, ניפוי-שגיאות
  = ניחוש** **[חדש]**
- `_budget.json` מורחב: spent-מול-budget פר-משימה, פירוק פר-שלב, מוני-bounce **[להתאים]**
- `build_report.py` **[להתאים]**: קבוצת-סטטוס `⏸ PARKED` (עם השאלה הכתובה) · שורת
  trace פר-משימה (`P→C→E→C→V`) · טבלת-תקציב · ההבחנה PARK/RED של §6

---

## 10. Gap → Milestones

### טבלת-רכיבים (מ-gap-map ה-recon 4/7)

| רכיב | מצב | הערה |
|---|---|---|
| orchestrator bash (guards, worktrees, caps, לולאה) | קיים→להתאים | ביטול window-guard בידני; חיתוך 2 ה-pushים; לולאת-שלבים |
| קורא-QUEUE | חדש | §3 |
| classifier-וטו (`classify_task.md`) | קיים→להתאים | מ-discovery-gate לוטו-על-תור; לקרוא CORE_UNSAFE.txt כמקור-יחיד (§10 חוק-ברזל — כיום הרשימה משוכפלת בפרומפט) |
| `triage_filter.py` | קיים | פורש מהזרימה; נשאר ל-triage-only |
| PLANNER / CRITIC / VERIFIER prompts | חדש | §4 |
| EXECUTOR prompt | קיים→להתאים | `execute_task.md` בלי שלבי commit/PR |
| scope-lock מכני | חדש | deny-rules פר-משימה מג'ונרטות מהתוכנית (M2) |
| park-logic + מונים | חדש | §6 |
| git-diff-verify מקודד | חדש | diff-ריק-עם-done / חריגת-whitelist — בקוד, לא במודל (M4) |
| hooks `block_secrets`/`block_core_unsafe` + settings.night | קיים | ללא שינוי |
| caps ליליים (600k/180min/max-turns) | קיים→להרחיב | + budget פר-משימה |
| instrumentation + `build_report.py` | קיים→להתאים | §9 |
| `tests/overnight/` (13 קבצים) | קיים→להרחיב | יחידות חדשות: queue-parse, park, scope-lock, orchestration |
| Agent #8 | קיים | ללא שינוי; כלי-בוקר של עמיחי, מחוץ ללולאה |

### אבני-דרך (M0 = מסמך זה)

תנאי-קדם גלובליים: **base GREEN** (מתקיים 4/7 per-CI; אימות-מקומי-מלא = שער-M5) ·
**launchd מנוטרל** (מאומת 4/7) · כל M נסגר ב-review של עמיחי; אין M בלי go מפורש.

- **M1 — תור-כניסה + entrypoint ידני:** קורא-QUEUE · ביטול window-guard בידני ·
  הכרעת gitignore-לתור · classifier=וטו.
- **M2 — פיצול RPI:** 4 פרומפטים · לולאת-שלבים ב-bash · artifacts · scope-lock מכני.
- **M3 — park + עצירות:** מונים · budget פר-משימה · `parked` · קריטריון-4 (marginal).
- **M4 — VERIFIER + git-diff-verify מקודד:** שער-אחרון · חיתוך ה-pushים (גבול-§8).
- **M5 — טסטים + DRY מפוקח:** הרחבת `tests/overnight/` · אימות base GREEN מקומי ·
  ריצת plan-only על 1-2 משימות-תור אמיתיות · ריצה מלאה מפוקחת ביום. **סוגר גם את
  ה-execute-proof שמעולם לא אומת** (החוב של TASK-186).
- **M6 — ריצה אמיתית ראשונה:** חימוש-ידני בערב → בוקר: דוח + diffs → push+PR של
  עמיחי → פוסטמורטם ריצה-1 → הכרעת-שגרה.

---

## 11. נספח — פתוחים / סיכונים

1. **TASK-186:** retitle ל-"The Auto Dancer" + עדכון-תיאור (הנחת-launchd מתה) — **רק
   אחרי go נפרד** של עמיחי; הבקלוג לא נגוע ב-M0.
2. **execute-proof:** מכונת-הביצוע מעולם לא אומתה end-to-end על משימה אמיתית (מה
   שתקע את 186). נסגר ב-DRY המפוקח של M5 — בלי משימות-סינתטיות.
3. **עלות/זמינות Opus על ה-Max:** 3 תפקידי-Opus פר-משימה. תקציבי-הטוקנים מחושבים
   לפי-זה; fallback אם rate-limited: CRITIC יורד ל-Sonnet (הכרעה ב-M2, לא עכשיו).
4. **QUEUE מלכלך את העץ:** קובץ לא-committed מפיל את `guard_base_ready` — הכרעת
   gitignore-מול-commit ב-M1 (§3.3).
5. **כפילות CORE_UNSAFE:** הרשימה חיה גם ב-`CORE_UNSAFE.txt` וגם בגוף
   `classify_task.md` — drift-risk מול חוק-ברזל §10; איחוד למקור-יחיד ב-M2.
6. **שם settings:** `settings.night.json` נשאר בשמו (התשתית לא נגועה ב-M0); שינוי-שם
   ל-`settings.dancer.json` = הכרעה נדחית (§12 versioned-filenames — קובץ חדש, לא דריסה).
7. **מייל-בוקר ירד ב-v1** (נגזרת §8.2) — אם עמיחי ירצה התראת-סיום, פתרון מקומי
   (terminal-notifier / דוח-בלבד) יוגדר ב-M4, בלי push.
8. **re-arm של launchd אסור בעיצוב זה.** אם אי-פעם יידון מחדש — לפי checklist-ה-postmortem
   של TASK-220 (bootout **וגם** rename) ותחת §11 supervised gates בלבד.

**מקורות (חיזוקי-הביקורת):** מבוססים על דפוס generator-critic-verifier המוכח (3–5 סבבים,
בידוד-בודק, ראיית-כלי) ועל התאמה ל-Composio-AO (pipeline סדרתי, בלי shared-state collision).
