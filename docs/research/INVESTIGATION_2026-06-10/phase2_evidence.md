# שלב 2 — ראיות גולמיות (auto_scanner.py, 1380 שורות)

## 1. analyze_ticker — טיפול Change% של FINVIZ

`auto_scanner.py:124-126`:
```python
change = float(finviz_row.get('Change', None))
if pd.isna(change): return None
change = change * 100
```
finvizfinance מחזיר Change כשבר עשרוני → הכפלה ב-100 נכונה. בענף ה-tracked-tickers
(`:371-373`) change מחושב באחוזים ואז נארז `{'Change': change/100}` לפני הקריאה ל-analyze_ticker —
**עקבי, נבדק — נקי**. זה מקור ScanChange% המאוחסן (FINVIZ live) — מסביר את ממצא ה-lineage משלב 1.

## 2. נקודות שבהן הערך הנכתב ≠ המחושב / חוסר-עקביות פנימי

| # | מיקום | ממצא |
|---|---|---|
| 2.1 | `:225-232` | `typical_price`/`TypicalPriceDist` מחושבים מה-high המקורי של הבר, ואז `if high_today <= price: high_today = price` משכתב את high_today. כשהבר היומי מפגר: High_today הנכתב=price (מותאם), TypicalPrice הנכתב=מבוסס high ישן, PriceToHigh=0.0 בדיוק. שלושה ערכים באותה שורה לא עקביים זה עם זה. |
| 2.2 | `:880-886` | update_ticker_follow_up מחשב RSI ידנית עם `rolling(14).mean()` (SMA) בעוד analyze_ticker משתמש ב-`ta.RSIIndicator` (Wilder EWM) — שני אלגוריתמי RSI שונים מספרית לאותה עמודת RSI. הפרת §10 (single calculator). |
| 2.3 | `:906-907` | typical_price_dist מחושב inline במקום formulas.calculate_typical_price_dist (שקול מתמטית, אבל מחשבון כפול — §10). |
| 2.4 | `:1183` | sync_score_tracker רושם "Price"=close של בר יומי (לא ציטוט חי) תחת ScanTime דקתי — סמנטיקת Price שונה בין timeline_live (FINVIZ live) ל-score_tracker (daily bar). |
| 2.5 | `:1036,1040` | update_live_trades בעת SL/TP: PnL מחושב מ-sl_price/tp10_price המדויקים — מניח יציאה בדיוק במחיר הסף (אפס slippage/gap-through). RunningHigh יכול להיות הרבה מעל SL והרישום עדיין -10.0%. רלוונטי לריאליזם (שלב 6ג). |
| 2.6 | `:1320-1344` (run_eod) | portfolio EOD: BuyPrice = המחיר בשורת **peak-Score** של היום (drop_duplicates על peak) — "כניסה" שנקבעת בדיעבד בסוף היום במחיר שהיה ידוע רק אינטרא-דיי. זהו מנגנון look-ahead מובנה בכניסות ה-portfolio (נבחן כמותית בשלב 6ד). |

## 3. side effects שקטים

- `analyze_ticker` ממוטט הכל ל-`except: return None` (:308) — טיקר שנכשל נעלם בלי זכר.
- גלובלים `_mc_cache`/`_shares_cache` מתמלאים תוך כדי analyze; `save_mc_cache()` כותב JSON מקומי על ה-runner (אפמרלי — נעלם בסוף ה-job; ה-cache בפועל חי רק בתוך ריצה).
- `df_to_sheet` = `ws.clear()` ואז `safe_update` — דפוס דריסה מלאה. משמש כל דקה ל-portfolio_live ול-live_trades: כשל בין clear ל-update (למשל 429 שמיצה retries) = אובדן כל הגיליון. ה-retry של safe_update מקטין אך לא מאפס את הסיכון.
- כשלי כתיבה בכל המעדכנים נבלעים ב-print בלבד — הריצה מסתיימת "ירוקה" ב-Actions גם אם אף כתיבה לא הצליחה (אין exit-code שאינו 0).

## 4. ספירת קריאות Sheets לריצת run_scan (סטטית, מהקוד)

ריצת דקה רגילה (לא snapshot, דקה%5≠0):
| קריאה | מקור | API reads |
|---|---|---|
| timeline_live (cache, pre-write) | :353 | 1 |
| timeline_live header row_values(1) | :425 | 1 |
| portfolio get_all_values | :607 | 1 |
| portfolio_live get_all_values | :627 | 1 |
| live_trades get_all_values | :993 | 1 |
| **סה"כ** | | **~5** (+ קריאות metadata של open_by_key לכל get_worksheet) |

דקה%5==0 מוסיף: ticker_follow_up get_all_values (1), timeline_live post-write (1, cache-miss אחרי invalidate), portfolio נוסף ב-score_tracker (1), score_tracker row_values(1) (1) → **~9**.
חלון snapshot (14:55-15:05) מוסיף: daily_snapshots (1), portfolio (1), daily_summary (1), timeline post-write (1) → **עד ~12-13**.

הערה חשובה: מונה TASK-112 ("total=1") סופר **רק cache-misses דרך get_sheet_values** — כל ה-get_all_values הגולמיים של portfolio/portfolio_live/live_trades/ticker_follow_up עוקפים את המונה. הקביעה "scanner=1 read/run" שב-PK v2.81 נכונה רק למונה, לא לקריאות בפועל (~5-13). CAVEAT הזה כבר מתועד ב-PK v2.81 + TASK-113, אבל שווה לחדד שהפער הוא פי-5 ויותר.

## 5. run_eod

קורא timeline_live מלא פעם ביום (raw get_all_values, :1302 — מחוץ ל-cache בכוונה, פעם ביום),
מוסיף ל-portfolio את עוברי ה-70 שפוספסו בחלון ה-snapshot (לפי peak), ומריץ _save_daily_summary.
דריסת daily_summary היא upsert מלא (df_to_sheet). נבדק — תואם לתיעוד.

## סקילים שבוצעו בשלב זה
systematic-debugging (מעקב זרימת ערכים writer-by-writer), data-quality-checker (עקביות ערכים נכתבים).
