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
        port_rows = sm.get_sheet_values("paper_portfolio")
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
        dec_rows = sm.get_sheet_values("decision_log")
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

    def daily_facts(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Collect dry facts about what each agent did on a given day.

        No judgments — just counts and facts from each agent's output sheet.
        Each source is independently try/excepted so one failure doesn't
        prevent the others from reporting.

        Args:
            date_str: "YYYY-MM-DD". Defaults to today in America/Lima.

        Returns dict with keys: date, trader, sentinel, market_context,
        news_detective, errors.
        """
        import pytz
        import sheets_manager as sm
        from datetime import datetime

        peru = pytz.timezone("America/Lima")
        if date_str is None:
            date_str = datetime.now(peru).strftime("%Y-%m-%d")

        errors = []

        # --- 1. THE TRADER (decision_log) ---
        # Note: SKIP rows were written to decision_log only until 2026-05-11.
        # From 2026-05-12 onward (commit b1a4e4f), SKIP goes to stdout only.
        # So skips=0 after that date means "not recorded", not "none happened".
        trader_facts: Dict[str, Any] = {
            "enters": 0, "skips": None, "skip_data_available": False,
            "entered_tickers": [], "entered_tickers_unique": {},
        }
        try:
            rows = sm.get_sheet_values("decision_log")
            if len(rows) > 1:
                header = rows[0]
                ts_idx = header.index("Timestamp") if "Timestamp" in header else None
                act_idx = header.index("Action") if "Action" in header else None
                tk_idx = header.index("Ticker") if "Ticker" in header else None

                skip_count = 0
                if ts_idx is not None and act_idx is not None:
                    for r in rows[1:]:
                        if ts_idx < len(r) and r[ts_idx].startswith(date_str):
                            action = r[act_idx] if act_idx < len(r) else ""
                            if action == "ENTER":
                                trader_facts["enters"] += 1
                                ticker = r[tk_idx] if tk_idx is not None and tk_idx < len(r) else "?"
                                trader_facts["entered_tickers"].append(ticker)
                            elif action == "SKIP":
                                skip_count += 1

                if skip_count > 0:
                    trader_facts["skips"] = skip_count
                    trader_facts["skip_data_available"] = True
                # else: skips stays None, skip_data_available stays False

                # Build unique ticker counts — derived from entered_tickers
                # so both fields are always consistent
                from collections import Counter as _Counter
                trader_facts["entered_tickers_unique"] = dict(
                    _Counter(trader_facts["entered_tickers"])
                )
                # Sanity: enters must equal len(entered_tickers)
                trader_facts["enters"] = len(trader_facts["entered_tickers"])
        except Exception as e:
            logger.warning("daily_facts: decision_log failed: %s", e)
            errors.append(f"decision_log: {e}")

        # --- 2. DATA SENTINEL (system_events) ---
        sentinel_facts = {"blocks": 0, "warns": 0}
        try:
            rows = sm.get_sheet_values("system_events")
            if len(rows) > 1:
                header = rows[0]
                ts_idx = header.index("Timestamp") if "Timestamp" in header else 0
                evt_idx = header.index("EventType") if "EventType" in header else None

                if evt_idx is not None:
                    for r in rows[1:]:
                        if ts_idx < len(r) and r[ts_idx].startswith(date_str):
                            evt = r[evt_idx] if evt_idx < len(r) else ""
                            if "BLOCK" in evt:
                                sentinel_facts["blocks"] += 1
                            elif "WARN" in evt:
                                sentinel_facts["warns"] += 1
        except Exception as e:
            logger.warning("daily_facts: system_events failed: %s", e)
            errors.append(f"system_events: {e}")

        # --- 3. MARKET CONTEXT (market_context) ---
        mc_facts: Dict[str, Any] = {"regime": None, "changed_during_day": False}
        try:
            rows = sm.get_sheet_values("market_context")
            if len(rows) > 1:
                header = rows[0]
                ts_idx = header.index("Timestamp") if "Timestamp" in header else 0
                reg_idx = header.index("Market_Regime") if "Market_Regime" in header else None

                if reg_idx is not None:
                    day_regimes = []
                    for r in rows[1:]:
                        if ts_idx < len(r) and r[ts_idx].startswith(date_str):
                            regime = r[reg_idx] if reg_idx < len(r) else ""
                            if regime:
                                day_regimes.append(regime)

                    if day_regimes:
                        mc_facts["regime"] = day_regimes[-1]
                        mc_facts["changed_during_day"] = len(set(day_regimes)) > 1
        except Exception as e:
            logger.warning("daily_facts: market_context failed: %s", e)
            errors.append(f"market_context: {e}")

        # --- 4. NEWS DETECTIVE (news_findings) ---
        nd_facts = {"tickers_checked": 0, "material_news_count": 0}
        try:
            rows = sm.get_sheet_values("news_findings")
            if len(rows) > 1:
                header = rows[0]
                ts_idx = header.index("Timestamp") if "Timestamp" in header else 0
                mat_idx = header.index("Has_Material_News") if "Has_Material_News" in header else None

                for r in rows[1:]:
                    if ts_idx < len(r) and r[ts_idx].startswith(date_str):
                        nd_facts["tickers_checked"] += 1
                        if mat_idx is not None and mat_idx < len(r):
                            if r[mat_idx].upper() == "TRUE":
                                nd_facts["material_news_count"] += 1
        except Exception as e:
            logger.warning("daily_facts: news_findings failed: %s", e)
            errors.append(f"news_findings: {e}")

        # --- Anomaly detection ---
        # Each rule is a callable that receives the collected facts and
        # returns a list of anomaly dicts. Easy to extend with new rules.
        anomalies: List[Dict[str, str]] = []

        _MAX_ENTRIES_PER_TICKER = 3

        anomaly_rules = [
            # Rule 1: excessive entries for the same ticker
            lambda: [
                {"severity": "HIGH", "agent": "Trader",
                 "description": f"ריבוי כניסות — {tk} נכנסה {n} פעמים ביום אחד (סף תקין: {_MAX_ENTRIES_PER_TICKER})",
                 "detail": f"ticker={tk}, count={n}"}
                for tk, n in trader_facts["entered_tickers_unique"].items()
                if n > _MAX_ENTRIES_PER_TICKER
            ],
            # Rule 2: SKIP data missing
            lambda: [
                {"severity": "MEDIUM", "agent": "Trader",
                 "description": "נתוני SKIP חסרים בגיליון ליום זה",
                 "detail": "skip_data_available=False, SKIP not recorded since 2026-05-12"}
            ] if not trader_facts["skip_data_available"] and trader_facts["enters"] > 0 else [],
            # Rule 3: collection errors
            lambda: [
                {"severity": "MEDIUM", "agent": "System",
                 "description": f"שגיאת איסוף נתונים: {err}",
                 "detail": err}
                for err in errors
            ],
        ]

        for rule in anomaly_rules:
            try:
                anomalies.extend(rule())
            except Exception as e:
                logger.warning("Anomaly rule failed: %s", e)

        return {
            "date": date_str,
            "trader": trader_facts,
            "sentinel": sentinel_facts,
            "market_context": mc_facts,
            "news_detective": nd_facts,
            "anomalies": anomalies,
            "errors": errors,
        }

    def write_scorecard(self, date_str: Optional[str] = None) -> bool:
        """Run daily_facts and write 4 rows (one per agent) to agent_scorecard.

        Returns True on success, False on failure.
        Failures are swallowed (logged) — never break the calling loop.
        """
        try:
            import json as _json
            import pytz as _pytz
            import sheets_manager as sm
            from datetime import datetime as _dt

            peru = _pytz.timezone("America/Lima")
            facts = self.daily_facts(date_str)
            generated_at = _dt.now(peru).isoformat()
            anomalies = facts.get("anomalies", [])

            agent_map = {
                "Trader": facts["trader"],
                "Sentinel": facts["sentinel"],
                "Market Context": facts["market_context"],
                "News Detective": facts["news_detective"],
            }

            ws = sm.get_worksheet("agent_scorecard")

            for agent_name, agent_facts in agent_map.items():
                agent_anomalies = [a for a in anomalies if a.get("agent") == agent_name]
                # Also include "System" anomalies in the first agent (Trader) for visibility
                if agent_name == "Trader":
                    agent_anomalies += [a for a in anomalies if a.get("agent") == "System"]

                row = [
                    facts["date"],
                    agent_name,
                    _json.dumps(agent_facts, ensure_ascii=False, default=str),
                    len(agent_anomalies),
                    sum(1 for a in agent_anomalies if a.get("severity") == "HIGH"),
                    " | ".join(a.get("description", "") for a in agent_anomalies) if agent_anomalies else "",
                    generated_at,
                ]
                ws.append_row(row, value_input_option="USER_ENTERED")

            logger.info("Wrote scorecard for %s: %d anomalies", facts["date"], len(anomalies))
            return True
        except Exception as e:
            logger.warning("Failed to write scorecard: %s", e)
            return False

    def unified_positions(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Build a per-ticker table merging all agents' views for a given day.

        Each agent source is defined declaratively — adding a future agent
        means appending one dict to SOURCES, no logic changes needed.

        Returns dict with keys: date, regime, positions (dict keyed by ticker),
        conflicts (list of tickers with ENTER + material news), summary.
        """
        import pytz as _pytz
        import sheets_manager as sm
        from datetime import datetime as _dt
        from collections import defaultdict

        peru = _pytz.timezone("America/Lima")
        if date_str is None:
            date_str = _dt.now(peru).strftime("%Y-%m-%d")

        # ── Declarative source definitions ──────────────────────────────
        # Each source: agent name, sheet key, ticker column, timestamp column,
        # and list of fields to extract.
        SOURCES = [
            {
                "agent": "Trader",
                "sheet": "decision_log",
                "ticker_col": "Ticker",
                "ts_col": "Timestamp",
                "fields": ["Action", "Score", "Reason", "SkipReason"],
            },
            {
                "agent": "News Detective",
                "sheet": "news_findings",
                "ticker_col": "Ticker",
                "ts_col": "Timestamp",
                "fields": ["Has_Material_News", "EDGAR_Latest_Form", "Finnhub_Latest_Headline"],
            },
        ]

        errors = []
        # positions[ticker][agent] = {count, last_values}
        positions: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # ── Read each source ────────────────────────────────────────────
        for src in SOURCES:
            agent = src["agent"]
            try:
                rows = sm.get_sheet_values(src["sheet"])
                if len(rows) <= 1:
                    continue

                header = rows[0]
                tk_idx = header.index(src["ticker_col"]) if src["ticker_col"] in header else None
                ts_idx = header.index(src["ts_col"]) if src["ts_col"] in header else None
                field_idxs = {}
                for f in src["fields"]:
                    if f in header:
                        field_idxs[f] = header.index(f)

                if tk_idx is None or ts_idx is None:
                    continue

                for r in rows[1:]:
                    if ts_idx >= len(r) or not r[ts_idx].startswith(date_str):
                        continue
                    ticker = r[tk_idx] if tk_idx < len(r) else "?"
                    vals = {f: r[i] if i < len(r) else "" for f, i in field_idxs.items()}

                    existing = positions[ticker].get(agent)
                    if existing is None:
                        positions[ticker][agent] = {"count": 1, "last": vals}
                    else:
                        existing["count"] += 1
                        existing["last"] = vals  # keep latest

            except Exception as e:
                logger.warning("unified_positions: %s failed: %s", agent, e)
                errors.append(f"{agent}: {e}")

        # ── Market context (market-wide, not per-ticker) ────────────────
        regime = None
        try:
            rows = sm.get_sheet_values("market_context")
            if len(rows) > 1:
                header = rows[0]
                ts_idx = header.index("Timestamp") if "Timestamp" in header else 0
                reg_idx = header.index("Market_Regime") if "Market_Regime" in header else None
                if reg_idx is not None:
                    for r in rows[1:]:
                        if ts_idx < len(r) and r[ts_idx].startswith(date_str):
                            regime = r[reg_idx] if reg_idx < len(r) else regime
        except Exception as e:
            logger.warning("unified_positions: market_context failed: %s", e)
            errors.append(f"market_context: {e}")

        # ── Derive computed fields per ticker ───────────────────────────
        result_positions = {}
        conflicts = []

        for ticker, agents in positions.items():
            pos: Dict[str, Any] = {"ticker": ticker, "regime": regime}

            # Trader stance
            trader = agents.get("Trader")
            if trader:
                actions = set()
                # We only have the last action, but count tells us how many
                last_action = trader["last"].get("Action", "")
                pos["trader_count"] = trader["count"]
                pos["trader_last_action"] = last_action
                pos["trader_score"] = _safe_float(trader["last"].get("Score", ""))
                # For stance, check if all entries were ENTER (decision_log
                # only records ENTER post-2026-05-12, so if it's there it's ENTER)
                pos["trader_stance"] = last_action if last_action else "NONE"
            else:
                pos["trader_stance"] = "NONE"
                pos["trader_count"] = 0
                pos["trader_score"] = None

            # News flag
            nd = agents.get("News Detective")
            if nd:
                mat = nd["last"].get("Has_Material_News", "")
                pos["news_flag"] = mat.upper() == "TRUE"
                pos["news_edgar"] = nd["last"].get("EDGAR_Latest_Form", "")
                pos["news_headline"] = nd["last"].get("Finnhub_Latest_Headline", "")
            else:
                pos["news_flag"] = None  # not checked

            # Conflict detection
            pos["conflict"] = (
                pos["trader_stance"] == "ENTER"
                and pos.get("news_flag") is True
            )
            if pos["conflict"]:
                conflicts.append(ticker)

            result_positions[ticker] = pos

        return {
            "date": date_str,
            "regime": regime,
            "positions": result_positions,
            "conflicts": conflicts,
            "summary": {
                "total_tickers": len(result_positions),
                "conflict_count": len(conflicts),
            },
            "errors": errors,
        }

    def weekly_summary(self, end_date_str: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate daily facts + positions across the trading week ending on end_date.

        Computes Mon-Fri of the week containing end_date, calls daily_facts
        and unified_positions for each day, and returns weekly totals +
        daily breakdown + recurring anomaly tickers.

        Args:
            end_date_str: "YYYY-MM-DD" (Friday). Defaults to today in America/Lima.
        """
        import pytz as _pytz
        from datetime import datetime as _dt, timedelta as _td

        peru = _pytz.timezone("America/Lima")
        if end_date_str is None:
            end_date_str = _dt.now(peru).strftime("%Y-%m-%d")

        end_date = _dt.strptime(end_date_str, "%Y-%m-%d").date()
        # Find Monday of this week (weekday: Mon=0 ... Fri=4)
        monday = end_date - _td(days=end_date.weekday())
        week_days = [monday + _td(days=i) for i in range(5)]  # Mon-Fri

        totals = {
            "enters": 0, "skips": 0, "skips_available": False,
            "tickers_checked": 0, "anomalies": 0, "anomalies_high": 0,
            "conflicts": 0,
        }
        daily_breakdown = []
        anomaly_tickers_by_day: Dict[str, List[str]] = {}  # ticker → list of dates

        for day in week_days:
            day_str = day.strftime("%Y-%m-%d")
            day_enters = 0
            day_anomalies = 0
            day_conflicts = 0

            # daily_facts
            try:
                facts = self.daily_facts(day_str)
                trader = facts.get("trader", {})
                day_enters = trader.get("enters", 0)
                totals["enters"] += day_enters
                if trader.get("skip_data_available"):
                    totals["skips"] += trader.get("skips", 0) or 0
                    totals["skips_available"] = True
                totals["tickers_checked"] += facts.get("news_detective", {}).get("tickers_checked", 0)

                for a in facts.get("anomalies", []):
                    day_anomalies += 1
                    totals["anomalies"] += 1
                    if a.get("severity") == "HIGH":
                        totals["anomalies_high"] += 1
                    # Track recurring anomaly tickers
                    desc = a.get("description", "")
                    if "\u2014" in desc:  # em-dash
                        parts = desc.split("\u2014")
                        if len(parts) > 1:
                            ticker_part = parts[1].strip().split(" ")[0]
                            anomaly_tickers_by_day.setdefault(ticker_part, []).append(day_str)
            except Exception as e:
                logger.warning("weekly_summary: daily_facts(%s) failed: %s", day_str, e)

            # unified_positions
            try:
                positions = self.unified_positions(day_str)
                day_conflicts = positions.get("summary", {}).get("conflict_count", 0)
                totals["conflicts"] += day_conflicts
            except Exception as e:
                logger.warning("weekly_summary: unified_positions(%s) failed: %s", day_str, e)

            daily_breakdown.append({
                "date": day_str,
                "enters": day_enters,
                "anomalies": day_anomalies,
                "conflicts": day_conflicts,
            })

        # Recurring: tickers that appeared as anomaly on >1 day
        recurring = {t: len(days) for t, days in anomaly_tickers_by_day.items() if len(days) > 1}

        return {
            "week_start": monday.strftime("%Y-%m-%d"),
            "week_end": week_days[-1].strftime("%Y-%m-%d"),
            "totals": totals,
            "daily_breakdown": daily_breakdown,
            "recurring_anomaly_tickers": recurring,
        }
