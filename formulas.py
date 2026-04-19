"""
formulas.py - RidingHigh Pro Centralized Metric Formulas
=========================================================

Single source of truth for ALL metric calculations in the system.
All other modules (auto_scanner, dashboard, post_analysis_collector,
backfill_ohlc) MUST import from this module. Do NOT duplicate formulas
elsewhere.

Version: 2.0
Created: 2026-04-17 (v1.0)
Extended: 2026-04-17 (v2.0 - added 7 more functions)
Author: Amihay Levy

Why this module exists:
-----------------------
Before this file was created, the same formulas existed in multiple places:
- calculate_mxv() in auto_scanner.py AND dashboard.py (copy-paste duplicate)
- ATRX calculated 2 different ways in auto_scanner (ratio) vs dashboard (percentage)
- REL_VOL cap centralized in config.REL_VOL_CAP (applied in calculate_rel_vol)
- Float% measured Turnover in dashboard but actual Float in auto_scanner

This created risk of divergence: a fix in one place would leave the other broken.
This module consolidates all formulas so changes happen in ONE place only.

v2.0 additions (2026-04-17):
----------------------------
Added 7 more functions that were calculated inline across multiple files:
- calculate_price_to_high       (PriceToHigh metric)
- calculate_price_to_52w_high   (PriceTo52WHigh metric)
- calculate_scan_change         (ScanChange% metric)
- calculate_drop_from_high      (drop_from_high_pct for live tracking)
- calculate_max_drop            (MaxDrop for post analysis)
- calculate_d1_gap              (D1 gap from scan price)
- calculate_pnl_pct             (Short P&L percentage)

Usage:
------
    from formulas import (
        # Core metrics (v1.0)
        calculate_mxv,
        calculate_runup,
        calculate_atrx,
        validate_atrx,
        calculate_gap,
        calculate_vwap_dist,
        calculate_rel_vol,
        calculate_float_pct,
        # Extended metrics (v2.0)
        calculate_price_to_high,
        calculate_price_to_52w_high,
        calculate_scan_change,
        calculate_drop_from_high,
        calculate_max_drop,
        calculate_d1_gap,
        calculate_pnl_pct,
    )

Design Principles:
------------------
1. Each function has ONE clear responsibility
2. All edge cases handled (division by zero, None inputs, etc.)
3. Return values are predictable: always float, always in expected range
4. No side effects - pure functions only
5. Validated caps where applicable (e.g., REL_VOL max 100)
"""

from config import SCORE_WEIGHTS_V2, SCORE_CAPS_V2, SCORE_RSI_PARAMS, REL_VOL_CAP


# ═══════════════════════════════════════════════════════════════════════
# Constants - Validation Thresholds
# ═══════════════════════════════════════════════════════════════════════

ATRX_VALIDATION_THRESHOLD = 5.0
ATRX_VALIDATION_ATR_RATIO = 0.005


# ═══════════════════════════════════════════════════════════════════════
# Core Metric Calculations (v1.0)
# ═══════════════════════════════════════════════════════════════════════

def calculate_mxv(market_cap, price, volume):
    """MxV - Market Cap vs Volume ratio. Returns percentage."""
    try:
        if market_cap is None or market_cap == 0:
            return 0.0
        if price is None or volume is None:
            return 0.0
        return float(((market_cap - (price * volume)) / market_cap) * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_runup(price, open_price):
    """RunUp - Intraday rise from open. Returns percentage."""
    try:
        if open_price is None or open_price == 0:
            return 0.0
        if price is None:
            return 0.0
        return float((price - open_price) / open_price * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_atrx(high, low, atr):
    """ATRX - Today's range as ratio of ATR14. Returns RATIO (not percentage)."""
    try:
        if atr is None or atr == 0:
            return 0.0
        if high is None or low is None:
            return 0.0
        return float((high - low) / atr)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def validate_atrx(atrx, atr, price):
    """Validate ATRX - returns 0 if yfinance bad data pattern detected."""
    try:
        if atrx is None or atr is None or price is None:
            return 0.0
        if price == 0:
            return 0.0
        if atr < (ATRX_VALIDATION_ATR_RATIO * price) and atrx > ATRX_VALIDATION_THRESHOLD:
            return 0.0
        return float(atrx)
    except (TypeError, ValueError):
        return 0.0


def calculate_gap(open_price, prev_close):
    """Gap - Opening price gap from previous close. Returns percentage."""
    try:
        if prev_close is None or prev_close == 0:
            return 0.0
        if open_price is None:
            return 0.0
        return float((open_price - prev_close) / prev_close * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_vwap_dist(price, high, low):
    """VWAP Distance - Price vs Typical Price. Returns percentage.
    NOTE: Despite the name, this is distance from Typical Price (H+L+C)/3,
    not true volume-weighted VWAP.
    """
    try:
        if price is None or high is None or low is None:
            return 0.0
        typical_price = (high + low + price) / 3
        if typical_price == 0:
            return 0.0
        return float((price / typical_price - 1) * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_rel_vol(volume, avg_volume):
    """REL_VOL - Today's volume vs 20-day average. Capped at 100."""
    try:
        if volume is None:
            return 1.0
        if avg_volume is None or avg_volume == 0:
            return 1.0
        rel_vol = volume / avg_volume
        if rel_vol > REL_VOL_CAP:
            return REL_VOL_CAP
        return float(rel_vol)
    except (TypeError, ValueError, ZeroDivisionError):
        return 1.0


def calculate_float_pct(float_shares, shares_outstanding):
    """Float% - Percentage of shares in public float.
    IMPORTANT: This is TRUE float percentage, NOT volume turnover.
    """
    try:
        if shares_outstanding is None or shares_outstanding == 0:
            return 0.0
        if float_shares is None or float_shares == 0:
            return 0.0
        return float(float_shares / shares_outstanding * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


# ═══════════════════════════════════════════════════════════════════════
# Extended Metric Calculations (v2.0 - added 2026-04-17)
# ═══════════════════════════════════════════════════════════════════════

def calculate_price_to_high(price, high_today):
    """PriceToHigh - Price distance from today's high. Returns percentage (typically negative).
    
    Formula:
        PriceToHigh = (Price - HighToday) / HighToday × 100
    
    Returns 0 if price equals high, negative if below.
    """
    try:
        if high_today is None or high_today == 0:
            return 0.0
        if price is None:
            return 0.0
        return float((price - high_today) / high_today * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_price_to_52w_high(price, high_52w):
    """PriceTo52WHigh - Price distance from 52-week high. Returns percentage (typically negative).
    
    Formula:
        PriceTo52WHigh = (Price - High52W) / High52W × 100
    """
    try:
        if high_52w is None or high_52w == 0:
            return 0.0
        if price is None:
            return 0.0
        return float((price - high_52w) / high_52w * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_scan_change(price, prev_close):
    """ScanChange% - Change from previous close. Returns percentage.
    
    Different from Gap (which is open vs prev close).
    ScanChange is current price vs prev close.
    
    This is the STRONGEST single predictor based on 124-row analysis
    (r = -0.348 with MaxDrop).
    
    Formula:
        ScanChange% = (Price - PrevClose) / PrevClose × 100
    """
    try:
        if prev_close is None or prev_close == 0:
            return 0.0
        if price is None:
            return 0.0
        return float((price - prev_close) / prev_close * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_drop_from_high(current_price, intraday_high):
    """DropFromHigh - How much price dropped from intraday high (positive value).
    
    Used for live tracking during trading day.
    Returns POSITIVE value (magnitude of drop).
    
    Formula:
        DropFromHigh = (IntradayHigh - CurrentPrice) / IntradayHigh × 100
    """
    try:
        if intraday_high is None or intraday_high == 0:
            return 0.0
        if current_price is None:
            return 0.0
        drop = (intraday_high - current_price) / intraday_high * 100
        return float(max(0.0, drop))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_max_drop(min_low, scan_price):
    """MaxDrop - Maximum drop from scan price (post-analysis).
    
    This is the PRIMARY ground truth for evaluating short opportunities.
    Typically NEGATIVE (we hope price drops below scan price).
    
    Formula:
        MaxDrop = (MinLow - ScanPrice) / ScanPrice × 100
    """
    try:
        if scan_price is None or scan_price == 0:
            return 0.0
        if min_low is None:
            return 0.0
        return float((min_low - scan_price) / scan_price * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_d1_gap(d1_open, scan_price):
    """D1Gap - Next trading day overnight gap from scan price.
    
    For short positions, negative D1Gap (gap down) is favorable.
    Returns 0 if d1_open is None (not yet available).
    
    Formula:
        D1Gap = (D1Open - ScanPrice) / ScanPrice × 100
    """
    try:
        if scan_price is None or scan_price == 0:
            return 0.0
        if d1_open is None:
            return 0.0
        return float((d1_open - scan_price) / scan_price * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_pnl_pct(entry_price, exit_price, is_short=True):
    """PnL% - Profit/Loss percentage.
    
    For SHORT (default): we profit when price drops.
        PnL% = (entry_price - exit_price) / entry_price × 100
    
    For LONG: we profit when price rises.
        PnL% = (exit_price - entry_price) / entry_price × 100
    """
    try:
        if entry_price is None or entry_price == 0:
            return 0.0
        if exit_price is None:
            return 0.0
        if is_short:
            return float((entry_price - exit_price) / entry_price * 100)
        else:
            return float((exit_price - entry_price) / entry_price * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


# ═══════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════
# Dynamic Score (v2.0 - experimental, based on empirical correlations)
# ═══════════════════════════════════════════════════════════════════════

def normalize_mxv(mxv, min_val=-5000, max_val=0):
    """Normalize MxV to 0-100 scale. More negative MxV = higher score."""
    try:
        if mxv is None:
            return 0.0
        clipped = max(min(mxv, max_val), min_val)
        return float(((clipped - max_val) / (min_val - max_val)) * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def normalize_atrx(atrx, min_val=0, max_val=50):
    """Normalize ATRX to 0-100 scale. Higher ATRX = higher score."""
    try:
        if atrx is None:
            return 0.0
        clipped = max(min(atrx, max_val), min_val)
        return float((clipped - min_val) / (max_val - min_val) * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_dynamic_score(mxv, atrx, mxv_weight=0.6, atrx_weight=0.4,
                             mxv_min=-5000, mxv_max=0,
                             atrx_min=0, atrx_max=50):
    """DynamicScore - Based ONLY on MxV and ATRX (proven correlations).

    Returns: Score from 0-100
    """
    try:
        mxv_norm = normalize_mxv(mxv, mxv_min, mxv_max)
        atrx_norm = normalize_atrx(atrx, atrx_min, atrx_max)
        return round(float(mxv_norm * mxv_weight + atrx_norm * atrx_weight), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


# ═══════════════════════════════════════════════════════════════════════
# Score Functions (9 variants + entry score)
# Migrated from auto_scanner.py — Issue #7.1
# ═══════════════════════════════════════════════════════════════════════

def calculate_score(metrics):
    """
    Main Score v2 calculation. Reads weights and caps from config.py.

    Weights (must sum to 100):
        MxV=25, RunUp=25, ATRX=20, RSI=10, VWAP=10, ScanChange=5, REL_VOL=5
    Caps (thresholds for max contribution per metric):
        MxV=200 (|mxv|), RunUp=30%, ATRX=5x, VWAP=8%, ScanChange=60%, REL_VOL=15x
    RSI: bell curve centered at 50-70 sweet spot.
    """
    W = SCORE_WEIGHTS_V2
    C = SCORE_CAPS_V2
    R = SCORE_RSI_PARAMS
    score = 0
    # MxV — negative values only (pump signal)
    try:
        if metrics['mxv'] < 0:
            score += min(abs(metrics['mxv']) / C["MxV"], 1) * W["MxV"]
    except: pass
    # RunUp — positive only
    try:
        if metrics['run_up'] > 0:
            score += min(metrics['run_up'] / C["RunUp"], 1) * W["RunUp"]
    except: pass
    # ATRX — always scored
    try:
        score += min(metrics['atrx'] / C["ATRX"], 1) * W["ATRX"]
    except: pass
    # RSI — bell curve (linear up to 50, peak 50-70, decay 70+)
    try:
        rsi = metrics['rsi']
        half = W["RSI"] / 2  # e.g., 5 when weight=10
        if rsi < R["CENTER_LOW"]:
            score += (rsi / R["CENTER_LOW"]) * half
        elif rsi <= R["SWEET_HIGH"]:
            score += half + ((rsi - R["CENTER_LOW"]) / R["HALF_POINT"]) * half
        else:
            score += max(0, W["RSI"] - ((rsi - R["SWEET_HIGH"]) / R["OVER_DECAY"]) * half)
    except: pass
    # VWAP — positive distance above VWAP
    try:
        if metrics['vwap_dist'] > 0:
            score += min(metrics['vwap_dist'] / C["VWAP"], 1) * W["VWAP"]
    except: pass
    # ScanChange — positive only
    try:
        if metrics.get('change', 0) > 0:
            score += min(metrics['change'] / C["ScanChange"], 1) * W["ScanChange"]
    except: pass
    # REL_VOL — always scored
    try:
        score += min(metrics['rel_vol'] / C["REL_VOL"], 1) * W["REL_VOL"]
    except: pass
    # Gap removed from v2 entirely
    return round(score, 2)


def calculate_score_i(metrics):
    """MxV dominant — 50% weight"""
    score = 0
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/150, 1) * 50
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/30, 1) * 20
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/5, 1) * 20
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/60, 1) * 10
    except: pass
    return round(score, 2)


def calculate_score_b(metrics):
    """Score_B: MxV=30%/cap300, RunUp=30%/cap40, ATRX=25%/cap6, VWAP=10%/cap10, Change=5%/cap80"""
    score = 0
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/300, 1) * 30
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/40, 1) * 30
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/6, 1) * 25
    except: pass
    try:
        vwap = float(metrics.get('vwap_dist', 0) or 0)
        if vwap > 0: score += min(vwap/10, 1) * 10
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/80, 1) * 5
    except: pass
    return round(score, 2)


def calculate_score_c(metrics):
    """Score_C: ATRX=35%/cap8, Change=25%/cap100, RunUp=20%/cap50, VWAP=15%/cap12, MxV=5%/cap500"""
    score = 0
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/8, 1) * 35
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/100, 1) * 25
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/50, 1) * 20
    except: pass
    try:
        vwap = float(metrics.get('vwap_dist', 0) or 0)
        if vwap > 0: score += min(vwap/12, 1) * 15
    except: pass
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/500, 1) * 5
    except: pass
    return round(score, 2)


def calculate_score_d(metrics):
    """Score_D: MxV=40%/cap150, RunUp=25%/cap25, Change=20%/cap60, ATRX=10%/cap4, VWAP=5%/cap8"""
    score = 0
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/150, 1) * 40
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/25, 1) * 25
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/60, 1) * 20
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/4, 1) * 10
    except: pass
    try:
        vwap = float(metrics.get('vwap_dist', 0) or 0)
        if vwap > 0: score += min(vwap/8, 1) * 5
    except: pass
    return round(score, 2)


def calculate_score_e(metrics):
    """Score_E: Change=35%/cap150, RunUp=30%/cap60, MxV=20%/cap400, ATRX=15%/cap5"""
    score = 0
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/150, 1) * 35
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/60, 1) * 30
    except: pass
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/400, 1) * 20
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/5, 1) * 15
    except: pass
    return round(score, 2)


def calculate_score_f(metrics):
    """Score_F: VWAP=40%/cap20, RunUp=25%/cap35, ATRX=20%/cap5, MxV=10%/cap200, Change=5%/cap50"""
    score = 0
    try:
        vwap = float(metrics.get('vwap_dist', 0) or 0)
        if vwap > 0: score += min(vwap/20, 1) * 40
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/35, 1) * 25
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/5, 1) * 20
    except: pass
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/200, 1) * 10
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/50, 1) * 5
    except: pass
    return round(score, 2)


def calculate_score_g(metrics):
    """Score_G: MxV=25%/cap250, RunUp=25%/cap30, ATRX=20%/cap5, RelVol sweet spot 10-100x=20pts (penalty above 200x), Change=10%/cap60"""
    score = 0
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/250, 1) * 25
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/30, 1) * 25
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/5, 1) * 20
    except: pass
    try:
        rel_vol = float(metrics.get('rel_vol', 0) or 0)
        if 10 <= rel_vol <= 100:
            score += 20
        elif rel_vol > 100:
            penalty = min((rel_vol - 100) / 100, 1) * 20
            score += max(0, 20 - penalty)
        elif rel_vol > 0:
            score += min(rel_vol / 10, 1) * 20
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/60, 1) * 10
    except: pass
    return round(score, 2)


def calculate_score_h(metrics):
    """Score_H: MxV=25%/cap200, RunUp=25%/cap30, ATRX=25%/cap5, VWAP=15%/cap8, Change=10%/cap60"""
    score = 0
    try:
        mxv = float(metrics.get('mxv', 0) or 0)
        if mxv < 0: score += min(abs(mxv)/200, 1) * 25
    except: pass
    try:
        ru = float(metrics.get('run_up', 0) or 0)
        if ru > 0: score += min(ru/30, 1) * 25
    except: pass
    try:
        atrx = float(metrics.get('atrx', 0) or 0)
        score += min(atrx/5, 1) * 25
    except: pass
    try:
        vwap = float(metrics.get('vwap_dist', 0) or 0)
        if vwap > 0: score += min(vwap/8, 1) * 15
    except: pass
    try:
        change = float(metrics.get('change', 0) or 0)
        if change > 0: score += min(change/60, 1) * 10
    except: pass
    return round(score, 2)


def calculate_entry_score(current_price, intra_high, scan_price, vwap_price, now_peru):
    """
    Entry Score 0-100: how good is THIS MOMENT to enter a short.
    Run only on stocks with Score >= 60.

    Components:
    - PeakConfirm (40pts): stock has dropped from intraday high
    - ReversalDepth (30pts): how far below the high is current price
    - TimeToClose (20pts): closer to EOD = better (14:00-15:00 ideal)
    - VWAPCross (10pts): price crossed below VWAP = confirmed reversal
    """
    score = 0

    try:
        if intra_high > 0 and current_price < intra_high:
            # PeakConfirm: 40pts — dropped at least 1% from high
            drop_from_high_pct = (intra_high - current_price) / intra_high * 100
            if drop_from_high_pct >= 1:
                score += min(drop_from_high_pct / 5, 1) * 40  # 5% drop = max
    except: pass

    try:
        if intra_high > 0 and scan_price > 0:
            # ReversalDepth: 30pts — how much of the pump has reversed
            total_pump = intra_high - scan_price
            reversal = intra_high - current_price
            if total_pump > 0:
                reversal_pct = reversal / total_pump  # 0-1 (1 = fully reversed)
                score += max(0, min(reversal_pct, 1)) * 30
    except: pass

    try:
        # TimeToClose: 20pts — ideal window 14:00-15:00
        close_time = now_peru.replace(hour=15, minute=0, second=0, microsecond=0)
        mins_to_close = (close_time - now_peru).total_seconds() / 60
        if 0 <= mins_to_close <= 60:    # last hour = max
            score += 20
        elif 60 < mins_to_close <= 120: # 13:00-14:00 = half
            score += 10
        elif mins_to_close < 0:
            score += 0  # after close
    except: pass

    try:
        # VWAPCross: 10pts — current price below VWAP
        if vwap_price > 0 and current_price < vwap_price:
            score += 10
    except: pass

    return round(score, 2)


# Module self-test when run directly
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Quick sanity check. For comprehensive tests, run: python3 test_formulas.py"""
    print("=" * 60)
    print("formulas.py v2.0 - Quick Sanity Check")
    print("=" * 60)
    
    print("\n── Core Metrics (v1.0) ──")
    print(f"calculate_mxv(100M, $5, 50M vol) = {calculate_mxv(100_000_000, 5, 50_000_000):.2f}")
    print(f"calculate_runup(price=$13, open=$10) = {calculate_runup(13, 10):.2f}")
    print(f"calculate_atrx(high=10, low=8, atr=1) = {calculate_atrx(10, 8, 1):.2f}")
    print(f"validate_atrx(atrx=25, atr=0.02, price=10) = {validate_atrx(25, 0.02, 10):.2f}")
    print(f"calculate_gap(open=12, prev_close=10) = {calculate_gap(12, 10):.2f}")
    print(f"calculate_vwap_dist(price=11, high=12, low=9) = {calculate_vwap_dist(11, 12, 9):.2f}")
    print(f"calculate_rel_vol(vol=1M, avg=500K) = {calculate_rel_vol(1_000_000, 500_000):.2f}")
    print(f"calculate_rel_vol(vol=5B, avg=10K) = {calculate_rel_vol(5_000_000_000, 10_000):.2f} (CAPPED)")
    print(f"calculate_float_pct(float=8M, out=10M) = {calculate_float_pct(8_000_000, 10_000_000):.2f}")
    
    print("\n── Extended Metrics (v2.0 - NEW) ──")
    print(f"calculate_price_to_high(9, 10) = {calculate_price_to_high(9, 10):.2f}")
    print(f"calculate_price_to_52w_high(5, 10) = {calculate_price_to_52w_high(5, 10):.2f}")
    print(f"calculate_scan_change(15, 10) = {calculate_scan_change(15, 10):.2f}")
    print(f"calculate_drop_from_high(8, 10) = {calculate_drop_from_high(8, 10):.2f}")
    print(f"calculate_max_drop(9, 10) = {calculate_max_drop(9, 10):.2f}")
    print(f"calculate_d1_gap(9.5, 10) = {calculate_d1_gap(9.5, 10):.2f}")
    print(f"calculate_pnl_pct(10, 9) = {calculate_pnl_pct(10, 9):.2f} (short profit)")
    print(f"calculate_pnl_pct(10, 11) = {calculate_pnl_pct(10, 11):.2f} (short loss)")
    
    print("\n" + "=" * 60)
    print("All 15 formulas loaded successfully ✅")
    print("=" * 60)
