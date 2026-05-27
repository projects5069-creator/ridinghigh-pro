"""
Risk Sentinel (Agent #6/#7) — portfolio-level risk gate. v1.

v1 BLOCK checks (cheap — only account_state + paper_portfolio, NO external fetch):
  - daily_pnl_floor:     today's realized P&L < -$200 -> block new entries
  - buying_power_buffer: cash reserve < 10% of account -> block

Deferred (documented, not implemented in v1):
  - concentration: redundant under fixed $1000 sizing — reduces to the
    concurrent / re-entry count caps already enforced in decision_logic.py
    (§10 Single Source of Truth). Re-add only if position sizing becomes variable.
  - sector / correlation: need fundamentals / price-history per ENTER ->
    quota + latency risk; require caching first (v2).

Short system: realized P&L = (EntryPrice - ExitPrice) * Quantity, stored in the
RealizedPnL column on close (see position_manager._close_position).
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import pytz

logger = logging.getLogger(__name__)
PERU_TZ = pytz.timezone("America/Lima")

_CLOSED_STATUSES = ("TP_HIT", "SL_HIT", "EOD_CLOSE", "CLOSED")
_OPEN_STATUSES = ("OPEN", "DRY_RUN_OPEN")


@dataclass
class RiskResult:
    allow: bool
    reason: str = ""
    warnings: List[str] = field(default_factory=list)


class RiskSentinel:
    def __init__(self, config):
        self.config = config
        # Hard daily-loss floor, reusing the existing $200 alert threshold.
        self.DAILY_LOSS_FLOOR = -abs(float(config.AGENT_COLD_START_DAILY_LOSS_ALERT_USD))
        self.BUYING_POWER_MIN_BUFFER_PCT = 0.10

    def check_entry(self, ticker: str, account_state: Dict, paper_portfolio: List[Dict]) -> RiskResult:
        """Per-ENTER gate. Returns RiskResult(allow, reason, warnings)."""
        for check in (self._check_daily_pnl_floor, self._check_buying_power_buffer):
            r = check(ticker, account_state, paper_portfolio)
            if not r.allow:
                logger.warning("[RiskSentinel] BLOCK %s: %s", ticker, r.reason)
                return r
        return RiskResult(allow=True)

    def _check_daily_pnl_floor(self, ticker, account_state, paper_portfolio) -> RiskResult:
        """Block once TODAY's realized P&L breaches the floor (today only)."""
        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        realized = 0.0
        for pos in paper_portfolio:
            status = str(pos.get("Status", "")).upper()
            if status in _CLOSED_STATUSES and str(pos.get("ExitDate", "")).startswith(today):
                try:
                    realized += float(pos.get("RealizedPnL", 0) or 0)
                except (TypeError, ValueError):
                    continue
        if realized < self.DAILY_LOSS_FLOOR:
            return RiskResult(False, f"DAILY_LOSS: today realized ${realized:.2f} < floor ${self.DAILY_LOSS_FLOOR:.2f}")
        return RiskResult(allow=True)

    def _check_buying_power_buffer(self, ticker, account_state, paper_portfolio) -> RiskResult:
        """Keep >=10% cash buffer of total account value (deployed notional + cash)."""
        bp = float(account_state.get("buying_power", 0) or 0)
        deployed = 0.0
        for pos in paper_portfolio:
            if str(pos.get("Status", "")).upper() in _OPEN_STATUSES:
                try:
                    deployed += float(pos.get("EntryPrice", 0) or 0) * int(pos.get("Quantity", 0) or 0)
                except (TypeError, ValueError):
                    continue
        account_value = deployed + bp
        if account_value <= 0:
            return RiskResult(allow=True)
        buffer_pct = bp / account_value
        if buffer_pct < self.BUYING_POWER_MIN_BUFFER_PCT:
            return RiskResult(False, f"BUYING_POWER: buffer {buffer_pct*100:.1f}% < {self.BUYING_POWER_MIN_BUFFER_PCT*100:.0f}%")
        return RiskResult(allow=True)


def get_risk_sentinel(config) -> RiskSentinel:
    return RiskSentinel(config)
