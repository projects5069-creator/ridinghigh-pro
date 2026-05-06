# 📋 RidingHigh Pro — Session Handoff 2026-05-05

🌍 Owner: Amihay Levy (Lima, Peru, UTC-5)
📅 סשן: שלישי 5.5.2026, ~2.5 שעות עבודה (18:00–19:22 Peru)
🛠️ סשן הבא: ___________

## 🏆 מה הושג היום

### חקירה מעמיקה — מאפיינים מנבאי-ירידה במניות (8 phases)

סשן מחקרי מלא — **READ-ONLY**, אפס שינויים לקוד/sheets. כל ה-output ב-`/tmp/research/`.

#### Phase 1 — Data Inventory
- 12 sheets נסרקו (RH: 3 months × 5 sheets + DropsLab: 2 sheets)
- סה"כ 338,821 שורות data
- 2026-06 ריק (חודש לא התחיל)
- DropsLab-Data sheet (1M-ofm...) — **403 Permission Denied** לשני ה-service accounts

#### Phase 2 — Outcome Definition (154 records from post_analysis)
- 75.3% hit TP10 (drop 10%+), 63% hit SL7 (rise 7%+)
- 44.8% hit BOTH — סדר TP/SL לא ידוע (gap קריטי ב-data)

#### Phase 3 — Univariate Analysis (23 metrics)
- **D1_Gap%**: AUC=0.838 (הכי חזק, אבל after-the-fact)
- **Float%**: AUC=0.667 (#1 pre-trade)
- **MinToClose**: AUC=0.623 (time-of-day)
- **TypicalPriceDist/VWAP**: AUC=0.501 (חסר ערך — 10% weight ב-Score v2!)

#### Phase 4 — Bivariate Interactions (45 pairs)
- Top: Float% × MxV → spread=66.7%
- Multicollinearity: Score↔ScanChange (0.82), MxV↔Volume (-0.80)

#### Phase 5 — Time-of-Day
- 8:30 entries: TP10=78%, SL7=38% — **הכי טוב**
- 9:30 entries: TP10=40%, SL7=80% — **הכי גרוע**
- MinToClose >= 240: TP10=87%, SL7=20%

#### Phase 6 — DropsLab Cross-Reference
- 72/93 RH tickers (77%) found in DropsLab
- 163 predictive matches (RH detected pump BEFORE DL detected drop)
- Average lead time: 5.4 days
- Matched TP10 rate: 85.3% vs unmatched 65.1%

#### Phase 7 — ML Feature Importance
- RF CV AUC: 0.766 (all features) / 0.629 (pre-trade only)
- Top pre-trade: Float%(0.154), MarketCap(0.080), D0_Drop%(0.075)

#### Phase 8 — Synthesis + Deep EDA v1 + v2 + Sanity Check
- Filters simulation: MinToClose>=240 → PnL/trade=+6.4 (best)
- Ticker leakage found: 101 unique / 164 records (33 repeats)
- **BIMODAL distribution**: stocks either crash (-50% to -10%) or keep pumping (+5% to +50%)
- **Pure shorts** (5 stocks): net_d5 mean=-33.6%, 4/5 had Score > 70
- **Pure longs** (13 stocks): net_d5 mean=+55.2%, mostly under $5

## 📦 Deliverables — כל הקבצים

### /tmp/research/ (28 קבצים + 29 plots)
```
FINDINGS.md                      — דוח עברית ראשי (216 שורות)
proposed_config.py               — config חדש לAgent (data-driven thresholds)
proposed_score_v3.py             — Score v3 formula (passes self-test)
feature_importance.csv           — דירוג 24 מטריקות
univariate_analysis.csv          — AUC/F1/thresholds per metric
interactions.csv                 — 45 metric pair interactions
cross_reference.csv              — 177 RH×DL matches
proposed_filters_simulation.csv  — 19 filter backtests
outcomes.csv / outcomes.pkl      — 154 records with outcome variables
time_analysis.csv                — win rate by scan time
data_inventory.txt               — full sheets catalog
correlation_matrix.png           — Spearman heatmap
interaction_heatmaps.png         — top 3 pair heatmaps
feature_importance_plots.png     — RF + LR + combined ranking
time_analysis_plots.png          — 4 time analysis charts
univariate_plots/                — 29 PNG (1 per metric)
checkpoints/                     — phase1-8 completion markers
```

### ~/RidingHighPro/ (EDA outputs)
```
eda_findings.txt                 — EDA v1 (leakage, low-score mystery, bimodal)
eda_v2_findings.txt              — EDA v2 (long vs short, 2x2 matrix)
eda_plots/metric_distributions.png
eda_v2_plots/net_d5_distribution.png
eda_v2_plots/net_d5_by_tier.png
eda_v2_plots/drop_vs_rise_scatter.png
```

## ⚠️ ממצאים קריטיים שדורשים פעולה

### 1. VWAP/TypicalPriceDist = 10% weight בScore, אבל AUC=0.501 (אפס ערך)
**המלצה:** הורד ל-0-2% או הסר

### 2. MinToClose — ה-game changer שלא משתמשים בו
Entries עם 4+ שעות לסגירה: TP10=87%, SL7=20%
**המלצה:** הוסף filter MinToClose >= 120 (לפחות 60)

### 3. 9:30 time slot — הכי מסוכן
TP10=40%, SL7=80%
**המלצה:** block/flag entries ב-9:15-9:45 Peru

### 4. TP/SL order not tracked — biggest data gap
63 records hit both TP AND SL. אין מידע מה hit ראשון.
**המלצה:** הוסף IntraDay_TP_first / IntraDay_SL_first boolean

### 5. Ticker leakage
33 tickers appear >1x. SKYQ 6x, UGRO 6x. Inflates TP rate.
**המלצה:** deduplicate in analysis, consider in agent logic

### 6. BIMODAL outcomes — stocks crash OR keep pumping
Distribution is not normal — two distinct clusters.
**Implication:** Score should predict WHICH cluster, not magnitude.

## ⏸️ מה לא הושג / data gaps

- DropsLab-Data sheet (38 metrics) — no access (403)
- 2026-05 post_analysis — only 10 records (month just started)
- TP/SL timing order — not tracked
- Sector data — 60% missing
- Intraday price path — not linked to outcomes
- D5_Close available for only 58/101 deduped records

## 🎯 משימות מומלצות לסשן הבא

### P0 (מיידי — impact גבוה, effort נמוך)
- [ ] הוסף MinToClose filter לagent (≥60 min) — **30m, highest ROI change**
- [ ] Block 9:15-9:45 entry window — **15m**
- [ ] הורד VWAP weight מ-10% ל-2% בScore — **15m**

### P1 (קרוב — דורש design)
- [ ] Score v3 implementation — use proposed_score_v3.py as starting point
- [ ] Add TP/SL order tracking to post_analysis_collector
- [ ] Share DropsLab-Data sheet with RH service account
- [ ] Float% filter (≥10) to agent entry logic

### P2 (research — needs more data)
- [ ] Re-run analysis when 200+ v2 records available (~2 months)
- [ ] Investigate RDGT MaxRise=11,814% — data error?
- [ ] Build cluster classifier (crash vs pump) instead of score
- [ ] SL tightening to 5% — simulate impact

## 📂 משאבים

- PK: docs/RidingHigh_Pro_PK_v2.md
- Research: /tmp/research/ (⚠️ ephemeral — copy to permanent location!)
- EDA: ~/RidingHighPro/eda_findings.txt, eda_v2_findings.txt
- Repo: projects5069-creator/ridinghigh-pro
- App: ridinghigh-pro-v2.streamlit.app

## 🚀 פתיחה לסשן הבא

```
שלום, ממשיך מסשן 2026-05-05.
סשן מחקרי הושלם — 8 phases של feature analysis על post_analysis.
ממצאים ב-/tmp/research/FINDINGS.md ו-~/RidingHighPro/eda_v2_findings.txt.

Top findings:
1. MinToClose הוא ה-filter הכי משפיע (87% TP, 20% SL כשentry מוקדם)
2. VWAP/TypicalPriceDist חסר ערך ניבויי (AUC=0.501) למרות 10% weight
3. Distribution is bimodal — stocks crash or keep pumping, rarely flat
4. 77% of RH tickers confirmed by DropsLab (5.4 day lead time)

נמשיך עם [MinToClose filter / Score v3 / TP-SL tracking / משימה אחרת].
```

חוקי ברזל:
✓ time-check first
✓ str_replace בלבד
✓ syntax check
✓ אישור ידני לפני commit
✓ STOP על uniqueness
✓ backup לפני שינויים
✓ no truncated output
✓ Hebrew RTL
✓ versioned filenames
