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
# Market Cap Smart Lookup (UNIFIED — Issue #9 Phase 2)
# ═══════════════════════════════════════════════════════════════════════
# This is the single source of truth for market cap resolution.
# Previously there were 2 implementations (utils + dashboard) — unified here.
# Dashboard-specific features (cache file, history lookup) are now optional
# callbacks so all callers can opt in.

def get_market_cap_smart(
    ticker,
    price=None,
    finviz_mc=None,
    shares_cache=None,
    fund_info=None,
    cache_get=None,
    cache_set=None,
    history_lookup=None,
    return_tuple=False,
):
    """
    Get market cap with smart fallback priority chain.

    Priority order:
        1. FINVIZ value (if provided and valid)
        2. fundamentals_provider marketCap field
        3. Calculated from shares * price (if shares available)
        4. History lookup (if history_lookup callback provided)
        5. Cache file (if cache_get callback provided)
        6. None if all fail

    Sources (3, 4, 5) write back to cache_set if provided.

    Args:
        ticker:         Stock ticker symbol
        price:          Current price (used for shares*price fallback). Optional.
        finviz_mc:      Market cap from FINVIZ (already parsed to float). Optional.
        shares_cache:   Dict of {ticker: shares_outstanding} for fallback. Optional.
        fund_info:      Pre-fetched fundamentals dict (avoid re-fetching).
                        Format: dict with keys 'market_cap', 'shares_outstanding'.
                        Optional.
        cache_get:      Callable(ticker) -> Optional[int]. Reads from cache.
                        Optional. Used as last-resort fallback.
        cache_set:      Callable(ticker, market_cap) -> None. Writes to cache.
                        Optional. Called after each successful lookup.
        history_lookup: Callable(ticker, field='MarketCap') -> Optional[float].
                        Looks up MC from historical data.
                        Optional.
        return_tuple:   If True, returns (market_cap, shares_outstanding).
                        If False, returns market_cap only.
                        Default: False (matches dashboard behavior).

    Returns:
        int or None  (or tuple if return_tuple=True)
    """
    def _persist(mc):
        """Helper to persist to cache if callback provided."""
        if cache_set is not None and mc is not None and mc > 0:
            try:
                cache_set(ticker, int(mc))
            except Exception:
                pass

    # Priority 1: FINVIZ value
    if finviz_mc is not None and finviz_mc > 0:
        mc = int(finviz_mc)
        shares = shares_cache.get(ticker, 0) if shares_cache else 0
        _persist(mc)
        return (mc, shares) if return_tuple else mc

    # Priority 2: fundamentals_provider
    try:
        if fund_info is None:
            from data_provider import get_fundamentals_provider
            fund_info = get_fundamentals_provider().get_fundamentals(ticker)

        mc_raw = fund_info.get('market_cap') if fund_info else None
        shares = fund_info.get('shares_outstanding', 0) if fund_info else 0
        shares = shares or 0

        if mc_raw and mc_raw > 0:
            mc = int(mc_raw)
            _persist(mc)
            return (mc, shares) if return_tuple else mc

        # Priority 3: shares * price
        if shares > 0 and price is not None and price > 0:
            mc = int(shares * price)
            _persist(mc)
            return (mc, shares) if return_tuple else mc
    except Exception:
        pass

    # Priority 4: History lookup callback (dashboard-only feature)
    if history_lookup is not None:
        try:
            hist_mc = history_lookup(ticker, 'MarketCap')
            if hist_mc and hist_mc > 0:
                mc = int(hist_mc)
                _persist(mc)
                return (mc, 0) if return_tuple else mc
        except Exception:
            pass

    # Priority 5: Cache file callback (dashboard-only feature)
    if cache_get is not None:
        try:
            cached_mc = cache_get(ticker)
            if cached_mc and cached_mc > 0:
                mc = int(cached_mc)
                # Don't re-persist on read
                return (mc, 0) if return_tuple else mc
        except Exception:
            pass

    return (None, None) if return_tuple else None


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
            - SL_Hit_D5: 1 if price rose ≥SL_THRESHOLD_PCT% on ANY day D1-D5
                         (Renamed from SL7_Hit_D1 on 2026-04-25 — Issue #1
                          SL unification. Previously checked only D1 with 7%;
                          now checks full 5-day window with unified threshold.)
            - IntraDay_SL: 1 if price rose ≥SL_THRESHOLD_PCT% any day during tracking
                           (kept for backward compat — same value as SL_Hit_D5 now)
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
            "SL_Hit_D5": None,
            "IntraDay_SL": None,
        }
    
    best_day, min_low = min(lows, key=lambda x: x[1])
    max_drop = round(calculate_max_drop(min_low, scan_price), 2)
    
    d1_open = ohlc.get("D1_Open")
    d1_gap = round(calculate_d1_gap(d1_open, scan_price), 2) if d1_open else None
    
    # SL checks (short position loses when price RISES)
    # SL_Hit_D5: did price rise ≥SL_THRESHOLD_PCT% on ANY of D1-D5?
    sl_hit_d5 = 0
    for i in range(1, 6):
        high = ohlc.get(f"D{i}_High", 0) or 0
        if high >= scan_price * (1 + SL_THRESHOLD_FRAC):
            sl_hit_d5 = 1
            break
    
    return {
        "MaxDrop%": max_drop,
        "BestDay": best_day,
        "TP10_Hit": 1 if min_low <= scan_price * (1 - TP_THRESHOLD_FRAC) else 0,
        "TP15_Hit": 1 if min_low <= scan_price * 0.85 else 0,
        "TP20_Hit": 1 if min_low <= scan_price * 0.80 else 0,
        "D1_Gap%": d1_gap,
        "SL_Hit_D5": sl_hit_d5,
        "IntraDay_SL": sl_hit_d5,  # alias kept for backward compat
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


def validate_stock_data(price, week52high, atr14, high_today=None, low_today=None,
                       open_price=None, avg_volume=None):
    """
    Validate stock data for common yfinance issues.
    Returns: "CLEAN" | "SUSPICIOUS" | "BROKEN" | "PRE_SPLIT" | "NO_DATA"
    """
    try:
        if price is None or price == 0:
            return "NO_DATA"

        price = float(price)

        # BROKEN — physical impossibilities
        if high_today is not None and low_today is not None:
            if float(high_today) < float(low_today):
                return "BROKEN"
        if price > 10000:
            return "BROKEN"
        if avg_volume is not None and float(avg_volume) < 0:
            return "BROKEN"

        # PRE_SPLIT — Week52High absurdly high vs current price
        if week52high is not None and float(week52high) > 0:
            if float(week52high) > price * 50:
                return "PRE_SPLIT"

        # PRE_SPLIT — ATR14 absurdly high vs current price
        if atr14 is not None and float(atr14) > 0:
            if float(atr14) > price * 3:
                return "PRE_SPLIT"

        # SUSPICIOUS — legitimate but extreme volatility
        if open_price is not None and high_today is not None:
            op = float(open_price)
            hi = float(high_today)
            if op > 0 and hi > op * 2:
                return "SUSPICIOUS"

        return "CLEAN"
    except (TypeError, ValueError):
        return "BROKEN"


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


def strip_comments(line):
    """Strip # comments from a Python code line.

    Basic implementation — ignores # inside strings.
    Used by code_auditor and daily_audit for scanning code.
    """
    in_string = False
    quote = None
    for i, c in enumerate(line):
        if c in ('"', "'") and (i == 0 or line[i-1] != '\\'):
            if not in_string:
                in_string = True
                quote = c
            elif c == quote:
                in_string = False
        elif c == '#' and not in_string:
            return line[:i]
    return line
