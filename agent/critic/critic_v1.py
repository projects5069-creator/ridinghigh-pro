"""
agent/critic/critic_v1.py
─────────────────────────
Critic Agent v1 — factual review of completed trades.

Reads paper_portfolio (closed trades with outcomes) and cross-references
decision_log (entry metrics) to produce per-trade verdicts and aggregate
statistics.

Data quality awareness:
  Trades with DataQuality="PRE_FIX" are from a buggy period and are
  flagged but not excluded from the full summary. A separate "clean"
  summary covers only reliable data.

No sheet writing, no orchestrator wiring — computation and return only.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("agent.critic")

# Statuses that indicate a closed trade with a result
_CLOSED_STATUSES = {
    "TP_HIT", "SL_HIT", "TIMEOUT", "MANUAL_CLOSE",
    "DRY_RUN_CLOSED", "CLOSED", "EOD_CLOSE",
}


def _safe_float(val, default=0.0) -> float:
    try:
        if val in (None, "", "None", "nan"):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


class CriticAgent:
    """Reviews completed trades and produces factual summaries."""

    def review_completed_trades(self) -> List[Dict[str, Any]]:
        """Read paper_portfolio + decision_log, return per-trade verdicts.

        Returns list of dicts, one per closed trade, with keys:
            ticker, position_id, entry_date, exit_date, entry_price,
            exit_price, verdict (WIN/LOSS/FLAT), pnl_pct, exit_reason,
            data_quality, score_at_entry, mxv, run_up, atrx, float_pct.
        """
        import sheets_manager as sm

        # --- Load paper_portfolio ---
        ws_port = sm.get_worksheet("paper_portfolio")
        port_rows = ws_port.get_all_values()
        if len(port_rows) <= 1:
            logger.warning("paper_portfolio is empty")
            return []

        port_header = port_rows[0]
        port_data = port_rows[1:]

        def _pcol(name):
            return port_header.index(name) if name in port_header else None

        pi_pos_id = _pcol("PositionID")
        pi_ticker = _pcol("Ticker")
        pi_entry_date = _pcol("EntryDate")
        pi_exit_date = _pcol("ExitDate")
        pi_entry_price = _pcol("EntryPrice")
        pi_exit_price = _pcol("ExitPrice")
        pi_status = _pcol("Status")
        pi_exit_reason = _pcol("ExitReason")
        pi_pnl = _pcol("RealizedPnL")
        pi_pnl_pct = _pcol("RealizedPnLPct")
        pi_dq = _pcol("DataQuality")

        # --- Load decision_log for cross-reference ---
        ws_dec = sm.get_worksheet("decision_log")
        dec_rows = ws_dec.get_all_values()
        dec_header = dec_rows[0] if dec_rows else []
        dec_data = dec_rows[1:] if len(dec_rows) > 1 else []

        def _dcol(name):
            return dec_header.index(name) if name in dec_header else None

        di_dec_id = _dcol("DecisionID")
        di_score = _dcol("Score")
        di_mxv = _dcol("MxV")
        di_runup = _dcol("RunUp")
        di_atrx = _dcol("ATRX")
        di_float = _dcol("FloatPct")

        # Build lookup: DecisionID → row
        dec_lookup: Dict[str, list] = {}
        if di_dec_id is not None:
            for row in dec_data:
                if di_dec_id < len(row) and row[di_dec_id]:
                    dec_lookup[row[di_dec_id]] = row

        # --- Process each closed trade ---
        results = []
        for row in port_data:
            status = row[pi_status] if pi_status is not None and pi_status < len(row) else ""
            # Check if trade is closed
            if status not in _CLOSED_STATUSES:
                continue

            pnl = _safe_float(row[pi_pnl] if pi_pnl is not None and pi_pnl < len(row) else "")
            pnl_pct = _safe_float(row[pi_pnl_pct] if pi_pnl_pct is not None and pi_pnl_pct < len(row) else "")

            if pnl > 0:
                verdict = "WIN"
            elif pnl < 0:
                verdict = "LOSS"
            else:
                verdict = "FLAT"

            pos_id = row[pi_pos_id] if pi_pos_id is not None and pi_pos_id < len(row) else ""
            data_quality = row[pi_dq] if pi_dq is not None and pi_dq < len(row) else ""

            # Cross-reference with decision_log
            dec_row = dec_lookup.get(pos_id, [])
            score = _safe_float(dec_row[di_score] if di_score is not None and di_score < len(dec_row) else "")
            mxv = _safe_float(dec_row[di_mxv] if di_mxv is not None and di_mxv < len(dec_row) else "")
            run_up = _safe_float(dec_row[di_runup] if di_runup is not None and di_runup < len(dec_row) else "")
            atrx = _safe_float(dec_row[di_atrx] if di_atrx is not None and di_atrx < len(dec_row) else "")
            float_pct = _safe_float(dec_row[di_float] if di_float is not None and di_float < len(dec_row) else "")

            results.append({
                "ticker": row[pi_ticker] if pi_ticker is not None and pi_ticker < len(row) else "?",
                "position_id": pos_id,
                "entry_date": row[pi_entry_date] if pi_entry_date is not None and pi_entry_date < len(row) else "",
                "exit_date": row[pi_exit_date] if pi_exit_date is not None and pi_exit_date < len(row) else "",
                "entry_price": _safe_float(row[pi_entry_price] if pi_entry_price is not None and pi_entry_price < len(row) else ""),
                "exit_price": _safe_float(row[pi_exit_price] if pi_exit_price is not None and pi_exit_price < len(row) else ""),
                "verdict": verdict,
                "pnl_pct": pnl_pct,
                "exit_reason": row[pi_exit_reason] if pi_exit_reason is not None and pi_exit_reason < len(row) else "",
                "data_quality": data_quality,
                "score_at_entry": score,
                "mxv": mxv,
                "run_up": run_up,
                "atrx": atrx,
                "float_pct": float_pct,
            })

        logger.info("Reviewed %d closed trades (%d clean)",
                     len(results),
                     sum(1 for r in results if r["data_quality"] != "PRE_FIX"))
        return results

    def summarize(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce factual summary from trade verdicts.

        Returns dict with keys:
            all: {total, wins, losses, flat, win_rate, avg_win_pct, avg_loss_pct}
            clean: same structure, excluding DataQuality="PRE_FIX"
        """
        def _stats(subset: List[Dict]) -> Dict[str, Any]:
            total = len(subset)
            if total == 0:
                return {"total": 0, "wins": 0, "losses": 0, "flat": 0,
                        "win_rate": None, "avg_win_pct": None, "avg_loss_pct": None}

            wins = [t for t in subset if t["verdict"] == "WIN"]
            losses = [t for t in subset if t["verdict"] == "LOSS"]
            flat = [t for t in subset if t["verdict"] == "FLAT"]

            win_pcts = [t["pnl_pct"] for t in wins]
            loss_pcts = [t["pnl_pct"] for t in losses]

            return {
                "total": total,
                "wins": len(wins),
                "losses": len(losses),
                "flat": len(flat),
                "win_rate": round(len(wins) / total * 100, 1) if total else None,
                "avg_win_pct": round(sum(win_pcts) / len(win_pcts), 2) if win_pcts else None,
                "avg_loss_pct": round(sum(loss_pcts) / len(loss_pcts), 2) if loss_pcts else None,
            }

        clean = [t for t in trades if t["data_quality"] != "PRE_FIX"]

        return {
            "all": _stats(trades),
            "clean": _stats(clean),
        }
