"""
News Detective Agent — SEC EDGAR filings + Finnhub news for signal tickers.

Checks for material news (8-K filings, significant headlines) that may
explain or invalidate a scanner signal before the Trader acts on it.
"""
from agent.news_detective.news_detective_v1 import NewsDetectiveAgent

__all__ = ["NewsDetectiveAgent"]
