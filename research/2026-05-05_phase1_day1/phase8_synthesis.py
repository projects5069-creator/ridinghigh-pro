"""Phase 8: Synthesis — Generate FINDINGS.md, proposed_config.py, proposed_score_v3.py, simulation."""
import pandas as pd
import numpy as np
from datetime import datetime

outcomes = pd.read_csv("/tmp/research/outcomes.csv")
univariate = pd.read_csv("/tmp/research/univariate_analysis.csv")
feature_imp = pd.read_csv("/tmp/research/feature_importance.csv")
lr_coefs = pd.read_csv("/tmp/research/lr_coefs.csv")

binary = outcomes[outcomes["net_outcome"].isin(["TP_HIT","SL_HIT"])].copy()
binary["target"] = (binary["net_outcome"] == "TP_HIT").astype(int)

n_tp = (outcomes["net_outcome"]=="TP_HIT").sum()
n_sl = (outcomes["net_outcome"]=="SL_HIT").sum()
n_partial = (outcomes["net_outcome"]=="PARTIAL").sum()
n_open = (outcomes["net_outcome"]=="OPEN").sum() if "OPEN" in outcomes["net_outcome"].values else 0
n_total = len(outcomes)

# Date range
date_min = outcomes["ScanDate"].min()
date_max = outcomes["ScanDate"].max()

# ========================
# FINDINGS.md
# ========================
findings = f"""# ממצאי מחקר עומק — RidingHigh Pro
## ניתוח חזוי: אילו מאפיינים מנבאים ירידה אחרי סריקה

**תאריך ניתוח:** {datetime.now().strftime('%Y-%m-%d')}
**גרסה:** v1.0

---

## 1. תקציר מנהלים (Executive Summary)

ניתחנו {n_total} סריקות (scans) מתקופת {date_min} עד {date_max}.
מתוכן {n_tp} ({n_tp/n_total*100:.0f}%) סווגו כ-TP_HIT (ירידה של 10%+ ללא SL),
{n_sl} ({n_sl/n_total*100:.0f}%) כ-SL_HIT (עלייה של 7%+ מחיר הסריקה),
ו-{n_partial} כ-PARTIAL.

**הממצא המרכזי:** אף מדד בודד אינו מנבא חזק מספיק (AUC מקסימלי = 0.609 עבור ATRX).
מודל Logistic Regression שילובי השיג AUC של 0.537 בלבד (5-fold CV).
**Score הנוכחי (v14.6) אינו מנבא כלל** — AUC = 0.489, קרוב למטבע.

**עם SL של 7% עלייה, רוב המניות (65%) פוגעות ב-SL** גם אם בסופו של דבר יורדות 10%+.
64 מתוך 140 מניות פגעו בשני היעדים (TP10 וגם SL7), אך SL נספר ראשון.

---

## 2. גודל מדגם ומגבלות (Sample Size & Caveats)

| מדד | ערך |
|------|------|
| N (TP_HIT) | {n_tp} |
| N (SL_HIT) | {n_sl} |
| N (PARTIAL) | {n_partial} |
| N (OPEN) | {n_open} |
| N (סה"כ outcomes) | {n_total} |
| N (binary classification) | {n_tp + n_sl} |
| טווח תאריכים | {date_min} — {date_max} |
| חודשים עם data | 2026-04 (154 rows), 2026-05 (8 rows, 2 with full OHLC) |
| 2026-06 | ריק |
| DropsLab | **לא זמין** (שגיאת הרשאות 403) |

### חולשות הנתונים
- **גודל מדגם קטן מאוד** — 140 רשומות לא מספיקות לתוקף סטטיסטי (נדרשים 300+)
- **תקופה קצרה** — ~5 שבועות מסחר בלבד
- **חוסר איזון** — 34% TP vs 66% SL (יחס 1:1.9)
- **SL אגרסיבי** — 7% rise כ-SL תופס 65% מהמניות כולל כאלה שבסוף יורדות
- **Hour** חסר ב-54% מהרשומות (לא נכלל ב-ML)
- **ATRX, Volume, MarketCap** חסרים ב-14% מהרשומות (19 rows)
- **חודש מאי** כמעט ריק — רק 2 רשומות עם OHLC מלא

⚠️ **תוצאות ML אינדיקטיביות בלבד. עם N={n_tp + n_sl} records, נדרשים 300+ records לתוקף סטטיסטי. CV variance גבוה.**

---

## 3. חמשת המדדים הכי מנבאים (Top 5 Predictive Metrics)

"""
# Get top 5 by univariate AUC
uni_sorted = univariate.sort_values("auc", ascending=False).head(5)
for i, (_, row) in enumerate(uni_sorted.iterrows(), 1):
    metric = row["metric"]
    auc = row["auc"]
    thr = row["best_threshold"]
    prec = row.get("precision_at_thr", "N/A")
    rec = row.get("recall_at_thr", "N/A")
    p = row["mann_whitney_p"]
    mean_tp = row["mean_tp"]
    mean_sl = row["mean_sl"]
    
    findings += f"""### {i}. {metric}
- **AUC:** {auc:.3f}
- **Mann-Whitney p:** {p:.4f}
- **TP_HIT mean:** {mean_tp:.2f} | **SL_HIT mean:** {mean_sl:.2f}
- **Best threshold:** {thr} → precision={prec}, recall={rec}
- **הסבר:** """
    
    if metric == "ATRX":
        findings += "ATR מנורמל גבוה יותר אצל winners. מניות עם תנודתיות יחסית גבוהה נוטות ליפול יותר."
    elif metric == "REL_VOL":
        findings += "ווליום יחסי גבוה יותר אצל winners. נפח מסחר חריג מעל הממוצע מנבא ירידה."
    elif metric == "RunUp":
        findings += "עלייה מצטברת גבוהה יותר לפני הסריקה אצל winners. עלייה חדה = נפילה חדה."
    elif metric == "Volume":
        findings += "ווליום מוחלט גבוה אצל winners. מניות עם סחירות גבוהה נוטות ליפול."
    elif metric == "MarketCap":
        findings += "שווי שוק נמוך יותר אצל winners. מניות קטנות יותר נוטות לנפילות חזקות."
    else:
        findings += f"ראה ניתוח מפורט."
    findings += "\n\n"

findings += f"""---

## 4. שלושת המדדים הכי חסרי ערך (Top 3 USELESS)

"""
uni_bottom = univariate.sort_values("auc").head(3)
for i, (_, row) in enumerate(uni_bottom.iterrows(), 1):
    findings += f"""### {i}. {row["metric"]}
- **AUC:** {row["auc"]:.3f} ({"הפוך מהצפוי" if row["auc"] < 0.5 else "כמו מטבע"})
- **p-value:** {row["mann_whitney_p"]:.4f}
- **הסבר:** {"RSI נוטה להיות גבוה יותר אצל losers — ייתכן כי RSI גבוה מסמן שהpump עדיין חזק ומסוכן לshort" if row["metric"]=="RSI" else "אין הבחנה סטטיסטית בין winners ל-losers" if row["metric"]=="Hour" else "Score אינו מנבא כלל. זהו ממצא מפתיע ומדאיג — הscore צריך rethink."  if row["metric"]=="Score" else "אין הבחנה."}

"""

findings += f"""---

## 5. טבלת סף אופטימלי (Optimal Thresholds)

| מדד | סף | Precision | Recall | F1 | n_qualified |
|------|-----|-----------|--------|-----|-------------|
"""
for _, row in univariate.sort_values("auc", ascending=False).iterrows():
    thr = row.get("best_threshold", "N/A")
    prec = row.get("precision_at_thr", "")
    rec = row.get("recall_at_thr", "")
    f1 = row.get("best_f1", "")
    nq = row.get("n_qualified", "")
    findings += f"| {row['metric']} | {thr} | {prec} | {rec} | {f1} | {nq} |\n"

findings += f"""
---

## 6. שילובי מדדים מיטביים (Best Combinations)

מתוך ניתוח ביוואריאטי (Phase 4):

| שילוב | Bucket מיטבי | TP Rate | n |
|--------|-------------|---------|---|
| ATRX × MarketCap | Q4 × Q4 | 77.8% | 9 |
| REL_VOL × RunUp | Q3 × Q4 | 63.6% | 11 |
| ATRX × Volume | Q4 × Q3 | 66.7% | 6 |
| ATRX × RunUp | Q3 × Q4 | 57.1% | 7 |
| RunUp × Volume | Q3 × Q4 | 60.0% | 5 |

⚠️ גודל מדגם קטן מאוד בכל bucket — תוצאות לא אמינות.

### Multicollinearity:
- **MxV ↔ Volume**: Spearman = -0.853 (כפילות — לבחור אחד מהם)

---

## 7. תובנות שעת סריקה (Time-of-Day)

| שעה (Peru) | סריקות | TP Rate | Avg MaxDrop% |
|------------|--------|---------|-------------|
| 08:xx | 28 | **57.1%** | -27.5% |
| 09:xx | 15 | 33.3% | -17.4% |
| 10:xx | 3 | 33.3% | -23.9% |
| 11:xx | 8 | 37.5% | -19.3% |
| 12:xx | 7 | 28.6% | -17.5% |
| 13:xx | 1 | 100% | -16.8% |
| 14:xx | 3 | 0% | -18.5% |

**ממצא מפתיע:** שעה 8 (08:30-08:59 Peru = 13:30-13:59 UTC = pre-market/first minutes)
היא בעלת TP rate הגבוה ביותר (57.1%) וגם ממוצע ירידה הגדול ביותר (-27.5%).

**Winners נסרקים מוקדם יותר:**
- First scan ממוצע: TP = 09:39, SL = 10:26
- Peak score delay: TP = 146 דקות, SL = 184 דקות (winners מגיעים לשיא מהר יותר)

---

## 8. Stratification לפי שווי שוק

| קטגוריה | n | TP Rate | Avg Score | Avg MxV |
|----------|---|---------|-----------|---------|
| <$50M | 112 | 34.8% | 58.4 | -2,341 |
| $50M-$500M | 23 | 39.1% | 61.7 | -160 |
| $500M-$5B | 5 | 0.0% | 40.2 | 67 |
| $5B+ | 0 | - | - | - |

**ממצא:** רוב המניות (80%) הן מתחת ל-$50M. אין מספיק נתונים לhigh-cap.
מניות $50M-$500M מראות TP rate מעט גבוה יותר (39.1% vs 34.8%), אך n קטן.

---

## 9. DropsLab Cross-Reference

**לא זמין** — service account אין לו הרשאות לגיליון DropsLab (שגיאה 403).
יש לשתף את הגיליון עם: `ridinghigh-sheets@ridinghigh-pro.iam.gserviceaccount.com`

---

## 10. נוסחת Score מומלצת (v3)

### בעיית ה-Score הנוכחי
Score v14.6 עם משקלים (30/20/20/10/10/5/5) **אינו מנבא כלל** (AUC=0.489).
זה אומר שscore גבוה לא מעלה את הסיכוי לTP_HIT.

### משקלים מוצעים (מבוססי LR |coef|)
מקדמי ה-LR (ב-abs) אחרי standardization:

| מדד | LR |coef| | משקל מנורמל | v14.6 | שינוי |
|------|-----------|--------------|---------|--------|
| MarketCap | 0.726 | 21.3% | 0% | **חדש** |
| Gap | 0.714 | 21.0% | 5% | ↑↑↑ |
| MxV | 0.467 | 13.7% | 30% | ↓↓ |
| Volume | 0.389 | 11.4% | 0% | **חדש** |
| ScanPrice | 0.385 | 11.3% | 0% | **חדש** |
| VWAP_dev | 0.297 | 8.7% | 5% | ↑ |
| REL_VOL | 0.177 | 5.2% | 20% | ↓↓ |
| RunUp | 0.161 | 4.7% | 20% | ↓↓ |
| Score(self) | 0.154 | 4.5% | N/A | N/A |
| RSI | 0.144 | 4.2% | 10% | ↓ |
| ATRX | 0.014 | 0.4% | 10% | ↓↓ |

**⚠️ אזהרה חשובה:** המשקלים מבוססים על n=121 בלבד ו-CV AUC=0.537.
אין לאמץ ללא בדיקה נוספת על dataset גדול יותר.

---

## 11. פילטרים מומלצים ל-Agent

בהתבסס על thresholds מ-Phase 3 (best F1):

```python
# מומלץ — conservative, data-driven
AGENT_MIN_SCORE = None      # Score לא מנבא — לא לסנן לפיו
AGENT_MXV_MAX   = None      # MxV לא מנבא בבירור
AGENT_RUNUP_MIN = None      # RunUp חלש
AGENT_RELVOL_MIN= 4.22      # REL_VOL >= 4.22 (F1=0.52)
AGENT_HOUR_RANGE= (8, 9)    # שעות 8-9 Peru (TP rate 57%+33%)
AGENT_MIN_MCAP  = None      # MarketCap — כיוון לא ברור
AGENT_ATRX_MIN  = 3.52      # ATRX >= 3.52 (F1=0.52, best univariate)
```

**ההמלצה העיקרית:** *לא לסנן אגרסיבית* עם n=140. כל threshold הוא רועש.
עדיף לצבור עוד data (300+ rows) לפני שינוי פילטרים.

---

## 12. שאלות פתוחות ופערי נתונים

1. **SL 7% — אולי גבוה מדי?** 65% מהמניות פוגעות ב-SL. אולי SL של 10% או 12% יהיה ריאלי יותר?
2. **DropsLab** — חסרה הרשאה. נדרש שיתוף עם service account.
3. **D0 vs D1+** — האם ה-drop הגדול קורה ב-D0 (יום הסריקה) או D1+? זה משפיע על אסטרטגיית entry.
4. **Score formula** — Score אינו מנבא. צריך re-think מוחלט: מה בדיוק Score אמור למדוד?
5. **Sector** — האם יש ענפים עם TP rate גבוה יותר? (לא נבדק בגלל מגבלות n)
6. **Multiple scans per ticker** — אותו ticker מופיע בימים שונים. האם ישנה autocorrelation?
7. **Pre-market vs market hours** — שעות 8 (pre-market) מראות TP rate גבוה, אך n=28 בלבד.

---

## 13. צעדים הבאים (Next Steps)

### 1. צבירת נתונים נוספים (עדיפות עליונה)
- לצבור לפחות 300 רשומות עם OHLC מלא (D1-D5)
- לוודא ש-Hour נשמר לכל scan (חסר ב-54% מהרשומות)
- ATRX, Volume, MarketCap חסרים ב-14% — לטפל ב-enrichment

### 2. בחינת SL threshold
- לחזור על ניתוח עם SL=10%, SL=12%, SL=15%
- לבדוק sensitivity: כמה TP_HITs "ננצלים" בכל רמת SL

### 3. שיתוף DropsLab
- לשתף את DropsLab sheet עם service account
- להריץ את Phase 6 מחדש

"""

with open("/tmp/research/FINDINGS.md", "w") as f:
    f.write(findings)
print("FINDINGS.md written")

# ========================
# proposed_config.py
# ========================
config = f"""# Generated from data analysis on {datetime.now().strftime('%Y-%m-%d')}
# Based on N={n_tp + n_sl} records (binary), LR CV AUC=0.537
# WARNING: Sample size too small for reliable thresholds. Use with extreme caution.

AGENT_MIN_SCORE = None      # Score AUC=0.489 — not predictive, do not filter
AGENT_MXV_MAX   = None      # MxV AUC=0.478 — not predictive
AGENT_RUNUP_MIN = None      # RunUp AUC=0.565, but p=0.21 — insufficient evidence
AGENT_RELVOL_MIN= 4.22      # REL_VOL AUC=0.576, best F1 threshold (weak)
AGENT_HOUR_RANGE= (8, 9)    # Hour 8 TP rate=57.1%, Hour 9 TP rate=33.3%
AGENT_MIN_MCAP  = None      # MarketCap — direction unclear (LR says smaller=better)
AGENT_ATRX_MIN  = 3.52      # ATRX AUC=0.609 (best univariate, p=0.062)

# Additional (if implemented):
AGENT_MAX_RSI   = None      # RSI AUC=0.432, lower RSI=more TP, but weak signal
AGENT_SL_PCT    = 7         # Current SL at 7% rise — consider raising to 10-12%
AGENT_TP_PCT    = 10        # TP at 10% drop — seems working (79% hit rate without SL)
"""

with open("/tmp/research/proposed_config.py", "w") as f:
    f.write(config)
print("proposed_config.py written")

# ========================
# proposed_score_v3.py
# ========================
# Normalize LR |coef| to weights
lr_data = lr_coefs[["feature","lr_coef","lr_abs_coef"]].copy()
# Keep only the 7 original score metrics
score_metrics = ["MxV","RunUp","REL_VOL","RSI","ATRX","Gap","VWAP_dev"]
lr_score = lr_data[lr_data["feature"].isin(score_metrics)].copy()
total_abs = lr_score["lr_abs_coef"].sum()
lr_score["weight_pct"] = (lr_score["lr_abs_coef"] / total_abs * 100).round(1)

score_v3 = f"""# Score v3 — Data-Driven Weights
# Generated from data analysis on {datetime.now().strftime('%Y-%m-%d')}
# Based on N={n_tp + n_sl} records, LR CV AUC=0.537
#
# WARNING: These weights are derived from a very small dataset (n={n_tp+n_sl}).
# Do NOT deploy without validation on 300+ records.
#
# Comparison with v14.6:
# Metric      v14.6   v3 (data)   Direction in LR
# ─────────   ─────   ─────────   ───────────────
# MxV         30%     {lr_score[lr_score['feature']=='MxV']['weight_pct'].values[0]}%       higher = more TP (positive coef)
# RunUp       20%     {lr_score[lr_score['feature']=='RunUp']['weight_pct'].values[0]}%        higher = more TP
# REL_VOL     20%     {lr_score[lr_score['feature']=='REL_VOL']['weight_pct'].values[0]}%        higher = more TP
# RSI         10%     {lr_score[lr_score['feature']=='RSI']['weight_pct'].values[0]}%        LOWER = more TP (inverted)
# ATRX        10%     {lr_score[lr_score['feature']=='ATRX']['weight_pct'].values[0]}%        essentially zero signal
# Gap          5%     {lr_score[lr_score['feature']=='Gap']['weight_pct'].values[0]}%       higher = more TP
# VWAP_dev     5%     {lr_score[lr_score['feature']=='VWAP_dev']['weight_pct'].values[0]}%       LOWER = more TP (inverted)
#
# Key observations:
# 1. Gap weight should be MUCH higher (5% → {lr_score[lr_score['feature']=='Gap']['weight_pct'].values[0]}%)
# 2. MxV weight should be lower (30% → {lr_score[lr_score['feature']=='MxV']['weight_pct'].values[0]}%)
# 3. ATRX has near-zero signal in multivariate context despite best univariate AUC
# 4. RSI is inverted — high RSI = MORE SL hits (bad for short)
# 5. VWAP_dev is inverted — stocks closer to VWAP do better as shorts
#
# BUT: With LR AUC=0.537, these weights are NOT meaningfully better than v14.6.
# The problem is NOT the weights — it's that these metrics are weak predictors overall.

SCORE_WEIGHTS_V3 = {{
"""
for _, row in lr_score.iterrows():
    direction = "positive" if row["lr_coef"] > 0 else "INVERTED"
    score_v3 += f'    "{row["feature"]}": {row["weight_pct"]},  # LR coef={row["lr_coef"]:.4f} ({direction})\n'
score_v3 += "}\n"

with open("/tmp/research/proposed_score_v3.py", "w") as f:
    f.write(score_v3)
print("proposed_score_v3.py written")

# ========================
# proposed_filters_simulation.csv
# ========================
# Simulate: if new filters were active, what would the results be?
binary_full = outcomes[outcomes["net_outcome"].isin(["TP_HIT","SL_HIT"])].copy()
binary_full["target"] = (binary_full["net_outcome"] == "TP_HIT").astype(int)

simulations = []

# Baseline
simulations.append({
    "filter_name": "BASELINE (no filter)",
    "n_trades": len(binary_full),
    "n_tp": binary_full["target"].sum(),
    "n_sl": (1-binary_full["target"]).sum(),
    "win_rate": binary_full["target"].mean(),
    "avg_drop": binary_full["drop_max_pct"].mean(),
})

# Filter 1: ATRX >= 3.52
if "ATRX" in binary_full.columns:
    f1 = binary_full[binary_full["ATRX"] >= 3.52]
    if len(f1) > 0:
        simulations.append({
            "filter_name": "ATRX >= 3.52",
            "n_trades": len(f1),
            "n_tp": f1["target"].sum(),
            "n_sl": (1-f1["target"]).sum(),
            "win_rate": f1["target"].mean(),
            "avg_drop": f1["drop_max_pct"].mean(),
        })

# Filter 2: REL_VOL >= 4.22
if "REL_VOL" in binary_full.columns:
    f2 = binary_full[binary_full["REL_VOL"] >= 4.22]
    if len(f2) > 0:
        simulations.append({
            "filter_name": "REL_VOL >= 4.22",
            "n_trades": len(f2),
            "n_tp": f2["target"].sum(),
            "n_sl": (1-f2["target"]).sum(),
            "win_rate": f2["target"].mean(),
            "avg_drop": f2["drop_max_pct"].mean(),
        })

# Filter 3: Hour <= 9
if "Hour" in binary_full.columns:
    f3 = binary_full[binary_full["Hour"] <= 9]
    if len(f3) > 0:
        simulations.append({
            "filter_name": "Hour <= 9",
            "n_trades": len(f3),
            "n_tp": f3["target"].sum(),
            "n_sl": (1-f3["target"]).sum(),
            "win_rate": f3["target"].mean(),
            "avg_drop": f3["drop_max_pct"].mean(),
        })

# Filter 4: Combined ATRX + REL_VOL
if "ATRX" in binary_full.columns and "REL_VOL" in binary_full.columns:
    f4 = binary_full[(binary_full["ATRX"] >= 3.52) & (binary_full["REL_VOL"] >= 4.22)]
    if len(f4) > 0:
        simulations.append({
            "filter_name": "ATRX>=3.52 AND REL_VOL>=4.22",
            "n_trades": len(f4),
            "n_tp": f4["target"].sum(),
            "n_sl": (1-f4["target"]).sum(),
            "win_rate": f4["target"].mean(),
            "avg_drop": f4["drop_max_pct"].mean(),
        })

# Filter 5: Combined ATRX + Hour
if "ATRX" in binary_full.columns and "Hour" in binary_full.columns:
    f5 = binary_full[(binary_full["ATRX"] >= 3.52) & (binary_full["Hour"] <= 9)]
    if len(f5) > 0:
        simulations.append({
            "filter_name": "ATRX>=3.52 AND Hour<=9",
            "n_trades": len(f5),
            "n_tp": f5["target"].sum(),
            "n_sl": (1-f5["target"]).sum(),
            "win_rate": f5["target"].mean(),
            "avg_drop": f5["drop_max_pct"].mean(),
        })

# Filter 6: Score >= 70 (test if current approach works)
f6 = binary_full[binary_full["Score"] >= 70]
if len(f6) > 0:
    simulations.append({
        "filter_name": "Score >= 70",
        "n_trades": len(f6),
        "n_tp": f6["target"].sum(),
        "n_sl": (1-f6["target"]).sum(),
        "win_rate": f6["target"].mean(),
        "avg_drop": f6["drop_max_pct"].mean(),
    })

# Filter 7: Score >= 50
f7 = binary_full[binary_full["Score"] >= 50]
if len(f7) > 0:
    simulations.append({
        "filter_name": "Score >= 50",
        "n_trades": len(f7),
        "n_tp": f7["target"].sum(),
        "n_sl": (1-f7["target"]).sum(),
        "win_rate": f7["target"].mean(),
        "avg_drop": f7["drop_max_pct"].mean(),
    })

sim_df = pd.DataFrame(simulations)
sim_df["win_rate"] = sim_df["win_rate"].round(4)
sim_df["avg_drop"] = sim_df["avg_drop"].round(2)
sim_df.to_csv("/tmp/research/proposed_filters_simulation.csv", index=False)

print("\nFILTER SIMULATION RESULTS:")
print(sim_df.to_string(index=False))

with open("/tmp/research/checkpoints/phase8.done", "w") as f:
    f.write("done\n")
print("\n✓ Phase 8 complete")
