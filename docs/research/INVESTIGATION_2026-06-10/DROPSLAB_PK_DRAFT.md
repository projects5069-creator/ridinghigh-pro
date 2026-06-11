# DropsLab — Project Knowledge (טיוטה ראשונה, v0.1)

*נוצר 2026-06-10 במסגרת TASK-139-INV (חקירת עומק). טיוטה — טרם אושרה ע"י עמיחי.*
*עקרון: כמו RidingHigh_Pro_PK_v2 — מסמך זה אמור להפוך למקור-האמת היחיד של DropsLab.*

## 1. מהות

סורק יומי של מניות NASDAQ/NYSE שירדו ≥10% ביום מסחר אחד ("נופלות"), + עוקב post-analysis
שמודד התאוששות/המשך-נפילה ב-D1-D5. מטרה מחקרית: האם יש edge בנופלות (לונג-התאוששות או שורט-המשך).
**ורדיקט מחקרי נוכחי (9/6, אומת מחדש 10/6 על n=2,231): אין אות כיווני יומי בזמן הכניסה.**

## 2. רכיבים

| רכיב | קובץ | תפקיד |
|---|---|---|
| Scanner | `~/DropsLab/drops_scanner.py` (517 שורות) | FINVIZ "Down 10%" → 38 מדדים/מניה → drops_raw |
| Collector | `~/DropsLab/drops_collector.py` (427) | לכל שורת raw: D1-D5 closes מ-yfinance → drops_post |
| Dashboard | `~/DropsLab/dashboard.py` (480) | Streamlit |
| Sheets I/O | `~/DropsLab/gsheets_sync.py` (132) | gspread helpers |
| Migration | `~/DropsLab/migrate_dropslab.py` (131) | חד-פעמי; מכיל OLD_SHEET_ID היסטורי |

- רפו: `projects5069-creator/DropsLab` (git@github.com:projects5069-creator/DropsLab.git)
- **Spreadsheet ID (יחיד, מאומת בקוד בכל 3 הקבצים):** `1XM-qId7HAwEu-8-1GGHcy3RoyyAnsYshjZfDrKFnTMI`
  - טאבים: `drops_raw`, `drops_post`. (ID ישן 1M-ofmSmU... מופיע רק בסקריפט ההגירה — לא בשימוש.)

## 3. Workflows (GitHub Actions ברפו DropsLab)

| workflow | cron | מצב 10/6 |
|---|---|---|
| drops_scan.yml ("Daily Drops Scanner") | יומי ~22:45-22:55Z | ✅ ירוק יומי |
| drops_collect.yml ("Daily Drops Collector") | 30 21 * * 1-5, timeout 20m | ❌ **cancelled יומי מאז 5/6** (timeout; backlog 1,766 שורות; drops_post קפוא על 27/5) |

## 4. סכימה

### drops_raw — 39 עמודות (38 מדדים + scanned_at)
זיהוי (6): date, ticker, company_name, exchange, sector, industry.
גודל (3): market_cap, market_cap_category, shares_float.
מחיר (8): prev_close, open, high, low, close, pct_change, gap_down_pct, intraday_reversal_pct.
ווליום (3): volume, avg_volume_10d, volume_ratio.
טכני (10): week_52_high/low, pct_from_52w_high/low, sma_50, sma_200, pct_vs_sma50/200, rsi_14, beta.
פונדמנטלי (7): pe_ratio, forward_pe, pb_ratio, ps_ratio, debt_to_equity, revenue_ttm, short_float_pct.
אירוע (1): earnings_within_7d. מטא (1): scanned_at.

שיעורי NULL נמדדו 10/6: פונדמנטלים 20-80% חסרים (pe 80%, beta 46%); ליבה מחירית/טכנית ~0-3%.

### drops_post — 25 עמודות בפועל
זהות (4): scan_date, ticker, exchange, sector. בסיס (2): scan_close, scan_pct_change.
D1-D5 (15): d{i}_date, d{i}_close, d{i}_pct. סיכום (3): max_recovery_5d_pct, max_further_drop_5d_pct, pattern_tag. מטא (1): updated_at.
**drift פנימי ידוע: ה-docstring בקוד אומר "22 columns" אבל ה-HEADER בפועל 25.**

## 5. מצב דאטה (נכון ל-2026-06-10 23:00Z)

- drops_raw: 3,994 שורות, 2026-04-02 → 2026-06-10 (~160/יום).
- drops_post: 2,227 שורות, עד 2026-05-27 בלבד (collector תקוע).
- כפילויות מפתח date|ticker: raw 2, post 1.
- זיהום ידוע: d1_pct mean +124% מול median 0.0 — ארטיפקטים של reverse-split ללא דגל audit.

## 6. ממצאי מחקר מצטברים

1. **אין אות כיווני יומי**: P(D1 up)=.496; AUC כל 14 המדדים .457-.524 (אומת 10/6, n=2,231).
2. שורט לא-מסונן ≈ breakeven; לונג bottom-reversal מפסיד בכניסת D1 (מחקר 9/6).
3. ~41% מהנופלים נופלים יותר מפעם (serial fallers, TASK-62/80) — אין edge חזוי גם שם.
4. survivorship: drops_raw מודד עומק-בתוך-נופלים, לא "מי ייפול" (TASK-79).
5. שימוש צולב מבצעי: CHRONIC_DROPPER_BLACKLIST של RidingHigh (AEHL, TDIC) נגזר מ-DropsLab.

## 7. בעיות פתוחות (10/6)

- P1: collector timeout death-spiral (ראו §3) — דורש עיבוד-באצ'ים/checkpoint או הגדלת timeout + ריצת השלמה.
- P2: אין דגל ארטיפקט-split ב-post (מזהם את כל מדדי ה-D).
- P3: docstring "22 columns" מול 25 בפועל; 2+1 כפילויות מפתח.

## 8. Anti-Drift

מסמך זה חייב עדכון בכל שינוי סכימה/workflow/ID — כמו ה-PK של RidingHigh.
גרסה: v0.1 (טיוטה, 2026-06-10, לא מאושרת).
