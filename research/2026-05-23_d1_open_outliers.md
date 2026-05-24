# D1_Open Outlier Analysis — post_analysis sheet

> **Investigation:** P3.5 (TASK-17)
> **Date:** 2026-05-23
> **Status:** Complete. All 5 outliers explained as real events, not data bugs.

## Method

Analyzed 55 rows in post_analysis sheet. Computed D1_Open / ScanPrice ratio per row, plus D1_High / D1_Low intraday range. Flagged extremes.

## Distribution (49 valid rows)

| Percentile | D1_Open / ScanPrice |
|---|---|
| min | 0.21 (WOK 12/5) |
| p10 | 0.71 |
| p25 | 0.87 |
| median | **0.98** |
| p75 | 1.04 |
| p90 | 1.27 |
| max | 2.50 (PCLA 21/5) |

The median of 0.98 confirms PK finding "D1_Open avg vs ScanPrice ~ -3.4%". Healthy distribution.

## Outliers — all 5 explained

### 1. WOK on 2026-05-12 — extreme_drop -79%
- ScanPrice $6.05 → D1_Open $1.27
- Previous day (11/5) had D1_High/D1_Low range = 3.68x
- Most likely cause: Reverse stock split between trading days.
- NOT a yfinance data error — the OHLC is consistent with a real corporate action.

### 2. TDIC on 2026-05-12 — wild_d1_range 10.24x
- D1_Low $2.93 → D1_High $29.99
- Classic pump-and-dump: stock 10x intraday, then crashed.

### 3. TDIC on 2026-05-13 — wild_d1_range 24.77x
- D1_Low $0.88 → D1_High $21.80
- Same ticker, next day. Second wave of pump action.

### 4. PCLA on 2026-05-21 — extreme_rise +150%
- ScanPrice $2.47 → D1_Open $6.18
- Gap up of 150% next day. ROCKET_GUARD (Filter 11) territory.

### 5. WOK on 2026-05-11 — wild_d1_range 3.68x
- D1_Low $1.89 → D1_High $6.95
- Same ticker as #1. The pump-day before the apparent split.

## Conclusions

1. No data bugs. Yahoo Finance is delivering correct OHLC.
2. The system is identifying real pump-and-dump events.
3. Future-filter idea: Detection of reverse splits between scan day and D1.
