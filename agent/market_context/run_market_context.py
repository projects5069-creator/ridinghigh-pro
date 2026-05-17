"""
agent/market_context/run_market_context.py
──────────────────────────────────────────
Standalone entry point for the Market Context Agent.

Usage:
    python3 -m agent.market_context.run_market_context

Fetches SPY/IWM/VIX, derives market regime, writes one row to the
market_context sheet, and exits with code 0 (success) or 1 (failure).
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(message)s",
)

from agent.market_context import MarketContextAgent


def main():
    mc = MarketContextAgent()
    ctx = mc.get_context()
    regime = ctx.get("market_regime", "UNKNOWN")

    ok = mc.write_context()
    if ok:
        print(f"OK: market_regime={regime}")
        sys.exit(0)
    else:
        print(f"FAIL: write_context() returned False (regime={regime})")
        sys.exit(1)


if __name__ == "__main__":
    main()
