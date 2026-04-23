#!/usr/bin/env python3
"""
config.py - RidingHigh Pro Centralized Configuration
=====================================================

Single source of truth for all configuration values:
- Score weights and thresholds
- Trading thresholds (SL, TP, position size)
- Display thresholds (high/medium/low score tiers)
- System timing (market hours, cutoff dates)
- Colors and UI constants

Version: 2.0
Created: 2026-04-17 (v1.0 was for Score v1)
Updated: 2026-04-17 (v2.0 - matches Score v2 and system state)
Author: Amihay Levy

Usage:
------
    from config import (
        SCORE_WEIGHTS_V2,
        MIN_SCORE_DISPLAY,
        CRITICAL_SCORE,
        SL_THRESHOLD_PCT,
        TP_THRESHOLD_PCT,
        POSITION_SIZE_USD,
    )

Migration note:
---------------
Previous config.py had Score v1 weights (MXV=30%, Gap=10%, etc).
Current system uses Score v2 weights (MXV=25%, ATRX=20%, Gap=0%, etc).
The old WEIGHTS dict is kept under WEIGHTS_V1_LEGACY for reference only.
"""


# ═══════════════════════════════════════════════════════════════════════
# Score v2 Weights & Caps (ACTIVE)
# ═══════════════════════════════════════════════════════════════════════
# These are the weights currently used by calculate_score() in auto_scanner.py
# Committed: 2026-04-11 (commit f3d96ca)
# Last modified: 2026-04-17 (verified match in audit)

SCORE_WEIGHTS_V2 = {
    "MxV":        25,   # % of total score (max 25 points)
    "RunUp":      25,
    "ATRX":       20,
    "RSI":        10,
    "VWAP":       10,
    "ScanChange": 5,
    "REL_VOL":    5,
    # Total: 100
}
"""Active Score v2 weights. Sum must equal 100."""

SCORE_CAPS_V2 = {
    "MxV":        200,   # abs value (scores based on |mxv|/200)
    "RunUp":      30,    # percentage
    "ATRX":       5,     # ratio
    "RSI_HIGH":   70,    # bell curve center high
    "RSI_LOW":    60,    # bell curve center low
    "VWAP":       8,     # percentage
    "ScanChange": 60,    # percentage
    "REL_VOL":    15,    # ratio (for score contribution only)
}
"""Score v2 caps - thresholds for max contribution per metric."""

SCORE_RSI_PARAMS = {
    "CENTER_LOW":   50,   # RSI below this → linear ramp up
    "CENTER_HIGH":  50,   # (alias of CENTER_LOW for clarity in formula)
    "SWEET_HIGH":   70,   # RSI 50-70 → peak zone
    "OVER_DECAY":   30,   # RSI above 70 decays over this range (70-100)
    "HALF_POINT":   20,   # midpoint weight transition (50 → 70 spans 20)
}
"""RSI bell curve parameters for calculate_score.
Formula:
  if rsi < CENTER_LOW (50):   linear ramp to SWEET_HIGH
  if CENTER_LOW <= rsi <= SWEET_HIGH (50-70): peak zone
  if rsi > SWEET_HIGH (70):   linear decay over OVER_DECAY (30) to zero
"""


# ═══════════════════════════════════════════════════════════════════════
# Metric-Level Caps (absolute limits applied before any scoring)
# ═══════════════════════════════════════════════════════════════════════
# These caps protect against yfinance data outliers — applied in formulas.py
# BEFORE scoring logic sees them. Different from SCORE_CAPS_V2 which are
# "max contribution per metric" thresholds for the score formula.

REL_VOL_CAP = 100.0
"""Hard cap on REL_VOL (volume / avg_volume) to prevent yfinance outliers.
   Values above this (e.g., 26794x seen in past data) are clipped to 100.
   Applied in formulas.calculate_rel_vol() before any downstream use."""


# ═══════════════════════════════════════════════════════════════════════
# Display Thresholds
# ═══════════════════════════════════════════════════════════════════════

MIN_SCORE_DISPLAY = 60
"""Minimum score to display in 'top picks' views (dashboard, reports)."""

HIGH_SCORE = 60
"""Score ≥ this is considered 'High' (orange tier)."""

CRITICAL_SCORE = 85
"""Score ≥ this is considered 'Critical' (red tier - strongest signal)."""

MEDIUM_SCORE = 40
"""Score ≥ this is considered 'Medium' (yellow tier)."""

# ─────────────────────────────────────────────────────────────────────
# Trade Entry Threshold (Issue #30, 2026-04-23)
# ─────────────────────────────────────────────────────────────────────
# Minimum score to open a simulated trade in live_trades + portfolio.
# Applies to: live_trades, portfolio (post_analysis inherits from these)
# Does NOT apply to: timeline_live, daily_snapshots (those capture all scans)
# Rationale: E1c research showed Score 60-69 dilute expectancy ~$40/trade
TRADE_ENTRY_MIN_SCORE = 70

# Legacy alias — kept for backwards compat. DO NOT use in new code.
SCANNER_MIN_SCORE = TRADE_ENTRY_MIN_SCORE


# ═══════════════════════════════════════════════════════════════════════
# Trade Simulation Parameters
# ═══════════════════════════════════════════════════════════════════════

POSITION_SIZE_USD = 1000
"""Position size for simulated trades (USD)."""

TP_THRESHOLD_PCT = 10
"""Take Profit: close position when price drops this % (short)."""

SL_THRESHOLD_PCT = 7
"""Stop Loss: close position when price rises this % (short)."""

MAX_HOLDING_DAYS = 5
"""Maximum days to hold a position before forced exit."""

# PnL calculations
TP_THRESHOLD_FRAC = TP_THRESHOLD_PCT / 100.0  # 0.10
SL_THRESHOLD_FRAC = SL_THRESHOLD_PCT / 100.0  # 0.07

# Stretch targets — used only for labeling/metrics, not active trading
TP15_THRESHOLD_PCT = 15
"""TP15 stretch target: mark when price drops ≥15% (informational only)."""

TP20_THRESHOLD_PCT = 20
"""TP20 stretch target: mark when price drops ≥20% (informational only)."""

TP15_THRESHOLD_FRAC = TP15_THRESHOLD_PCT / 100.0  # 0.15
TP20_THRESHOLD_FRAC = TP20_THRESHOLD_PCT / 100.0  # 0.20


# ═══════════════════════════════════════════════════════════════════════
# Data & Timing
# ═══════════════════════════════════════════════════════════════════════

DATA_CUTOFF_DATE = "2026-04-10"
"""Earliest date with clean Score v2 data.
Rows before this have broken scores (before REL_VOL cap, MxV ×100 fix, etc).
Used in Portfolio Score Tracker page to filter out contaminated history."""

SCAN_FREQUENCY_SECONDS = 60
"""Scanner runs every 60 seconds during market hours."""

MARKET_OPEN_HOUR_PERU = 8  # (actually 8:30, but hour check used for rough filter)
"""NYSE market opens at 08:30 Peru time."""

MARKET_OPEN_MINUTE_PERU = 30

MARKET_CLOSE_HOUR_PERU = 15
"""NYSE market closes at 15:00 Peru time."""

POST_ANALYSIS_HOUR_PERU = 16
"""post_analysis_collector.py runs at 16:00 Peru (1 hour after close)."""


# ═══════════════════════════════════════════════════════════════════════
# Data Validation
# ═══════════════════════════════════════════════════════════════════════

MIN_PRICE = 2.00
"""Minimum stock price to include in scans."""

MIN_VOLUME = 100_000
"""Minimum daily volume to include in scans."""

MIN_MARKET_CAP = 1_000_000  # $1M
"""Minimum market cap to include in scans."""


# ═══════════════════════════════════════════════════════════════════════
# Sheets Configuration
# ═══════════════════════════════════════════════════════════════════════

SHEETS_CONFIG_FILE = "sheets_config.json"
"""File containing monthly sheet IDs."""

GOOGLE_CREDS_FILE = "google_credentials.json"
"""Google service account credentials file (gitignored)."""


# ═══════════════════════════════════════════════════════════════════════
# Colors (UI)
# ═══════════════════════════════════════════════════════════════════════

COLORS = {
    "CRITICAL":  "#ff4444",    # red (score >= 85)
    "HIGH":      "#ffaa00",    # orange (score >= 60)
    "MEDIUM":    "#ffdd00",    # yellow (score >= 40)
    "LOW":       "#999999",    # gray (score < 40)
    
    "WIN":       "#00cc66",    # green (TP hit)
    "LOSS":      "#cc3333",    # red (SL hit)
    "PENDING":   "#ffaa00",    # yellow (open position)
    
    # Dashboard cell backgrounds
    "CELL_RED":    "background-color: #5a0000; color: #ff6666",
    "CELL_ORANGE": "background-color: #5a3a00; color: #ffcc80",
    "CELL_YELLOW": "background-color: #5a5500; color: #ffee80",
    "CELL_GREEN":  "background-color: #1a4a1a; color: #80ff80",
}


# ═══════════════════════════════════════════════════════════════════════
# Legacy (DEPRECATED - DO NOT USE)
# ═══════════════════════════════════════════════════════════════════════
# Kept for reference only. These were Score v1 weights.
# Score v1 was replaced by Score v2 on 2026-04-11.

WEIGHTS_V1_LEGACY = {
    'MXV':     20,   # was 20%, now 25%
    'RUN_UP':  5,    # was 5%, now 25% (also v1 scored negative runup!)
    'ATRX':    10,   # was 10%, now 20% (and v1 used /15 cap not /5)
    'RSI':     15,   # was 15% linear, now 10% bell curve
    'VWAP':    2,    # was 2%, now 10%
    'GAP':     3,    # was 3%, now REMOVED
    'REL_VOL': 15,   # was 15%, now 5% (and v1 had /2 cap not /15)
    'FLOAT':   5,    # was 5%, now REMOVED
    'P52W':    10,   # was 10%, now REMOVED
    'PTH':     15,   # was 15%, now REMOVED
}
"""DEPRECATED: Score v1 weights. DO NOT USE.
Current system uses SCORE_WEIGHTS_V2."""


# ═══════════════════════════════════════════════════════════════════════
# Module self-test
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("config.py v2.0 - Configuration Check")
    print("=" * 60)
    
    print("\n── Score v2 Weights (ACTIVE) ──")
    total = 0
    for metric, weight in SCORE_WEIGHTS_V2.items():
        print(f"  {metric:<12} = {weight}%")
        total += weight
    print(f"  {'TOTAL':<12} = {total}%")
    
    if total == 100:
        print("  ✅ Weights sum to 100")
    else:
        print(f"  ❌ Weights sum to {total}, should be 100!")
    
    print("\n── Display Thresholds ──")
    print(f"  MIN_SCORE_DISPLAY  = {MIN_SCORE_DISPLAY}")
    print(f"  HIGH_SCORE         = {HIGH_SCORE}")
    print(f"  CRITICAL_SCORE     = {CRITICAL_SCORE}")
    print(f"  MEDIUM_SCORE       = {MEDIUM_SCORE}")
    print(f"  TRADE_ENTRY_MIN_SCORE = {TRADE_ENTRY_MIN_SCORE}")
    print(f"  SCANNER_MIN_SCORE    = {SCANNER_MIN_SCORE}  (legacy alias)")
    
    print("\n── Trade Parameters ──")
    print(f"  POSITION_SIZE_USD     = ${POSITION_SIZE_USD}")
    print(f"  TP_THRESHOLD_PCT      = {TP_THRESHOLD_PCT}%  (= {TP_THRESHOLD_FRAC} frac)")
    print(f"  SL_THRESHOLD_PCT      = {SL_THRESHOLD_PCT}%  (= {SL_THRESHOLD_FRAC} frac)")
    print(f"  TP15_THRESHOLD_PCT    = {TP15_THRESHOLD_PCT}%  (= {TP15_THRESHOLD_FRAC} frac)")
    print(f"  TP20_THRESHOLD_PCT    = {TP20_THRESHOLD_PCT}%  (= {TP20_THRESHOLD_FRAC} frac)")
    print(f"  MAX_HOLDING_DAYS      = {MAX_HOLDING_DAYS}")
    
    print("\n── System Timing ──")
    print(f"  MARKET_OPEN   = {MARKET_OPEN_HOUR_PERU}:{MARKET_OPEN_MINUTE_PERU:02d} Peru")
    print(f"  MARKET_CLOSE  = {MARKET_CLOSE_HOUR_PERU}:00 Peru")
    print(f"  POST_ANALYSIS = {POST_ANALYSIS_HOUR_PERU}:00 Peru")
    
    print("\n── Data Quality ──")
    print(f"  DATA_CUTOFF_DATE = {DATA_CUTOFF_DATE}")
    print(f"  MIN_PRICE        = ${MIN_PRICE}")
    print(f"  MIN_VOLUME       = {MIN_VOLUME:,}")
    print(f"  MIN_MARKET_CAP   = ${MIN_MARKET_CAP:,}")
    
    print("\n" + "=" * 60)
    print("Configuration loaded ✅")
    print("=" * 60)
