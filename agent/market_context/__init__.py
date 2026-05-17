"""
Market Context Agent — broad market regime detection.

Fetches SPY, IWM (Alpaca) and VIX (yfinance) to derive a single
market_regime label: RISK_ON / NEUTRAL / RISK_OFF.
"""
from agent.market_context.market_context_v1 import MarketContextAgent

__all__ = ["MarketContextAgent"]
