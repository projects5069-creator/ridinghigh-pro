# שלושת ה-commits על הבקלוג — ביצוע ואימות

**נכתב 2026-08-05 13:41 Lima.** שלושה commits על `backlog/tasks/` בלבד. **אין push.**
לא נגעתי בקוד/workflow/config, לא ב-Sheets/Drive/FINVIZ, לא הרצתי pytest.

**סקילים:**
| סקיל | path | wc -l |
|---|---|---|
| rhpro-live | `~/.claude/skills/rhpro-live/SKILL.md` | 180 |
| verification-before-completion | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/verification-before-completion/SKILL.md` | 139 |

נקודת הפתיחה: `72d357d` (2026-08-03).

---

## 0. תיקון "58 open" ב-TASK-186

**באיזו דרך תיקנתי: `str_replace` (כלי Edit) עם גיבוי — לא דרך ה-CLI.**

הסיבה, עם ראיה. `backlog task edit --help` מציע שתי אפשרויות ל-Notes:

```
--notes <text>          set implementation notes (replaces existing)
--append-notes <text>   append to implementation notes
```

`--append-notes` מוסיף בסוף ואינו יכול לשנות מספר בתוך פסקה קיימת.
`--notes` **כן** יכול — אבל הוא **דורס את כל בלוק ה-Notes** (32 שורות) כדי לשנות מילה אחת.
זה בדיוק ה-full-file-replace שפרוטוקול ה-commit של הפרויקט אוסר. לכן `str_replace`.

גיבוי לפני העריכה (מחוץ לריפו, כדי שלא ייכנס ל-commit בשום מצב):
```
/private/tmp/.../scratchpad/task-186.md.bak_20260805-134141
```

לפני:
```
השפעה על הספירה: לפני ההעברה 53 תיקים פתוחים. אחריה 57 (234-237), ועם TASK-255 שנפתח
באותה הכרעה — 58. כל דוח או תוכנית שמניחים 53 התיישנו ברגע הזה.
```

אחרי:
```
השפעה על הספירה: לפני ההעברה 53 תיקים פתוחים. אחריה 57 (234-237), ועם TASK-255/256/257
שנפתחו באותה הכרעה 60, ובניכוי TASK-10 שנסגר — 59. כל דוח או תוכנית שמניחים 53 התיישנו
ברגע הזה.
```

התיקון הוסיף שורה אחת (הפסקה נשברה מ-2 שורות ל-3). זו הסיבה שה-commit הראשון מראה
**329** insertions ולא 328 כפי שדווח הבוקר.

---

## 1. Commit ראשון — ההכרעות

```
1c2b54d  docs(backlog): record nine owner rulings 2026-08-05, close TASK-10
```

`git show --stat HEAD`:
```
 ....3-—-Filter-12-ticker_reputation.md"              | 44 ++++++++++++++++++++-
 ...opt-DROPSLAB_PK_DRAFT-as-docs-DropsLab_PK.md.md   | 28 +++++++++++++-
 ... - Build-overnight-autonomous-bug-fix-runner.md   | 38 +++++++++++++++++-
 ...ner-ranking-portfolio-selection-auto_scanner.md   | 27 ++++++++++++-
 ...or-demote-to-logged-diagnostic-~15-consumers.md   | 34 +++++++++++++++-
 ...cated-skip_reason-notional-uniformity-ruling.md   | 45 ++++++++++++++++++++++
 ...rch-volume-fade-halts-premarket-fills-borrow.md   | 45 +++++++++++++++++++++-
 ...nance-0.14.6-which-cannot-parse-finviz-today.md   | 35 +++++++++++++++++
 ...\327\231\327\235-\327\234-DropsLab-RidingHigh.md" | 40 ++++++++++++++++++-
 9 files changed, 329 insertions(+), 7 deletions(-)
```

**9 קבצים בדיוק** — 10, 82, 153, 186, 208, 209, 224, 230, 248. השמות ל-`git add` נגזרו
מ-`git status --porcelain=v1` בתור הזה, לא מהזיכרון. אפס `-A`, אפס wildcards.

⚠️ **סטייה טכנית שצריכה להיאמר:** ברגע ה-commit הזה כבר היו 234–237 ב-index (staged
מהתור הקודם). `git commit` סתם היה כולל אותם. לכן השתמשתי ב-**`git commit -F msg -- <9 נתיבים>`**
— pathspec מפורש שמצמצם את ה-commit לתשעה הקבצים בלבד ומשאיר את 234–237 ב-index.
ה-stat למעלה מוכיח שזה עבד: 9 קבצים, לא 13.

הודעת ה-commit נכתבה מקובץ (`-F`) ולא מ-`-m`, כי הגוף מכיל גרש ב-`WON'T-DO`.
**ללא `Co-Authored-By`, ללא "Generated with"** — כפי שביקשת.

---

## 2. Commit שני — שלושת התיקים החדשים

```
31b3ca3  docs(backlog): open TASK-255/256/257 from decision review
```

`git show --stat HEAD`:
```
 ...r-—-gated-on-TASK-179-validation.md"            | 54 ++++++++++++++++++
 ...izfinance-0.14.6-while-production-runs-1.3.0.md | 65 ++++++++++++++++++++++
 ...—-six-tickets-cite-it-as-evidence-source.md"    | 58 +++++++++++++++++++
 3 files changed, 177 insertions(+)

 create mode 100644 backlog/tasks/task-255 - ...
 create mode 100644 backlog/tasks/task-256 - ...
 create mode 100644 backlog/tasks/task-257 - ...
```

שלושתם `create mode 100644` — קבצים חדשים, לא שינוי של קיים.

---

## 3. Commit שלישי — ייבוא 234–237

```
eb1b026  docs(backlog): import TASK-234..237 from fix/auto-dancer-planmd
```

`git show --stat HEAD`:
```
 ...plan.md-resolve-run_plan_only-P3-name-collision.md | 19 +++++++++++++++++++
 ....-fail-closed-needs_human-blocks-manual-execute.md | 19 +++++++++++++++++++
 ...ask_resultstage_error-execute-proof-final-stage.md | 18 ++++++++++++++++++
 ...e-task-burned-2.8M-tokens-4.7x-the-600k-ceiling.md | 18 ++++++++++++++++++
 4 files changed, 74 insertions(+)
```

ה-index לפני ה-commit הכיל **בדיוק** את ארבעת הקבצים האלה ותו לא (הודפס ואומת לפני
ההרצה), ולכן כאן `git commit` ללא pathspec היה בטוח. לא הוספתי דבר.

---

## 4. אימות אחרי שלושת ה-commits

### 4.1 — `git log -4 --oneline`
```
eb1b026 docs(backlog): import TASK-234..237 from fix/auto-dancer-planmd
31b3ca3 docs(backlog): open TASK-255/256/257 from decision review
1c2b54d docs(backlog): record nine owner rulings 2026-08-05, close TASK-10
72d357d chore(backlog): three rulings and two accuracy fixes, 56 open down to 53
```
שלושה commits חדשים מעל `72d357d`. סה"כ 16 קבצים: 9 + 3 + 4.

### 4.2 — מצב העץ אחרי
```
$ git status --porcelain=v1 --untracked-files=all
?? docs/auto-dancer/queue/QUEUE_2026-07-04.md
?? docs/auto-dancer/queue/QUEUE_2026-07-05.md
?? reports/  (12 קבצים)
```
**`backlog/tasks/` נקי לחלוטין** — אפס `M`, אפס `A`, אפס `??`. כל מה שנשאר untracked היה
untracked עוד לפני התור: תור ה-auto-dancer (מ-7/04–7/05) ותיקיית `reports/` של היום.

### 4.3 — אפס קבצי קוד
```
$ git status --porcelain | grep -E '\.py$|\.yml$|\.json$|\.txt$'
CLEAN: no code files touched
```
`PROJECT_STATE.md` רוענן ע"י ה-post-commit hook בכל אחד משלושת ה-commits, כרגיל, והוא
gitignored — לא נכנס לאף commit (ההוק עצמו מדפיס זאת).

### 4.4 — ahead / behind מול origin/main
```
$ git rev-list --left-right --count HEAD...origin/main
3	11
```
הענף `docs/handoff-2026-07-29` הוא **3 לפני** ו-**11 אחרי** `origin/main`.
שלושת ה"לפני" הם בדיוק שלושת ה-commits שנעשו עכשיו. **לא בוצע push.**

### 4.5 — TASK-238 ו-239 לא נגעו
```
$ grep -H '^status:' backlog/tasks/task-238*.md backlog/tasks/task-239*.md
task-238 - Pin-finvizfinance-in-CI-and-sanitize-doubled-letter-tickers.md:status: Done
task-239 - Fix-post_analysis-collector-15min-GHA-timeout.md:status: Done
```
**שניהם עדיין `Done`.** ההימנעות מ-cherry-pick עשתה את שלה.

⚠️ הערת-דיוק: אותו grep על `task-239*` תופס גם שני גיבויים —
`task-239 - ....md.bak_20260803-160315` ו-`.bak_20260803-193206` — ובשניהם כתוב `To Do`.
אלה תצלומים מ-8/03 **מלפני** שהתיק נסגר, הם gitignored, ואינם תיקים חיים (`backlog task list`
לא רואה אותם). התיק החי הוא `.md` בלבד, והוא Done.

### 4.6 — הספירה הסופית
```
$ backlog task list --plain | awk '/^Done:/{f=1} /TASK-/&&!f{c++} END{print "OPEN:", c}'
OPEN: 59
```
**59 תיקים פתוחים.** 53 (הבוקר) +4 (234–237) +3 (255–257) −1 (TASK-10 נסגר) = 59.
המספר תואם את מה שכתוב עכשיו בגוף TASK-186 אחרי תיקון §0.

---

## 5. סטיות מההוראה

| # | מה | פירוט |
|---|---|---|
| 1 | **`git commit -- <paths>` בקומיט הראשון** | ההוראה אמרה `git add` בשמות מפורשים ואז commit. עשיתי `git add` בשמות מפורשים כפי שנאמר, אבל ה-`commit` עצמו נדרש pathspec מפורש — כי 234–237 כבר היו ב-index מהתור הקודם ו-`git commit` נקי היה בולע אותם לתוך commit #1. ה-stat מוכיח שהתוצאה היא בדיוק מה שהתכוונת אליו: 9 קבצים. |
| 2 | **הודעות ה-commit נכתבו מקובץ (`-F`)** | ולא מ-`-m`. הסיבה טכנית בלבד: הגרש ב-`WON'T-DO` והמקף-ארוך `—` שוברים ציטוט ב-zsh. הטקסט זהה מילה-במילה למה שנתת. |
| 3 | **§0 תוקן ב-`str_replace` ולא ב-CLI** | מוצהר במלואו ב-§0 עם הסיבה והראיה מ-`--help`. זו בדיוק החלופה שאישרת מראש. |
| 4 | **RULE #12 — ללא `.rh-run.sh`** | הפקודות הורצו ישירות. הפלט יועד לדוח הזה, לא ללוח. |

**לא בוצעו, במכוון, כפי שביקשת:** אין `push` · אין `-A` · אין wildcards ב-`git add` ·
אין נגיעה בקוד/workflow/config · אין pytest · אין Sheets/Drive/FINVIZ.

**הערה אחת שאינה סטייה אבל ראויה לציון:** ה-Anti-Drift Contract (rhpro-live §4) דורש
bump ל-PK על כל commit שנוגע בנוסחאות/משקלים/workflows/schema/health-checks. שלושת
ה-commits האלה נוגעים **רק** ב-markdown של הבקלוג — אפס נוסחאות, אפס קונפיג — ולכן
לא נדרש bump ולא ביצעתי אחד.
