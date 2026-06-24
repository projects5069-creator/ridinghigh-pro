# אבחון — כשל post_analysis collector

> **חתימה:** 2026-06-23 ~20:40 Peru · READ-ONLY · אבחון בלבד (לא תוקן, לא נפתח TASK).
> **עוגן:** HEAD `1da6f2c` · ראיות: `gh run view --log` + `.github/workflows/post_analysis.yml` + `backfill_ohlc_v2.py`.

## ROOT CAUSE
**job-timeout קשיח.** ל-job `collect` יש `timeout-minutes: 15` (`post_analysis.yml:11`).
שרשרת ה-steps 1–7 (checkout/setup/deps/EOD-snapshot/collector/enrich) צורכת ~7–8 דק', וה-step
האחרון **"Backfill missing OHLC"** (`post_analysis.yml:65` → `python backfill_ohlc_v2.py --recent 2 --apply`)
זקוק ליותר מהזמן-השארי. כשסך-ה-job מגיע ל-15 דק', GitHub Actions **הורג את ה-job** וה-step
ה-backfill (האחרון, שעדיין רץ) מסומן `cancelled` עם `##[error]The operation was canceled.`.
**לא concurrency** (אין בלוק `concurrency` ב-yml — אומת 0). **לא exception** (אין Traceback; ה-step נחתך מבחוץ באמצע ריצה).

## ראיות (run-ids + timestamps + ציטוטי-לוג)
דפוס מ-`gh run list --workflow=post_analysis.yml`:
| run-id | conclusion | משך | תאריך |
|---|---|---|---|
| 28060995599 | **cancelled** | 15m17s | 2026-06-23 |
| 27989449695 | **cancelled** | 15m19s | 2026-06-22 |
| 27850704300 | success | 10m11s | 2026-06-19 |
| 27794519433 | **cancelled** | 15m18s | 2026-06-18 |
| 27724742617 | **cancelled** | 15m17s | 2026-06-17 |
| 27653552827 | **cancelled** | 15m18s | 2026-06-16 |
| 27582297971 | success | 9m58s | 2026-06-15 |
| 27447268863 | success | 6m35s | 2026-06-12 |
| 27382516970 | success | 6m51s | 2026-06-11 |
| 27171696789 | success | 1m38s | 2026-06-08 |

- **כל** ה-cancelled מסתיימים ב-**15m17–19s = בדיוק `timeout-minutes: 15`** (+overhead). זו חתימת-timeout.
- log run 28060995599: `22:28:05 python backfill_ohlc_v2.py --recent 2 --apply` → `22:35:20 ##[error]The operation was canceled.` (job-start 22:20:05 → 15m15s).
- log run 27724742617: `22:57:21 backfill started` → `23:05:00 ##[error]The operation was canceled.` (job-start 22:49:46 → 15m14s).
- step-conclusions (jobs API), שתי הריצות זהות: steps 1–7 = **success**; **"Backfill missing OHLC" = cancelled**; "Complete job" = success.

## מנגנון (symptom→origin)
1. **origin:** עומס ה-backfill גָּדֵל עם הזמן — `backfill_ohlc_v2.py` עובר על כל שורה חסרת-OHLC בחלון `--recent 2` (חודש נוכחי+קודם), ולכל מועמד עושה `fetch_ohlc` (רשת, 4 ניסיונות, חלון 15-יום — `backfill_ohlc.py:37`) + `time.sleep(0.4)` rate-limit per-row (`backfill_ohlc_v2.py:152,172`). ככל שהחודש מצטבר (6/17: "75 total" → 6/23: "90 total" שורות), מספר המועמדים והזמן גדלים.
2. גם ה-steps הקודמים שמנים (collector לבד ~6 דק' בלוג) → נשארות ~7 דק' בלבד ל-backfill.
3. סך-הריצה חצה את תקרת ה-15 דק' — בהדרגה: 6/08 ~1.6דק' → 6/10–12 ~6.5דק' → 6/15/19 ~10דק' → **6/16 ואילך נוגע/חוצה 15דק'**.
4. ב-15 דק' GitHub הורג את ה-job; ה-backfill (אחרון) נחתך → `cancelled`.
5. **הצלחות-ביניים (6/19, 10דק')** = ימים שבהם עומס-ה-backfill במקרה נכנס מתחת ל-15 → לסירוגין-אך-תכוף, צמוד-לתקרה.

## DOWNSTREAM (מה נשבר — ומה לא)
- **לא נשבר:** EOD-snapshot, Collector (6/23: "90 upserted"), Enrich — **כולם הושלמו ב-success**. הליבה היומית כן נשמרת ל-sheets.
- **כן נשבר:** רק שלב ה-backfill — מילוי D1–D5 OHLC לשורות שחסרו + recompute של TP10_Hit/MaxDrop%/NetPnL לאותן שורות (`STATS_KEYS`). שורות שדרשו backfill נשארות עם **OHLC/stats חסרים** עד שריצה תספיק. (תואם לממצא §4 בדו"ח-הסטטוס: TP10_Hit/MaxDrop% fill ~87% ביוני — אלה בדיוק השורות הלא-backfilled.)
- אבחנה מתקנת לדו"ח-הסטטוס: לא "pipeline שבור" — אלא **"ה-pipeline מסתיים עד enrich; רק backfill חסר"**.

## אופציות-תיקון (flags מנומקים — לא המלצה, לא בוצע; ההכרעה שלך)
- ⚐ **(א) הגדלת `timeout-minutes`** (15→25/30). trade-off: הכי פשוט; אבל מסתיר את הגידול (יחזור כשהדאטה תגדל עוד), וצורך עוד GH-minutes.
- ⚐ **(ב) פיצול ה-backfill ל-workflow/job נפרד** עם timeout משלו. trade-off: ה-collector מסתיים מהר ואמין; ה-backfill מבודד; עלות = עוד workflow לתחזק.
- ⚐ **(ג) חסימת/ייעול העומס** — `--recent 1` או cap-מועמדים-לריצה, או batch-fetch / הסרת `time.sleep(0.4)`. trade-off: backfill עשוי להתפרס על כמה ימים להדביק פער; הסרת sleep = סיכון rate-limit מול Alpaca.
- (משני) ה-steps הקודמים שמנים (~7–8דק') — ייעול collector/enrich יפנה תקציב, אך לא שורש.

---
*אבחון read-only. ללא commit. ראיות: gh run-ids 28060995599 / 27724742617 / רשימת 12 ריצות; post_analysis.yml:11,65; backfill_ohlc_v2.py:37,138,152,172.*
