# RidingHigh Pro - תיעוד מלא של הפרויקט

**תאריך יצירה:** 17 מרץ 2026  
**משתמש:** adilevy (Lima, Peru - UTC-5)  
**מחשב:** MacBook Pro  
**מטרה:** סורק מניות אוטומטי לאסטרטגיית short-selling

---

## 📋 תוכן עניינים

1. [מידע כללי](#מידע-כללי)
2. [ארכיטקטורה](#ארכיטקטורה)
3. [מערכת הציונים](#מערכת-הציונים)
4. [קבצים ותיקיות](#קבצים-ותיקיות)
5. [שעות מסחר](#שעות-מסחר)
6. [תהליכים אוטומטיים](#תהליכים-אוטומטיים)
7. [בעיות שנפתרו](#בעיות-שנפתרו)
8. [משימות עתידיות](#משימות-עתידיות)
9. [פקודות שימושיות](#פקודות-שימושיות)

---

## 🎯 מידע כללי

### מטרת המערכת
- סריקת מניות בזמן אמת לזיהוי הזדמנויות short-selling
- מעקב אחר 10 מדדים טכניים משוקללים
- ציון סופי 0-100 (85+ = CRITICAL, 60-84 = High Risk)

### העקרונות המנחים
1. **אמינות נתונים** - FINVIZ כמקור ראשי, Yahoo Finance למדדים טכניים
2. **מעקב רציף** - מניה שנכנסה למעקב ממשיכה עד סוף יום המסחר
3. **שמירת נתונים** - כל דבר נשמר ומגובה
4. **Market Cap מההיסטוריה** - אם פעם היה Market Cap, הוא תמיד זמין

---

## 🏗️ ארכיטקטורה

### גרסה נוכחית: v12.0 (17 מרץ 2026)

### מרכיבים עיקריים:

#### 1. Dashboard Class
**תפקיד:** מנהל את כל הסריקות והניתוחים

**מתודות מרכזיות:**
- `fetch_finviz_data()` - משיכת Top 20 מניות מ-FINVIZ
- `preload_market_caps()` - טעינה מוקדמת של Market Caps
- `analyze_ticker_complete()` - ניתוח מלא של מניה מ-FINVIZ
- `analyze_ticker_from_yahoo()` - ניתוח מניה שיצאה מ-Top 20
- `get_from_history_all_days()` - חיפוש Market Cap בכל ההיסטוריה
- `scan()` - סריקה מלאה (Top 20 + מניות במעקב)
- `calculate_score()` - חישוב ציון משוקלל

**Cache System:**
```python
self.market_cap_cache = {}  # Market Cap של כל מניה
self.shares_cache = {}      # Shares Outstanding
```

#### 2. LiveTracker Class
**תפקיד:** ניהול Timeline Grid וארכיון

**מתודות מרכזיות:**
- `add_minute_data()` - הוספת ציון לטיימליין
- `get_today_grid()` - קריאת Timeline של היום
- `save_daily_snapshot()` - שמירת TABLE 1 ב-14:59
- `archive_today()` - ארכיון TABLE 2 ב-14:59
- `get_tracked_tickers()` - רשימת מניות במעקב

#### 3. DataLogger Class
**מיקום:** `data_logger.py`

**תפקיד:** שמירת snapshots יומיים

---

## 🎯 מערכת הציונים

### 10 מדדים (סה"כ 100 נקודות)

| # | מדד | משקל | סף (Threshold) | הסבר |
|---|------|------|----------------|------|
| 1 | **MxV** | 20% | -50% | Market Cap vs Volume - ככל שיותר שלילי, יותר מסוכן |
| 2 | **Price to 52W High** | 10% | +100% | המחיר ביחס לשיא שנתי |
| 3 | **Price to High (daily)** | 15% | -10% | כמה המחיר ירד מהשיא היומי |
| 4 | **REL VOL** | 15% | 2x | נפח יחסי לממוצע |
| 5 | **RSI** | 15% | 80 | Relative Strength Index |
| 6 | **ATRX** | 10% | 15% | Average True Range % |
| 7 | **Run-Up** | 5% | -5% | עלייה מהפתיחה |
| 8 | **Float %** | 5% | 10% | אחוז המניות הנסחרות |
| 9 | **Gap** | 3% | 20% | פער בפתיחה |
| 10 | **VWAP** | 2% | 15% | מרחק מ-VWAP |

### קוד צבעים:
```
🟥 Bordeaux (#800020): 85-100  - CRITICAL (סיכון קריטי)
🔴 Red (#cc0000):     60-84   - High Risk (סיכון גבוה)
🟠 Orange (#ff6600):  40-59   - Medium Risk (סיכון בינוני)
🟡 Yellow (#ffcc00):  0-39    - Low Risk (סיכון נמוך)
```

---

## 📁 קבצים ותיקיות

### מבנה התיקיות:
```
~/RidingHighPro/
├── dashboard.py              # קובץ ראשי (v12.0)
├── data_logger.py           # שמירת snapshots
├── config.py                # קונפיגורציה
├── PROJECT_DOCUMENTATION.md # התיעוד הזה
│
├── data/
│   ├── 2026-03-17.csv       # Snapshot אחרון (מתעדכן כל סריקה)
│   │
│   ├── live_tracker/
│   │   └── tracker_YYYY-MM-DD.csv    # Timeline Grid יומי
│   │
│   ├── timeline_archive/
│   │   └── timeline_YYYY-MM-DD.csv   # ארכיון ב-14:59
│   │
│   └── daily_snapshots/
│       └── snapshot_YYYY-MM-DD.csv   # TABLE 1 ב-14:59
│
└── Desktop/
    └── RidingHighPro.command         # קיצור דרך
```

### פורמט הקבצים:

#### tracker_YYYY-MM-DD.csv (Timeline Grid):
```csv
Ticker,11:51,11:55,12:00,12:01,...,14:59
BIAF,80.73,80.34,80.33,80.25,...,79.98
CREG,78.09,77.85,None,None,...,76.54
```
- **Index:** Ticker
- **Columns:** זמנים (HH:MM)
- **Values:** ציונים (0-100)

#### snapshot_YYYY-MM-DD.csv (TABLE 1):
```csv
Ticker,Score,Price,Change,MxV,RSI,ATRX,REL_VOL,...
BIAF,80.73,12.45,+36.9%,-204.5%,78.2,12.6,21.9,...
```
- כל העמודות והמדדים
- נשמר ב-14:59

---

## ⏰ שעות מסחר

### Peru Time (UTC-5):
```python
market_open  = 08:30  # פתיחת מסחר
market_close = 15:00  # סגירת מסחר
```

### New York Time (UTC-5):
```
Same as Peru!
```

### בדיקה:
```python
def is_market_hours():
    now = datetime.now()
    market_open = dt_time(8, 30)
    market_close = dt_time(15, 0)
    current_time = now.time()
    is_weekday = now.weekday() < 5
    return is_weekday and market_open <= current_time <= market_close
```

---

## 🤖 תהליכים אוטומטיים

### 1. Auto-Scan (כל דקה בשעות מסחר)

**מתי:** 08:30-15:00 (ימי א'-ה')  
**תדירות:** כל 60 שניות  
**מה קורה:**
1. סריקת Top 20 מ-FINVIZ
2. ניתוח מניות שבמעקב אבל לא ב-Top 20
3. שמירה ל-Timeline Grid
4. עדכון TABLE 1 ו-TABLE 2

**קוד:**
```python
auto_scan = st.sidebar.checkbox(
    "🔄 Auto-Scan (every minute)", 
    value=is_market_hours()
)
```

### 2. Snapshot + Archive ב-14:59

**מתי:** 14:59:00 - 14:59:59  
**מה קורה:**
1. ✅ שמירת TABLE 1 → `daily_snapshots/snapshot_YYYY-MM-DD.csv`
2. ✅ ארכיון TABLE 2 → `timeline_archive/timeline_YYYY-MM-DD.csv`

**למה:** כדי שתוכל לסגור את המחשב ב-15:00 והכל יישמר!

**קוד:**
```python
if check_snapshot_time() and not st.session_state.snapshot_done_today:
    tracker = LiveTracker()
    
    # TABLE 1
    if st.session_state.results:
        tracker.save_daily_snapshot(st.session_state.results)
    
    # TABLE 2
    tracker.archive_today()
    
    st.session_state.snapshot_done_today = True
```

### 3. איפוס דגלים בחצות

**מתי:** 00:00-00:05  
**מה קורה:** איפוס `snapshot_done_today` ל-False

---

## 🔧 בעיות שנפתרו

### 1. ✅ None בטיימליין (פתרון חלקי)
**בעיה:** מניות מקבלות None אחרי שהיה להן ציון  
**סיבה:** Yahoo Finance לא מחזיר Market Cap  
**פתרון נוכחי:** חיפוש בהיסטוריה עם `get_from_history_all_days()`  
**פתרון עתידי:** קובץ cache קבוע (מחר!)

### 2. ✅ גלילה פנימית בטבלאות
**בעיה:** טבלאות עם גלילה פנימית  
**פתרון:**
- TABLE 1: `height=600`
- TABLE 2: `height=1000`
- גלילה רק בדפדפן

### 3. ✅ Change% מ-FINVIZ
**בעיה:** FINVIZ מחזיר 0.3726 במקום 37.26%  
**פתרון:** `change = float(change) * 100`

### 4. ✅ ארכיון לפני כיבוי המחשב
**בעיה:** ב-18:00 המחשב כבוי → אין ארכיון  
**פתרון:** Snapshot + Archive ב-14:59!

### 5. ✅ מעקב רציף
**בעיה:** מניה יוצאת מ-Top 20 → מפסיקים לעקוב  
**פתרון:** `tracked_tickers` + `analyze_ticker_from_yahoo()`

### 6. ✅ Session State persistence
**בעיה:** כל סריקה אוטומטית יוצרת Dashboard() חדש → cache ריק  
**פתרון:** `st.session_state.dashboard = Dashboard()` (פעם אחת!)

### 7. ✅ Market Cap Fallback (4 שכבות)
```python
1. FINVIZ → parse_market_cap()
2. Yahoo.info → info.get('marketCap')
3. Yahoo.calc → shares * price
4. History → get_from_history_all_days()
```

---

## 📝 משימות עתידיות

### ⏳ מחר (18 מרץ 2026):

#### 1. Market Cap Cache File 🔥
**בעיה:** מניות מקבלות None למרות שיש להן Market Cap בהיסטוריה  
**פתרון:**
```python
# קובץ: data/market_cap_cache.json
{
  "CREG": 234567890,
  "LIDR": 345678901,
  "LFS": 456789012,
  ...
}
```

**תהליך:**
1. טעינת cache בהתחלה
2. כל Market Cap שנמצא → שמירה לקובץ
3. קריאה מהקובץ לפני חיפוש בהיסטוריה
4. **לעולם לא צריך לחפש פעמיים!**

### 🔮 עתיד רחוק:

#### 2. Deploy ל-PythonAnywhere
- $5/חודש
- 24/7 uptime
- לא תלוי במחשב

#### 3. התראות Telegram
- ציון > 85 → התראה מיידית
- ציון > 90 → התראה דחופה

#### 4. ניתוח שבועי/חודשי
- אילו מדדים חזו הכי טוב את הירידות?
- כמה מניות עם ציון 85+ באמת צנחו?
- התאמת משקלי המדדים

#### 5. Trend Reversal Detection
- זיהוי היפוך מגמה
- פאניק בשוק
- עלייה חדה בנפח

---

## 💻 פקודות שימושיות

### הרצה:
```bash
python3 -m streamlit run ~/RidingHighPro/dashboard.py
```

### קיצור דרך מהדסקטופ:
```bash
~/Desktop/RidingHighPro.command
```

### בדיקת קבצים:
```bash
# Timeline של היום
cat ~/RidingHighPro/data/live_tracker/tracker_$(date +%Y-%m-%d).csv

# Snapshot של היום
cat ~/RidingHighPro/data/daily_snapshots/snapshot_$(date +%Y-%m-%d).csv

# ארכיון של היום
cat ~/RidingHighPro/data/timeline_archive/timeline_$(date +%Y-%m-%d).csv

# רשימת כל הקבצים
ls -lh ~/RidingHighPro/data/
```

### ניקוי Timeline:
```bash
rm ~/RidingHighPro/data/live_tracker/tracker_$(date +%Y-%m-%d).csv
```

### ארכיון ידני (אם צריך):
```bash
cd ~/RidingHighPro
python3 << 'EOF'
import shutil
import os
from datetime import datetime

tracker_file = f"data/live_tracker/tracker_{datetime.now().strftime('%Y-%m-%d')}.csv"
archive_dir = "data/timeline_archive"
os.makedirs(archive_dir, exist_ok=True)

if os.path.exists(tracker_file):
    archive_file = os.path.join(archive_dir, f"timeline_{datetime.now().strftime('%Y-%m-%d')}.csv")
    shutil.copy2(tracker_file, archive_file)
    print(f"✅ Archived: {archive_file}")
EOF
```

---

## 🐛 איך לדבג בעיות

### מניה מקבלת None:

1. **בדוק אם יש לה Market Cap בהיסטוריה:**
```bash
cd ~/RidingHighPro
python3 << 'EOF'
import pandas as pd
from data_logger import DataLogger

logger = DataLogger()
dates = logger.get_all_dates()

ticker = "CREG"  # שנה לטיקר שאתה מחפש

for date in dates:
    df = logger.load_date(date)
    if df is not None and 'Ticker' in df.columns:
        matching = df[df['Ticker'] == ticker]
        if not matching.empty:
            mc = matching.iloc[-1].get('MarketCap', None)
            if mc and mc > 0:
                print(f"{date}: MarketCap = {mc:,.0f}")
EOF
```

2. **בדוק אם היא במעקב:**
```bash
cd ~/RidingHighPro
python3 << 'EOF'
import pandas as pd

tracker_file = "data/live_tracker/tracker_2026-03-17.csv"
df = pd.read_csv(tracker_file, index_col=0)

ticker = "CREG"
if ticker in df.index:
    print(f"✅ {ticker} is tracked!")
    print(df.loc[ticker])
else:
    print(f"❌ {ticker} NOT tracked")
EOF
```

3. **בדוק את ה-cache:**
```python
# בתוך dashboard.py
print(f"Market Cap Cache: {st.session_state.dashboard.market_cap_cache}")
print(f"Shares Cache: {st.session_state.dashboard.shares_cache}")
```

---

## 📊 Google Sheets (רפרנס)

### מבנה הגיליון המקורי:

| עמודה | שם | פורמולה |
|-------|-----|----------|
| L | STOCK | - |
| M | PRICE | - |
| N | CHANGE | - |
| O | MxV | `=(L2-(M2*N2))/L2` |
| P | RSI | - |
| Q | ATR-X | - |
| R | REL VOL | - |
| S | Run-Up | - |
| T | Gap | - |
| U | VWAP | - |
| V | Score | נוסחה משוקללת |

### FINVIZ Import:
```
=IMPORTHTML("https://finviz.com/screener.ashx?v=171&f=sh_price_o2,ta_perf_d10o&ft=4&o=-change","table",32)
```

---

## 🎓 הערות חשובות

### העדפות משתמש (adilevy):
1. ✅ **תמיד קוד מלא** - לא קטעים חלקיים
2. ✅ **לא יודע לערוך שורות** - רק copy-paste
3. ✅ **תמיד לבדוק לפני כתיבה** - הרצת בדיקות debug
4. ✅ **שעות מסחר בזמן Peru** - 08:30-15:00
5. ✅ **2 ספרות אחרי הנקודה** - תמיד 77.63 (לא 77.6 או 77.633)

### כללי תקשורת:
- 🇮🇱 תקשורת בעברית
- 📝 תיעוד באנגלית
- 💬 הסברים בעברית + אמוג'י
- 🚀 תמיד אופטימי ומעודד!

---

## 🔐 אבטחה ופרטיות

### לא לשמור:
- ❌ API Keys
- ❌ Passwords
- ❌ Personal data

### כן לשמור:
- ✅ Ticker symbols
- ✅ Market data
- ✅ Scores
- ✅ Timestamps

---

## 📞 תמיכה

### אם משהו לא עובד:

1. **בדוק את ה-logs:**
```bash
# בטרמינל שבו רץ streamlit
# תראה שגיאות אדומות
```

2. **restart את Streamlit:**
```bash
# Ctrl + C בטרמינל
# אחר כך:
python3 -m streamlit run ~/RidingHighPro/dashboard.py
```

3. **בדוק את הקבצים:**
```bash
ls -lh ~/RidingHighPro/data/
```

4. **נקה cache:**
```bash
rm -rf ~/.streamlit/cache
```

---

## 📜 היסטוריית גרסאות

### v12.0 (17 מרץ 2026) - CURRENT
- ✅ Snapshot + Archive ב-14:59
- ✅ גלילה אופקית ב-TABLE 2
- ✅ מעקב רציף עם Market Cap מההיסטוריה

### v11.0 (17 מרץ 2026)
- ✅ Snapshot ב-14:59
- ✅ Archive ב-18:00

### v10.0 (17 מרץ 2026)
- ✅ Market Cap fallback מההיסטוריה
- ✅ גלילה אופקית

### v9.0 (17 מרץ 2026)
- ✅ מעקב רציף
- ✅ Timeline Archive page

### v8.0 (17 מרץ 2026)
- ✅ Session state persistence
- ✅ Pre-loading cache system
- ✅ FINVIZ כמקור ראשי

### v1.0-v7.0 (15-17 מרץ 2026)
- התפתחות ראשונית
- UI fixes
- Background scanning
- Data sources

---

## 🎯 סיכום

**RidingHigh Pro הוא מערכת מעקב מניות מתקדמת שמשלבת:**
- 📊 10 מדדים טכניים משוקללים
- 🔄 מעקב אוטומטי כל דקה
- 💾 שמירת נתונים מלאה
- 📈 Timeline Grid עם גלילה אופקית
- 🎯 ציונים צבעוניים לזיהוי מהיר
- 🤖 ארכיון אוטומטי

**המערכת פועלת 24/6 (ימי א'-ה', 08:30-15:00) ושומרת את כל הנתונים לניתוח עתידי!**

---

**תאריך עדכון אחרון:** 17 מרץ 2026, 20:30  
**גרסה:** v12.0  
**סטטוס:** ✅ Production Ready (מלבד Market Cap cache)
