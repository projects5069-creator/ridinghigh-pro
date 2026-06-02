# RidingHigh Pro — Night Run Template
*תבנית פרומפט-לילה אוטונומי. מבוסס על אימות חי של /goal + auto-mode ב-2026-06-02.*
*נוצר 2026-06-02 · סוגר TASK-102 · נשען על RUN_MODE_DECISION.md (TASK-103)*

---

## מה אומת חי (CLI v2.1.156, 2026-06-02)
- /goal קיים: "Set a goal — keep working until the condition is met".
- תחביר: /goal <condition> — התנאי בטקסט טבעי אנגלית (למשל: until all tests pass).
- אינדיקטור פעיל: "/goal active (Xs/Xm)" למטה מימין + timer.
- הפעלת /goal מעבירה אוטומטית ל-accept-edits mode.
- Esc = עוצר פעולה נוכחית, לא מבטל את המטרה.
- כל /goal <x> מחליף את המטרה, לא מבטל.
- ביטול ודאי = restart session (/exit + claude, או /clear).
- auto-mode: claude --permission-mode auto (ערך תקף ב-choices). דורש v2.1.83+.
- auto-mode מוריד אוטומטית הרשאות shell/python גורפות — ה-classifier בודק כל פעולה.

---

## מבנה פרומפט-לילה (קבוצה A + /goal)
1. פתיחה: view הסקיל הרלוונטי + wc -l (הוכחת טעינה).
2. recon קצר: git status נקי, branch נכון, הקשר המשימה.
3. צור branch ייעודי: git checkout -b night/TASK-NN-<slug>.
4. הגדר /goal עם תנאי-סיום מדיד אובייקטיבי (ראה דוגמאות למטה).
5. עבוד עד השגת התנאי — CC לולאה תור-אחר-תור, Haiku בודק כל תור.
6. בסיום: git add <שמות מפורשים> + commit ב-branch. שום push ל-main, שום merge.
7. פתח PR (לא merge). עמיחי בודק diff בבוקר ומאשר merge ידנית.
8. נקה: restart session (ביטול /goal ודאי) או /clear.

---

## דוגמאות תנאי-סיום מדיד (תקף ל-/goal)
- "until pytest tests/agent/ passes with zero failures"
- "until grep -rn \"duplicate_function\" returns no results"
- "until the file docs/DATA_SOURCES_MAP.md exists and has 20+ lines"
- "until git status shows the .bak files removed and committed on this branch"
לא תקף (לולאה אינסופית): "make it better", "improve the code", "clean up everything".

---

## 7 כללי הבטיחות (מ-RUN_MODE_DECISION.md — מחייבים)
1. שום push ל-main, שום merge. branch + PR בלבד. עמיחי מאשר merge בבוקר.
2. נתיבים אסורים לעריכה אוטומטית: config.py, formulas.py, ~/.claude/skills/*.
3. קבוצה A בלבד: repo-scoped + לא קוראת FINVIZ/news/Sheets (prompt-injection).
4. /goal רק עם תנאי-סיום מדיד.
5. ספי עצירה מובנים: 3 חסימות רצופות או 20 בסה"כ → CC עוצר.
6. תקרת לילה: 3 משימות, כל אחת ב-branch נפרד.
7. תקופת מבחן בפיקוח לפני לילה לא-מפוקח.

---

## קבצים קשורים
- `docs/RUN_MODE_DECISION.md` — ה-"מתי" (איזה מצב ריצה לכל משימה). קובץ זה הוא ה-"איך".

## הפעלה (איך עמיחי מריץ לילה)
cd ~/RidingHighPro && claude --permission-mode auto
ואז בתוך ה-session: /goal <תנאי-סיום מדיד למשימת קבוצה-A>.
auto-mode מאשר read + in-project edits; ה-classifier חוסם מסוכן.
Agent #8 (Routine Checker, TASK-94) יבקר בבוקר ויפיק דוח עברית.
