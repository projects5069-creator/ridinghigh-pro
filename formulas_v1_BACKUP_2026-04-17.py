"""
formulas.py - RidingHigh Pro Centralized Metric Formulas
=========================================================

Single source of truth for ALL metric calculations in the system.
All other modules (auto_scanner, dashboard, post_analysis_collector)
MUST import from this module. Do NOT duplicate formulas elsewhere.

Version: 1.0
Created: 2026-04-17
Author: Amihay Levy

Why this module exists:
-----------------------
Before this file was created, the same formulas existed in multiple places:
- calculate_mxv() in auto_scanner.py AND dashboard.py (copy-paste duplicate)
- ATRX calculated 2 different ways in auto_scanner (ratio) vs dashboard (percentage)
- REL_VOL capped in auto_scanner but not in dashboard
- Float% measured Turnover in dashboard but actual Float in auto_scanner

This created risk of divergence: a fix in one place would leave the other broken.
This module consolidates all formulas so changes happen in ONE place only.

Usage:
------
    from formulas import (
        calculate_mxv,
        calculate_runup,
        calculate_atrx,
        calculate_gap,
        calculate_vwap_dist,
        calculate_rel_vol,
        calculate_float_pct,
        validate_atrx,
    )

Design Principles:
------------------
1. Each function has ONE clear responsibility
2. All edge cases handled (division by zero, None inputs, etc.)
3. Return values are predictable: always float, always in expected range
4. No side effects - pure functions only
5. Validated caps where applicable (e.g., REL_VOL max 100)

Return Units:
-------------
- MxV:         percentage (-2000 to +100)
- RunUp:       percentage (can be negative, typical -50 to +300)
- ATRX:        ratio (0 to ~10, typical 1-5)
- Gap:         percentage (typical -50 to +200)
- VWAP_dist:   percentage (typical -20 to +20)
- REL_VOL:     ratio (0 to 100, capped)
- Float%:      percentage (0 to 100)
"""


# ═══════════════════════════════════════════════════════════════════════
# Constants - Validation Thresholds
# ═══════════════════════════════════════════════════════════════════════

REL_VOL_CAP = 100.0
"""Maximum allowed REL_VOL. yfinance sometimes returns extreme outliers (26,000+)
from stale average_volume data. Cap prevents score manipulation."""

ATRX_VALIDATION_THRESHOLD = 5.0
"""ATRX above this AND ATR below 0.5% of price indicates yfinance bug.
Pattern: ATR calculated on bad historical data gives artificially inflated ATRX."""

ATRX_VALIDATION_ATR_RATIO = 0.005
"""If ATR is less than 0.5% of price AND ATRX > threshold, it's likely bad data."""


# ═══════════════════════════════════════════════════════════════════════
# Metric Calculations
# ═══════════════════════════════════════════════════════════════════════

def calculate_mxv(market_cap, price, volume):
    """
    MxV - Market Cap vs Volume ratio.

    Measures how the day's dollar turnover compares to the company's market cap.
    A very negative value indicates the stock traded multiple times its market cap
    in a single day - a strong pump signal.

    Formula:
        MxV = ((Market Cap - (Price × Volume)) / Market Cap) × 100

    Interpretation:
        MxV = +90%   → Very low turnover (P×V = 10% of MC)
        MxV =   0%   → P×V equals MC
        MxV = -100%  → P×V is 2× MC (moderate pump)
        MxV = -400%  → P×V is 5× MC (strong pump)
        MxV < -1000% → Extreme pump

    Args:
        market_cap: Company market cap in USD
        price: Current stock price
        volume: Day's trading volume (shares)

    Returns:
        float: MxV value as percentage. Returns 0 for invalid inputs.

    Examples:
        >>> calculate_mxv(100_000_000, 5, 50_000_000)  # P×V = 250M, MC = 100M
        -150.0
        >>> calculate_mxv(100_000_000, 2, 10_000_000)  # P×V = 20M, MC = 100M
        80.0
        >>> calculate_mxv(0, 5, 50_000_000)
        0
    """
    try:
        if market_cap is None or market_cap == 0:
            return 0.0
        if price is None or volume is None:
            return 0.0
        return float(((market_cap - (price * volume)) / market_cap) * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_runup(price, open_price):
    """
    RunUp - Intraday rise from open.

    Measures percentage change from today's open to current price.
    Used to identify stocks that have risen sharply during the trading day.

    Formula:
        RunUp = (Price - Open) / Open × 100

    Interpretation:
        RunUp = 0    → No change from open
        RunUp = +30  → Stock up 30% from open
        RunUp = -10  → Stock down 10% from open

    Args:
        price: Current stock price
        open_price: Today's opening price

    Returns:
        float: RunUp as percentage. Returns 0 if open is 0 or invalid.

    Examples:
        >>> calculate_runup(13.00, 10.00)
        30.0
        >>> calculate_runup(10.00, 10.00)
        0.0
        >>> calculate_runup(9.00, 10.00)
        -10.0
    """
    try:
        if open_price is None or open_price == 0:
            return 0.0
        if price is None:
            return 0.0
        return float((price - open_price) / open_price * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_atrx(high, low, atr):
    """
    ATRX - Today's range as ratio of ATR14.

    Measures how volatile today was compared to the average of last 14 days.
    Higher ATRX indicates unusual intraday volatility.

    Formula:
        ATRX = (High - Low) / ATR14

    Interpretation:
        ATRX = 1.0 → Today's range equals average 14-day range
        ATRX = 2.0 → Today moved 2× more than average
        ATRX = 5.0 → Extreme day (5× normal volatility)

    IMPORTANT: This function returns a RATIO, not a percentage.
    Do not confuse with ATR/Price which gives volatility as % of price.

    Args:
        high: Today's high price
        low: Today's low price
        atr: ATR14 value (from ta library)

    Returns:
        float: ATRX ratio. Returns 0 for invalid inputs.

    Examples:
        >>> calculate_atrx(10.0, 8.0, 1.0)  # range $2, ATR $1
        2.0
        >>> calculate_atrx(5.0, 5.0, 1.0)  # no range
        0.0
        >>> calculate_atrx(10.0, 8.0, 0)  # no ATR
        0
    """
    try:
        if atr is None or atr == 0:
            return 0.0
        if high is None or low is None:
            return 0.0
        return float((high - low) / atr)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def validate_atrx(atrx, atr, price):
    """
    Validate ATRX against yfinance bad data patterns.

    yfinance sometimes returns historical ATR values calculated on incorrect data
    (e.g., pre-split prices). This creates an artificial ATR that's tiny relative
    to the current price, which makes ATRX explode to 20+ values.

    Detection pattern:
        If ATR is less than 0.5% of price AND ATRX > 5, it's likely bad data.

    Args:
        atrx: Calculated ATRX ratio
        atr: ATR14 value
        price: Current price

    Returns:
        float: atrx if valid, 0 if detected as bad data

    Examples:
        >>> validate_atrx(3.0, 0.5, 10)  # Normal: ATR is 5% of price
        3.0
        >>> validate_atrx(25.0, 0.02, 10)  # Bad: ATR is 0.2% of price + ATRX huge
        0
        >>> validate_atrx(2.0, 0.01, 10)  # Edge: Low ATR but ATRX reasonable
        2.0
    """
    try:
        if atrx is None or atr is None or price is None:
            return 0.0
        if price == 0:
            return 0.0
        # Bad data pattern: ATR tiny relative to price AND ATRX inflated
        if atr < (ATRX_VALIDATION_ATR_RATIO * price) and atrx > ATRX_VALIDATION_THRESHOLD:
            return 0.0
        return float(atrx)
    except (TypeError, ValueError):
        return 0.0


def calculate_gap(open_price, prev_close):
    """
    Gap - Opening price gap from previous close.

    Measures percentage change between yesterday's close and today's open.
    Large gaps (up or down) often precede volatile trading.

    Formula:
        Gap = (Open - PrevClose) / PrevClose × 100

    Interpretation:
        Gap = 0     → No gap (opened at previous close)
        Gap = +20   → Opened 20% above previous close (gap up)
        Gap = -15   → Opened 15% below previous close (gap down)

    Args:
        open_price: Today's opening price
        prev_close: Previous trading day's closing price

    Returns:
        float: Gap as percentage. Returns 0 for invalid inputs.

    Examples:
        >>> calculate_gap(12.0, 10.0)
        20.0
        >>> calculate_gap(10.0, 10.0)
        0.0
        >>> calculate_gap(8.0, 10.0)
        -20.0
    """
    try:
        if prev_close is None or prev_close == 0:
            return 0.0
        if open_price is None:
            return 0.0
        return float((open_price - prev_close) / prev_close * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_vwap_dist(price, high, low):
    """
    VWAP Distance - Price vs Typical Price.

    NOTE: Despite the name, this calculates distance from Typical Price,
    not true VWAP (Volume-Weighted Average Price).

    Typical Price = (High + Low + Close) / 3

    This is a simpler proxy that doesn't require volume-weighted calculation.
    For true VWAP, would need all intraday bars with volume.

    Formula:
        TypicalPrice = (High + Low + Price) / 3
        VWAP_dist   = (Price / TypicalPrice - 1) × 100

    Interpretation:
        VWAP_dist > 0  → Price above typical (stock trading high in range)
        VWAP_dist < 0  → Price below typical (stock trading low in range)

    Args:
        price: Current price
        high: Today's high
        low: Today's low

    Returns:
        float: VWAP distance as percentage. Returns 0 for invalid inputs.

    Examples:
        >>> calculate_vwap_dist(11.0, 12.0, 9.0)  # typical = 10.67, price 11
        3.125
        >>> calculate_vwap_dist(10.0, 12.0, 8.0)  # typical = 10, price 10
        0.0
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
    """
    REL_VOL - Relative Volume (today's volume vs 20-day average).

    Measures how today's trading volume compares to average.
    High REL_VOL indicates unusual interest in the stock.

    Formula:
        REL_VOL = Volume / AverageVolume(20d)
        REL_VOL = min(REL_VOL, 100)  # cap to prevent outliers

    The cap is applied because yfinance occasionally returns stale or
    incorrect avg_volume values, leading to REL_VOL values of 26,000+.
    Capping at 100 is reasonable: any volume 100× average is already
    the maximum meaningful signal.

    Interpretation:
        REL_VOL = 1.0  → Normal volume (equals 20-day average)
        REL_VOL = 5.0  → 5× normal (unusual activity)
        REL_VOL = 20   → 20× normal (massive pump)
        REL_VOL = 100  → Capped (truly exceptional)

    Args:
        volume: Today's trading volume (shares)
        avg_volume: 20-day average volume

    Returns:
        float: REL_VOL ratio, capped at REL_VOL_CAP (100). Returns 1.0 if avg is 0.

    Examples:
        >>> calculate_rel_vol(1_000_000, 500_000)
        2.0
        >>> calculate_rel_vol(1_000_000, 0)
        1.0
        >>> calculate_rel_vol(5_000_000_000, 10_000)  # Would be 500k, capped
        100.0
    """
    try:
        if volume is None:
            return 1.0
        if avg_volume is None or avg_volume == 0:
            return 1.0
        rel_vol = volume / avg_volume
        # Apply cap to prevent yfinance outliers
        if rel_vol > REL_VOL_CAP:
            return REL_VOL_CAP
        return float(rel_vol)
    except (TypeError, ValueError, ZeroDivisionError):
        return 1.0


def calculate_float_pct(float_shares, shares_outstanding):
    """
    Float% - Percentage of shares available for public trading.

    Measures what percent of total shares are in public float (available to trade).
    Low float stocks (< 50%) are more volatile - many shares are held by insiders
    or long-term holders, so trading has outsized impact on price.

    IMPORTANT: This is TRUE float percentage, NOT volume turnover.
    Older code in dashboard.py incorrectly calculated:
        dashboard (WRONG): volume / shares_outstanding * 100  (this is Turnover Rate)
        formulas (CORRECT): float_shares / shares_outstanding * 100

    Formula:
        Float% = (FloatShares / SharesOutstanding) × 100

    Interpretation:
        Float% = 100  → All shares tradable (most common for large caps)
        Float% = 60   → 40% held by insiders/long-term (typical small cap)
        Float% = 20   → Very low float (high volatility, short squeeze risk)

    Args:
        float_shares: Number of shares available for public trading
        shares_outstanding: Total shares issued by the company

    Returns:
        float: Float percentage (0-100). Returns 0 for invalid inputs.

    Examples:
        >>> calculate_float_pct(8_000_000, 10_000_000)
        80.0
        >>> calculate_float_pct(2_000_000, 10_000_000)
        20.0
        >>> calculate_float_pct(0, 10_000_000)
        0.0
        >>> calculate_float_pct(5_000_000, 0)
        0.0
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
# Module self-test when run directly
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Quick sanity check when running this file directly.
    For comprehensive tests, run: python3 test_formulas.py
    """
    print("=" * 60)
    print("formulas.py - Quick Sanity Check")
    print("=" * 60)
    
    # Test each formula with one example
    print(f"\ncalculate_mxv(100M, $5, 50M vol) = {calculate_mxv(100_000_000, 5, 50_000_000):.2f}")
    print(f"  Expected: -150.00 (turnover is 2.5× market cap)")
    
    print(f"\ncalculate_runup(price=$13, open=$10) = {calculate_runup(13, 10):.2f}")
    print(f"  Expected: 30.00 (up 30% from open)")
    
    print(f"\ncalculate_atrx(high=10, low=8, atr=1) = {calculate_atrx(10, 8, 1):.2f}")
    print(f"  Expected: 2.00 (today's range 2× average)")
    
    print(f"\nvalidate_atrx(atrx=25, atr=0.02, price=10) = {validate_atrx(25, 0.02, 10):.2f}")
    print(f"  Expected: 0.00 (yfinance bad data detected)")
    
    print(f"\ncalculate_gap(open=12, prev_close=10) = {calculate_gap(12, 10):.2f}")
    print(f"  Expected: 20.00 (opened 20% higher)")
    
    print(f"\ncalculate_vwap_dist(price=11, high=12, low=9) = {calculate_vwap_dist(11, 12, 9):.2f}")
    print(f"  Expected: ~3.12 (above typical)")
    
    print(f"\ncalculate_rel_vol(vol=1M, avg=500K) = {calculate_rel_vol(1_000_000, 500_000):.2f}")
    print(f"  Expected: 2.00 (2× normal volume)")
    
    print(f"\ncalculate_rel_vol(vol=5B, avg=10K) = {calculate_rel_vol(5_000_000_000, 10_000):.2f}")
    print(f"  Expected: 100.00 (CAPPED - would be 500,000)")
    
    print(f"\ncalculate_float_pct(float=8M, out=10M) = {calculate_float_pct(8_000_000, 10_000_000):.2f}")
    print(f"  Expected: 80.00 (80% of shares are tradable)")
    
    print("\n" + "=" * 60)
    print("All formulas loaded successfully. ✅")
    print("=" * 60)
