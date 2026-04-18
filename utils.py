"""
utils.py - RidingHigh Pro Shared Utilities
===========================================

Centralized utility functions used across multiple modules.
Eliminates code duplication and ensures consistent behavior.

Version: 1.0
Created: 2026-04-17
Author: Amihay Levy

Why this module exists:
-----------------------
Before this file was created, the same utility functions existed in
multiple places, leading to code duplication and potential inconsistency:

- parse_market_cap()       existed in auto_scanner.py AND dashboard.py
- parse_volume()           existed in auto_scanner.py AND dashboard.py
- get_market_cap_smart()   existed in auto_scanner.py AND dashboard.py
- is_trading_day()         existed in auto_scanner.py, post_analysis_collector.py, enrich_post_analysis.py
- get_trading_days_after() existed in backfill_ohlc.py AND post_analysis_collector.py
- is_day_complete()        existed in backfill_ohlc.py AND post_analysis_collector.py
- calculate_stats()        existed in backfill_ohlc.py AND post_analysis_collector.py

Now all these live here with ONE canonical implementation.

Usage:
------
    from utils import (
        parse_market_cap,
        parse_volume,
        get_market_cap_smart,
        is_trading_day,
        get_trading_days_after,
        is_day_complete,
        calculate_stats,
        get_peru_time,
    )

Dependencies:
-------------
- pandas (for pd.isna)
- pytz (for timezone handling)
- pandas_market_calendars (optional - for holiday detection)
"""
import pytz
from datetime import datetime, timedelta
from config import TP_THRESHOLD_FRAC, SL_THRESHOLD_FRAC


# ═══════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════

PERU_TZ = pytz.timezone("America/Lima")
"""Peru timezone - used throughout the system (UTC-5, no DST)."""

MARKET_CLOSE_HOUR_PERU = 15
"""NYSE closes at 15:00 Peru time (16:00 EST / 20:00 UTC)."""


# ═══════════════════════════════════════════════════════════════════════
# Time & Date Utilities
# ═══════════════════════════════════════════════════════════════════════

def get_peru_time():
    """Return current time in Peru timezone.
    
    Returns:
        datetime: Current datetime with Peru tzinfo
    """
    return datetime.now(PERU_TZ)


def is_trading_day(date=None):
    """
    Returns True if the given date is a NASDAQ trading day.
    
    Checks weekends + US market holidays via pandas_market_calendars.
    Falls back to weekday-only check if library unavailable.
    
    Args:
        date: date object (default: today in Peru time)
    
    Returns:
        bool: True if it's a trading day, False otherwise
    
    Examples:
        >>> is_trading_day()  # today
        True  # if today is a weekday + non-holiday
        >>> is_trading_day(datetime(2026, 4, 11).date())  # Saturday
        False
    """
    if date is None:
        date = get_peru_time().date()
    
    try:
        import pandas_market_calendars as mcal
        nyse = mcal.get_calendar("NASDAQ")
        schedule = nyse.schedule(
            start_date=date.strftime("%Y-%m-%d"),
            end_date=date.strftime("%Y-%m-%d")
        )
        return not schedule.empty
    except Exception:
        # Fallback: weekday only (no holiday detection)
        return date.weekday() < 5


def is_market_hours():
    """True if NYSE market is currently open (Peru time).

    Takes into account trading days (weekdays + non-holidays) via is_trading_day().

    Returns:
        bool: True if market is open NOW in Peru time
    """
    from datetime import time as dt_time
    now = get_peru_time()
    market_open  = dt_time(8, 30)
    market_close = dt_time(15, 0)
    return is_trading_day(now.date()) and market_open <= now.time() <= market_close


def is_day_complete(date_str):
    """
    True when the full trading day for date_str has closed.
    
    Market close = 15:00 Peru time.
    - Past weekdays: always complete
    - Today: complete only after 15:00 Peru
    - Future or weekends: never complete
    
    Args:
        date_str: Date string in 'YYYY-MM-DD' format
    
    Returns:
        bool: True if trading day is complete
    
    Examples:
        >>> is_day_complete("2026-04-16")  # past weekday
        True
        >>> is_day_complete("2026-04-17")  # today, before 15:00
        False  # or True depending on current time
    """
    now_peru = get_peru_time()
    today = now_peru.date()
    day = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # Weekend - never complete
    if day.weekday() >= 5:
        return False
    
    # Past weekdays - always complete
    if day < today:
        return True
    
    # Today - complete after market close
    if day == today:
        return now_peru.hour >= MARKET_CLOSE_HOUR_PERU
    
    # Future - never complete yet
    return False


def get_trading_days_after(scan_date_str, n=5):
    """
    Get the next N trading days after a given scan date.
    
    Delegates to sheets_manager.trading_days_after() for the actual logic.
    
    Args:
        scan_date_str: Start date in 'YYYY-MM-DD' format
        n: Number of trading days to return (default 5)
    
    Returns:
        list: List of trading day strings in 'YYYY-MM-DD' format
    """
    import sheets_manager
    return sheets_manager.trading_days_after(scan_date_str, n)


def _is_missing(val) -> bool:
    """True if value is None, NaN, empty string, or literal 'nan'/'None'/'NaN'.

    Used across backfill/enrich/health_check modules to detect missing data.
    """
    if val is None:
        return True
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except (TypeError, ValueError):
        pass
    try:
        import pandas as pd
        if isinstance(val, float) and pd.isna(val):
            return True
    except (ImportError, TypeError, ValueError):
        pass
    return str(val).strip() in ("", "nan", "None", "NaN")


# ═══════════════════════════════════════════════════════════════════════
# FINVIZ Parsing
# ═══════════════════════════════════════════════════════════════════════

def parse_market_cap(s):
    """
    Parse FINVIZ market cap string to float.
    
    FINVIZ returns values like '125.50M' or '1.25B' or '-'.
    Converts to full numeric value (e.g., 125_500_000.0 or 1_250_000_000.0).
    
    Args:
        s: Market cap string from FINVIZ (e.g., '125.50M', '1.25B', '-')
    
    Returns:
        float: Numeric market cap, or None if unparseable
    
    Examples:
        >>> parse_market_cap('125.50M')
        125500000.0
        >>> parse_market_cap('1.25B')
        1250000000.0
        >>> parse_market_cap('-')
        None
    """
    try:
        import pandas as pd
        if pd.isna(s) or s == '-':
            return None
        s = str(s).replace(',', '')
        if 'B' in s:
            return float(s.replace('B', '')) * 1_000_000_000
        if 'M' in s:
            return float(s.replace('M', '')) * 1_000_000
        return float(s)
    except (TypeError, ValueError, AttributeError):
        return None


def parse_volume(s):
    """
    Parse FINVIZ volume string to integer.
    
    Handles comma-separated numbers, M/K suffixes, and edge cases.
    
    Args:
        s: Volume string from FINVIZ
    
    Returns:
        int: Volume as integer, or None if unparseable
    
    Examples:
        >>> parse_volume('1,250,000')
        1250000
        >>> parse_volume('1.5M')
        1500000
        >>> parse_volume('-')
        None
    """
    try:
        import pandas as pd
        if pd.isna(s) or s == '-':
            return None
        s = str(s).replace(',', '')
        if 'M' in s:
            return int(float(s.replace('M', '')) * 1_000_000)
        if 'K' in s:
            return int(float(s.replace('K', '')) * 1_000)
        return int(float(s))
    except (TypeError, ValueError, AttributeError):
        return None


# ═══════════════════════════════════════════════════════════════════════
# Market Cap Smart Lookup
# ═══════════════════════════════════════════════════════════════════════

def get_market_cap_smart(ticker, finviz_mc=None, shares_cache=None, yf_info=None):
    """
    Get market cap with smart fallback priority:
    1. FINVIZ value (if valid)
    2. yfinance marketCap field
    3. Calculated from shares * price (if cache available)
    4. None if all fail
    
    Args:
        ticker: Stock ticker symbol
        finviz_mc: Market cap from FINVIZ (already parsed to float)
        shares_cache: Dict of {ticker: shares_outstanding} for fallback
        yf_info: yfinance Ticker.info dict (optional, to avoid re-fetching)
    
    Returns:
        tuple: (market_cap, shares_outstanding) or (None, None)
    """
    # Priority 1: Use FINVIZ value if available and valid
    if finviz_mc is not None and finviz_mc > 0:
        shares = shares_cache.get(ticker, 0) if shares_cache else 0
        return finviz_mc, shares
    
    # Priority 2: Try yfinance
    try:
        if yf_info is None:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            yf_info = stock.info
        
        mc = yf_info.get('marketCap', 0) or 0
        shares = yf_info.get('sharesOutstanding', 0) or 0
        
        if mc > 0:
            return mc, shares
        
        # Priority 3: Calculate from shares * price
        price = yf_info.get('currentPrice', 0) or yf_info.get('regularMarketPrice', 0) or 0
        if shares > 0 and price > 0:
            return shares * price, shares
        
    except Exception:
        pass
    
    return None, None


# ═══════════════════════════════════════════════════════════════════════
# Statistics & Analysis
# ═══════════════════════════════════════════════════════════════════════

def calculate_stats(scan_price, ohlc):
    """
    Calculate trading statistics from scan price and OHLC data.
    
    Used by post_analysis_collector and backfill_ohlc to compute
    max drop, TP/SL hits, and D1 gap from 5-day price history.
    
    Args:
        scan_price: Price at time of scan (entry price)
        ohlc: Dict with keys like 'D1_Low', 'D1_Open', 'D2_Low', etc.
    
    Returns:
        dict: Statistics including:
            - MaxDrop%: Lowest price as % below scan price (negative)
            - BestDay: Day number (1-5) when min low occurred
            - TP10_Hit: 1 if price dropped ≥10%, 0 otherwise
            - TP15_Hit: 1 if price dropped ≥15%
            - TP20_Hit: 1 if price dropped ≥20%
            - D1_Gap%: Next day overnight gap
            - SL7_Hit_D1: 1 if price rose ≥7% on D1
            - IntraDay_SL: 1 if price rose ≥7% any day during tracking
    """
    # Use formulas.py for consistent calculations
    from formulas import calculate_max_drop, calculate_d1_gap
    
    lows = [(i, ohlc[f"D{i}_Low"]) for i in range(1, 6) 
            if ohlc.get(f"D{i}_Low") is not None]
    
    if not lows or scan_price <= 0:
        return {
            "MaxDrop%": None,
            "BestDay": None,
            "TP10_Hit": None,
            "TP15_Hit": None,
            "TP20_Hit": None,
            "D1_Gap%": None,
            "SL7_Hit_D1": None,
            "IntraDay_SL": None,
        }
    
    best_day, min_low = min(lows, key=lambda x: x[1])
    max_drop = round(calculate_max_drop(min_low, scan_price), 2)
    
    d1_open = ohlc.get("D1_Open")
    d1_gap = round(calculate_d1_gap(d1_open, scan_price), 2) if d1_open else None
    
    # SL checks (short position loses when price RISES)
    d1_high = ohlc.get("D1_High", 0) or 0
    sl7_hit_d1 = 1 if d1_high >= scan_price * (1 + SL_THRESHOLD_FRAC) else 0
    
    intra_sl = 0
    for i in range(1, 6):
        high = ohlc.get(f"D{i}_High", 0) or 0
        if high >= scan_price * (1 + SL_THRESHOLD_FRAC):
            intra_sl = 1
            break
    
    return {
        "MaxDrop%": max_drop,
        "BestDay": best_day,
        "TP10_Hit": 1 if min_low <= scan_price * (1 - TP_THRESHOLD_FRAC) else 0,
        "TP15_Hit": 1 if min_low <= scan_price * 0.85 else 0,
        "TP20_Hit": 1 if min_low <= scan_price * 0.80 else 0,
        "D1_Gap%": d1_gap,
        "SL7_Hit_D1": sl7_hit_d1,
        "IntraDay_SL": intra_sl,
    }


# ═══════════════════════════════════════════════════════════════════════
# Module self-test
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Run this file directly to verify functions work."""
    print("=" * 60)
    print("utils.py - Quick Sanity Check")
    print("=" * 60)
    
    # Test parsing
    print("\n── Parsing Functions ──")
    print(f"parse_market_cap('125.50M')  = {parse_market_cap('125.50M')}")
    print(f"parse_market_cap('1.25B')    = {parse_market_cap('1.25B')}")
    print(f"parse_market_cap('-')        = {parse_market_cap('-')}")
    print(f"parse_volume('1,250,000')    = {parse_volume('1,250,000')}")
    print(f"parse_volume('1.5M')         = {parse_volume('1.5M')}")
    print(f"parse_volume('500K')         = {parse_volume('500K')}")
    
    # Test time
    print("\n── Time Functions ──")
    now = get_peru_time()
    print(f"get_peru_time()              = {now}")
    print(f"is_trading_day()             = {is_trading_day()}")
    
    # Test is_day_complete
    print("\n── Day Complete Checks ──")
    import datetime as dt
    yesterday = (now.date() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = now.date().strftime("%Y-%m-%d")
    print(f"is_day_complete({yesterday}) = {is_day_complete(yesterday)}  (past)")
    print(f"is_day_complete({today_str})    = {is_day_complete(today_str)}  (today)")
    
    # Test calculate_stats
    print("\n── Statistics ──")
    ohlc = {
        "D1_Open": 9.5, "D1_High": 10.2, "D1_Low": 8.5,
        "D2_Open": 8.5, "D2_High": 9.0,  "D2_Low": 7.5,
        "D3_Open": 7.5, "D3_High": 8.5,  "D3_Low": 7.0,
    }
    stats = calculate_stats(10.0, ohlc)
    print(f"calculate_stats(scan=10, 3 days):")
    for k, v in stats.items():
        print(f"  {k:<14} = {v}")
    
    print("\n" + "=" * 60)
    print("All utils loaded successfully ✅")
    print("=" * 60)
