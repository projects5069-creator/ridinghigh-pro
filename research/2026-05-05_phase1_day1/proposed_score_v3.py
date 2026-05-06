# Score v3 — Data-Driven Weights
# Generated from data analysis on 2026-05-05
# Based on N=140 records, LR CV AUC=0.537
#
# WARNING: These weights are derived from a very small dataset (n=140).
# Do NOT deploy without validation on 300+ records.
#
# Comparison with v14.6:
# Metric      v14.6   v3 (data)   Direction in LR
# ─────────   ─────   ─────────   ───────────────
# MxV         30%     23.7%       higher = more TP (positive coef)
# RunUp       20%     8.2%        higher = more TP
# REL_VOL     20%     9.0%        higher = more TP
# RSI         10%     7.3%        LOWER = more TP (inverted)
# ATRX        10%     0.7%        essentially zero signal
# Gap          5%     36.2%       higher = more TP
# VWAP_dev     5%     15.0%       LOWER = more TP (inverted)
#
# Key observations:
# 1. Gap weight should be MUCH higher (5% → 36.2%)
# 2. MxV weight should be lower (30% → 23.7%)
# 3. ATRX has near-zero signal in multivariate context despite best univariate AUC
# 4. RSI is inverted — high RSI = MORE SL hits (bad for short)
# 5. VWAP_dev is inverted — stocks closer to VWAP do better as shorts
#
# BUT: With LR AUC=0.537, these weights are NOT meaningfully better than v14.6.
# The problem is NOT the weights — it's that these metrics are weak predictors overall.

SCORE_WEIGHTS_V3 = {
    "Gap": 36.2,  # LR coef=0.7144 (positive)
    "MxV": 23.7,  # LR coef=0.4674 (positive)
    "VWAP_dev": 15.0,  # LR coef=-0.2971 (INVERTED)
    "REL_VOL": 9.0,  # LR coef=0.1772 (positive)
    "RunUp": 8.2,  # LR coef=0.1615 (positive)
    "RSI": 7.3,  # LR coef=-0.1442 (INVERTED)
    "ATRX": 0.7,  # LR coef=-0.0140 (INVERTED)
}
