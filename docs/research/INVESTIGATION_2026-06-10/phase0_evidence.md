# שלב 0 — ראיות גולמיות (אימות תיקוני 10/6)

ריצה: 2026-06-10 20:30–20:45 America/Lima (שוק סגור). כל הפקודות הורצו חי.

## (א) TASK-130 — טסטים holiday-aware

```
$ uv run --offline --with pytest --with pytz --with pandas --with gspread --with google-auth --with pandas-market-calendars python3 -m pytest tests/test_trading_days_holiday_v1.py -v
tests/test_trading_days_holiday_v1.py::test_good_friday_skipped PASSED
tests/test_trading_days_holiday_v1.py::test_memorial_day_skipped PASSED
tests/test_trading_days_holiday_v1.py::test_independence_day_observed_skipped PASSED
tests/test_trading_days_holiday_v1.py::test_regular_weekend_still_skipped PASSED
tests/test_trading_days_holiday_v1.py::test_fallback_weekday_only_keeps_weekend_skip PASSED
5 passed in 0.04s
```

baseline נוסחאות: `python3 test_formulas.py` → `Results: 107/107 passed`.

הערת סביבה: `python3 -m pytest` חסום ע"י hook; pytest אינו מותקן בסביבת uv —
הריצה התאפשרה רק עם `--offline --with pytest ...` (cache קיים, אפס התקנת רשת).

## (ב) n מוכרעות + PENDING + fill-only

מקורות דאטה (אפס get_all על timeline_live):
- 2026-06: artifact של workflow ‏"Daily Backup — post_analysis" ריצה 27312259524 (23:09Z היום) → `post_analysis_2026-06-10_18-09.csv`, ‏54 שורות.
- 2026-04 (154 שורות, 122 עמודות) + 2026-05 (78 שורות, 105 עמודות): קריאת Sheets חיה מרוסנת (sleep 3) — `fetch_phase0_data.py`.

סיווג עם `utils.classify_trade_row` (הפונקציה של המערכת):

| חתך | WIN | LOSS | WHIPSAW | PENDING | NO_TOUCH | מוכרעות |
|---|---|---|---|---|---|---|
| כל השורות (286) | 130 | 75 | 48 | 32 | 1 | 205 |
| score_version=v2 (182) | **81** | **42** | 26 | 32 | 1 | **123** |

- **n=123 אומת בדיוק** (WIN 81 + LOSS 42, v2 בלבד) — תואם PK v2.99.
- פער זעיר: PK טוען "150 כולל WHIPSAW"; בפועל 123+26=**149** (או 150 רק אם סופרים NO_TOUCH).
- PENDING=32: ‏31 ביוני — כולן ScanDate ‏3/6 ואילך (טרם הבשילו 5 ימי מסחר; אפס stale), ‏1 באפריל = SBLX ‏2026-04-28 (delisted, ידוע).
- fill-only spot-check — 3 שורות אפריל שהיו שלמות בגיבוי `post_analysis_backup_recalc_2026-04-16_2005.csv` הושוו תא-תא (20 תאי OHLC לשורה) מול הקריאה הטרייה:
```
AHMA|2026-03-23 diffs: NONE — fill-only held
BIAF|2026-03-23 diffs: NONE — fill-only held
PTLE|2026-03-23 diffs: NONE — fill-only held
```
- אישוש קוד: `backfill_ohlc_v2.py:146` — `if not _is_missing(df.at[pos, key]): continue  # FILL-ONLY`. הערה: שדות stats נגזרים כן נדרסים ב-recompute (by design).
- dry-run חי לא הורץ: `fetch_ohlc` דורש רשת (yfinance) שאסורה בריצה זו → אימות דרך קוד + השוואת snapshot בלבד.

## (ג) skip_summary 2026-06

קריאת הטאב (11Mu1uPBb5izl2eGP4RTsr89wwNqXcmHc62J2fphlo4M): **0 שורות דאטה** (header בלבד).

הסבר מאומת: commit ‏2e88383 (TASK-125) נוצר `2026-06-10T17:49:36-05:00` = אחרי סגירת השוק (15:00 פרו).
אף ריצת agent_minute בשעות מסחר לא רצה עם הקוד החדש → ריק = צפוי, לא כשל.
ריצת 20:59Z (לוג run 27305949435): "Outside market hours, skipping run".
**אימות אמיתי אפשרי רק מחר 11/6 אחרי 08:30 פרו.**

## (ד) 4 כשלי ליל 9/6

```
$ gh run list --created "2026-06-09T20:00:00Z..2026-06-10T02:00:00Z" ... select(.conclusion!="success")
23:07:42Z Agent — Critic (daily) failure 27241647342
23:01:06Z Daily Backup — post_analysis failure 27241370628
22:59:06Z Agent — Daily Brief Email failure 27241283597
22:43:57Z Post Analysis Collector failure 27240647395
```

בכל 4 הריצות אותה שורת שורש (gh run view --log-failed):
```
##[error]error: unable to create file backlog/tasks/task-122 - סנכרון-drift-PK-v2.90-…-.md: File name too long
##[error]The process '/usr/bin/git' failed with exit code 1
```
= שבירת checkout משם-קובץ ארוך, תואם לתיקון `307c0e5` (rename 347B→51B).
מאז התיקון: כל הריצות ב-10/6 (30 האחרונות נבדקו) ירוקות — success.

## (ה) TASK-43 — אפס קריאות Sheets

`git show e061978 --stat`: נגע רק ב-dashboard.py (+13), tests/test_page_visit_v1.py (חדש), PROJECT_STATE.md.
grep על שורות ה-`+` של הקומיט עבור `get_sheet|gspread|open_by_key|worksheet|sheets_manager` → **ריק**.
הלוגר כותב שורת `[PAGE_VISIT]` ל-stdout של Streamlit בלבד.

## סקילים שבוצעו בשלב זה
systematic-debugging (חקירת כשלי לילה), data-quality-checker (אימות n/PENDING).
