#!/usr/bin/env python3
"""
providers/yfinance_provider.py - yfinance implementation
============================================================

Two providers in one file:
  - YFinanceDataProvider:        prices (fallback to Alpaca)
  - YFinanceFundamentalsProvider: shares, market cap, sector, etc.

yfinance is kept for two reasons:
  1. **Fundamentals** — Alpaca does not expose sharesOutstanding,
     floatShares, or averageVolume. yfinance does, for free.
  2. **Fallback** — if Alpaca is down, the system can keep operating.

Created: 2026-04-25 (Issue #9)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd

from data_provider import DataProvider, FundamentalsProvider

logger = logging.getLogger("data_provider.yfinance")


def _import_sdk():
    """Lazy import of yfinance to avoid hard dependency."""
    try:
        import yfinance as yf
        return yf
    except ImportError as e:
        raise ImportError(
            "yfinance is not installed. Install with:\n"
            "    pip install yfinance"
        ) from e


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════

def _normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert yfinance Ticker.history() output to our standard format.
    
    yfinance returns columns: Open, High, Low, Close, Volume (capitalized).
    We want lowercase: open, high, low, close, volume.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    
    # Multi-index columns? Flatten (happens with yf.download for multiple tickers)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() if isinstance(c, tuple) else str(c).lower()
                      for c in df.columns]
    
    keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    return df[keep]


def _parse_scan_date(scan_date: Union[str, datetime]) -> datetime:
    if isinstance(scan_date, str):
        return datetime.strptime(scan_date[:10], "%Y-%m-%d")
    if isinstance(scan_date, datetime):
        return datetime(scan_date.year, scan_date.month, scan_date.day)
    raise ValueError(f"Invalid scan_date type: {type(scan_date)}")


def _is_trading_day(d: datetime) -> bool:
    return d.weekday() < 5


def _next_n_trading_days(start: datetime, n: int) -> List[datetime]:
    out = []
    d = start
    while len(out) < n:
        d += timedelta(days=1)
        if _is_trading_day(d):
            out.append(d)
    return out


# ════════════════════════════════════════════════════════════════════════
# YFinanceDataProvider
# ════════════════════════════════════════════════════════════════════════

class YFinanceDataProvider(DataProvider):
    """yfinance implementation of DataProvider — used as fallback."""
    
    def __init__(self):
        self._yf = _import_sdk()
    
    @property
    def name(self) -> str:
        return "yfinance"
    
    # ── Daily bars ──────────────────────────────────────────────────
    
    def get_daily_bars(
        self,
        ticker: str,
        days: int = 60,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        try:
            # yfinance period strings: '1d', '5d', '1mo', '3mo', '1y', etc.
            # We'll convert days to closest period or use date range.
            if end_date is None:
                # Use period for simplicity
                period = self._days_to_period(days)
                stock = self._yf.Ticker(ticker)
                hist = stock.history(period=period, auto_adjust=True)
            else:
                start_date = end_date - timedelta(days=int(days * 1.5) + 5)
                hist = self._yf.download(
                    ticker,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    progress=False,
                    auto_adjust=True,
                )
            
            df = _normalize_history(hist)
            if len(df) > days:
                df = df.iloc[-days:].copy()
            return df
        except Exception as e:
            logger.warning(f"yfinance get_daily_bars({ticker}) failed: {e}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    @staticmethod
    def _days_to_period(days: int) -> str:
        """Map calendar days to closest yfinance period string."""
        if days <= 5:    return "5d"
        if days <= 30:   return "1mo"
        if days <= 90:   return "3mo"
        if days <= 180:  return "6mo"
        if days <= 365:  return "1y"
        if days <= 730:  return "2y"
        return "5y"
    
    # ── 5-day OHLC ──────────────────────────────────────────────────
    
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
            
            start = target_days[0] - timedelta(days=1)
            end = target_days[-1] + timedelta(days=2)
            
            now = datetime.now()
            if start >= now:
                return empty
            
            hist = self._yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )
            df = _normalize_history(hist)
            if df.empty:
                return empty
            
            # Match by date
            df_dates = [d.date() if hasattr(d, "date") else d for d in df.index]
            
            out = dict(empty)
            for i, target_dt in enumerate(target_days, 1):
                target_date = target_dt.date()
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
            logger.warning(f"yfinance get_5day_ohlc({ticker}, {scan_date}) failed: {e}")
            return empty
    
    # ── Latest quote ────────────────────────────────────────────────
    
    def get_latest_quote(self, ticker: str) -> Optional[Dict]:
        try:
            stock = self._yf.Ticker(ticker)
            info = stock.info
            bid = info.get("bid")
            ask = info.get("ask")
            last = info.get("currentPrice") or info.get("regularMarketPrice")
            return {
                "bid_price": float(bid) if bid else None,
                "ask_price": float(ask) if ask else None,
                "last_price": float(last) if last else None,
                "timestamp": datetime.now(),
            }
        except Exception as e:
            logger.warning(f"yfinance get_latest_quote({ticker}) failed: {e}")
            return None
    
    # ── Latest bar ──────────────────────────────────────────────────
    
    def get_latest_bar(self, ticker: str) -> Optional[Dict]:
        try:
            hist = self._yf.Ticker(ticker).history(period="1d", auto_adjust=True)
            if hist.empty:
                return None
            row = hist.iloc[-1]
            return {
                "open":   float(row["Open"]),
                "high":   float(row["High"]),
                "low":    float(row["Low"]),
                "close":  float(row["Close"]),
                "volume": int(row["Volume"]),
                "timestamp": hist.index[-1],
            }
        except Exception as e:
            logger.warning(f"yfinance get_latest_bar({ticker}) failed: {e}")
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
            interval_map = {"1Min": "1m", "5Min": "5m", "15Min": "15m", "1H": "1h"}
            interval = interval_map.get(timeframe, "1m")
            
            start = target_dt.strftime("%Y-%m-%d")
            end = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            
            hist = self._yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                auto_adjust=True,
            )
            return _normalize_history(hist)
        except Exception as e:
            logger.warning(f"yfinance get_intraday_bars({ticker}, {date}) failed: {e}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    # ── Health check ────────────────────────────────────────────────
    
    def is_healthy(self) -> bool:
        try:
            # Quick sanity check — fetch SPY's last close
            hist = self._yf.Ticker("SPY").history(period="5d")
            return not hist.empty
        except Exception as e:
            logger.warning(f"yfinance health check failed: {e}")
            return False


# ════════════════════════════════════════════════════════════════════════
# YFinanceFundamentalsProvider
# ════════════════════════════════════════════════════════════════════════

class YFinanceFundamentalsProvider(FundamentalsProvider):
    """yfinance implementation of FundamentalsProvider."""
    
    def __init__(self):
        self._yf = _import_sdk()
    
    @property
    def name(self) -> str:
        return "yfinance-fundamentals"
    
    def get_fundamentals(self, ticker: str) -> Dict:
        empty = {
            "market_cap": None,
            "shares_outstanding": None,
            "float_shares": None,
            "average_volume": None,
            "sector": None,
            "industry": None,
        }
        try:
            info = self._yf.Ticker(ticker).info
            return {
                "market_cap":         _safe_int(info.get("marketCap")),
                "shares_outstanding": _safe_int(info.get("sharesOutstanding")),
                "float_shares":       _safe_int(info.get("floatShares")),
                "average_volume":     _safe_int(info.get("averageVolume")),
                "sector":             info.get("sector"),
                "industry":           info.get("industry"),
            }
        except Exception as e:
            logger.warning(f"yfinance fundamentals({ticker}) failed: {e}")
            return empty


def _safe_int(v) -> Optional[int]:
    try:
        return int(v) if v is not None and v != 0 else None
    except (TypeError, ValueError):
        return None
