# תוכנית-חקירה — אודיט edge + data-pipeline ל-RidingHigh Pro (מתודולוגיה)

> **סטטוס:** מתודולוגיה בלבד — לא ממצאים, לא נתונים, לא מספרים. הביצוע מתחיל רק בהוראה נפרדת.
> **מבנה:** שלב-0 + 8 שלבים + reconciliation-gate חוסם. כל שלב: scan-line (סקיל+סיבה),
> (א) מה הסקיל מציע · (ב) pitfalls · (ג) התוצר המדויק.

## Context
שיטת-חקירה מסודרת, מחוזקת-סקילים ומוכנה-לביצוע, לבדיקה האם ל-RidingHigh Pro (מערכת מחקר
short-selling) יש edge אמיתי, והאם ה-data-pipeline + הקוד תומכים במסקנות.

## עקרונות-על (מוטמעים בכל שלב)
- **מקור חי מאומת:** כל קביעה עתידית = קובץ:שורה או sheet חי. אין טענה מזיכרון/PK-pasted.
- **falsification:** המטרה לנסות לשבור את ה-edge, לא לאשר אותו (backtest-expert: 80% מהמאמץ על שבירה). תוצאה שלילית = תוצאה תקפה.
- **determinism:** כל קריאת-נתונים עתידית תתועד עם snapshot/תאריך, כדי שתהיה ניתנת-לשחזור.
- **§10 SSoT:** כל מטריקה מחושבת במקום אחד; כפילות = ממצא.
- **אין false-Done:** שלב לא מסומן "נקי" בלי אימות חי.

---

## שלב 0 — עיגון מקור-אמת
**scan-line:** rhpro-live (היררכיית מקור-אמת + פרוטוקול §2).
- **(א) הסקיל מציע:** איתור PK עדכני **by-mtime** (`ls -t docs/*PK*.md | head -1`, לא לפי שם/גרסה), קריאה silently; קביעת היררכיה **קוד חי > sheet חי > PK**; מיפוי קבצי-ליבה ו-Sheet IDs מ-`sheets_config.json`.
- **(ב) pitfalls:** קריאה מ-PK pasted/ישן (drift); הסקה מזיכרון; הדפסת גוף-PK ל-output (RULE #14).
- **(ג) תוצר:** מפת-מערכת בת עמוד (קבצי-ליבה, מקורות-נתונים, workflows, Sheet IDs, גרסת-PK+changelog) + עיגון ההיררכיה. **הצלחה:** כל מטריקה בשלבים הבאים מצביעה על קובץ-מקור יחיד ידוע.

## שלב 1 — נעילת CHARTER (לפני כל מבט בנתונים)
**scan-line:** trader-memory-core (pre-registration של תזה + lifecycle) + backtest-expert (ניסוח edge/ספים).
- **(א) הסקיל מציע:** ניסוח ה-edge במשפט אחד; קיבוע ספי **Deploy/Refine/Abandon מספריים מראש**; הגדרת holding-period + benchmark תואם-חשיפה (short מול sector-short); מודל-עלויות מלא (commission + slippage + **borrow-fee** עם מקור לכל אחד); inventory מלא (קבצים/workflows/sheets/constants שייבדקו); מספר ההשערות (ל-multiplicity).
- **(ב) pitfalls:** HARKing (קביעת ספים אחרי ראיית נתונים); benchmark לא-תואם; התעלמות מ-borrow-fee כעלות מסדר-ראשון לשורט (אם המקור NULL — לקבוע מראש כלל net vs gross); ערבוב idea-generation עם validation.
- **(ג) תוצר:** charter חתום בן עמוד שלא ישתנה אחרי תחילת המדידה. **הצלחה:** קיימים ערכי-סף מספריים + מודל-עלות + benchmark, כולם נעולים לפני שלב 4.

## שלב 2 — ביקורת קוד ו-drift תיעודי
**scan-line:** systematic-debugging (חקירת root-cause, לא תיקון) + data-quality-checker (סטנדרט notation).
- **(א) הסקיל מציע:** אימות כל מספר ב-PK מול קוד חי (weights/caps/ספים/ספירות workflows-sheets); ציד §10-violations (מחשבון כפול מחוץ ל-SSoT); hardcoded מחוץ ל-config; dead code (מוגדר ולא-נקרא); בדיקת רעננות PK-version מול git-log.
- **(ב) pitfalls:** הכרזת "תואם" מול PK שעצמו drifted (הקוד הוא ground-truth); "הפרש קטן לא משפיע"; פיתוי לתקן drift תוך-כדי (זה אודיט — לרשום, לא לתקן).
- **(ג) תוצר:** drift-register {מטריקה | PK אומר | קוד (קובץ:שורה) | תואם?/חומרה} + רשימת §10-violations/dead-code/hardcoded. **הצלחה:** כל קבוע בליבת-ה-Score מופה קוד↔PK.

## שלב 3 — Data Pipeline lineage מקצה-לקצה
**scan-line:** data-quality-checker (lineage/quirks) + systematic-debugging (evidence-at-boundaries, Phase-1.4).
- **(א) הסקיל מציע:** מיפוי lineage לכל שדה קריטי (source→transform→write→read) עם קובץ:שורה לכל שלב; instrumentation בכל גבול-רכיב; זיהוי כל join-key מפורשות; מיפוי extraction-quirks לכל מקור.
- **(ב) pitfalls:** truncation שקט; silent loss (write שאבד); join-key mismatch → silent None; coverage דליל; שדות שנשמרים ריקים/{} בשקט.
- **(ג) תוצר:** lineage-map לכל מטריקת-edge עם coverage% + cadence + נקודות-כשל-שקטות (scan-0-rows / write-lost / NaN pre-market / שורה שלא מתקדמת). **הצלחה:** אין שדה edge-קריטי בלי מקור-ידוע.

## שלב 4 — איכות נתונים ו-schema validation
**scan-line:** data-quality-checker (5 קטגוריות) + trader-memory-core (jsonschema integrity).
- **(א) הסקיל מציע:** הרצת `check_data_quality.py` (price-scale/notation/date/allocation/units); fill-rate per-column; range/accuracy (טווחים תקפים, אין NaN/inf); uniqueness (מפתח-זהות); schema-conformance מול חוזה; הפרדת anomaly-אמיתי מבאג.
- **(ב) pitfalls:** findings advisory-only (דורשים שיפוט, לא חוסמים); שדות NULL/{} שעוברים בשקט; ETF/futures scale-confusion; date-weekday לא-hermetic; section-aware (לא לסמן % שאינו allocation); survivorship בדאטה עצמה (שורות מחוקות חסרות → מתחבר לשלב 5).
- **(ג) תוצר:** דוח-איכות (fill% + schema pass/fail + findings לפי ERROR/WARNING/INFO) עם הדגשת **שדות edge-קריטיים ריקים/NULL/coverage-נמוך**. **הצלחה:** רשימת שדות-מסכנים מדורגת מוכנה לשלב 5.

## ⛔ RECONCILIATION-GATE (חוסם — לפני כל סטטיסטיקה)
**scan-line:** data-quality-checker + systematic-debugging.
- **(א) מציע:** reconciliation בין sheets שאמורים להסכים, ובין מקורות-מחיר; כל KPI מוצג מול המחשבון הקנוני היחיד (§10).
- **(ב) pitfalls:** הרצת סטטיסטיקה על מספר שלא אומת מול מקורו; mismatch שמסמן מחשבון כפול; tabs חסרים שלא ניתנים-לאימות מקומית.
- **(ג) תוצר:** טבלת reconciliation PASS/FAIL/CANNOT-VERIFY per זוג. **חוק:** שום KPI לא-מאוזן (או לא-בר-אימות) לא נכנס לשלבים 5–6 בלי תיוג מפורש.

## שלב 5 — ציד הטיות
**scan-line:** backtest-expert (bias core) + signal-postmortem (regime/realized-outcome).
- **(א) מציע:** point-in-time — כל input זמין-בזמן-ההחלטה; survivorship — האם ה-dataset כולל מניות שנמחקו/הושעו; overfitting — ספירת free-parameters מול n, ובדיקה אם ספים כוילו in-sample; entry-basis — האם נקודת-הכניסה בת-ביצוע.
- **(ב) pitfalls:** look-ahead דרך נתונים מתוקנים/revised; survivorship דרך sheet שמכיל שורדים בלבד; in-sample tuning שדולף ל-"validation"; means מונעי-זנב שנראים כ-edge.
- **(ג) תוצר:** bias-audit checklist {look-ahead/survivorship/overfitting → PASS/FAIL/**UNKNOWN** + מיקום-ראיה}; **כל edge-claim החשוף ל-survivorship נושא תווית UPPER-BOUND עד הוורדיקט**; ורדיקט point-in-time integrity. **הצלחה:** כל input סווג computable-at-decision-time או לא.

## שלב 6 — תוקף סטטיסטי של ה-edge
**scan-line:** backtest-expert (evaluate + ספי-n) + signal-postmortem (TP/FP/regime, min-n).
- **(א) מציע:** confidence-interval (Wilson/בינומי) ל-win-rate על הנפח הקיים — והצגת רוחב-ה-CI; אימות שה-"win" נקי ומיושם אחיד (WHIPSAW≠win); reward/risk + expectancy + profit-factor **net אחרי עלויות** (charter); **multiplicity-control** (Bonferroni/דגל מפורש כשנבדקים תאים רבים); **median לצד mean + %>benchmark**; ספי-sample (30 רעש / 100 בסיסי / 200 מוסדי).
- **(ב) pitfalls:** mean חיובי מונע-זנב; single-regime; gross במקום net; multiple-comparisons; survivor upper-bound נגרר משלב 5; CI שכולל את ה-breakeven/הסף ולא מבחין מרעש.
- **(ג) תוצר:** טבלת-edge לכל תא (n, WR, Wilson-CI, mean, **median**, %>benchmark, net-of-cost, regime-split) + ורדיקט "האם ה-edge נבדל מרעש?" עם נימוק סטטיסטי (לא רק סימן ה-mean) + ספי-multiplicity. **הצלחה:** כל טענת-edge נושאת n + ספי-מובהקות מתוקנים + תווית upper-bound היכן שרלוונטי.

## שלב 7 — תשתית, אמינות ו-reconciliation
**scan-line:** systematic-debugging (multi-component evidence + determinism).
- **(א) מציע:** כיסוי health-checks מול נקודות-הכשל משלב 3 (איפה הפערים); cron integrity (כל workflow רץ בזמן ובאמת מבצע; Peru→UTC); סיכוני 429 + backoff/circuit-breaker; אומדן GitHub-Actions minutes; determinism (freeze_time/hermetic-clock; holidays).
- **(ב) pitfalls:** red CI date-dependent ≠ regression; feeds קפואים; collector שקט ("0 rows" stale — לאמת tab חי); time-zone errors בקרון; reconciliation-mismatch = §10-violation.
- **(ג) תוצר:** reliability-scorecard (per-feed: refresh+coverage+gap-log; per-KPI: reconciled?; CI-status+date-dependency; cron-audit UTC+Peru; determinism-check). **הצלחה:** כל KPI שנכנס לשלב 6 עבר reconciliation או סומן לא-אמין.

## שלב 8 — סינתזה, דירוג ו-roadmap
**scan-line:** trader-memory-core (roadmap/lifecycle) + backtest-expert (Deploy/Refine/Abandon).
- **(א) מציע:** טבלת-ממצאים אחת מכל השלבים מדורגת לפי **severity = פוטנציאל לנתונים-שגויים-בשקט** (לא קוסמטיקה); הפרדה {פערי-תיעוד / באגי-נתונים / שאלות-מחקר / שיפורים}; roadmap מתועדף (impact×confidence) עם הצעד-הבא לכל פריט; backlog-entries; הכרעת Deploy/Refine/Abandon מול ספי שלב 1.
- **(ב) pitfalls:** חיבה-לרעיון שמטה ורדיקט; דירוג לפי קלות-תיקון במקום impact; טענה חדשה בסינתזה ללא ראיה משלבים 2–7; המלצת promotion כשהתוצאה upper-bound/noise.
- **(ג) תוצר:** finding-register מדורג + ורדיקט יחיד מנומק (כל מספר מצביע על ראיה משלבים 2–7) + roadmap + סיכום בתבנית rhpro-live §6 (📊/🔍/⚠️/💡). **הצלחה:** "צעד הבא" אחד ספציפי + הכרעה מול ה-charter.

---

## סדר-ביצוע מומלץ
```
0 → 1 (charter נעול) → 2 → 3 → 4 → ⛔GATE → 5 → 6 → 7 → 8
```
**נימוק:** אי-אפשר לצוד drift בלי עוגן (0→2); lineage לפני quality — המפה אומרת *מה* לאמת (3→4);
reconciliation לפני סטטיסטיקה — חייבים לסמוך על המספר לפני בדיקת מובהקותו (GATE→5–6);
bias לפני stats — אין טעם במובהקות על דאטה מוטה; סינתזה אחרונה — נגזרת בלבד.

## Verification (איך נדע שהחקירה בוצעה נכון בעתיד)
- שלב 0/1 חתומים **לפני** כל מבט בנתונים (charter שמשתנה אחרי המדידה = הפרה).
- GATE עבר — אין KPI לא-מאוזן בסטטיסטיקה.
- כל edge-claim נושא n + ספי-multiplicity + תווית upper-bound; כל מספר בוורדיקט מצביע על ראיה.
- כלי-עזר עתידיים: `check_data_quality.py`, `evaluate_backtest.py`, `postmortem_analyzer.py`, `trader_memory_cli.py`.
