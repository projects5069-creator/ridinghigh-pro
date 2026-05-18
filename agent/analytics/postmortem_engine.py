"""
agent/analytics/postmortem_engine.py
─────────────────────────────────────
Generates postmortem analysis for closed positions.

Per-position trigger: position_manager calls generate() right after closing.
Writes one row to postmortems Sheet (17 columns).

Computes:
- Duration (hours from entry to exit)
- MFE / MAE (max favorable/adverse excursion from real market data)
- Auto-lessons (rule-based pattern detection)

Both DRY_RUN and LIVE_PAPER positions get postmortems — DRY_RUN benefits
the most since the whole point is learning.

Score historical accuracy: ScoreAtEntry preserves the score AT THAT TIME.
If M7 changes the formula, old postmortems retain historical accuracy.
ScoreVersion (from config.AGENT_SCORE_VERSION) tags each postmortem.
"""

import sys
import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AGENT_SCORE_VERSION, AGENT_TP_PCT, AGENT_SL_PCT

logger = logging.getLogger("agent.analytics.postmortem_engine")

try:
    import pytz
    PERU_TZ = pytz.timezone("America/Lima")
except ImportError:
    from datetime import timezone
    PERU_TZ = timezone(timedelta(hours=-5))

# Status constants (matching paper_portfolio)
STATUS_DRY_RUN_CLOSED = "DRY_RUN_CLOSED"
AGENT_MODE_DRY_RUN = "DRY_RUN"
AGENT_MODE_LIVE = "LIVE_PAPER"


class PostmortemEngine:
    """
    Analyzes closed positions and writes postmortem records.

    Stateless: each generate() call is independent.
    """

    def __init__(
        self,
        data_provider=None,
        decision_reader=None,
        sheet_writer=None,
    ):
        """
        Args:
            data_provider: object with get_daily_bars(ticker, days, end_date)
            decision_reader: callable(decision_id) → decision dict from decision_log
            sheet_writer: callable(row: list) → None (writes to postmortems Sheet)
        """
        self.data_provider = data_provider
        self._decision_reader = decision_reader
        self._sheet_writer = sheet_writer

    def generate(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a postmortem for a closed position.

        Args:
            position: paper_portfolio row (must be CLOSED or DRY_RUN_CLOSED)

        Returns:
            postmortem dict (also written to Sheet via sheet_writer)
        """
        position_id = position.get("PositionID", "")
        ticker = position.get("Ticker", "")

        # Determine agent mode from position status
        is_dry_run = position.get("Status") == STATUS_DRY_RUN_CLOSED
        agent_mode = AGENT_MODE_DRY_RUN if is_dry_run else AGENT_MODE_LIVE

        # Compute duration
        duration_hours = self._compute_duration(position)

        # Get decision context (score, metrics at entry)
        decision_context = self._get_decision_context(position_id)

        # Compute MFE / MAE from market data
        mfe, mae = self._compute_mfe_mae(
            ticker=ticker,
            entry_date=position.get("EntryDate", ""),
            exit_date=position.get("ExitDate", ""),
            entry_price=self._safe_float(position.get("EntryPrice"), 0.0),
        )

        # Generate auto-lessons
        lessons = self._generate_lessons(
            position=position,
            decision_context=decision_context,
            mfe=mfe,
            mae=mae,
            duration=duration_hours,
            agent_mode=agent_mode,
        )

        # Build postmortem record (17 fields matching Sheet schema)
        postmortem_id = f"PM-{uuid.uuid4().hex[:12]}"
        postmortem = {
            "PostmortemID": postmortem_id,
            "PositionID": position_id,
            "Ticker": ticker,
            "EntryDate": position.get("EntryDate", ""),
            "EntryPrice": self._safe_float(position.get("EntryPrice"), 0.0),
            "ScoreAtEntry": decision_context.get("Score", 0.0),
            "MetricsAtEntry": json.dumps(decision_context.get("metrics", {})),
            "ExitDate": position.get("ExitDate", ""),
            "ExitPrice": self._safe_float(position.get("ExitPrice"), 0.0),
            "PnLPct": self._safe_float(position.get("RealizedPnLPct"), 0.0),
            "ExitReason": position.get("ExitReason", ""),
            "DurationHours": round(duration_hours, 2),
            "MaxFavorable": mfe if mfe is not None else "",
            "MaxAdverse": mae if mae is not None else "",
            "AutoLessons": json.dumps(lessons),
            "GeneratedAt": datetime.now(PERU_TZ).isoformat(),
            "ScoreVersion": AGENT_SCORE_VERSION,
        }

        # Write to Sheet
        self._write_postmortem(postmortem)

        return postmortem

    # ════════════════════════════════════════════════════════════════════
    # Duration
    # ════════════════════════════════════════════════════════════════════

    def _compute_duration(self, position: Dict[str, Any]) -> float:
        """Compute hold duration in hours from entry to exit."""
        try:
            entry_dt = datetime.strptime(
                f"{position['EntryDate']} {position['EntryTime']}",
                "%Y-%m-%d %H:%M:%S",
            )
            exit_dt = datetime.strptime(
                f"{position['ExitDate']} {position['ExitTime']}",
                "%Y-%m-%d %H:%M:%S",
            )
            return (exit_dt - entry_dt).total_seconds() / 3600.0
        except (KeyError, ValueError) as e:
            logger.warning("Cannot compute duration: %s", e)
            return 0.0

    # ════════════════════════════════════════════════════════════════════
    # Decision context (score + metrics at entry)
    # ════════════════════════════════════════════════════════════════════

    def _get_decision_context(self, position_id: str) -> Dict[str, Any]:
        """Look up decision_log row by PositionID = DecisionID."""
        if not self._decision_reader or not position_id:
            return {"Score": 0.0, "metrics": {}}

        try:
            decision = self._decision_reader(position_id)
            if not decision:
                return {"Score": 0.0, "metrics": {}}

            return {
                "Score": self._safe_float(decision.get("Score"), 0.0),
                "metrics": {
                    "MxV": self._safe_float(decision.get("MxV"), 0.0),
                    "RunUp": self._safe_float(decision.get("RunUp"), 0.0),
                    "ATRX": self._safe_float(decision.get("ATRX"), 0.0),
                    "RSI": self._safe_float(decision.get("RSI"), 0.0),
                    "REL_VOL": self._safe_float(decision.get("REL_VOL"), 0.0),
                    "ScanChange": self._safe_float(decision.get("ScanChange"), 0.0),
                    "ConfidenceScore": self._safe_float(decision.get("ConfidenceScore"), 0.0),
                },
            }
        except Exception as e:
            logger.warning("Failed to get decision context for %s: %s", position_id, e)
            return {"Score": 0.0, "metrics": {}}

    # ════════════════════════════════════════════════════════════════════
    # MFE / MAE (Max Favorable / Adverse Excursion)
    # ════════════════════════════════════════════════════════════════════

    def _compute_mfe_mae(
        self,
        ticker: str,
        entry_date: str,
        exit_date: str,
        entry_price: float,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Compute MFE/MAE from market bars during holding period.

        For SHORT position:
        - MFE (favorable) = lowest price during hold (lower = better for short)
        - MAE (adverse)   = highest price during hold (higher = worse for short)
        """
        if self.data_provider is None or not entry_date or not exit_date:
            return None, None

        try:
            entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
            exit_dt = datetime.strptime(exit_date, "%Y-%m-%d")
            days = max((exit_dt - entry_dt).days + 1, 1)

            bars = self.data_provider.get_daily_bars(ticker, days=days, end_date=exit_date)
            if bars is None or len(bars) == 0:
                return None, None

            mfe = float(bars["Low"].min()) if "Low" in bars.columns else None
            mae = float(bars["High"].max()) if "High" in bars.columns else None

            return mfe, mae
        except Exception as e:
            logger.warning("Failed to compute MFE/MAE for %s: %s", ticker, e)
            return None, None

    # ════════════════════════════════════════════════════════════════════
    # Auto-lessons (rule-based)
    # ════════════════════════════════════════════════════════════════════

    def _generate_lessons(
        self,
        position: Dict[str, Any],
        decision_context: Dict[str, Any],
        mfe: Optional[float],
        mae: Optional[float],
        duration: float,
        agent_mode: str,
    ) -> List[str]:
        """Rule-based auto-lesson generator (7 rules)."""
        lessons = []

        metrics = decision_context.get("metrics", {})
        atrx = metrics.get("ATRX", 0)
        rsi = metrics.get("RSI", 0)
        pnl_pct = self._safe_float(position.get("RealizedPnLPct"), 0.0)
        exit_reason = position.get("ExitReason", "")
        entry_price = self._safe_float(position.get("EntryPrice"), 0.0)
        sl_price = entry_price * (1 + AGENT_SL_PCT / 100) if entry_price else 0

        is_loss = pnl_pct < 0

        # Rule 1: LOSS + high ATRX
        if is_loss and atrx > 3:
            lessons.append("High ATRX — consider archetype-specific limits")

        # Rule 2: LOSS + RSI overbought (90+)
        if is_loss and rsi > 90:
            lessons.append("RSI 90+ at entry — momentum may have continued")

        # Rule 3: Fast outcome (LIVE_PAPER only — DRY_RUN has artificial timing)
        if duration < 1 and agent_mode == AGENT_MODE_LIVE:
            lessons.append("Very fast outcome — entry timing optimization candidate")

        # Rule 4: MAE > SL level → SL saved us
        if mae is not None and sl_price > 0 and mae > sl_price and not is_loss:
            lessons.append("MAE exceeded SL — stop-loss prevented larger loss")

        # Rule 5: MFE much better than TP → trailing TP candidate
        if mfe is not None and entry_price > 0:
            actual_drop_pct = (entry_price - mfe) / entry_price * 100
            if actual_drop_pct > AGENT_TP_PCT * 1.5:
                lessons.append(
                    f"Stock fell {actual_drop_pct:.1f}% (TP={AGENT_TP_PCT}%) — trailing TP candidate"
                )

        # Rule 6: EOD close + profit
        if exit_reason == "EOD_CLOSE" and pnl_pct > 0:
            lessons.append("EOD forced close with profit — consider extending hold")

        # Rule 7: EOD close + loss
        if exit_reason == "EOD_CLOSE" and pnl_pct < 0:
            lessons.append("EOD forced close with loss — earlier exit signal needed")

        # Special: no bar data available
        if mfe is None and mae is None:
            lessons.append("No bar data available — MFE/MAE not computed")

        return lessons

    # ════════════════════════════════════════════════════════════════════
    # Sheet writing
    # ════════════════════════════════════════════════════════════════════

    def _write_postmortem(self, postmortem: Dict[str, Any]):
        """Write postmortem to Sheet (17 columns)."""
        row = [
            postmortem["PostmortemID"],
            postmortem["PositionID"],
            postmortem["Ticker"],
            postmortem["EntryDate"],
            postmortem["EntryPrice"],
            postmortem["ScoreAtEntry"],
            postmortem["MetricsAtEntry"],
            postmortem["ExitDate"],
            postmortem["ExitPrice"],
            postmortem["PnLPct"],
            postmortem["ExitReason"],
            postmortem["DurationHours"],
            postmortem["MaxFavorable"],
            postmortem["MaxAdverse"],
            postmortem["AutoLessons"],
            postmortem["GeneratedAt"],
            postmortem["ScoreVersion"],
        ]

        if self._sheet_writer:
            try:
                self._sheet_writer(row)
            except Exception as e:
                logger.error("Postmortem write failed: %s", e)
        else:
            self._default_sheet_write(row)

    def _default_sheet_write(self, row: list):
        """Default: use sheets_manager."""
        try:
            import sheets_manager
            ws = sheets_manager.get_worksheet("postmortems")
            if ws:
                sheets_manager.safe_append_row(ws, row, dedup_col=0, dedup_val=row[0])
            else:
                logger.error("postmortems worksheet not available")
        except Exception as e:
            logger.error("postmortems write failed: %s", e)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert to float, return default on failure."""
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
