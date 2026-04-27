#!/usr/bin/env python3
"""
data_provider.py - RidingHigh Pro Data Provider Abstraction Layer
====================================================================

Single source of truth for all market data access. Provides a uniform
interface across multiple data providers (Alpaca, yfinance) so that
calling code does not need to know where prices come from.

Design goals:
1. **Twin systems** — same prices feed simulation AND Alpaca trades.
2. **Pluggable** — switch providers via DATA_PROVIDER env var.
3. **Validatable** — A/B compare providers side by side.
4. **Failover** — fallback to alternative provider on outage.

Architecture:
    DataProvider (abstract base class)
    ├── AlpacaDataProvider     — primary, real-time + historical
    ├── YFinanceDataProvider   — fallback + legacy
    └── FundamentalsProvider   — yfinance only (Alpaca lacks these)

Typical usage:
    from data_provider import get_data_provider, get_fundamentals_provider
    
    prices = get_data_provider()
    fundamentals = get_fundamentals_provider()
    
    bars = prices.get_daily_bars("AAPL", days=60)
    info = fundamentals.get_fundamentals("AAPL")

Created: 2026-04-25 (Issue #9 — twin system data layer)
Author:  RidingHigh Pro
"""

import os
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

# ════════════════════════════════════════════════════════════════════════
# Environment loading (.env if present)
# ════════════════════════════════════════════════════════════════════════

def _load_env():
    """Load .env file from project root if not already loaded."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)

_load_env()


# ════════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════════

# Which provider to use for prices (OHLC, quotes, intraday)
DATA_PROVIDER = os.environ.get("DATA_PROVIDER", "alpaca").lower()

# Which provider to use for fundamentals (always yfinance for now —
# Alpaca does not expose sharesOutstanding / floatShares)
FUNDAMENTALS_PROVIDER = os.environ.get("FUNDAMENTALS_PROVIDER", "yfinance").lower()

# Alpaca paper trading endpoints
ALPACA_API_KEY_ID = os.environ.get("ALPACA_API_KEY_ID", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_PAPER = os.environ.get("ALPACA_PAPER", "true").lower() == "true"

# Logging
logger = logging.getLogger("data_provider")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ════════════════════════════════════════════════════════════════════════
# Standard data shapes — what every provider returns
# ════════════════════════════════════════════════════════════════════════

# Bar data (returned from get_daily_bars / get_intraday_bars):
#   pandas DataFrame with columns: open, high, low, close, volume
#   Index: pandas DatetimeIndex (date or datetime, tz-aware in UTC)
#   Empty DataFrame if no data.

# Latest quote (returned from get_latest_quote):
#   dict with keys:
#     - bid_price (float)
#     - ask_price (float)
#     - last_price (float, optional)
#     - timestamp (datetime, UTC)
#   None if quote unavailable.

# 5-day OHLC (returned from get_5day_ohlc):
#   dict with keys:
#     - D1_Open, D1_High, D1_Low, D1_Close, D1_Volume
#     - D2_Open, ..., D2_Volume
#     - ... up to D5_*
#   Missing days have None values.


# ════════════════════════════════════════════════════════════════════════
# Abstract base class
# ════════════════════════════════════════════════════════════════════════

class DataProvider(ABC):
    """
    Abstract base class for market data providers.
    
    Every provider must implement all abstract methods. Methods should:
    - Return data in the standard shapes documented above.
    - Handle errors gracefully — return empty DataFrame / None on failure.
    - NEVER raise on transient errors (network, rate limit) — log and return empty.
    - Raise only on configuration errors (missing keys, etc).
    """

    # ── Identification ──────────────────────────────────────────────
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Short human-readable provider name (e.g. 'alpaca', 'yfinance')."""
        ...

    # ── Daily bars ──────────────────────────────────────────────────
    
    @abstractmethod
    def get_daily_bars(
        self,
        ticker: str,
        days: int = 60,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars for a ticker.
        
        Args:
            ticker: Stock symbol (e.g. 'AAPL')
            days: Number of trading days back from end_date
            end_date: End of range (default: today)
        
        Returns:
            DataFrame with columns [open, high, low, close, volume]
            indexed by date (DatetimeIndex). Empty if no data available.
        """
        ...

    # ── 5-day OHLC after a scan date ────────────────────────────────
    
    @abstractmethod
    def get_5day_ohlc(
        self,
        ticker: str,
        scan_date: Union[str, datetime],
    ) -> Dict[str, Optional[float]]:
        """
        Fetch D1-D5 OHLC after a scan date.
        
        Args:
            ticker: Stock symbol
            scan_date: Date of the scan (string 'YYYY-MM-DD' or datetime)
        
        Returns:
            Dict with keys D1_Open, D1_High, D1_Low, D1_Close, D1_Volume,
            ... up to D5_*. Missing days have None values.
            Returns dict of all-None if ticker has no post-scan data yet.
        """
        ...

    # ── Latest quote ────────────────────────────────────────────────
    
    @abstractmethod
    def get_latest_quote(self, ticker: str) -> Optional[Dict]:
        """
        Fetch the latest quote (bid/ask) for a ticker.
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Dict with bid_price, ask_price, last_price, timestamp.
            None if unavailable (e.g. market closed).
        """
        ...

    # ── Latest bar (today's open/high/low/close so far) ─────────────
    
    @abstractmethod
    def get_latest_bar(self, ticker: str) -> Optional[Dict]:
        """
        Fetch today's latest bar (current trading day).
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Dict with open, high, low, close, volume.
            None if market not open / no data.
        """
        ...

    # ── Intraday bars ───────────────────────────────────────────────
    
    @abstractmethod
    def get_intraday_bars(
        self,
        ticker: str,
        date: Union[str, datetime],
        timeframe: str = "1Min",
    ) -> pd.DataFrame:
        """
        Fetch intraday bars for a specific date.
        
        Args:
            ticker: Stock symbol
            date: Trading date
            timeframe: '1Min', '5Min', '15Min', '1H'
        
        Returns:
            DataFrame with [open, high, low, close, volume].
            Empty if no data.
        """
        ...

    # ── Health check ────────────────────────────────────────────────
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the provider is reachable and authenticated.
        
        Returns:
            True if provider is operational, False otherwise.
        """
        ...


# ════════════════════════════════════════════════════════════════════════
# Fundamentals provider (separate — Alpaca lacks these)
# ════════════════════════════════════════════════════════════════════════

class FundamentalsProvider(ABC):
    """
    Abstract base class for fundamentals providers.
    
    Fundamentals = static company data (shares, market cap, sector, etc).
    Currently only yfinance exposes these for free; Alpaca does not.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Dict:
        """
        Fetch fundamentals for a ticker.
        
        Returns:
            Dict with keys:
              - market_cap (int)
              - shares_outstanding (int)
              - float_shares (int)
              - average_volume (int)  — typically 30-day average
              - sector (str)
              - industry (str)
              - ipo_epoch (int) — Unix timestamp of first trade date.
                                  Convert to days-since-IPO via:
                                  (datetime.now() - datetime.fromtimestamp(ipo_epoch)).days
                                  None if unavailable.
            Missing keys = None.
        """
        ...


# ════════════════════════════════════════════════════════════════════════
# Factory functions
# ════════════════════════════════════════════════════════════════════════

_data_provider_instance = None
_fundamentals_provider_instance = None


def get_data_provider(force_provider: Optional[str] = None) -> DataProvider:
    """
    Return the configured data provider (singleton).
    
    Args:
        force_provider: Override DATA_PROVIDER env var.
                        Useful for A/B testing.
    
    Returns:
        DataProvider instance.
    
    Raises:
        ValueError: If provider name is unknown or required credentials missing.
    """
    global _data_provider_instance
    
    provider_name = (force_provider or DATA_PROVIDER).lower()
    
    # Singleton — but only if not forced
    if force_provider is None and _data_provider_instance is not None:
        return _data_provider_instance
    
    if provider_name == "alpaca":
        from providers.alpaca_provider import AlpacaDataProvider
        instance = AlpacaDataProvider()
    elif provider_name == "yfinance":
        from providers.yfinance_provider import YFinanceDataProvider
        instance = YFinanceDataProvider()
    else:
        raise ValueError(
            f"Unknown DATA_PROVIDER: {provider_name!r}. "
            f"Valid options: 'alpaca', 'yfinance'"
        )
    
    if force_provider is None:
        _data_provider_instance = instance
    
    logger.info(f"Initialized data provider: {instance.name}")
    return instance


def get_fundamentals_provider(force_provider: Optional[str] = None) -> FundamentalsProvider:
    """
    Return the configured fundamentals provider (singleton).
    
    Args:
        force_provider: Override FUNDAMENTALS_PROVIDER env var.
    
    Returns:
        FundamentalsProvider instance.
    """
    global _fundamentals_provider_instance
    
    provider_name = (force_provider or FUNDAMENTALS_PROVIDER).lower()
    
    if force_provider is None and _fundamentals_provider_instance is not None:
        return _fundamentals_provider_instance
    
    if provider_name == "yfinance":
        from providers.yfinance_provider import YFinanceFundamentalsProvider
        instance = YFinanceFundamentalsProvider()
    else:
        raise ValueError(
            f"Unknown FUNDAMENTALS_PROVIDER: {provider_name!r}. "
            f"Valid options: 'yfinance'"
        )
    
    if force_provider is None:
        _fundamentals_provider_instance = instance
    
    logger.info(f"Initialized fundamentals provider: {instance.name}")
    return instance


def reset_providers():
    """Reset singleton instances. Useful for testing."""
    global _data_provider_instance, _fundamentals_provider_instance
    _data_provider_instance = None
    _fundamentals_provider_instance = None


# ════════════════════════════════════════════════════════════════════════
# Convenience top-level functions
# ════════════════════════════════════════════════════════════════════════
# These mirror the standard yfinance usage patterns so that calling code
# can switch with minimal changes.

def get_daily_bars(ticker: str, days: int = 60, end_date: Optional[datetime] = None) -> pd.DataFrame:
    """Top-level convenience — uses configured provider."""
    return get_data_provider().get_daily_bars(ticker, days=days, end_date=end_date)


def get_5day_ohlc(ticker: str, scan_date: Union[str, datetime]) -> Dict:
    """Top-level convenience — uses configured provider."""
    return get_data_provider().get_5day_ohlc(ticker, scan_date)


def get_latest_quote(ticker: str) -> Optional[Dict]:
    """Top-level convenience — uses configured provider."""
    return get_data_provider().get_latest_quote(ticker)


def get_latest_bar(ticker: str) -> Optional[Dict]:
    """Top-level convenience — uses configured provider."""
    return get_data_provider().get_latest_bar(ticker)


def get_intraday_bars(ticker: str, date: Union[str, datetime], timeframe: str = "1Min") -> pd.DataFrame:
    """Top-level convenience — uses configured provider."""
    return get_data_provider().get_intraday_bars(ticker, date, timeframe=timeframe)


def get_fundamentals(ticker: str) -> Dict:
    """Top-level convenience — uses configured fundamentals provider."""
    return get_fundamentals_provider().get_fundamentals(ticker)


# ════════════════════════════════════════════════════════════════════════
# Self-test entry point
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("data_provider.py — self-check")
    print("=" * 60)
    print(f"DATA_PROVIDER:         {DATA_PROVIDER}")
    print(f"FUNDAMENTALS_PROVIDER: {FUNDAMENTALS_PROVIDER}")
    print(f"ALPACA_API_KEY_ID:     {'configured' if ALPACA_API_KEY_ID else 'NOT SET'}")
    print(f"ALPACA_PAPER:          {ALPACA_PAPER}")
    print()
    
    try:
        prov = get_data_provider()
        print(f"✅ Data provider:        {prov.name}")
        print(f"   Healthy:              {prov.is_healthy()}")
    except Exception as e:
        print(f"❌ Data provider failed: {e}")
    
    try:
        fund = get_fundamentals_provider()
        print(f"✅ Fundamentals:         {fund.name}")
    except Exception as e:
        print(f"❌ Fundamentals failed:  {e}")
