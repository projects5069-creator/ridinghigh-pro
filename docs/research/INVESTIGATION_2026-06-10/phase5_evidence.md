# שלב 5 — ראיות גולמיות (תשתית: workflows / health_audit / גיבויים / minutes)

## 1. cron מוצהר מול ריצות בפועל + אחוז כשל 30 יום (מאז 11/5, gh API)

| workflow | cron מוצהר | ריצות 30d | כשלים | כשל% | הערות |
|---|---|---|---|---|---|
| agent_minute | */1 13-20 1-5 | 10,613 | 212 | 2.0% | רוב הכשלים = חלון ה-16ש' של task-122 (9-10/6) |
| auto_scan | */1 13-19 1-5 | 10,600 | 213 | 2.0% | כנ"ל |
| backup | 7 13-21 + 7 20 + 30 21 1-5 | 105 | 1 | 1.0% | תקין |
| health_audit | 0 11, 30 20, 0 3 | 91 | 5 | 5.5% | |
| agent_market_context | 30 13 + **0 14-20** 1-5 (8/יום) | 61 | 9 | **14.8%** | כשל אמיתי חוזר: 429 read-quota (ראיה: run 27293631392 — "Quota exceeded... Read requests per minute") — רץ בראש שעה עגולה, מתנגש עם זוג ה-minute workflows |
| agent_eod | 0 21 1-6 | 49 | 0 | 0% | |
| agent_email_daily | 30 21 1-5 | 45 | 1 | 2.2% | |
| agent_email_morning | 30 13 1-5 | 44 | 1 | 2.3% | |
| agent_critic_monthly | 0 6 1 * * | 32 | 7 | — | 30/32 = workflow_dispatch ידני ב-2/6 (אימות TASK-60) — לא אנומליה של cron |
| post_analysis | 5 21 1-5 | 23 | 2 | 8.7% | אחד מהכשלים = ליל 9/6 (task-122) |
| agent_critic | 0 22 1-5 | 20 | 1 | 5% | |
| warm_oauth_token | 0 12 */3 | 12 | 3 | 25% | **הריצה האחרונה (10/6 15:42Z) נכשלה** — שורש task-122 (לפני התיקון 16:41Z); הבא 13/6. token חומם לאחרונה 7/6 |
| agent_critic_weekly | 0 23 * * 5 | 1 | 0 | — | הופעל ~30/5; שישי ראשון מאז = 5/6, רץ ✓ (drift של GH דחף ל-00:04 6/6) |
| monthly_rotation / prepare_next_month | 1/5 5 1 * * | 1/1 | 0 | — | רצו 1/6 ✓ (אבל ראו ממצא הכפילות בשלב 4ה) |

## 2. health_audit — בפועל 28 בדיקות (לא 18)

רשימה מ-`health_audit.py` (grep def check_): 01-28 ללא 29+ — **28 בדיקות**. סיווג מהות/סימפטום:

- **מהות** (בודקות נכונות): 01 duplicate-functions (§10), 02 hardcoded-thresholds (AST), 05 post_analysis completeness, 07 score-range, 08 required-columns, 09 dup-rows, 11 config-current-month, 12 weights-sum, 19 PK-sync (anti-drift), 28 agent-sheets-complete.
- **סימפטום** (בודקות ש"משהו רץ/קיים", לא שהוא נכון): 04 timeline-freshness, 06 Actions success<80%, 22 post_analysis-ran-today, 13 critical-files-exist, 14 uncommitted-count, 15 gitignore, 25/26/27 agent-tabs freshness (row-count/טריות בלבד), 23 nan-ScanTime.
- **canaries לדאטה**: 10 outliers, 16 REL_VOL-stuck, 20 float-stuck, 21 gap-outliers, 17/18 providers, 24 sentinel-health.

פערי-מהות שאף בדיקה לא מכסה: (א) זיהוי reverse-split שקרה אחרי הסריקה (ממצא 4ד — TDIC CLEAN);
(ב) אימות persisted-writes מול decisions (מכוסה חלקית ע"י reconciler, לא ב-audit);
(ג) skip_summary נכתב בימי מסחר (טאב חדש — אין בדיקה); (ד) עותקי-Sheets יתומים (ממצא 4ה).

## 3. גיבויים — טריות

- artifact אחרון: post_analysis_27312259524 (10/6 23:09Z, success) — **טרי מהיום** ✓; retention 90 יום; יוני-בלבד (חודש פעיל).
- backups/ מקומי: קבצים אחרונים מ-22/5 (sheets_2026-05_pre_rewrite) — המקומי אינו מנגנון הגיבוי; הגיבוי החי הוא artifact+Drive דרך backup_manager (רץ ב-CI).
- חודשים סגורים (אפריל/מאי): אין גיבוי שוטף — מגובים רק כשהיו פעילים. שינוי בהם (backfill) לא מגובה אוטומטית.

## 4. צריכת Actions minutes

- הרפו **PUBLIC** (gh repo view: isPrivate=false) → minutes חינם על runners סטנדרטיים; אין חשיפת עלות.
- אומדן שימוש: agent_minute ~37s/ריצה, auto_scan ~30s (מדידת timing API על 5 ריצות כ"א) × ~480 טריגרים/יום לכל אחד ≈ ~536 דק'/יום + ~25 דק' לשאר ≈ **~12,000 דק'/חודש**. אם הרפו יהפוך פרטי אי-פעם — זה פי-6 מהמכסה החינמית (2,000).
- הערת אגב לפרטיות: רפו public = כל הקוד, ה-backlog וה-Sheet IDs חשופים (credentials לא ב-git — אומת ב-git ls-files ✓; הגיליונות עצמם דורשים הרשאה).

## סקילים שבוצעו בשלב זה
systematic-debugging (חקירת אנומליות ריצה), data-quality-checker.
