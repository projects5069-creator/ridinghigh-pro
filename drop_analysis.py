"""
RidingHigh Pro — Deep Drops Analysis
מריץ ניתוח מעמיק על post_analysis כדי להבין מה אפשר להפיק מהירידות.
"""
import gspread, json
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('google_credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

config = json.load(open('sheets_config.json'))
all_dfs = []
for month, sheets in config.items():
    try:
        ws = gc.open_by_key(sheets['post_analysis']).sheet1
        rows = ws.get_all_values()
        if len(rows) < 2:
            continue
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df['_month'] = month
        all_dfs.append(df)
    except Exception as e:
        print(f"❌ {month}: {e}")

df = pd.concat(all_dfs, ignore_index=True)
print(f"\n{'='*70}")
print(f"📊 RidingHigh Pro — ניתוח עומק ירידות")
print(f"{'='*70}\n")
print(f"סה\"כ רשומות: {len(df)}")
print(f"חודשים: {sorted(df['_month'].unique())}\n")
print(f"עמודות זמינות ({len(df.columns)}):")
for i, c in enumerate(df.columns):
    print(f"  {i+1:2d}. {c}")

# המר עמודות מספריות
numeric_cols = []
for c in df.columns:
    if c in ['Ticker', 'ScanDate', '_month']:
        continue
    try:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        if df[c].notna().sum() > 10:
            numeric_cols.append(c)
    except:
        pass

print(f"\nעמודות מספריות עם דאטה: {len(numeric_cols)}")

# חפש עמודות ירידה רלוונטיות
drop_cols = [c for c in df.columns if any(k in c.lower() for k in 
             ['drop', 'low', 'max', 'min', 'd1', 'd2', 'd3', 'd4', 'd5', 'tp', 'sl', 'pnl'])]
print(f"\nעמודות רלוונטיות לירידות: {drop_cols}\n")

# ===== ניתוח 1: התפלגות MaxDrop% =====
print(f"\n{'='*70}")
print("1️⃣  התפלגות ירידה מקסימלית (MaxDrop%) — מה גודל הירידה האמיתי?")
print(f"{'='*70}")

drop_col = None
for candidate in ['MaxDrop%', 'MaxDrop', 'Max_Drop', 'MaxDropPct']:
    if candidate in df.columns:
        drop_col = candidate
        break

if drop_col:
    dd = df[drop_col].dropna()
    print(f"\nעמודה: {drop_col}")
    print(f"תצפיות: {len(dd)}")
    print(f"ממוצע:  {dd.mean():.2f}%")
    print(f"חציון:  {dd.median():.2f}%")
    print(f"מינימום: {dd.min():.2f}%")
    print(f"מקסימום: {dd.max():.2f}%")
    print(f"\nהתפלגות:")
    bins = [-100, -30, -20, -15, -10, -7, -5, -3, 0, 100]
    labels = ['<-30%', '-30 עד -20', '-20 עד -15', '-15 עד -10', '-10 עד -7', 
              '-7 עד -5', '-5 עד -3', '-3 עד 0', '>0%']
    dd_bin = pd.cut(dd, bins=bins, labels=labels)
    counts = dd_bin.value_counts().sort_index(ascending=False)
    for label, c in counts.items():
        pct = c / len(dd) * 100
        bar = '█' * int(pct / 2)
        print(f"  {label:18s} {c:4d}  ({pct:5.1f}%)  {bar}")

# ===== ניתוח 2: TP10, TP15, TP20 Hit Rates =====
print(f"\n{'='*70}")
print("2️⃣  Hit Rates בשיעורי TP שונים — מה הסף האופטימלי?")
print(f"{'='*70}")

if drop_col:
    dd = df[drop_col].dropna()
    for tp in [-5, -7, -10, -12, -15, -20, -25]:
        hit = (dd <= tp).sum()
        rate = hit / len(dd) * 100
        bar = '█' * int(rate / 3)
        print(f"  TP={tp:4d}%  hits={hit:4d}/{len(dd)}  rate={rate:5.1f}%  {bar}")

# ===== ניתוח 3: היכן נמצאת הירידה המקסימלית (יום) =====
print(f"\n{'='*70}")
print("3️⃣  באיזה יום (D1–D5) מתרחשת הירידה המקסימלית?")
print(f"{'='*70}")

d_lows = [f"D{i}_Low" for i in range(1, 6) if f"D{i}_Low" in df.columns]
d_opens = [f"D{i}_Open" for i in range(1, 6) if f"D{i}_Open" in df.columns]

if 'ScanPrice' in df.columns and d_lows:
    sp = df['ScanPrice']
    print(f"\nטבלה A — כניסה ב-ScanPrice:")
    print(f"  יום  | %ירידה ממוצע ל-Low  | % מתחת ל-10%")
    for dl in d_lows:
        if dl in df.columns:
            pct_drop = ((df[dl] - sp) / sp * 100).dropna()
            avg = pct_drop.mean()
            hit10 = (pct_drop <= -10).sum() / len(pct_drop) * 100
            print(f"  {dl[:2]}   | {avg:6.2f}%            | {hit10:5.1f}%")

if 'D1_Open' in df.columns and d_lows:
    print(f"\nטבלה B — כניסה ב-D1_Open:")
    d1o = df['D1_Open']
    print(f"  יום  | %ירידה ממוצע ל-Low  | % מתחת ל-10%")
    for dl in d_lows:
        if dl in df.columns:
            pct_drop = ((df[dl] - d1o) / d1o * 100).dropna()
            avg = pct_drop.mean()
            hit10 = (pct_drop <= -10).sum() / len(pct_drop) * 100
            print(f"  {dl[:2]}   | {avg:6.2f}%            | {hit10:5.1f}%")

# ===== ניתוח 4: MxV vs MaxDrop — חיפוש הקורלציה החזקה =====
print(f"\n{'='*70}")
print("4️⃣  MxV & ATRX vs גודל הירידה — מי באמת חוזה?")
print(f"{'='*70}")

if drop_col:
    for metric in ['MxV', 'ATRX', 'RunUp', 'REL_VOL', 'RSI', 'Score', 'Gap%', 'Gap']:
        if metric in df.columns:
            clean = df[[metric, drop_col]].dropna()
            if len(clean) > 20:
                corr = clean[metric].corr(clean[drop_col])
                print(f"  {metric:10s} vs {drop_col}: r = {corr:+.3f}  (n={len(clean)})")

# ===== ניתוח 5: MxV buckets — איפה ה-Sweet Spot האמיתי? =====
print(f"\n{'='*70}")
print("5️⃣  MxV Buckets — באיזה טווח MxV הירידה הכי גדולה?")
print(f"{'='*70}")

if 'MxV' in df.columns and drop_col:
    clean = df[['MxV', drop_col]].dropna()
    # טווחים שהגדרת: -30 עד -1500
    buckets = [
        ('MxV > -30',         clean[clean['MxV'] > -30]),
        ('-30 to -100',       clean[(clean['MxV'] <= -30) & (clean['MxV'] > -100)]),
        ('-100 to -300',      clean[(clean['MxV'] <= -100) & (clean['MxV'] > -300)]),
        ('-300 to -600',      clean[(clean['MxV'] <= -300) & (clean['MxV'] > -600)]),
        ('-600 to -1000',     clean[(clean['MxV'] <= -600) & (clean['MxV'] > -1000)]),
        ('-1000 to -1500',    clean[(clean['MxV'] <= -1000) & (clean['MxV'] > -1500)]),
        ('MxV < -1500',       clean[clean['MxV'] <= -1500]),
    ]
    print(f"\n  {'טווח MxV':<20} {'n':>5} {'ממוצע Drop':>12} {'חציון':>10} {'TP10 hit%':>10}")
    for name, sub in buckets:
        if len(sub) > 0:
            avg = sub[drop_col].mean()
            med = sub[drop_col].median()
            tp10 = (sub[drop_col] <= -10).sum() / len(sub) * 100
            print(f"  {name:<20} {len(sub):>5} {avg:>11.2f}% {med:>9.2f}% {tp10:>9.1f}%")

# ===== ניתוח 6: ATRX buckets — האם ATRX גבוה = ירידה עמוקה יותר? =====
print(f"\n{'='*70}")
print("6️⃣  ATRX Buckets — האם תנודתיות = ירידה עמוקה?")
print(f"{'='*70}")

if 'ATRX' in df.columns and drop_col:
    clean = df[['ATRX', drop_col]].dropna()
    buckets = [
        ('ATRX 0-1',    clean[(clean['ATRX'] >= 0) & (clean['ATRX'] < 1)]),
        ('ATRX 1-1.5',  clean[(clean['ATRX'] >= 1) & (clean['ATRX'] < 1.5)]),
        ('ATRX 1.5-2',  clean[(clean['ATRX'] >= 1.5) & (clean['ATRX'] < 2)]),
        ('ATRX 2-2.5',  clean[(clean['ATRX'] >= 2) & (clean['ATRX'] < 2.5)]),
        ('ATRX 2.5-3',  clean[(clean['ATRX'] >= 2.5) & (clean['ATRX'] <= 3)]),
    ]
    print(f"\n  {'טווח ATRX':<15} {'n':>5} {'ממוצע Drop':>12} {'TP10':>8} {'TP15':>8} {'TP20':>8}")
    for name, sub in buckets:
        if len(sub) > 0:
            avg = sub[drop_col].mean()
            tp10 = (sub[drop_col] <= -10).sum() / len(sub) * 100
            tp15 = (sub[drop_col] <= -15).sum() / len(sub) * 100
            tp20 = (sub[drop_col] <= -20).sum() / len(sub) * 100
            print(f"  {name:<15} {len(sub):>5} {avg:>11.2f}% {tp10:>7.1f}% {tp15:>7.1f}% {tp20:>7.1f}%")

# ===== ניתוח 7: Dynamic TP simulation — מה היה קורה אם TP=ATRX*factor? =====
print(f"\n{'='*70}")
print("7️⃣  Dynamic TP Simulation — TP מותאם ל-ATRX")
print(f"{'='*70}")

if 'ATRX' in df.columns and drop_col:
    clean = df[['ATRX', drop_col]].dropna()
    print(f"\nאסטרטגיות שונות (n={len(clean)}):\n")
    
    # אסטרטגיה קבועה
    static_10 = (clean[drop_col] <= -10).sum() / len(clean) * 100
    print(f"  📌 TP=-10% קבוע:                     hit rate = {static_10:.1f}%")
    
    # דינמיים
    for factor in [4, 5, 6, 7, 8]:
        dynamic_tp = -clean['ATRX'] * factor
        hits = (clean[drop_col] <= dynamic_tp).sum() / len(clean) * 100
        avg_tp = dynamic_tp.mean()
        print(f"  🎯 TP = -ATRX × {factor}  (ממוצע {avg_tp:.1f}%):  hit rate = {hits:.1f}%")
    
    # היברידי: max(-10%, -ATRX*factor) כלומר "לפחות 10% או יותר"
    print(f"\n  היברידי (לוקח את המחמיר ביותר לטובת השורט):")
    for factor in [5, 6, 7]:
        dynamic_tp = np.minimum(-10, -clean['ATRX'] * factor)
        hits = (clean[drop_col] <= dynamic_tp).sum() / len(clean) * 100
        avg_tp = dynamic_tp.mean()
        print(f"  🎯 TP = min(-10%, -ATRX×{factor}) (ממוצע {avg_tp:.1f}%): hit rate = {hits:.1f}%")

# ===== ניתוח 8: פרופיל המניה שצוללת הכי עמוק =====
print(f"\n{'='*70}")
print("8️⃣  הטופ 10 הצלילות הגדולות — מה מאפיין אותן?")
print(f"{'='*70}")

if drop_col and 'Ticker' in df.columns:
    show_cols = ['Ticker', 'ScanDate', 'Score', 'MxV', 'ATRX', 'RunUp', 'REL_VOL', 'RSI', drop_col]
    show_cols = [c for c in show_cols if c in df.columns]
    top10 = df.nsmallest(10, drop_col)[show_cols]
    print("\n", top10.to_string(index=False))

print(f"\n{'='*70}\n✅ סיום\n")
