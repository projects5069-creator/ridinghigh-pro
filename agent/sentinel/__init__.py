"""
Data Sentinel — gatekeeper layer for The Trader.

Runs validation checks on signals before they reach decision logic.
Operates in 3 modes (config.SENTINEL_MODE):
  - "shadow": log decisions but don't block (DEFAULT for first week)
  - "active": block bad signals
  - "off": disabled completely

Phase 1: Foundation + dummy check (always ALLOW).
Phase 2: 4 lightweight checks (completeness, scan freshness, price sanity, position sync).
Phase 3: 3 heavy checks (price freshness vs Alpaca, quota health, provider health).
"""
from agent.sentinel.data_sentinel import DataSentinel, SentinelResult

__all__ = ["DataSentinel", "SentinelResult"]
