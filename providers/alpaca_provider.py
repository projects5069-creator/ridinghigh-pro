#!/usr/bin/env python3
"""
providers/alpaca_provider.py - Alpaca implementation of DataProvider
=======================================================================

Uses the alpaca-py SDK to fetch market data from Alpaca's IEX/SIP feeds.

Plan tier: Basic (free)
- Historical bars: SIP (full market) — works perfectly for D1-D5 OHLC
- Real-time quotes: IEX feed only OR SIP with 15-min delay
- Live latest bar: 15-min delayed if using SIP, real-time on IEX

For our short-selling scanner this is plenty:
- post_analysis (D1-D5) — uses historical SIP — perfect ✅
- Backfill OHLC — historical SIP — perfect ✅
- Live scanner — FINVIZ does the screening, Alpaca for verification only

Created: 2026-04-25 (Issue #9)
"""

import logging
import os
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Union

import pandas as pd

from data_provider import DataProvider

logger = logging.getLogger("data_provider.alpaca")


# ════════════════════════════════════════════════════════════════════════
# Lazy SDK imports — only imported when AlpacaDataProvider is instantiated
# ════════════════════════════════════════════════════════════════════════

def _import_sdk():
    """Lazy import of alpaca-py SDK to avoid hard dependency."""
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import (
            StockBarsRequest,
            StockLatestQuoteRequest,
            StockLatestBarRequest,
        )
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
        from alpaca.data.enums import DataFeed
        from alpaca.trading.client import TradingClient
        return {
            "StockHistoricalDataClient": StockHistoricalDataClient,
            "StockBarsRequest": StockBarsRequest,
            "StockLatestQuoteRequest": StockLatestQuoteRequest,
            "StockLatestBarRequest": StockLatestBarRequest,
            "TimeFrame": TimeFrame,
            "TimeFrameUnit": TimeFrameUnit,
            "DataFeed": DataFeed,
            "TradingClient": TradingClient,
        }
    except ImportError as e:
        raise ImportError(
            "alpaca-py is not installed. Install with:\n"
            "    pip install alpaca-py"
        ) from e


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════

def _normalize_bars_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Convert Alpaca BarSet.df output to our standard format.
    
    Alpaca returns a multi-index DataFrame (symbol, timestamp).
    We want a single-index DataFrame with date/datetime index and
    standard column names: open, high, low, close, volume.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    # Multi-index? Filter to our ticker.
    if isinstance(df.index, pd.MultiIndex):
        if ticker in df.index.get_level_values(0):
            df = df.xs(ticker, level=0).copy()
        else:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    # Standardize columns to lowercase
    df.columns = [c.lower() for c in df.columns]
    
    # Keep only OHLCV columns (ignore vwap, trade_count if present)
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep]
    
    return df


def _parse_scan_date(scan_date: Union[str, datetime, date]) -> datetime:
    """Parse scan_date input to a tz-naive datetime at midnight.

    Accepts: str ('YYYY-MM-DD'), datetime, or date.
    Issue #9 Phase 2 — added date support for now_peru.date() callsites.
    """
    if isinstance(scan_date, str):
        return datetime.strptime(scan_date[:10], "%Y-%m-%d")
    # IMPORTANT: datetime is a subclass of date, so check datetime FIRST
    if isinstance(scan_date, datetime):
        return datetime(scan_date.year, scan_date.month, scan_date.day)
    if isinstance(scan_date, date):
        return datetime(scan_date.year, scan_date.month, scan_date.day)
    raise ValueError(f"Invalid scan_date type: {type(scan_date)}")


def _is_trading_day(d: datetime) -> bool:
    """Mon-Fri (no holiday calendar — good enough for our use case)."""
    return d.weekday() < 5


def _next_n_trading_days(start: datetime, n: int) -> List[datetime]:
    """Return next N trading days strictly after start."""
    out = []
    d = start
    while len(out) < n:
        d += timedelta(days=1)
        if _is_trading_day(d):
            out.append(d)
    return out


# ════════════════════════════════════════════════════════════════════════
# AlpacaDataProvider
# ════════════════════════════════════════════════════════════════════════

class AlpacaDataProvider(DataProvider):
    """
    Alpaca implementation of DataProvider.
    
    Uses the free Basic plan: SIP for historical bars, IEX or 15-min
    delayed SIP for latest quote.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: Optional[bool] = None,
    ):
        api_key = api_key or os.environ.get("ALPACA_API_KEY_ID", "")
        secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        if paper is None:
            paper = os.environ.get("ALPACA_PAPER", "true").lower() == "true"
        
        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca API credentials missing. Set ALPACA_API_KEY_ID and "
                "ALPACA_SECRET_KEY in .env or environment."
            )
        
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        
        # Import SDK on first use
        sdk = _import_sdk()
        self._sdk = sdk
        
        # Lazy clients — created on first use to fail fast if creds bad
        self._data_client = None
        self._trading_client = None
    
    @property
    def name(self) -> str:
        return f"alpaca-{'paper' if self._paper else 'live'}"
    
    @property
    def data_client(self):
        if self._data_client is None:
            self._data_client = self._sdk["StockHistoricalDataClient"](
                self._api_key, self._secret_key
            )
        return self._data_client
    
    @property
    def trading_client(self):
        if self._trading_client is None:
            self._trading_client = self._sdk["TradingClient"](
                self._api_key, self._secret_key, paper=self._paper
            )
        return self._trading_client
    
    # ── Daily bars ──────────────────────────────────────────────────
    
    def get_daily_bars(
        self,
        ticker: str,
        days: int = 60,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        try:
            if end_date is None:
                end_date = datetime.now() - timedelta(minutes=20)
            # Calendar days back, with buffer for weekends
            start_date = end_date - timedelta(days=int(days * 1.5) + 5)
            
            req = self._sdk["StockBarsRequest"](
                symbol_or_symbols=[ticker],
                timeframe=self._sdk["TimeFrame"].Day,
                start=start_date,
                end=end_date,
                feed=self._sdk["DataFeed"].IEX,  # Issue #9 fix 2026-04-27 — paper plan only allows IEX
            )
            bars = self.data_client.get_stock_bars(req)
            df = _normalize_bars_df(bars.df, ticker)
            
            # Trim to requested number of trading days
            if len(df) > days:
                df = df.iloc[-days:].copy()
            
            return df
        except Exception as e:
            logger.warning(f"Alpaca get_daily_bars({ticker}) failed: {e}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    # ── 5-day OHLC after a scan date ────────────────────────────────
    
    def get_5day_ohlc(
        self,
        ticker: str,
        scan_date: Union[str, datetime],
    ) -> Dict[str, Optional[float]]:
        empty = {f"D{d}_{f}": None
                 for d in range(1, 6)
                 for f in ("Open", "High", "Low", "Close", "Volume")}
        
        try:
            scan_dt = _parse_scan_date(scan_date)
            target_days = _next_n_trading_days(scan_dt, 5)
            
            # Pull a window covering all 5 expected days plus buffer
            start = target_days[0] - timedelta(days=1)
            end = target_days[-1] + timedelta(days=1)
            
            # Don't request data for the future — clip end to now
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if end > now_utc:
                end = now_utc - timedelta(minutes=20)
            
            if start >= end:
                return empty  # all 5 days are in the future
            
            req = self._sdk["StockBarsRequest"](
                symbol_or_symbols=[ticker],
                timeframe=self._sdk["TimeFrame"].Day,
                start=start,
                end=end,
                feed=self._sdk["DataFeed"].IEX,  # Issue #9 fix 2026-04-27 — paper plan only allows IEX
            )
            bars = self.data_client.get_stock_bars(req)
            df = _normalize_bars_df(bars.df, ticker)
            
            if df.empty:
                return empty
            
            # Index might be tz-aware — convert to date-only for matching
            if hasattr(df.index, "date"):
                df_dates = pd.Index([d.date() if hasattr(d, "date") else d for d in df.index])
            else:
                df_dates = df.index
            
            out = dict(empty)
            for i, target_dt in enumerate(target_days, 1):
                target_date = target_dt.date()
                # Find row matching this date
                mask = [td == target_date for td in df_dates]
                if not any(mask):
                    continue
                row = df[mask].iloc[0]
                out[f"D{i}_Open"]   = round(float(row["open"]), 2)
                out[f"D{i}_High"]   = round(float(row["high"]), 2)
                out[f"D{i}_Low"]    = round(float(row["low"]), 2)
                out[f"D{i}_Close"]  = round(float(row["close"]), 2)
                out[f"D{i}_Volume"] = int(row["volume"])
            
            return out
        except Exception as e:
            logger.warning(f"Alpaca get_5day_ohlc({ticker}, {scan_date}) failed: {e}")
            return empty
    
    # ── Latest quote ────────────────────────────────────────────────
    
    def get_latest_quote(self, ticker: str) -> Optional[Dict]:
        try:
            req = self._sdk["StockLatestQuoteRequest"](
                symbol_or_symbols=[ticker],
                feed=self._sdk["DataFeed"].IEX,  # Issue #9 fix 2026-04-27 — paper plan only allows IEX
            )
            quotes = self.data_client.get_stock_latest_quote(req)
            if ticker not in quotes:
                return None
            q = quotes[ticker]
            return {
                "bid_price": float(q.bid_price) if q.bid_price else None,
                "ask_price": float(q.ask_price) if q.ask_price else None,
                "last_price": None,  # quote doesn't include last; use get_latest_bar
                "timestamp": q.timestamp,
            }
        except Exception as e:
            logger.warning(f"Alpaca get_latest_quote({ticker}) failed: {e}")
            return None
    
    # ── Latest bar (today's session) ────────────────────────────────
    
    def get_latest_bar(self, ticker: str) -> Optional[Dict]:
        try:
            req = self._sdk["StockLatestBarRequest"](
                symbol_or_symbols=[ticker],
                feed=self._sdk["DataFeed"].IEX,  # Issue #9 fix 2026-04-27 — paper plan only allows IEX
            )
            bars = self.data_client.get_stock_latest_bar(req)
            if ticker not in bars:
                return None
            b = bars[ticker]
            return {
                "open":   float(b.open),
                "high":   float(b.high),
                "low":    float(b.low),
                "close":  float(b.close),
                "volume": int(b.volume),
                "timestamp": b.timestamp,
            }
        except Exception as e:
            logger.warning(f"Alpaca get_latest_bar({ticker}) failed: {e}")
            return None
    
    # ── Intraday bars ───────────────────────────────────────────────
    
    def get_intraday_bars(
        self,
        ticker: str,
        date: Union[str, datetime],
        timeframe: str = "1Min",
    ) -> pd.DataFrame:
        try:
            target_dt = _parse_scan_date(date)
            start = target_dt
            end = target_dt + timedelta(days=1)
            
            # Map timeframe string to TimeFrame object
            TimeFrame = self._sdk["TimeFrame"]
            TimeFrameUnit = self._sdk["TimeFrameUnit"]
            tf_map = {
                "1Min":  TimeFrame.Minute,
                "5Min":  TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "1H":    TimeFrame.Hour,
            }
            tf = tf_map.get(timeframe, TimeFrame.Minute)
            
            req = self._sdk["StockBarsRequest"](
                symbol_or_symbols=[ticker],
                timeframe=tf,
                start=start,
                end=end,
                feed=self._sdk["DataFeed"].IEX,  # Issue #9 fix 2026-04-27 — paper plan only allows IEX (this was the cron failure!)
            )
            bars = self.data_client.get_stock_bars(req)
            return _normalize_bars_df(bars.df, ticker)
        except Exception as e:
            logger.warning(f"Alpaca get_intraday_bars({ticker}, {date}) failed: {e}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    # ── Health check ────────────────────────────────────────────────
    
    def is_healthy(self) -> bool:
        try:
            account = self.trading_client.get_account()
            return str(account.status).upper().endswith("ACTIVE")
        except Exception as e:
            logger.warning(f"Alpaca health check failed: {e}")
            return False
