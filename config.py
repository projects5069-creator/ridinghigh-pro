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
    "VWAP":       8,     # percentage
    "ScanChange": 60,    # percentage
    "REL_VOL":    15,    # ratio (for score contribution only)
}
"""Score v2 caps - thresholds for max contribution per metric."""

# Note: RSI has no cap/params entry — calculate_score uses hardcoded overbought
# tiers (>=90/85/80). The former SCORE_RSI_PARAMS + RSI_HIGH/RSI_LOW bell-curve
# constants were dead config (never read) and removed in TASK-188.


# ═══════════════════════════════════════════════════════════════════════
# Raw Data Caps (applied before scoring)
# ═══════════════════════════════════════════════════════════════════════

REL_VOL_CAP = 100.0
"""Hard cap on REL_VOL (volume / avg_volume) to prevent yfinance outliers.
   Values above this (e.g., 26794x seen in past data) are clipped to 100.
   Applied in formulas.calculate_rel_vol() before any downstream use."""

INTERDAY_ARTIFACT_THRESHOLD_PCT = 100.0
"""Data-integrity threshold (TASK-180): flag a close-to-close inter-day move
   whose magnitude exceeds this % as a suspected split/halt artifact.
   Calibrated from RH post_analysis distribution — median 9.8%, p95 49%,
   p99≈96% — so >100% cleanly isolates the artifact tail (TDIC +877%,
   UGRO +417%, PCLA +179%) from real pump moves. Non-destructive: the
   detector only flags rows, never mutates values. Used by
   formulas.is_interday_artifact()."""


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

# TASK-177 — post_analysis outcome windows (SSoT for the two distinct horizons)
# CLASSIFY_DAYS: the OFFICIAL outcome window that feeds calculate_stats / classify_trade.
#   FROZEN at 5 — changing it would alter the official WR/classification. Do NOT widen.
CLASSIFY_DAYS = 5
# NOTE — three representations of the "5-day classification window" coexist intentionally:
#   1. `range(1, 6)` in utils.py (calculate_stats/classify_trade) — the REAL classifier, FROZEN.
#   2. `MAX_HOLDING_DAYS` (above) — legacy DISPLAY-ONLY constant (print only; not in any logic).
#   3. `CLASSIFY_DAYS` (here) — the collection boundary used by post_analysis_collector to split
#      full-OHLC (D1..CLASSIFY_DAYS) from Close+Low (D6..COLLECT_DAYS_FORWARD).
# CLASSIFY_DAYS is DELIBERATELY NOT wired into utils.range(1,6): the classifier stays literal-frozen
# so a window change here can never silently alter the official WR. Do NOT "DRY" this by feeding
# CLASSIFY_DAYS into range(1,6) without a full TDD pass on the classification — that decoupling is
# a feature (TASK-177), not an oversight.
# COLLECT_DAYS_FORWARD: how many forward trading days post_analysis collects OHLC for.
#   D1-D5 = full OHLC (classification); D6..COLLECT_DAYS_FORWARD = Close+Low only — data for
#   the HYP-001 crossover-short hold-window, re-anchored to the drop-event downstream (179).
COLLECT_DAYS_FORWARD = 25
# COLLECT_DAYS_FORWARD_FROM: forward-only cutoff (TASK-177; ties HYPOTHESES.md §A.6 + §D).
#   Rows scanned BEFORE this date are legacy — complete at CLASSIFY_DAYS (D1-D5) and NEVER
#   re-touched for D6-D25 (the discovery / pre-178 sample stays locked; no mass re-write).
#   Rows scanned ON/AFTER it collect the full D1..COLLECT_DAYS_FORWARD horizon.
COLLECT_DAYS_FORWARD_FROM = "2026-06-13"

# TASK-140 net-PnL cost model
SLIP = 0.01                            # slippage 1%/side, adverse (entry fill lower + cover higher)
BORROW_SCENARIOS = [0.50, 2.00, 5.00]  # assumed annual borrow rates (fee=NULL from TASK-139 — assumptions flagged)


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
AGENT_RUNUP_MIN = 0               # %, intraday rise
AGENT_VOLUME_MIN = 100_000         # Liquidity floor
AGENT_MIN_SCANPRICE_USD = 3.0          # L6 (2026-05-25 layers): block sub-$3 stocks (penny-stock-adjacent, wide spread, halt risk)
CHRONIC_DROPPER_BLACKLIST = ["AEHL", "TDIC"]   # L3-precursor (2026-05-26 Stage 2): chronic droppers from DropsLab x-ref (3+ drops in 30d in Apr 2026), accounted for major DRY_RUN losses
AGENT_MARKET_CAP_MIN = 5_000_000   # $5M minimum
AGENT_MARKET_CAP_MAX = 2_000_000_000  # $2B maximum

# Exit criteria — same as scanner except no time limit
AGENT_TP_PCT = 10                  # Same as TP_THRESHOLD_PCT
AGENT_SL_PCT = 10                  # Same as SL_THRESHOLD_PCT
# (AGENT_NO_TIME_LIMIT removed TASK-151 — dead constant, 0 code refs; the agent's
#  no-holding-time-limit design is enforced by the absence of a time check, not a flag.)

# Force-close all OPEN positions at 14:55-14:59 Peru (just before market close).
# Disabled 2026-05-07 — real trader cannot trade after market close, so simulating
# EOD close at 15:00 with stale price corrupts TP_HIT/SL_HIT classification.
# Open positions roll over to next trading day.
AGENT_FORCE_EOD_CLOSE = False
AGENT_EOD_CLOSE_MIN_BEFORE = 5     # Close 5 min before market close
RECONCILE_AUTO_REPAIR = False      # TASK-108: EOD auto-repair of missing paper_portfolio rows from decision_log. GATE: keep OFF until TASK-106 flag-only proves accurate over time (0 proof days as of 2026-06-03); auto-repair WRITES to the sheet.

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
SCORE_WRITE_FROZEN = True          # Stage 1 (ADR-009, TASK-127.2): freeze Score sheet-writes (-> ""); flip False to roll back. forward-only scoreless-data era.
AGENT_LIVE_PAPER = False           # Becomes True after M10 approval

# Postmortem schema versioning — bump when score formula changes
AGENT_SCORE_VERSION = "v2.6"


# ════════════════════════════════════════════════════════════════════
# Data Sentinel — gatekeeper layer (Phase 1 added 2026-05-11)
# ════════════════════════════════════════════════════════════════════
DATA_SENTINEL_ENABLED = True
SENTINEL_MODE = "shadow"  # "shadow" (log only) | "active" (block) | "off" — TASK-66 2026-06-03: active→shadow (counterfactual: would-block WR 64% vs 41%, n=36 single-regime; active was HALTing on false positives). Restore selectively later.

# TASK-128 / Option-B shadow-first (resolves decision-gates 141+174): explicit
# proven-filter gate (Score decoupled from entry). Mirrors SENTINEL_MODE semantics:
#   "shadow" (default) — observe-only: log what the explicit-only gate WOULD decide,
#                        never changes the live action. Score gate stays authoritative.
#   "active"  — RESERVED for the future Stage-2 live flip (NOT wired yet — observes only).
#   "off"     — full no-op (no observation computed).
EXPLICIT_GATE_MODE = "shadow"

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
