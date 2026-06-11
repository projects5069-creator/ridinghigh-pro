# שלב 4 — ראיות גולמיות (דאטה: headers / כפילויות / PENDING / splits / 2026-07 / DropsLab ID)

מקורות: אפריל+מאי — קריאת Sheets חיה מרוסנת (שלב 0); יוני — artifact גיבוי 23:09Z.
כל החיבורים לפי שם-עמודה (header-aware), אפס מיקומים.

## (א) השוואת headers — post_analysis 04/05/06

- אפריל: 122 עמודות; מאי/יוני: 105.
- 17 עמודות קיימות רק באפריל: `Volume, MarketCap, CurrentPrice, EntryChange%, Float_pct_raw, PriceToHigh_raw, PriceTo52WHigh_raw, Score_B..Score_I, EntryScore, Score_recalc_date` — שאריות מחקר v1/וריאנטים.
- מאי מול יוני: **אותה קבוצת עמודות אך בסדר שונה** — מאינדקס 60: ביוני `score_version` הוזז לפני בלוק IntraHigh (מאי: `...ScoreStd, audit_flag, IntraHigh...score_version בסוף`; יוני: `audit_flag, score_version, IntraHigh...`).
- השלכה: כל קורא מבוסס-מיקום ישבר בין חודשים. (הקוד קורא לפי שם — תקין; סקריפטים חד-פעמיים בסיכון.)

## (ב) כפילויות Ticker+ScanDate

אפריל 0, מאי 0, יוני 0 — **נבדק — נקי**.

## (ג) מיפוי PENDING + הטיית delisting

| חודש | PENDING | סיווג |
|---|---|---|
| 2026-04 | 1 | SBLX 28/4 — delisted (ידוע) |
| 2026-05 | 0 | — |
| 2026-06 | 31 | כולן ScanDate ≥3/6 — טרם הבשילו 5 ימי מסחר (3/6→D5=10/6 שנסגר רק היום); אפס fetch-ריק, אפס חג |

**הטיית delisting: מועמדת אחת בלבד (SBLX).** שורט על מניה שנמחקת הוא לרוב ניצחון מקסימלי
שלא נספר ב-WR — אבל גם לא-ניתן-לכיסוי בפועל. בהיקף נוכחי (1/124 ≈ 0.8%) ההטיה זניחה.
(40 שורות-החג שוחררו היום ע"י ה-backfill — אומת בשלב 0.)

## (ד) חשודות reverse-split / ערכים קיצוניים

קריטריון: audit_flag BROKEN/PRE_SPLIT, או ScanPrice>500, או |RunUp|>1000%, או D1_High/ScanPrice>5.

| חודש | n | פירוט |
|---|---|---|
| אפריל | 8 | AHMA, RDGT (D1_High=417 על ScanPrice=3.5!), UCAR — BROKEN v1; UGRO (D1 36.3/7.2, **CLEAN** — לא מסומן); PBM, WNW, ELPW, GNLN — PRE_SPLIT v2 |
| מאי | 1 | **TDIC 12/5: D1_High=29.99 על ScanPrice=2.63, audit_flag=CLEAN, v2** — כמעט ודאי reverse-split; מסווג LOSS ונכלל ב-n=123 |
| יוני | 2 | INHD 8/6 (RunUp 1009%), PAVS 8/6 (D1_High 26.0/ScanPrice 2.28) — שניהם SUSPICIOUS בלבד |

השלכה: לפחות שורה אחת (TDIC) מזהמת את ה-123 כ-LOSS מלאכותי; PAVS צפויה להזדהם בהבשלה.
validate_stock_data בודק PRE_SPLIT רק בזמן הסריקה (Week52High/ATR מול מחיר) — split שקורה
**אחרי** הסריקה (בחלון D1-D5) לא נתפס לעולם. אין בדיקת D-day-jump ב-audit.

## (ה) כפילות RH-2026-07-post_analysis

Drive query (OAuth, name exact, READ-ONLY):
```
RH-2026-07-post_analysis | 1C_9rjTIvxcXwkQ34xtkqI2SzkWFAw2O3Uf_Dypc05_k | created=2026-06-01T20:48:18Z | parent=1U2Syqbf...
RH-2026-07-post_analysis | 1ASXu2wvJyPqIBaBrgc3Nffg3ExC6a_CvEcRP-7yEJwM | created=2026-06-01T20:47:07Z | parent=1IaqLrVq...
```
**שני עותקים קיימים** (נוצרו בהפרש 71ש' — כנראה ריצת prepare_next_month כפולה/חלקית ב-1/6).
sheets_config.json["2026-07"]["post_analysis"] מצביע על **1C_9rj** (המאוחר). העותק 1ASXu2 יתום —
ב-parent אחר. הערה: דרך ה-service-account נראה רק 1C_9rj (היתום לא משותף ל-SA) — סיכון בלבול עתידי. לא תוקן (READ-ONLY).

## (ו) DropsLab Sheet ID בשימוש

`~/DropsLab/drops_scanner.py:31`, `drops_collector.py:34`, `dashboard.py:23` — שלושתם:
`1XM-qId7HAwEu-8-1GGHcy3RoyyAnsYshjZfDrKFnTMI` ✓ (הנכון). הישן (1M-ofmSmUHAb...) מופיע רק
ב-migrate_dropslab.py כ-OLD_SHEET_ID (לגיטימי — סקריפט הגירה).

## סקילים שבוצעו בשלב זה
data-quality-checker (headers/dups/PENDING/splits), data:explore-data עקרונות פרופיילינג.
