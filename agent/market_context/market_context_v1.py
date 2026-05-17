"""
agent/market_context/market_context_v1.py
─────────────────────────────────────────
Market Context Agent v1 — broad-market regime detection.

Data sources:
  - SPY, IWM: AlpacaDataProvider.get_latest_bar()  (fallback: yfinance)
  - VIX:      yfinance Ticker('^VIX')               (Alpaca doesn't support indices)

Computed fields:
  - spy_direction:  "UP" / "FLAT" / "DOWN" (0.2% dead-zone threshold)
  - iwm_direction:  "UP" / "FLAT" / "DOWN" (same threshold)
  - vix_level:      "LOW" (<20) | "MEDIUM" (20-30) | "HIGH" (>30)

Direction threshold (0.2%):
  pct = (close - open) / open * 100
  "UP" if pct > 0.2, "DOWN" if pct < -0.2, "FLAT" otherwise.
  Chosen from 5-year historical analysis of SPY + IWM daily moves:
  at 0.2%, ~25% of SPY days and ~16% of IWM days are tagged FLAT —
  enough to filter intraday noise without swallowing real trend days.
  Distribution is stable across 2y and 5y windows.

Market regime derivation (simple majority rule):
  Three signals are scored: spy_direction, iwm_direction, vix_level.
  FLAT counts as neither bullish nor bearish.
  - bullish_count = (spy UP) + (iwm UP) + (vix LOW)
  - bearish_count = (spy DOWN) + (iwm DOWN) + (vix HIGH)
  - RISK_ON:  bullish_count >= 2 and bearish_count == 0
  - RISK_OFF: bearish_count >= 2 and bullish_count == 0
  - NEUTRAL:  everything else (mixed signals, FLAT days)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pytz

logger = logging.getLogger("agent.market_context")


def _fetch_bar_alpaca(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch latest bar from Alpaca. Returns dict with open/close or None."""
    try:
        from data_provider import get_data_provider
        dp = get_data_provider()
        bar = dp.get_latest_bar(ticker)
        if bar and isinstance(bar, dict) and "close" in bar and "open" in bar:
            return bar
    except Exception as e:
        logger.warning("Alpaca get_latest_bar(%s) failed: %s", ticker, e)
    return None


def _fetch_bar_yfinance(ticker: str) -> Optional[Dict[str, float]]:
    """Fetch latest bar from yfinance. Returns dict with open/close or None."""
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period="2d")
        if len(hist) == 0:
            return None
        last = hist.iloc[-1]
        return {"open": float(last["Open"]), "close": float(last["Close"])}
    except Exception as e:
        logger.warning("yfinance fetch(%s) failed: %s", ticker, e)
    return None


def _fetch_vix() -> Optional[float]:
    """Fetch VIX close from yfinance (Alpaca doesn't support index symbols)."""
    bar = _fetch_bar_yfinance("^VIX")
    if bar:
        return bar["close"]
    return None


_DIRECTION_THRESHOLD_PCT = 0.2  # dead-zone: see module docstring for rationale


def _direction(bar: Dict[str, float]) -> str:
    pct = (bar["close"] - bar["open"]) / bar["open"] * 100
    if pct > _DIRECTION_THRESHOLD_PCT:
        return "UP"
    if pct < -_DIRECTION_THRESHOLD_PCT:
        return "DOWN"
    return "FLAT"


def _vix_level(vix: float) -> str:
    if vix < 20:
        return "LOW"
    elif vix <= 30:
        return "MEDIUM"
    else:
        return "HIGH"


def _derive_regime(spy_dir: str, iwm_dir: str, vix_lvl: str) -> str:
    """Derive market regime from three signals. See module docstring for rules."""
    bullish = (spy_dir == "UP") + (iwm_dir == "UP") + (vix_lvl == "LOW")
    bearish = (spy_dir == "DOWN") + (iwm_dir == "DOWN") + (vix_lvl == "HIGH")
    if bullish >= 2 and bearish == 0:
        return "RISK_ON"
    if bearish >= 2 and bullish == 0:
        return "RISK_OFF"
    return "NEUTRAL"


class MarketContextAgent:
    """Fetches broad-market data and derives a regime label."""

    def get_context(self) -> Dict[str, Any]:
        """
        Fetch SPY, IWM, VIX and return market context dict.

        Returns dict with keys:
            spy_close, spy_open, spy_direction,
            iwm_close, iwm_open, iwm_direction,
            vix_close, vix_level,
            market_regime, timestamp, errors
        """
        peru = pytz.timezone("America/Lima")
        errors = []

        # --- SPY ---
        spy_bar = _fetch_bar_alpaca("SPY")
        if spy_bar is None:
            logger.info("SPY Alpaca failed, falling back to yfinance")
            spy_bar = _fetch_bar_yfinance("SPY")
        if spy_bar is None:
            errors.append("SPY: no data from Alpaca or yfinance")

        # --- IWM ---
        iwm_bar = _fetch_bar_alpaca("IWM")
        if iwm_bar is None:
            logger.info("IWM Alpaca failed, falling back to yfinance")
            iwm_bar = _fetch_bar_yfinance("IWM")
        if iwm_bar is None:
            errors.append("IWM: no data from Alpaca or yfinance")

        # --- VIX ---
        vix_close = _fetch_vix()
        if vix_close is None:
            errors.append("VIX: no data from yfinance")

        # --- Compute directions ---
        spy_dir = _direction(spy_bar) if spy_bar else None
        iwm_dir = _direction(iwm_bar) if iwm_bar else None
        vix_lvl = _vix_level(vix_close) if vix_close else None

        # --- Regime ---
        if spy_dir and iwm_dir and vix_lvl:
            regime = _derive_regime(spy_dir, iwm_dir, vix_lvl)
        else:
            regime = "UNKNOWN"
            errors.append("Insufficient data for regime derivation")

        return {
            "spy_open": spy_bar["open"] if spy_bar else None,
            "spy_close": spy_bar["close"] if spy_bar else None,
            "spy_direction": spy_dir,
            "iwm_open": iwm_bar["open"] if iwm_bar else None,
            "iwm_close": iwm_bar["close"] if iwm_bar else None,
            "iwm_direction": iwm_dir,
            "vix_close": vix_close,
            "vix_level": vix_lvl,
            "market_regime": regime,
            "timestamp": datetime.now(peru).isoformat(),
            "errors": errors,
        }
