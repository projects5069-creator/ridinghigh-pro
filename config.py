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

Score v2 (current) replaces Score v1 (deprecated 2026-04-11).
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
"""RSI scoring bell curve parameters."""


# ═══════════════════════════════════════════════════════════════════════
# Raw Data Caps (applied before scoring)
# ═══════════════════════════════════════════════════════════════════════

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

# Trade entry threshold — Score must be ≥ this to enter a trade.
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

SL_THRESHOLD_PCT = 10
"""Stop Loss: close position when price rises this % (short).

Changed from 7% to 10% on 2026-04-25 (Issue #1 SL unification):
Previous setup had inconsistent SL values across dashboard pages
(Portfolio Tracker=7%, Live Trades=10%, Score Comparison=7% D1-only).
Unified to 10% for breathing room on volatile pump stocks.

Future: replace with Dynamic SL by ATRX (see Phase 2 roadmap).
"""

MAX_HOLDING_DAYS = 5
"""Maximum days to hold a position before forced exit."""

# PnL calculations
TP_THRESHOLD_FRAC = TP_THRESHOLD_PCT / 100.0  # 0.10
SL_THRESHOLD_FRAC = SL_THRESHOLD_PCT / 100.0  # 0.10


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
    print(f"  SCANNER_MIN_SCORE  = {SCANNER_MIN_SCORE}")
    
    print("\n── Trade Parameters ──")
    print(f"  POSITION_SIZE_USD     = ${POSITION_SIZE_USD}")
    print(f"  TP_THRESHOLD_PCT      = {TP_THRESHOLD_PCT}%  (= {TP_THRESHOLD_FRAC} frac)")
    print(f"  SL_THRESHOLD_PCT      = {SL_THRESHOLD_PCT}%  (= {SL_THRESHOLD_FRAC} frac)")
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


# ═══════════════════════════════════════════════════════════════════════
# AGENT MODULE CONFIGURATION (Phase 1)
# Added: 2026-05-03 by Phase 1 implementation
# See: agent/ directory, FINAL-SPEC v2.0
# ═══════════════════════════════════════════════════════════════════════

# Entry criteria — DIFFERENT from scanner (intentionally)
AGENT_MIN_SCORE = 50               # Lowered from 60 — admits micro-cap pumps scoring 50-59
AGENT_MXV_MAX = -100               # Must be very negative
AGENT_RUNUP_MIN = 30               # %, intraday rise
AGENT_VOLUME_MIN = 100_000         # Liquidity floor
AGENT_MARKET_CAP_MIN = 5_000_000   # $5M minimum
AGENT_MARKET_CAP_MAX = 2_000_000_000  # $2B maximum

# Exit criteria — same as scanner except no time limit
AGENT_TP_PCT = 10                  # Same as TP_THRESHOLD_PCT
AGENT_SL_PCT = 10                  # Same as SL_THRESHOLD_PCT
AGENT_NO_TIME_LIMIT = True         # ⚠️ DIFFERENT from MAX_HOLDING_DAYS=5

# Force-close all OPEN positions at 14:55-14:59 Peru (just before market close).
# Disabled 2026-05-07 — real trader cannot trade after market close, so simulating
# EOD close at 15:00 with stale price corrupts TP_HIT/SL_HIT classification.
# Open positions roll over to next trading day.
AGENT_FORCE_EOD_CLOSE = False
AGENT_EOD_CLOSE_MIN_BEFORE = 5     # Close 5 min before market close

# Position sizing
AGENT_POSITION_SIZE_USD = 1000     # Same as POSITION_SIZE_USD

# Cold Start Mode (first 30 days)
AGENT_COLD_START_ENABLED = True
AGENT_COLD_START_DAYS = 30
AGENT_COLD_START_MAX_CONCURRENT = 5
AGENT_COLD_START_MAX_DAILY = 10
AGENT_COLD_START_DAILY_LOSS_ALERT_USD = 200
# Max times the agent may re-enter the SAME ticker in one day. Re-entry
# after a same-day SL/TP exit is intentional (volatile pumps give repeat
# setups) but must be bounded to limit churn / single-ticker exposure.
AGENT_MAX_REENTRIES_PER_TICKER = 3

# ROCKET_GUARD (Filter 11) — block shorting a stock still climbing vertically.
# Calibrated on 196 post_analysis rows: RunUp>=50 AND PriceToHigh>=-10
# blocks 16 historical losses, 0 winners. PIII 2026-05-15 sits exactly on it.
AGENT_ROCKET_GUARD_RUNUP = 50    # %, RunUp at/above this = still climbing
AGENT_ROCKET_GUARD_PTH   = -10   # %, PriceToHigh at/above this = still near peak

# Modes
AGENT_DRY_RUN = True               # Start in DRY_RUN; switch to False at M10
AGENT_LIVE_PAPER = False           # Becomes True after M10 approval

# Postmortem schema versioning — bump when score formula changes
AGENT_SCORE_VERSION = "v2.6"


# ════════════════════════════════════════════════════════════════════
# Data Sentinel — gatekeeper layer (Phase 1 added 2026-05-11)
# ════════════════════════════════════════════════════════════════════
DATA_SENTINEL_ENABLED = True
SENTINEL_MODE = "shadow"  # "shadow" (log only) | "active" (block) | "off"

# Per-check enable flags (Phase 2 + 3 use these)
SENTINEL_CHECK_PRICE_FRESHNESS = True       # FINVIZ vs Alpaca delta
SENTINEL_CHECK_COMPLETENESS = True          # 7 required metrics
SENTINEL_CHECK_SCAN_FRESHNESS = True        # scan age in minutes
SENTINEL_CHECK_QUOTA = True                 # Sheets writes/min
SENTINEL_CHECK_PROVIDER = True              # heartbeat to Alpaca
SENTINEL_CHECK_PRICE_SANITY = True          # min/max USD bounds
SENTINEL_CHECK_POSITION_SYNC = True         # paper_portfolio integrity

# Thresholds
SENTINEL_PRICE_DELTA_MAX_PCT = 2.0          # 2% gap = stale
SENTINEL_SCAN_MAX_AGE_MINUTES = 5           # warn at 5 min (was 3 — too tight vs ~1.6min scan cadence, gaps up to 3min are normal)
SENTINEL_SCAN_MAX_AGE_BLOCK_MINUTES = 10    # block at 10 min (was 5 — only block when pipeline truly stuck)
SENTINEL_QUOTA_DEFENSIVE_THRESHOLD = 50     # writes/min → defensive
SENTINEL_QUOTA_HALT_THRESHOLD = 60          # writes/min → halt
SENTINEL_PRICE_MIN_USD = 0.01
SENTINEL_PRICE_MAX_USD = 10000.0
