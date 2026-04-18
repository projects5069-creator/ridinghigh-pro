# 🌙 RidingHigh Pro — תיקונים לילה (16-17 באפריל 2026)

*עמיחי מבקש שהסריקה של מחר תהיה מדויקת. אלה תיקונים טכניים בלבד — בלי החלטות אסטרטגיות.*

---

## ⚠️ חוקי ברזל לפני שמתחילים

1. **לא למחוק כלום** (לא שורות, לא עמודות, לא קבצים)
2. **לגבות לפני כל שינוי** (backup CSV)
3. **Dry-run קודם, apply אחרי** (אם הסקריפט משנה נתונים)
4. **לעצור ולשאול** אם משהו לא ברור
5. **לעשות git commit ו-push רק בסוף**, אחרי שהכל עבד

---

## 🔧 תיקון 1 — באג MxV ב-update_score_tracker()

### הבעיה
`auto_scanner.py` שורה 1263-1266:
```python
mxv = (mkt_cap - price * volume) / mkt_cap    # יחס, למשל -0.31
# ...
metrics = {'mxv': mxv, ...}                    # מועבר ללא *100
calculate_score(metrics)                       # מצפה לאחוזים (-31)
```

**התוצאה:** MxV תורם 0.04 נק' מתוך 25 אפשריות ב-score_tracker.

### התיקון
הכפלת MxV ב-100 לפני העברה ל-metrics dict.

### שלבים
1. `grep -n "mxv" auto_scanner.py` לאיתור המקומות
2. שורה 1263 בערך — למצוא את החישוב
3. להוסיף `mxv = mxv * 100` אחרי החישוב
4. או לחילופין — להכפיל בתוך ה-metrics dict
5. לוודא ששאר המשתנים (analyze_ticker) לא נפגעים

### אימות
- unit test קטן: MxV=-0.31 → בעקבות התיקון → -31 ב-metrics
- לא לבצע push עדיין

---

## 🔧 תיקון 2 — REL_VOL cap

### הבעיה
`auto_scanner.py` שורה 506-507:
```python
avg_vol = info.get('averageVolume', volume)
rel_vol = volume / avg_vol if avg_vol > 0 else 1.0
```

**התוצאה:** max REL_VOL בגיליון = 26,794 (UGRO). ערך בלתי אפשרי פיזית.

### התיקון
הוספת cap של 100 (פי-100 מהממוצע זה כבר קיצוני).

### שלבים
1. מיקום 1: `analyze_ticker()` שורה 506-507
2. מיקום 2: `update_score_tracker()` שורה 1245-1246
3. להוסיף אחרי חישוב:
```python
if rel_vol > 100:
    rel_vol = 100  # cap — ערך גבוה מזה הוא דגל אדום של yfinance bug
```
4. בדיקה ב-dry-run על BATL/UGRO

---

## 🔧 תיקון 3 — בירור DynamicScore

### הבעיה
לא ברור אם DynamicScore נשמר בגיליון או מחושב on-the-fly.

### השלבים
1. `grep -n "DynamicScore" dashboard.py auto_scanner.py`
2. להראות לעמיחי:
   - איפה הוא מוגדר
   - איפה הוא מחושב
   - האם הוא נכתב לאיזה גיליון
3. **רק להראות, לא לתקן**. אם נשמר — נוסיף למשימות של מחר.

---

## 🔧 תיקון 4 — git push של התיקונים

### רק אחרי:
- תיקון 1 עבר unit test
- תיקון 2 עבר dry-run (אימות שמניות תקינות לא נפגעות)
- תיקון 3 רק הצגה (אין מה ל-push)

### שלבים
```bash
git add auto_scanner.py
git status  # לוודא שרק auto_scanner.py השתנה
git diff --stat
git commit -m "fix: MxV percentage bug in score_tracker + REL_VOL cap

- Fix MxV missing *100 multiplier in update_score_tracker()
- Add REL_VOL cap=100 to prevent yfinance outliers (max was 26,794)
- Both fixes prevent score distortion on future scans"
git push origin main
```

---

## ❌ מה אסור לעשות הלילה

- ❌ לתקן SL/TP בדפים (דורש החלטה אסטרטגית)
- ❌ להחזיר Gap ל-Score (דורש backtest)
- ❌ לעדכן KB (עד שתחליט על v1/v2)
- ❌ למחוק שורות BROKEN (השתמש ב-audit_flag במקום)
- ❌ למזג דפים בדשבורד (תכנון עתידי)
- ❌ לגעת ב-dashboard.py (161KB, קל לשבור)
- ❌ לגעת ב-live_trades sheet (דורש תכנון)

---

## ✅ בסוף התהליך

תן לעמיחי דוח קצר:
1. איזה תיקונים בוצעו
2. מה נשאר פתוח
3. האם ה-commit נשלח ל-GitHub
4. הערכה: הסריקה של מחר תהיה תקינה?

---

## 📝 הערה חשובה לך, Claude Code

עמיחי עבד היום הרבה שעות וזה **עייף מאוד**. הוא רוצה לישון בשקט ולדעת שמחר הדאטה יהיה נקי. אל תעשה פעולות מחוץ לרשימה הזו. אם אתה רואה בעיה נוספת — **תעד ב-OPEN_ISSUES.md** ותתרכז ב-4 תיקונים שלמעלה.
