# Conversation Summary - March 17, 2026

## Key Decisions Made:

### 1. Scoring System Evolution
- Started with Google Sheets weights
- Tested multiple combinations
- Final: 9 metrics without Run-Up from FINVIZ
- Added Price to 52W High and Float %

### 2. Data Format Clarifications
- Run-Up: DECIMAL in sheets, % in display
- VWAP: DECIMAL in sheets, % in display
- MxV: Graded (not binary)
- All others: Whole numbers

### 3. Live Tracker Design
- Excel-style grid (user request)
- Each row = ticker
- Each column = minute
- Only Score ≥ 40
- Auto-update every minute

### 4. User Preferences
- Full code always (no partial edits)
- Peru timezone (UTC-5)
- Market hours: 13:30-20:00 local
- Desktop shortcut created
- Local operation (no server yet)

### 5. Verified Accuracy
- AIRS: 61.70 (sheets) vs 61.56 (python)
- Difference: 0.14 points (0.23%)
- Acceptable for production

---

## Critical Formula (FINAL):
```python
score = 0

# MxV (20%) - graded
if mxv < 0:
    score += min(abs(mxv) / 50, 1) * 20

# Price to 52W High (10%)
if price_to_52w_high > 0:
    score += min(price_to_52w_high / 100, 1) * 10

# Price to High (15%)
if price_to_high < 0:
    score += min(abs(price_to_high) / 10, 1) * 15

# REL VOL (15%)
score += min(rel_vol / 2, 1) * 15

# RSI (15%)
if rsi > 80:
    score += 15
else:
    score += (rsi / 80) * 15

# ATRX (10%)
score += min(atrx / 15, 1) * 10

# Run-Up (5%)
if run_up < 0:
    score += min(abs(run_up) / 5, 1) * 5

# Float % (5%)
score += min(float_pct / 10, 1) * 5

# Gap (3%)
score += min(abs(gap) / 20, 1) * 3

# VWAP (2%)
score += min(abs(vwap_dist) / 15, 1) * 2
```

---

**User confirmed:** Ready for 1-2 weeks of data collection before optimization

