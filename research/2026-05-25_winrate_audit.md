# Win Rate Audit — task-44 (AUDIT.9)

**Date:** 2026-05-25
**Author:** עמיחי + Claude (session)
**Status:** Complete
**Outcome:** 1 bug fixed (Home page), 2 follow-up tasks identified

---

## Summary

The task originally framed as "Scanner vs Trader split" turned out to be a
misframing. The dashboard actually has **4 different Win Rate displays across
4 different pages**, each measuring a fundamentally different concept on
overlapping but not identical data.

Only **one** of the four was an active bug. The others are legitimately
different metrics measuring different things.

---

## The 4 Win Rate Sources

| # | Page | WR (before) | Source sheet | Method | Status |
|---|------|-------------|--------------|--------|--------|
| 1 | 🏠 Home | 78% | post_analysis | `TP10_Hit.mean()` | **BUG → FIXED** |
| 2 | 💼 Portfolio Tracker | 55.8% | post_analysis (sim) | Internal D1→D5 first-touch | Code duplication |
| 3 | 🔬 Post Analysis | 68.9% | post_analysis | `classify_trade_row` | **CANONICAL** |
| 4 | 📊 Trade History | 43.8% | paper_portfolio | `RealizedPnL > 0` | **ACTUAL** |

---

## What Each Measures

### 🏠 Home (78% → 69%)
**Question:** "What is the historical win rate?"
**Source code:** `dashboard.py:5106` (was `has_outcome['TP10_Hit'].mean()`)
**Bug:** `TP10_Hit=1` if the stock's low touched -10% **anywhere** in D1-D5,
even if the high touched +10% on the same day or on an earlier day. This
counts whipsaws as wins. PK v2.16 explicitly flagged this anti-pattern:

> "prior '~81% win rate' was an artifact — whipsaw rows counted as wins"

But Home page was never updated to use `classify_trade_row`. Fixed in this
session.

### 💼 Portfolio Tracker (55.8%)
**Question:** "If I shorted every Score≥60 stock, simulated $1,000 per
trade with TP/SL, what would the P&L look like?"
**Source code:** `dashboard.py:2043-2089` (`_simulate_short_trades`)
**Method:** Walks D1→D5 in order, checks SL before TP each day. When both
hit same day, counts as LOSS (conservative). Whipsaws are penalized.
**Status:** Code duplication — does its own classification instead of
calling `classify_trade_row`. Legitimate measure (different from canonical:
includes whipsaws as losses), but logic should be consolidated.

### 🔬 Post Analysis (68.9%)
**Question:** "What is the **theoretical** win rate of mean reversion on
Score≥60 pumps, excluding ambiguous cases?"
**Source code:** `dashboard.py:2318` (`classify_trade_row`)
**Method:** Canonical Single Source of Truth. WHIPSAW and NO_TOUCH are
**excluded** from the WR denominator (flagged as investigation categories).
**Status:** Canonical. The rest of the system should align to this.

### 📊 Trade History (43.8%)
**Question:** "What did the Trader Agent **actually achieve** with all 11
filters and execution simulation?"
**Source code:** `agent/dashboard/trade_history_page.py:228-253`
**Method:** `RealizedPnL > 0` from paper_portfolio (Alpaca DRY_RUN).
**Status:** Actual execution. The most realistic number — but lower because
the 11 filters block some signals that would have been winners (and many
that would have been losers).

---

## Why 4 Different Numbers Are OK

Each number answers a different question:

| What you want to know | Use this metric |
|----------------------|-----------------|
| What is the natural edge of this thesis? | Post Analysis (68.9%) |
| How would unfiltered simulation perform? | Portfolio Tracker (55.8%) |
| How does the actual Trader perform? | Trade History (43.8%) |
| Historical KPI for dashboard landing page | Home (was 78%, now 69%) |

The original task framing assumed these 4 should converge to one number.
They shouldn't.

---

## The Fix

### File: `dashboard.py`
### Lines: 5106-5111, 5123

**Before:**
```python
has_outcome   = df[df["TP10_Hit"].notna()] if "TP10_Hit" in df.columns else pd.DataFrame()
win_rate_hist = f"{has_outcome['TP10_Hit'].mean()*100:.0f}%" if not has_outcome.empty else "—"
winners       = has_outcome[has_outcome["TP10_Hit"] == 1] if not has_outcome.empty else pd.DataFrame()
...
m1.metric("🎯 Win Rate", win_rate_hist, delta=f"{len(has_outcome)} עם תוצאה")
```

**After:**
```python
from utils import classify_trade_row
_outcomes_home = df.apply(classify_trade_row, axis=1)
_n_win        = int((_outcomes_home == "WIN").sum())
_n_loss       = int((_outcomes_home == "LOSS").sum())
_n_decided    = _n_win + _n_loss
win_rate_hist = f"{_n_win / _n_decided * 100:.0f}%" if _n_decided > 0 else "—"
winners       = df[_outcomes_home == "WIN"]
has_outcome   = df[_outcomes_home.isin(["WIN", "LOSS"])]
...
m1.metric("🎯 Win Rate", win_rate_hist, delta=f"{_n_decided}/{len(df)} הוכרעו")
```

### Verified locally (2026-05-25 10:05 Peru)

| Metric | Old | New |
|--------|-----|-----|
| Win Rate | 78% | **69%** |
| n_decided | 89 (incl whipsaws+TP10_Hit) | **45** (W+L only) |
| Winners count | 69 | **31** |
| Avg Drop (winners) | -32.7% | **-38.1%** (cleaner — only real winners) |
| Delta display | "89 עם תוצאה" | **"45/105 הוכרעו"** (transparent) |

Outcome distribution on real data:
`WIN=31, LOSS=14, WHIPSAW=8, NO_TOUCH=1, PENDING=51`

Reconciles with Post Analysis page (68.9%)? **YES** (69% ≈ 68.9%)

---

## What the `portfolio` Sheet Actually Is

Common misconception: "the Scanner stream has a WR in the portfolio sheet."
**False.** The `portfolio` sheet (2026-05) has:

- 65 rows, **all Status=Open** — positions are never closed
- 6 columns: PositionKey, Date, Ticker, Score, BuyPrice, Status
- **No PnL column**, no exit data, no WR computation anywhere
- Used only as a **ticker list** by Score Tracker page
- Not read by any WR computation

The "55.8% Scanner WR" comes from `_simulate_short_trades()` operating on
`post_analysis` data, not from the `portfolio` sheet.

---

## Recommendations

### Already Done
1. ✅ Fixed Home page WR (TP10_Hit → classify_trade_row)

### Follow-up Tasks (NOT in this session)
2. **Portfolio Tracker WR consolidation** — `_simulate_short_trades` should
   call `classify_trade_row` instead of its own inline classification. Would
   eliminate the code duplication. Low priority — the inline sim is not
   buggy (it's conservative, counting whipsaws as losses), just duplicated.
3. **Dashboard annotation** — Add hover-text or caption to each WR metric
   explaining what it measures. Users currently have no way to know what
   "Win Rate 55.8%" vs "Win Rate 69%" vs "Win Rate 43.8%" means.
4. **task-44 AUDIT.9 itself** — The original task said "55.8% WR / +$1,018"
   for Scanner and "43.8% WR / -$221" for Trader. Both numbers are stale.
   Current actual: Scanner sim=55.8% (stable), Trader=58.9%/+$1,019.
   The -$221 was likely from an earlier period before bug fixes.
