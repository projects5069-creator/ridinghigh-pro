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

        # Build postmortem record (17 fields matching Sheet schema)
        postmortem_id = f"PM-{uuid.uuid4().hex[:12]}"
        postmortem = {
            "PostmortemID": postmortem_id,
            "PositionID": position_id,
            "Ticker": ticker,
            "EntryDate": position.get("EntryDate", ""),
            "EntryPrice": self._safe_float(position.get("EntryPrice"), 0.0),
            "ScoreAtEntry": ("" if decision_context.get("Score") is None
                             else round(decision_context.get("Score"), 2)),
            "MetricsAtEntry": json.dumps(decision_context.get("metrics", {})),
            "ExitDate": position.get("ExitDate", ""),
            "ExitPrice": self._safe_float(position.get("ExitPrice"), 0.0),
            "PnLPct": self._safe_float(position.get("RealizedPnLPct"), 0.0),
            "ExitReason": position.get("ExitReason", ""),
            "DurationHours": round(duration_hours, 2),
            "MaxFavorable": mfe if mfe is not None else "",
            "MaxAdverse": mae if mae is not None else "",
            "AutoLessons": self._build_forensic_prose(position, decision_context, mfe, mae, duration_hours),
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
            return {"Score": None, "metrics": {}}

        try:
            decision = self._decision_reader(position_id)
            if not decision:
                return {"Score": None, "metrics": {}}

            return {
                "Score": self._safe_float(decision.get("Score"), None),
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
            return {"Score": None, "metrics": {}}

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

    # ─────────────────────────────────────────────────────────────────
    # Forensic prose generator (added 2026-05-26)
    # Replaces generic AutoLessons with Hebrew narrative analysis.
    # Baseline references:
    #   Winner median: RSI=83.62, Price/SMA20=194%, MxV=-2507
    #   Toxic median:  RSI=92.61, Price/SMA20=305%, MxV=-887
    # ─────────────────────────────────────────────────────────────────

    WINNER_BASELINE = {"rsi": 83.62, "sma": 194, "mxv": -2507, "scan_change": 28}
    TOXIC_BASELINE = {"rsi": 92.61, "sma": 305, "mxv": -887, "scan_change": 45}

    def _build_forensic_prose(self, position, decision_ctx, mfe, mae, duration_hours):
        """
        Build forensic prose analysis in Hebrew for a closed trade.
        תיעוד בעברית של עסקה סגורה — מה הכניס, מה היו הטריגרים, השוואה ל-baseline.
        """
        if not decision_ctx:
            return "אין metrics לניתוח (decision_context ריק)"
        
        ticker = position.get("Ticker", "?")
        pnl_pct = position.get("RealizedPnLPct") or position.get("PnLPct") or 0
        exit_reason = position.get("ExitReason", "?")
        
        def f(v, default=0):
            try: return float(v)
            except (TypeError, ValueError): return default
        
        # Stage 0 (TASK-127.1): absence-safe — None means "no Score" (scoreless era),
        # never 0. Guarded everywhere below so None never enters a numeric compare.
        _raw_score = decision_ctx.get("Score")
        score = None if _raw_score is None else f(_raw_score, None)
        metrics = decision_ctx.get("metrics", {})
        rsi = f(metrics.get("RSI", 0))
        mxv = f(metrics.get("MxV", 0))
        run_up = f(metrics.get("RunUp", 0))
        rel_vol = f(metrics.get("REL_VOL", 0))
        scan_change = f(metrics.get("ScanChange", 0))
        sma_raw = decision_ctx.get("PriceVsSMA20")
        sma_v = f(sma_raw, None) if sma_raw not in (None, "", "MISSING") else None
        pnl = f(pnl_pct)
        
        winner = self.WINNER_BASELINE
        toxic = self.TOXIC_BASELINE
        
        lines = []
        
        is_win = "TP_HIT" in str(exit_reason) or pnl > 0
        is_loss = "SL_HIT" in str(exit_reason) or pnl < 0
        if is_win:
            lines.append(f"🟢 ניצחון — {exit_reason}, רווח {pnl:+.2f}% ({duration_hours:.1f}h)")
        elif is_loss:
            lines.append(f"🔴 הפסד — {exit_reason}, {pnl:+.2f}% ({duration_hours:.1f}h)")
        else:
            lines.append(f"⚪ סגירה — {exit_reason}, {pnl:+.2f}% ({duration_hours:.1f}h)")
        lines.append("")
        
        lines.append("📊 מה הכניס לעסקה:")
        if score is not None:
            if score < 60:
                lines.append(f"• Score={score:.2f} — נמוך, בקושי מעל הסף (50). הציון לבדו לא תמך בכניסה")
            elif score < 80:
                lines.append(f"• Score={score:.2f} — בינוני")
            else:
                lines.append(f"• Score={score:.2f} — גבוה")
        
        triggers = []
        if scan_change > 60:
            triggers.append(f"ScanChange={scan_change:.1f}% (פאמפ חזק)")
        elif scan_change > 30:
            triggers.append(f"ScanChange={scan_change:.1f}% (פאמפ בינוני)")
        if rel_vol > 10:
            triggers.append(f"REL_VOL={rel_vol:.1f}x (וולום חריג)")
        elif rel_vol > 5:
            triggers.append(f"REL_VOL={rel_vol:.1f}x (וולום מוגבר)")
        if mxv < -1000:
            triggers.append(f"MxV={mxv:.0f} (illiquidity חזק)")
        elif mxv < -300:
            triggers.append(f"MxV={mxv:.0f} (illiquidity מתון)")
        
        if triggers:
            lines.append(f"• הטריגרים: {' + '.join(triggers)}")
        lines.append("")
        
        lines.append("🎯 ה-DNA — איזה ארכיטיפ:")
        rsi_dist_to_winner = abs(rsi - winner["rsi"])
        rsi_dist_to_toxic = abs(rsi - toxic["rsi"])
        if rsi_dist_to_winner < rsi_dist_to_toxic:
            lines.append(f"• RSI={rsi:.2f} → קרוב ל-winner median ({winner['rsi']}), רחוק מ-toxic ({toxic['rsi']}) ✅")
        else:
            lines.append(f"• RSI={rsi:.2f} → קרוב ל-toxic median ({toxic['rsi']}), רחוק מ-winner ({winner['rsi']}) ⚠️")
        
        if sma_v is None:
            lines.append(f"• Price/SMA20: לא זמין → L3 בdefault PASS")
        elif sma_v < 250:
            lines.append(f"• Price/SMA20={sma_v:.0f}% — מתחת לסף toxic (250) ✅")
        else:
            lines.append(f"• Price/SMA20={sma_v:.0f}% — מעל סף toxic (250) ⚠️ (היה נחסם אם RSI>88)")
        lines.append("")
        
        close_calls = []
        if score is not None and 50 <= score <= 55:
            close_calls.append(f"Score={score:.2f} — 3 נק' פחות = SKIP")
        if 85 <= rsi <= 88:
            close_calls.append(f"RSI={rsi:.2f} — קרוב לסף L3 (88)")
        if sma_v is not None and 230 <= sma_v <= 250:
            close_calls.append(f"Price/SMA20={sma_v:.0f}% — קרוב לסף L3 (250%)")
        if -150 <= mxv <= -100:
            close_calls.append(f"MxV={mxv:.0f} — קרוב לסף MXV_TOO_HIGH (-100)")
        
        if close_calls:
            lines.append("⚠️ Close calls:")
            for cc in close_calls:
                lines.append(f"• {cc}")
            lines.append("")
        
        if mfe is not None and mae is not None:
            lines.append(f"📈 תנועה: MFE={mfe:+.2f}% (מקסימום לטובתי) | MAE={mae:+.2f}% (מקסימום נגדי)")
            lines.append("")
        
        lines.append("💡 תובנה:")
        if is_win and duration_hours < 2:
            lines.append(f"TP מהיר ({duration_hours:.1f}h) = pump-and-fade קלאסי. signature חזק.")
        elif is_win and duration_hours > 24:
            lines.append(f"TP איטי ({duration_hours:.1f}h) = mean reversion הדרגתי.")
        elif is_loss and duration_hours < 2:
            lines.append(f"SL מהיר ({duration_hours:.1f}h) = הפאמפ המשיך לעלות. בדוק אם ROCKET_GUARD היה צריך לחסום.")
        elif is_loss:
            lines.append(f"SL לאחר {duration_hours:.1f}h. בדוק אם RSI/SMA היו חריגים מ-baseline.")
        else:
            lines.append("עסקה ללא TP/SL — מקרה גבולי, ראוי לחקירה.")
        
        return "\n".join(lines)

