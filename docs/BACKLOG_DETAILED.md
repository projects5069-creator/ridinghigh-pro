# RidingHigh Pro — פירוט מלא של הבקלוג הפתוח

**עודכן:** 2026-06-30 (שלישי) · **מצב מערכת:** main מסונכרן · PK v3.79 · DRY_RUN · Sentinel=shadow
**פתוחות:** 40 (2 In Progress + 38 To Do) · פילוח: 2 HIGH · 15 MEDIUM · 5 LOW · 18 ללא-עדיפות
*(הפילוח כולל את 2 ה-In Progress: 186=HIGH, 128=MEDIUM; 2+15+5+18=40)*

> קובץ זה הוא הפירוט המסביר של כל משימה פתוחה — מספר, תאריך כניסה, מה המשימה אומרת,
> מה היא דורשת, מה מעכב אותה, מה היא תורמת, ו-RUN MODE מומלץ. נכתב כך שבכל סשן עתידי
> אפשר למשוך אותו ולהבין מיד מה כל משימה אומרת ולמה היא עלתה.
>
> מקור-אמת לעבודה שוטפת נשאר ה-`backlog` CLI החי. קובץ זה הוא שכבת-ההסבר הקריאה מעליו,
> מתוחזק תחת חוזה ה-Anti-Drift (לעדכן כשמשימות נפתחות/נסגרות/משתנות).
>
> **מבוטלות 30/6 (archived):** TASK-68, 69, 33, 67, 198 — ראה הערה בתחתית.

מקרא RUN MODE: PP=PING-PONG (דורש שיפוט/הכרעה) · auto=ביצוע חד-פעמי auto-safe · goal=לולאה עד תנאי-סיום מדיד.

---

## A. In Progress (2)

### TASK-186 · בניית overnight autonomous bug-fix runner `[HIGH]`
runner לילי מבוסס launchd + `claude -p` (מנוי Max) על feature/overnight-runner, עם פילטר auto-safe קשיח, draft PRs מבודדי-worktree, hooks ל-secret+CORE_UNSAFE ב-PreToolUse, ומפסק-זרם token/time. הקוד והטסטים DONE & GREEN, אבל הפעלת-התזמון חסומה מאחורי supervised gates §11, והמשימה במצב DISARMED (launchctl unload, 6/20). הפרמיסה שהצדיקה אותה ("יש עבודת auto-safe אמיתית בבקלוג להריץ עליה") הופרכה. מה היא תורמת: infra/אוטונומיה לילית — נמוך-ערך כרגע. נכנס 6/19, עודכן 6/19. RUN MODE: PP.

### TASK-128 · Gate כניסה מבוסס-מדדים ב-shadow `[MEDIUM]`
שכבת-shadow שמתעדת would-enter (MxV≤−100 ∧ price≥$3) בנתיב נפרד מ-`_check_filters`, בלי לגעת בהחלטה החיה. דורש (AC): #1 observer נפרד (לא לערוך את _check_filters המשותף, כי זה היה משנה את החי) · #2 Score/Toxic/ROCKET לא-חוסמים, נרשמים כ-tracking בלבד · #3 טבלת would-enter ב-DRY_RUN shadow, אפס שינוי להחלטות חיות · #4 promote ל-active רק אחרי multi-regime (~7/27) דרך TASK-194. קלט-מדדים מאומת (מחקר-199): הצעת-גייט עתידית מבוססת 4 ממדים אורתוגונליים — מנוע-רווח MxV≤−100 (כבר בגייט) + TPD≥6 (+6.5pp); מסנני-זנב REL_VOL≥15 (קטסט 8→4%) + Float%≥60 (קטסט 4→0%). גבול-אמינות: שמיש עד MxV+TPD+REL_VOL (n=28); הוספת Float% קורסת ל-n=13. ממצא-מפתח (master plan 6/29): הפילטרים-המגנים לא היו חלק משיטת-הכסף-האמיתי של השנתיים — כולם נוספו במאי-2026; רה-ולידציה ניפחה אותם (129pp→19.7pp; ROCKET_GUARD חוסם 12 מנצחות מול 7 מפסידות). מעכב: post-flip ה-WouldAllow מתאפס (live==explicit) — הניטור עובר ל-194 AC#4. מה היא תורמת: ליבת ה-edge (שער מבוסס-מדדים). נכנס 6/10, עודכן 6/29. RUN MODE: PP.

---

## B. To Do — HIGH (1)

### TASK-179 · Validate crossover-short on hold-out (n≥150) `[HIGH]`
ולידציה פורמלית של ההשערה ה-pre-registered (crossover-short) על נתון חדש בלבד — נאסף אחרי הרישום, ובמפורש אסור reuse של מדגם-הגילוי (n=62), כי אישור השערה על אותו נתון שעליו גילית אותה הוא טעות סטטיסטית. הבדיקה מריצה תחת תנאי-קצה פסימיים: מודל borrow worst-case (מנתוני TASK-172), slippage ×2, ומדד-הצלחה נעול מראש = net expectancy. דורש: ריצה רק על נתון פוסט-רישום + ורדיקט מתועד (edge שורד או נדחה — שני הכיוונים מתועדים). מעכב: n≥150 אירועי crossover (~450 שורות RH, ~4-5 חודשים בקצב הנוכחי, forward-only → ~אמצע יולי). תלויות 172/177/178 כבר הושלמו. מה היא תורמת: edge — ההכרעה הפורמלית היחידה אם יש edge אמיתי בכיוון שנרשם. נכנס 6/13. RUN MODE: PP.

---

## C. To Do — MEDIUM (14)

### TASK-9 · Sentinel Analytics module `[MEDIUM]`
מודול אנליטיקה ל-Data Sentinel (סוכן #2). כיום ה-Sentinel רץ ב-shadow ורושם BLOCK/WARN, אבל אין כלי שמסכם אותם. המודול יחשב: שיעור false-positive לכל אחת מ-7 הבדיקות, התפלגות חסימות לפי סיבה, ומגמה לאורך זמן. מה היא תורמת: observability — תנאי-מקדים למעבר shadow→active (בלי לדעת אילו בדיקות חוסמות-יתר, אי-אפשר להפעיל). נכנס 5/23. RUN MODE: PP.

### TASK-10 · Filter 12 ticker_reputation `[MEDIUM]`
פילטר 12 ל-Trader: ציון-מוניטין לכל טיקר לפי ביצועי-עבר, לדילוג טיקרים עם track-record גרוע (כמו HCWB — whipsaw כרוני). אם טיקר גרם שוב ושוב להפסדי-whipsaw, ציון-מוניטין נמוך → לא להיכנס. מה היא תורמת: איכות-כניסה (סינון מקור-רעש ידוע). נכנס 5/23. RUN MODE: PP.

### TASK-11 · Cross-month aggregation `[MEDIUM]`
הדשבורד והאנליטיקה צריכים לצבור נתונים לרוחב חודשים. הבעיה: Phase 1 מתפרס על מספר חודשים, אבל כל חודש "כלוא" (siloed) ב-entry נפרד ב-sheets_config — אין תצוגה אחת שמאחדת. מה היא תורמת: data-integrity/תצוגה — בלי זה כל ניתוח מוגבל לחודש בודד. נכנס 5/23. RUN MODE: PP.

### TASK-39 · Email consolidation `[MEDIUM]`
איחוד 6 מיילים/יום (3 health + morning + daily + critic) למייל-סיכום יומי אחד ב-16:30 פרו, עם התראות-מיידיות רק על שגיאות. הבעיה: כיום רוב 6 המיילים ירוקים (heartbeat) = רעש שמקהה רגישות; כשהכל ירוק מפסיקים להסתכל ומפספסים את האדום. מה היא תורמת: infra/ניקוי-רעש (יחס אות-לרעש בהתראות). נכנס 5/24. RUN MODE: PP.

### TASK-54 · PreToolUse Phase 2 — enforce RELEVANT skill `[MEDIUM]`
תשתית-אכיפת-סקילים. ה-gate הנוכחי (PreToolUse hook) הוא fail-open — מקבל קריאה של כל SKILL.md, לא בהכרח הנכון (ההוכחה: Test 3 טען time-check בשביל pwd ועבר). Phase 2 תמפה את tool_input.command ל-skill הרלוונטי כך שה-gate ידרוש את הסקיל הנכון לפי סוג-המשימה. אזהרה (AC#1): hook רע יכול לחסום את כל פעולות Claude Code (קרה ב-TASK-53 Stage D) — חובה kill-switch. הערה: ב-4/6 הוקשח ה-hook (v3.3) עם scan-line + מיפוי TASK-TYPE, אבל זו הנחיה בלבד; עדיין fail-open, וכל SKILL.md עובר. האכיפה הדטרמיניסטית עדיין נדרשת. מה היא תורמת: infra/אכיפת RULE #11. נכנס 5/29, עודכן 6/4. RUN MODE: PP.

### TASK-58 · SA נפרד ל-health_audit (סיום קונטנציית 429) `[MEDIUM]`
תיקון-שורש ל-Sheets 429. הבעיה המבנית: שלושה workflows (health_audit, agent_minute, auto_scan) חולקים service account אחד וביחד חוצים את תקרת Google של 60 reads/min/user בשעות-שוק. ה-mitigation מ-TASK-55 הוסיף backoff, אבל הבעיה המבנית נשארה. הפתרון: SA שני ייעודי ל-health_audit + שיתוף 9+9 גיליונות + GH secret חדש (GOOGLE_CREDENTIALS_JSON_HA) + config-switch — מוציא את health_audit מתקציב-ה-quota המסחרי. MEASURE-FIRST נסגר 6/26: ה-peak באמת מגיע ל-60, 429 חי בפרודקשן (ריצה 26964724118, 6/4). מונה-per-tab מספר בחסר, אבל עצם ה-429 הוא הוכחה. המסקנה: מוצדקת, לא מיותרת. מה היא תורמת: infra/quota (שורש אמיתי). נכנס 5/29, עודכן 6/26. RUN MODE: PP.

### TASK-62 · ניתוח %-edge מול $-edge למיילים `[MEDIUM]`
אב-המשימה של אשכול מחקר-המדדים. ניתוח per-trade לפי תאריך + פירוק MxV/ATRX/Gap/Volume בנצחונות מול הפסדים + פירוק לפי סוכן + תובנות-שיפור. החלק החשוב: הבחנה בין %-edge ל-$-edge — דוגמה אמיתית: net% = −1.6% אבל net$ = +144, כלומר ה-edge האחוזי שטוח/שלילי והרווח הדולרי נובע רק מגודל-הפוזיציה, לא מיתרון אמיתי. דגל: AvgWin < AvgLoss. (הערה: טענת "DropsLab EMPTY" מ-30/5 הייתה Sheet ID שגוי, תוקן ב-TASK-77.) חסום חלקית על n>91. מה היא תורמת: edge/insight (מבחין רווח-אמיתי מרווח-מדומה). נכנס 5/30. RUN MODE: PP.

### TASK-101 · התקנת security-guidance plugin `[MEDIUM]`
פלאגין-האבטחה הרשמי של Anthropic ל-Claude Code (security-guidance v2.0.2). 3 שכבות: (1) per-edit — אזהרות regex על ~25 דפוסים מסוכנים (yaml.load, pickle על קלט לא-מהימן, hardcoded-secrets), אפס עלות-מודל; (2) Stop — קריאת LLM שסוקרת diff בסוף תור; (3) commit — reviewer אג'נטי לפגיעויות חוצות-קבצים. רלוונטיות ל-rhpro: רוב מחלקות-web לא חלות (Python+Sheets+Alpaca), אבל hardcoded-secrets ו-unsafe-loading כן, ובעיקר שכבת-הגנה לבאטץ' הלילי האוטונומי. AC מעשי: התקנה (one-liner מאומת) + אימות שה-skill-gate ממשיך לחסום (סיכון נמוך, שניהם PreToolUse additive, יש kill-switches). gated על TASK-93/94 auto-mode — אין טעם להתקין לפני שיש באטץ' אוטונומי, כי עד אז המשתמש הוא הביקורת. נכנס 6/2, עודכן 6/4. RUN MODE: PP.

### TASK-126 · חילוץ SKIPs היסטוריים מלוגי Actions `[MEDIUM]` ⏰ דדליין קשיח
**המשימה היחידה בבקלוג עם דדליין-זמן קשיח.** מאז Route B, שורות [SKIP] מודפסות ל-stdout של GitHub Actions; הלוגים נשמרים ~90 יום, אז ריצות מ-12/5 יפקעו ~10/8. המשימה: scraper חד-פעמי (gh run list + gh run view --log, grep [SKIP]) שמשחזר את ה-dataset ה-counterfactual מ-12/5 עד היום ל-CSV מקומי, read-only, אפס כתיבה ל-Sheets. ה-SKIPs הם הנתון ה-counterfactual (מה לא נכנסנו אליו ולמה) — אחרי 10/8 אבוד לתמיד. מה היא תורמת: data-recovery עם חלון-זמן סגור. נכנס 6/10. RUN MODE: auto.

### TASK-154 · Evaluate private-repo migration `[MEDIUM]`
משימת-הערכה (לא ביצוע), follow-up להחלטה 4 (10/6): הריפו נשאר ציבורי, וקבצי-מחקר untracked אבל נמצאים בהיסטוריית-git (5b34304). תעריך: (1) private + self-hosted runner מול תשלום-דקות (~12k/חודש מול 2k חינם); (2) ניקוי היסטוריית-git (filter-repo); (3) tradeoff חשיפת-אסטרטגיה. קושר TASK-146 (Done) ו-196. מה היא תורמת: security/infra (הכרעה אסטרטגית חשיפה מול עלות). נכנס 6/11. RUN MODE: PP.

### TASK-166 · Daily lineage sentinel `[MEDIUM]`
health-check יומי לשלמות-נתונים: כל יום בוחר שורת post_analysis אקראית שכבר settled, מחשב מחדש end-to-end, ומשווה לערכים השמורים — WARNING על drift. תופס שחיתות-נתונים שקטה (שינוי-פורמולה, באג שקט) שאחרת לא היה מתגלה. AC#1: בוחר שורה/יום, מחשב, משווה, מזהיר על אי-התאמה. הערה: הקוד וה-CI כבר נחתו (PK v3.48), אבל live-verify נדחה — נשאר To Do עד אימות חי. מה היא תורמת: data-integrity (הגנה מ-drift שקט). נכנס 6/12. RUN MODE: PP.

### TASK-170 · Market-regime cluster (איחוד 15+42+70) `[MEDIUM]`
משימת-על שמאחדת שלושה פריטי מצב-שוק. ההיגיון: התנהגות שורט-על-pump תלויה במצב-השוק (יורד/עולה, תנודתיות). שלושת הרכיבים: (15) חיווט Market Context (SPY/IWM/VIX) ל-decision_logic כפילטר/מתאם-ציון; (42) מחיר-benchmark של SPY/IWM לכל שורת paper_portfolio בכניסה+יציאה למדידת תשואה-מול-השוק (לא עצמאית — חלק מהאשכול); (70) סימולציית VIX-מעל-סף כפילטר-כניסה. הסוכן Market Context כבר אוסף את הנתון. 3 AC, אחד לכל רכיב. מה היא תורמת: edge/regime (הקשר-שוק לכל החלטה). נכנס 6/12. RUN MODE: PP.

### TASK-176 · News Detective demotion (סופג את 67) `[MEDIUM]`
הורדה-בדרגה (או כיבוי) של סוכן #4, News Detective. ה-scorecard = 1/5: אין הבחנת WIN/LOSS (WR עם חדשות 60% מול בלי 62%, EDGAR r=−0.156), צריכת quota כבדה ב-agent_minute (TASK-136 סימן אותו ראשון לקיצוץ). נטו שלילי. **מאוחד עם TASK-67 (30/6):** כולל אימות מחקרי לפני ה-demotion — סימולציית "חדשות מהותיות→לא לשורט" (WITHOUT WR 62% > WITH 60%). הרצף: הוכח חוסר-ערך → EOD-only/disable. 2 AC: לא רץ per-minute + חיסכון-quota נמדד. מה היא תורמת: quota/ניקוי-רעש. נכנס 6/13. RUN MODE: auto→PP.

### TASK-194 · Stage 2 flip (ADR-009) — הסרת שער-Score החי `[MEDIUM]`
ליבת מהפכת-שער-הכניסה. ADR-009 הגדיר הסרת מנוע-ה-Score כשער; ה-flip נדחה (החלטות 141+174, shadow-first) עד שיצטברו שבועיים+ של shadow_gate_events רב-רז'ימיים שיוכיחו שההסטה (SCORE_TOO_LOW→would-ALLOW) בטוחה. **ה-flip בוצע בפועל 6/29 — לפני שתנאי-ההצטברות התקיים — כהחלטת-בעלים מודעת, ב-DRY_RUN והפיכה.** מנגנון: flip ו-revert = ערך-קונפיג יחיד (EXPLICIT_GATE_MODE), אפס שינוי-קוד. AC#1,2,3,5,6 כולם ✔ (הנתיב החי מכבד את הדגל; flip/revert=ערך יחיד; stage-1 ב-shadow ללא שינוי; אפס נגיעה ב-208/209; PK+ADR-009 עודכנו). **רק AC#4 פתוח-בכוונה = ניטור post-flip** (כניסות active מול Score-gated קודמות; revert=EXPLICIT_GATE_MODE shadow). מה היא תורמת: ליבת-edge. נכנס 6/24, עודכן 6/29. RUN MODE: PP.

---

## D. To Do — LOW (4)

### TASK-109 · enable RECONCILE_AUTO_REPAIR `[LOW]`
הפעלה בלבד (follow-up ל-TASK-108 שבנה auto-repair רדום, דגל OFF). הפעולה: flip של config.RECONCILE_AUTO_REPAIR ל-True. GATE קריטי: רק אחרי שה-reconciler ב-flag-only (TASK-106) מראה track-record נקי עם אפס false-positives — מיזוג-הקוד אינו הפעלה. הסיבה לזהירות: auto-repair כותב ל-paper_portfolio, אז FP אחד ייצור שורה שגויה. AC#1: אימות דיוק 106 לאורך תקופה עם 0 FP לפני ה-flip. DoD: דגל=True מקומומט, מאומת חי ב-EOD, PK bump. מה היא תורמת: data-integrity/אוטומציה. נכנס 6/4. RUN MODE: PP.

### TASK-145 · חקירת כשל agent_critic_monthly 21.9% `[LOW]`
חקירה (phase5 של TASK-139-INV): 7 מתוך 32 ריצות נכשלו מאז 11/5. הקונטקסט שכבר נמצא: 30 מתוך 32 הריצות היו manual workflow_dispatch tests ב-2/6 (אימות TASK-60) — כלומר ייתכן שהכשלים מתרכזים בטסטים-הידניים ולא בריצות-המתוזמנות האמיתיות. מה שצריך: לאמת אם הכשלים אכן מתרכזים בטסטים, ולצפות בריצה המתוזמנת הבאה — 1/7 (מחר). הראיה: phase5_evidence.md. מה היא תורמת: infra/observability. נכנס 6/11, עודכן 6/16. RUN MODE: PP.

### TASK-153 · אימוץ DROPSLAB_PK_DRAFT `[LOW]`
deliverable של phase7 ב-TASK-139-INV: קיים draft מלא של PK ל-DropsLab (docs/research/INVESTIGATION_2026-06-10/DROPSLAB_PK_DRAFT.md v0.1) עם schema מלא (38+25 עמודות), workflows, IDs, ורדיקטי-מחקר. המשימה: לסקור איתך ולאמץ כ-docs/DropsLab_PK.md חי תחת Anti-Drift. ⚠️ הערה קריטית: המשימה כתובה כסופגת את TASK-27 (אינטגרציית DropsLab→Trader, #N25) — אבל זה מתנגש עם ההפרדה המוחלטת בין המערכות (RidingHigh/ReboundPro/DropsLab נפרדים לחלוטין, תכניות-גשר בוטלו 22/6). אם נגיע למשימה — צריך להחליט אם רכיב-האינטגרציה הוא שריד היסטורי שיש להסיר מה-scope (סביר שכן). מה היא תורמת: docs/DropsLab. נכנס 6/11, עודכן 6/12. RUN MODE: PP.

### TASK-208 · Decouple Score מ-scanner ranking + portfolio selection `[LOW]` ⚠️ ייתכן באג חי
המשך ישיר ל-194 (Stage 2 של ה-flip). ה-auto_scanner עדיין מדרג/בוחר לפי Score (TRADE_ENTRY_MIN_SCORE≥70, idxmax/sort) ב-:490/578/1335/1338. ה-AC#1 הקונקרטי והקריטי: `borrow_collector.py:40` בוחר יעדי-borrow לפי score≥min_score — בעידן-חסר-Score (scoreless-era) ה-score ריק, מה ש**שובר את הבחירה בשקט**. זו לא ניקיון אסתטי — זו תקלה חיה פוטנציאלית שה-flip יצר. דורש recon חי קודם: האם borrow_collector רץ עכשיו והאם הוא כבר שבור מאז 29/6. אז להחליף ל-MxV-ranking בצעדים קטנים. מה היא תורמת: עקביות post-flip (מונע שבירה שקטה של בחירת-borrow). נכנס 6/29. RUN MODE: PP.

### TASK-209 · Retire/demote calculate_score `[LOW]`
Stage 3 של ה-flip. calculate_score מזין ~15 צרכני-תצוגה/ניתוח (dashboard, post_analysis_collector, health_check, health_audit). אחרי ש-194 ניתק את ה-Score מהכניסה, להחליט: retire מלא מול שמירה כ-diagnostic מתועד. blast-radius גבוה (15 צרכנים), והערכת-המשימה: סביר keep-as-diagnostic (מדד-אבחון שנרשם אבל לא מחליט). בעיקר החלטה + מעט קוד; לא דחופה, לא לביטול. מה היא תורמת: ניקוי-חוב/בהירות ארכיטקטונית post-flip. נכנס 6/29. RUN MODE: PP.

---

## E. To Do — ללא-עדיפות (18)

### אשכול מחקר-מדדים (from-task-62)

### TASK-71 · ניתוח "הצד השני" `[ללא-עדיפות]` 🔒 חסום
היפוך-פרספקטיבה: במקום "האם המדדים שלי עובדים על מי שנכנס", לשאול "אילו מדדים היו צריכים להוביל" — על כל המניות שתועדו (לא רק 104 שנכנסו). לזהות אילו ירדו/עלו הכי הרבה ואילו מדדים אפיינו אותן בדיעבד; edge חדש דו-צדדי (שורט+לונג). חסום על n דרך TASK-74 (אי-אפשר לנתח את הצד השני בלי תוצאות ל-946 החסרות). מה היא תורמת: edge חדש פוטנציאלי. נכנס 5/31. RUN MODE: PP.

### TASK-72 · סריקת-מדדים מורחבת `[ללא-עדיפות]`
סריקה של כל מדד שנאסף מעבר למדדי-הכניסה (timeline_live/post_analysis/daily_snapshots): Price_vs_SMA20, Gap, PriceToHigh, Consecutive_Up, DaysSinceIPO, ScoreMax/Min/Std. המטרה: למצוא מדד שעוקף את מדדי-הכניסה בכוח-ניבוי. שילדה את TASK-75 (DaysSinceIPO). מה היא תורמת: גילוי-מדדים (חיפוש שיטתי אחר אות טוב יותר). נכנס 5/31. RUN MODE: PP.

### TASK-73 · הרחבת CRITIC במודול ניתוח-עומק `[ללא-עדיפות]`
אוטומציה של הניתוח-הידני של TASK-62. ה-CRITIC (critic_v1.py, 835 שורות) כבר עושה סיכום בסיסי (build_weekly/monthly_row, scorecard, anomalies), אבל חסרה שכבת ניתוח-עומק. להוסיף: KPI מלא (Profit Factor, Expectancy, R:R, MaxDrawdown), קורלציה מדורגת של כל מדד-כניסה ל-PnL, counterfactual 4 הסוכנים, פילוחים, דגלים אוטומטיים (מדד לא-Score עוקף / סוכן בכיוון הפוך / Score r<0.05), ודוח עברית ל-research/. הרחבת CRITIC קיים, לא סוכן חדש (כבוד ל-FREEZE). מרחיב TASK-48. אישור-חקירה (6/27): score_analytics=0 שורות זה downstream של MetricsAtEntry-ריק (TASK-65), לא Critic מת. מה היא תורמת: insight/אוטומציה. נכנס 5/31, עודכן 6/28. RUN MODE: PP.

### TASK-74 · השלמת תוצאות ל-946 מניות חסרות `[ללא-עדיפות]` 🔑 מנוף
צוואר-הבקבוק של חצי מאשכול-המחקר. post_analysis מכסה רק 54 מתוך ~1000 מניות שנסרקו — 94% מהמניות שנסרקו אין להן תוצאה ידועה = עיוורון (timeline_live 1006 / daily_snapshots 948 / post_analysis 54 עם תוצאה). המשימה: למשוך 5-day OHLC ל-946 הנותרות מ-daily_snapshots, לחשב MaxDrop/TP10/תוצאה, כדי לנתח מדדים מול תוצאה על כל המדגם. חוסם את TASK-71. עבודה כבדה (משיכת Alpaca ל-946). מה היא תורמת: data-quality/הסרת-עיוורון — מנוף שמשחרר את כל אשכול-המחקר ל-n גדול. נכנס 5/31. RUN MODE: auto/goal.

### TASK-75 · DaysSinceIPO כמדד מועמד `[ללא-עדיפות]`
מועמד-מדד שצמח מ-TASK-72. בסריקה הרחבה (73 מניות, MaxDrop בפועל) DaysSinceIPO קיבל r=+0.261 — מניות צעירות (IPO טרי) יורדות חזק יותר = שורט טוב יותר. מדד שלא בציון ולא נבדק. RELIABLE ב-n=73, מובהקות חלקית (crit≈0.229), רז'ים-יחיד. לבחון הוספה לסכמת-המדדים. מה היא תורמת: מדד-מועמד חדש עם קורלציה מבטיחה. נכנס 5/31. RUN MODE: PP.

### אשכול DropsLab/מדדי-שורט (from-task-80)

### TASK-82 · 5 מדדי-שורט מקצועיים חסרים `[ללא-עדיפות]`
מחקר-רשת (31/5) זיהה 5 מדדים שהשחקנים-הגדולים מחפשים ואין לנו: (1) days-to-cover היסטורי + שינוי שורט-אינטרס [בתשלום]; (2) utilization rate [בתשלום]; (3) VWAP תוך-יומי אמיתי [בר-בנייה מדקה]; (4) Bollinger/sigma-bands [בר-בנייה מ-SMA+std]; (5) institutional/insider ownership [דורש מקור]. תכנית: שלב 1 זמינות+עלות, שלב 2 מימוש בני-החינם, שלב 3 החלטת-מקור-בתשלום. 4 AC: #1 קטליזט מסווג (offering/דילול/חקירה/delisting — דילולים מנבאים המשך-ירידה); #2 דגל reverse-split בזמן-אמת (TASK-80 מצא 82 אנומליות, +28000% CTNT/CODX); #3 מילוי חורים (short_float_pct ריק 22%, shares_float ריק 19%); #4 הקריטי — borrow_data ריקים (אומת), tradability mocked (is_shortable=True, fee=12.5 קבוע), edge breakeven ~388%/שנה borrow → מדדי-shortability אמיתיים הם הקלט החוסם. מה היא תורמת: edge + קלט-borrow חסר. נכנס 5/31, עודכן 6/11. RUN MODE: PP.

### TASK-83 · DropsLab — הרחבת חלון מ-5 ל-15 ימי מעקב `[ללא-עדיפות]` ⚠️ repo DEAD
משימת DropsLab (פרויקט נפרד). drops_post עוקב 5 ימים (d1-d5); ההשערה: קריסה עשויה לבוא אחרי 7-15 יום וחלון-5 חותך אותה (ADTX קרסה והעמיקה כל 5 הימים; 49.5% מתויגים Full-Recovery ב-5 יום — אולי חלקם Continued-Drop בחלון ארוך). 4 AC: #1 נקודות בדידות (d1,d2,d3,d5,d7,d10,d15,d20); #2 max_further_drop_20d + max_recovery_20d; #3 (עדיפות עליונה) VWAP ביום-הנפילה + מיקום-סגירה יחסית — האות שכל המקצוענים מחפשים, חסר לגמרי; #4 נקודות תוך-יומיות בפתיחת-יום-המחרת. ⚠️ repo Ambroseius/DropsLab = DEAD → דורש re-scoping מלא, ובכל מקרה שייך לסשן DropsLab נפרד. מה היא תורמת: edge ל-DropsLab. נכנס 5/31. RUN MODE: PP.

### אשכול מייל חודשי (task-48 follow-ups)

### TASK-88 · מייל חודשי — גרפים `[ללא-עדיפות]`
Follow-up ל-TASK-48. שני גרפים למייל-החודשי: (1) equity curve — קו רווח/הפסד מצטבר; (2) בר לכל מדד (Score/RunUp/ATRX/Float/MxV) שמראה רמת-השפעה ויזואלית במקום טבלה. דורש matplotlib→PNG מוטמע base64 + אימות CI + אימות שהתמונות נפתחות בתיבת-מייל. commit נפרד, לא לגעת ב-build_monthly_row/sheet. מה היא תורמת: תצוגה/UX של הדוח החודשי. נכנס 6/1. RUN MODE: auto.

### TASK-89 · מייל חודשי — זיהוי ימים/עסקאות חריגים `[ללא-עדיפות]`
Follow-up ל-TASK-48. לזהות חריגות מהדאטה שלנו בלבד (לא feed חיצוני): ימים עם נפח-עסקאות חריג או תוצאה קיצונית, לציין במייל. הקשר-מאקרו חיצוני (VIX/חדשות) הוצא במכוון מה-scope. commit נפרד. מה היא תורמת: insight (הסבת-תשומת-לב לחריגים). נכנס 6/1. RUN MODE: auto.

### אשכול data-integrity / recon-debt

### TASK-49 · NCT recon mismatch `[ללא-עדיפות]`
אנומליה מ-וורפיקציה 28/5: הטיקר NCT מופיע פעם ב-decision_log אבל פעמיים ב-paper_portfolio (dl=1, pp=2). ATPC/WGRX תקינים. שלוש השערות: (א) כתיבה כפולה ל-paper_portfolio ב-order_manager; (ב) ENTER שני שלא נכתב ל-decision_log (כשל 429); (ג) שורה ישנה מיום קודם שנספרה כהיום. חקירה לפני תיקון — אסור לגעת ב-order_manager עד שהשורש ברור. הבחנה (3/6): לא מכוסה ע"י TASK-106 (שמזהה את הכיוון ההפוך, pp<dl); 49 הוא pp>dl (שורה כפולה/יתומה). נדרש: reconciliation הפוכה + זיהוי PositionID כפול. מה היא תורמת: data-integrity. נכנס 5/28, עודכן 6/3. RUN MODE: PP.

### TASK-65 · פער postmortems (סופג את 198) `[ללא-עדיפות]`
עלה ב-TASK-62. AC: #1 read-only עד שלב-ההחלטה (כל backfill = צעד מאושר נפרד); #2 scope multi-month GLOBAL set-diff (לא per-month — postmortem נכתב בחודש-הסגירה ועלול לשבת ב-spreadsheet שונה מה-ENTER); #3 (scope סופי 6/27) הפער האמיתי = 36 פוזיציות CLOSED-בלי-postmortem (לא "9"). ממצא-לוואי קריטי (6/27): מעבר על 182 ה-postmortems מצא MetricsAtEntry ריק ב-55% (101/182) — בעיה מובחנת מ-36 החסרים. היפותזת-שורש (לא מאומת): _get_decision_context קורא ל-_read_decision שעושה linear-scan ב-decision_log ומחזיר {} ב-miss. **מאוחד עם TASK-198 (30/6): חקירת-שורש אחת על _read_decision המכסה שני סימפטומים — 36 ה-postmortems חסרי-המדדים + 20 ENTERs ללא שורת paper_portfolio.** (20 ה-ENTERs: השערות re-entry-duplicate מול rejected-ENTER מול pipeline-gap; דוגמאות EHGO/NXTS/ANY עם timestamps סמוכים, ו-AZI/RGNT/SUNE/SDOT.) read-only עד הכרעה. מה היא תורמת: data-quality. נכנס 5/31, עודכן 6/30. RUN MODE: PP.

### TASK-66 · Sentinel counterfactual הפוך `[ללא-עדיפות]` 🚫 blocker
ממצא מטריד מ-TASK-62: העסקאות שה-Sentinel היה חוסם ביום-הכניסה הן דווקא המנצחות — WR 64% בחסומות מול 41% בלא-חסומות (n=36, RELIABLE). רוב החסימות (6188/7466) הן scan_freshness; ההיגיון: סקאן ישן = מהלך חד שכבר קרה = שורט טוב. כלומר הפעלת active mode הייתה חוסמת בדיוק את הטובות. **blocker למעבר shadow→active.** אישור-חקירה (6/27): מ-45,008 שורות sentinel_events — scan_freshness=25,311 (דומיננטי), price_freshness=15,456; כל 13,033 ה-CRITICAL הם SENTINEL_BLOCK ב-shadow (לא-נאכף=רעש-לוג). הנמכת-severity מכוסה ב-TASK-96. מה היא תורמת: blocker מחקרי — לפני הפעלת ה-Sentinel חייבים להבין למה הוא חוסם מנצחות. נכנס 5/31, עודכן 6/28. RUN MODE: PP.

### TASK-196 · Decision-4 leak: research CSVs בהיסטוריית-git ציבורית `[ללא-עדיפות]`
TASK-195 הגן על ה-HEAD (skip + לא להוסיף CSV), אבל קבצי-המחקר כבר בהיסטוריית-git הציבורית (5b34304) — Decision-4 מודלף חלקית. צץ בקריאת TASK-154. 4 AC, כולם הערכה בלבד: #1 מה בדיוק חשוף (אילו CSVs, כמה שורות, איזו דאטת-מסחר); #2 חומרה (כמה זמן חשוף, סיכון בפועל); #3 מסלול — history-scrub מול private-migration (תלות ב-154); #4 תיעוד-בלבד, אפס scrub במשימה זו. מה היא תורמת: security (הערכת חשיפת-אסטרטגיה). נכנס 6/26. RUN MODE: PP.

### TASK-202 · fix collector cross-month backfill `[ללא-עדיפות]`
**אינה Float% (anchor שגוי נתפס 6/30).** הבעיה: post_analysis_collector.run() פותר כל פעולת-Sheet לחודש-הנוכחי, כך ש-backfill היסטורי חוצה-חודשים (--date) קורא/כותב לטאב החודשי הלא-נכון. התגלה ב-backfill של יוני (TASK-200) — יוני "עבד" רק כי החודש היה יוני. תיקון "read-only" מסוכן: יבנה שורות חודש-עבר וישמור בטאב הנוכחי. 5 AC + TDD: #1 run() גוזר חודש מ-target_date ומעביר ל-3 נקודות-קריאה (:396/411/454); #2 שינוי-חתימה ל-load/save/_get_post_analysis_ws; #3 backfill חוצה-חודשים קורא וכותב לטאב היעד; #4 month=None שומר ברירת-מחדל (live EOD + dashboard לא מושפעים); #5 TDD RED מתעד שהיום save/load נפתרים לחודש-נוכחי תמיד. 5 נקודות-שבירה: :396/411/454/461/617. מה היא תורמת: data-integrity (backfill היסטורי תקין). נכנס 6/28. RUN MODE: PP.

### אשכול תצוגה/data + latent

### TASK-205 · תצוגת D6-D25 בדשבורד `[ללא-עדיפות]`
תצוגה של נתון D6-D25 שכבר נאסף (D{i}_Low + D{i}_Close, לטיקרים שנסרקו מ-6/13). הנתון כבר נכתב ע"י ה-collector וכבר זורם ל-_cached_post_analysis() — אין עבודת-איסוף או schema. שכבת-תצוגה טהורה: מסע-25-יום per-ticker כטבלה וכגרף-מסלול. אין classification (אין High מעבר ל-D5, אז אין WIN/LOSS סימטרי). 4 AC: #1 דף/סקשן עם טבלת D1-D25; #2 גרף-מסלול (plotly) של נתיב-Low; #3 שורות לפני 6/13 מטופלות בחן (NA, לא אפסים-מזויפים); #4 אפס נגיעה ב-collector/schema/classify. מה היא תורמת: תצוגה (חשיפת נתון-מעקב ארוך קיים). נכנס 6/29. RUN MODE: auto.

### TASK-206 · שדות fundamental `[ללא-עדיפות]`
מקסום תיעוד-fundamental per-stock. זמינות אומתה על nano-cap (29/6): שדות מבניים/short + ownership + רווחיות (ShortFloat, Days-to-Cover, InstOwn, InsiderOwn, Beta, ROE, ProfitMargins, Sector, Industry) חוזרים נקיים גם ל-nano-caps משני המקורות (yfinance .info + FINVIZ-Custom). רק floatShares (TASK-201) וצמיחה לא-אמינים; P/E לרוב null ל-nano-caps לא-רווחיות (NA לגיטימי); delisted=404. עיצוב היברידי: FINVIZ-Custom one-call ראשי + yfinance fallback + raw_fundamentals_json catch-all, guard+source-tag per-field. 5 AC: core columns, JSON catch-all, guard+NaN-tolerance (reuse clamp TASK-203, להבחין NA-חסר מ-NA-delisted), FINVIZ-Custom ראשי + yfinance fallback, schema-union write בלי שבירת-reader. foundation נחת 6/29; collector-write+FINVIZ פתוחים. מה היא תורמת: data (מקסום תיעוד fundamental). נכנס 6/29, עודכן 6/29. RUN MODE: PP.

### TASK-211 · Fix is_day_complete DST `[ללא-עדיפות]` ⏰ latent ~נובמבר
אחות-התאומה של תיקון-ה-DST שכבר עשינו ב-is_market_hours. is_day_complete ב-utils.py משתמש ב-15:00 פרו hardcoded; בחורף (EST) הסגירה 16:00 פרו, אז חלון 15:00-16:00 בחורף מסומן בטעות כ"complete". הפתרון: לגזור מ-ET (America/New_York) כמו תיקון-ה-DST של is_market_hours. latent — צף ~נובמבר (מעבר לשעון-חורף). מה היא תורמת: תיקון-מונע (סוגר באג-DST ידוע לפני שיתפוצץ). נכנס 6/30. RUN MODE: auto/TDD.

### TASK-92 · דיון: צמצום/ביטול תיעוד-דקה ב-timeline_live `[ללא-עדיפות]` 💬 משימת-החלטה
אתה העלית (1/6): תיעוד כל-דקה ב-timeline_live אולי מעמיס וגורם ל-429 חוזרות. timeline_live הוא ה-writer הכבד ביותר (~250-300K שורות/חודש, ~390 כתיבות/יום). משימת-דיון — לא לבצע ביטול בלי הכרעה. שונה מ"ציון כסינון בינארי" (ADR-002) — שם ערכיות-הציון, כאן תיעוד-הדקה. שלושה סיכונים לאימות: (1) orchestrator.read_latest_signals קורא מ-timeline_live — ביטול ישבור את הסוכן; (2) post_analysis collector בונה את dataset-המחקר מאגרגציה — ביטול ישבור את המחקר; (3) "ביטול" = 3 רמות (הסתרת דף=בטוח / הפסקת Score / הפסקה מוחלטת=מסוכן). אופציות-ביניים: תדירות כל-5-דקות (−80%), כתיבה רק מעל סף-ציון, צבירה-בזיכרון+flush. 4 AC: מיפוי-תלויות, כימות חלק-429, הכרעת-עמיחי על הרמה, ביצוע (אם הוחלט) בלי לשבור סוכן+collector. קושר TASK-58. מה היא תורמת: quota/החלטה ארכיטקטונית. נכנס 6/1. RUN MODE: PP.

---

## נספח — משימות שבוטלו (archived) 30/6

לאחר ה-flip של 29/6 (הסרת שער-ה-Score), חמש משימות נשענו על הנחות-עולם שכבר לא תקפות או מוזגו לאחרות:

- **TASK-68** (RSI רמה מול divergence) — ARCHIVED: שיפור מדד-RSI לציון שכבר אינו שער; Score מנוטרל post-flip.
- **TASK-69** (היפוך-משקלי-Score) — ARCHIVED: אין מה לכייל בציון מנוטרל (AUC 0.531, SCORE_WRITE_FROZEN).
- **TASK-33** (Agent #6 Devils Advocate) — ARCHIVED: לא נדרש (החלטת עמיחי); FREEZE על agents חדשים ממילא.
- **TASK-67** (News Detective WIN/LOSS) — ARCHIVED→מוזג ל-TASK-176 (ה-AC המחקרי נספג שם).
- **TASK-198** (20 ENTERs ללא paper_portfolio) — ARCHIVED→מוזג ל-TASK-65 (חקירת-שורש _read_decision משותפת).

הקבצים עברו ל-`backlog/archive/tasks/` (הפיך ע"י unarchive). ה-notes המקוריים שרדו בארכיון.

---

*— סוף הפירוט · 40 משימות פתוחות · עודכן 2026-06-30 —*
