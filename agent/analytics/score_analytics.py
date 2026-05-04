"""
agent/analytics/score_analytics.py
───────────────────────────────────
Daily and weekly analysis of postmortem data.

OBSERVATIONAL ONLY (Phase 1):
- Daily: aggregate today's closed positions → 1 row to score_analytics Sheet
- Weekly (Saturday): aggregate week's data → suggestions to pending_suggestions Sheet

Suggestions are PENDING — user approves/rejects via M9 dashboard or weekly email (M8).
Phase 1 NEVER auto-modifies score formula or thresholds.

Sample size tiers determine suggestion confidence:
- INSUFFICIENT (<10): no suggestions, "INSUFFICIENT_DATA" recommendation
- EXPLORATORY (10-29): suggestions with Confidence="LOW"
- RELIABLE (30-99): suggestions with Confidence="MEDIUM"
- STRONG (100+): suggestions with Confidence="HIGH"
"""

import sys
import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np

logger = logging.getLogger("agent.analytics.score_analytics")

try:
    import pytz
    PERU_TZ = pytz.timezone("America/Lima")
except ImportError:
    from datetime import timezone
    PERU_TZ = timezone(timedelta(hours=-5))


# Sample size tiers
TIER_INSUFFICIENT = "INSUFFICIENT"
TIER_EXPLORATORY = "EXPLORATORY"
TIER_RELIABLE = "RELIABLE"
TIER_STRONG = "STRONG"

# Suggestion types
SUGGESTION_OBSERVATION = "OBSERVATION"
SUGGESTION_THRESHOLD = "THRESHOLD_CHANGE"
SUGGESTION_WEIGHT = "WEIGHT_ADJUSTMENT"

# Metrics tracked for correlations
METRICS = ["MxV", "RunUp", "ATRX", "RSI", "TypicalPriceDist", "ScanChange", "REL_VOL"]


class ScoreAnalytics:
    """Analyzes postmortems → writes to score_analytics + pending_suggestions Sheets."""

    def __init__(
        self,
        postmortem_reader=None,
        analytics_writer=None,
        suggestion_writer=None,
    ):
        """
        Args:
            postmortem_reader: callable() → list of postmortem dicts
            analytics_writer: callable(row: list of 25 values)
            suggestion_writer: callable(row: list of 14 values)
        """
        self._postmortem_reader = postmortem_reader
        self._analytics_writer = analytics_writer
        self._suggestion_writer = suggestion_writer

    # ════════════════════════════════════════════════════════════════════
    # Public API
    # ════════════════════════════════════════════════════════════════════

    def run_daily(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Run daily analysis. Returns the analytics row written.

        Args:
            date: YYYY-MM-DD string. If None, uses today (Peru).
        """
        if date is None:
            date = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

        postmortems = self._load_postmortems(start_date=date, end_date=date)

        return self._analyze_and_write(
            postmortems=postmortems,
            analysis_type="DAILY",
            period=date,
            generate_suggestions=False,
        )

    def run_weekly(self, week_end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Run weekly analysis (Saturday). Returns the analytics row written.

        Args:
            week_end_date: Saturday's date YYYY-MM-DD. If None, uses today.
        """
        if week_end_date is None:
            week_end_date = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

        # Week range: Sunday (week_end - 6) to Saturday (week_end)
        end_dt = datetime.strptime(week_end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=6)
        start_date = start_dt.strftime("%Y-%m-%d")
        period = f"{start_date}_to_{week_end_date}"

        postmortems = self._load_postmortems(start_date=start_date, end_date=week_end_date)

        return self._analyze_and_write(
            postmortems=postmortems,
            analysis_type="WEEKLY",
            period=period,
            generate_suggestions=True,
        )

    # ════════════════════════════════════════════════════════════════════
    # Data loading
    # ════════════════════════════════════════════════════════════════════

    def _load_postmortems(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load postmortems within date range. Returns DataFrame."""
        if not self._postmortem_reader:
            return pd.DataFrame()

        try:
            raw = self._postmortem_reader()
            if not raw:
                return pd.DataFrame()

            df = pd.DataFrame(raw)

            # Filter by date range
            if "ExitDate" in df.columns:
                df = df[(df["ExitDate"] >= start_date) & (df["ExitDate"] <= end_date)]

            # Parse JSON metrics
            if "MetricsAtEntry" in df.columns:
                df["_metrics"] = df["MetricsAtEntry"].apply(self._safe_json)

            # Numeric columns
            for col in ["PnLPct", "ScoreAtEntry", "DurationHours", "EntryPrice", "ExitPrice"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df
        except Exception as e:
            logger.error("Failed to load postmortems: %s", e)
            return pd.DataFrame()

    @staticmethod
    def _safe_json(s):
        try:
            return json.loads(s) if s else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    # ════════════════════════════════════════════════════════════════════
    # Analysis core
    # ════════════════════════════════════════════════════════════════════

    def _analyze_and_write(
        self,
        postmortems: pd.DataFrame,
        analysis_type: str,
        period: str,
        generate_suggestions: bool,
    ) -> Dict[str, Any]:
        """Compute stats, write analytics row, optionally write suggestions."""
        n = len(postmortems)
        tier, confidence = self._classify_sample(n)

        stats = self._compute_stats(postmortems, tier)

        # Build the 25-column analytics row
        now = datetime.now(PERU_TZ)
        date_str = now.strftime("%Y-%m-%d")

        analytics_row = [
            date_str,                       # 1. Date
            analysis_type,                  # 2. AnalysisType
            period,                         # 3. Period
            stats["TotalTrades"],           # 4. TotalTrades
            stats["WinRate"],               # 5. WinRate
            stats["TotalPnL"],             # 6. TotalPnL
            stats["AvgPnL"],               # 7. AvgPnL
            stats["MedianPnL"],            # 8. MedianPnL
            stats["WinRate_60_70"],        # 9
            stats["WinRate_70_80"],        # 10
            stats["WinRate_80_90"],        # 11
            stats["WinRate_90_plus"],      # 12
            stats["Corr_MxV"],             # 13
            stats["Corr_RunUp"],           # 14
            stats["Corr_ATRX"],            # 15
            stats["Corr_RSI"],             # 16
            stats["Corr_TypicalPriceDist"],  # 17
            stats["Corr_ScanChange"],      # 18
            stats["Corr_REL_VOL"],         # 19
            stats["StrongestPredictor"],   # 20
            stats["WeakestPredictor"],     # 21
            stats["SurpriseFinding"],      # 22
            stats["Recommendation"],       # 23
            n,                              # 24. SampleSize
            now.isoformat(),               # 25. GeneratedAt
        ]

        if self._analytics_writer:
            try:
                self._analytics_writer(analytics_row)
            except Exception as e:
                logger.error("Analytics write failed: %s", e)

        # Generate suggestions only on weekly + sufficient data
        suggestions = []
        if generate_suggestions and tier != TIER_INSUFFICIENT:
            suggestions = self._generate_suggestions(stats, period, confidence)
            for sugg in suggestions:
                if self._suggestion_writer:
                    try:
                        self._suggestion_writer(sugg)
                    except Exception as e:
                        logger.error("Suggestion write failed: %s", e)

        return {
            "analytics_row": analytics_row,
            "stats": stats,
            "tier": tier,
            "confidence": confidence,
            "suggestions": suggestions,
            "sample_size": n,
        }

    def _classify_sample(self, n: int) -> Tuple[str, Optional[str]]:
        """Classify sample size into tier + confidence."""
        if n < 10:
            return TIER_INSUFFICIENT, None
        if n < 30:
            return TIER_EXPLORATORY, "LOW"
        if n < 100:
            return TIER_RELIABLE, "MEDIUM"
        return TIER_STRONG, "HIGH"

    def _compute_stats(self, df: pd.DataFrame, tier: str) -> Dict[str, Any]:
        """Compute all statistics."""
        if len(df) == 0 or tier == TIER_INSUFFICIENT:
            return self._empty_stats(len(df), tier)

        # Basic performance
        total = len(df)
        wins = (df["PnLPct"] > 0).sum() if "PnLPct" in df.columns else 0
        win_rate = round((wins / total * 100), 2) if total > 0 else 0
        total_pnl = round(df["PnLPct"].sum(), 2) if "PnLPct" in df.columns else 0
        avg_pnl = round(df["PnLPct"].mean(), 2) if "PnLPct" in df.columns else 0
        median_pnl = round(df["PnLPct"].median(), 2) if "PnLPct" in df.columns else 0

        # Win rate per tier
        wr_tiers = self._compute_tier_winrates(df)

        # Correlations (Pearson)
        correlations = self._compute_correlations(df)

        # Strongest / weakest predictors
        if correlations:
            sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
            strongest = f"{sorted_corr[0][0]} (corr={sorted_corr[0][1]:.2f})"
            weakest = f"{sorted_corr[-1][0]} (corr={sorted_corr[-1][1]:.2f})"
        else:
            strongest = ""
            weakest = ""

        # Build correlation dict with all METRICS keys (default "" if not computed)
        corr_dict = {f"Corr_{m}": "" for m in METRICS}
        for k, v in correlations.items():
            corr_dict[f"Corr_{k}"] = round(v, 2) if v is not None else ""

        stats = {
            "TotalTrades": total,
            "WinRate": win_rate,
            "TotalPnL": total_pnl,
            "AvgPnL": avg_pnl,
            "MedianPnL": median_pnl,
            **{f"WinRate_{k}": v for k, v in wr_tiers.items()},
            **corr_dict,
            "StrongestPredictor": strongest,
            "WeakestPredictor": weakest,
            "correlations": correlations,
            "tier_rates_raw": wr_tiers,
        }

        # Surprise findings (after stats are built)
        stats["SurpriseFinding"] = self._detect_surprises(stats)

        # Recommendation (depends on everything else)
        stats["Recommendation"] = self._build_recommendation(stats, tier)

        return stats

    def _empty_stats(self, n: int, tier: str) -> Dict[str, Any]:
        """Stats dict when there's no data or insufficient."""
        return {
            "TotalTrades": n,
            "WinRate": 0,
            "TotalPnL": 0,
            "AvgPnL": 0,
            "MedianPnL": 0,
            "WinRate_60_70": "",
            "WinRate_70_80": "",
            "WinRate_80_90": "",
            "WinRate_90_plus": "",
            "Corr_MxV": "", "Corr_RunUp": "", "Corr_ATRX": "", "Corr_RSI": "",
            "Corr_TypicalPriceDist": "", "Corr_ScanChange": "", "Corr_REL_VOL": "",
            "StrongestPredictor": "",
            "WeakestPredictor": "",
            "SurpriseFinding": "",
            "Recommendation": f"INSUFFICIENT_DATA: n={n}, need ≥10",
            "correlations": {},
            "tier_rates_raw": {},
        }

    def _compute_tier_winrates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Win rate per score tier."""
        if "ScoreAtEntry" not in df.columns or "PnLPct" not in df.columns:
            return {"60_70": "", "70_80": "", "80_90": "", "90_plus": ""}

        results = {}
        ranges = [("60_70", 60, 70), ("70_80", 70, 80), ("80_90", 80, 90), ("90_plus", 90, 200)]
        for label, low, high in ranges:
            tier_df = df[(df["ScoreAtEntry"] >= low) & (df["ScoreAtEntry"] < high)]
            if len(tier_df) == 0:
                results[label] = ""
            else:
                wins = (tier_df["PnLPct"] > 0).sum()
                results[label] = round(wins / len(tier_df) * 100, 2)
        return results

    def _compute_correlations(self, df: pd.DataFrame) -> Dict[str, float]:
        """Pearson correlation between each metric and PnLPct."""
        if "PnLPct" not in df.columns or "_metrics" not in df.columns:
            return {}

        # Expand metrics into columns
        metrics_df = pd.json_normalize(df["_metrics"]).fillna(0)

        correlations = {}
        for metric in METRICS:
            if metric in metrics_df.columns:
                try:
                    series = pd.to_numeric(metrics_df[metric], errors="coerce")
                    if series.std() > 0:
                        corr = series.corr(df["PnLPct"].reset_index(drop=True))
                        correlations[metric] = corr if not pd.isna(corr) else None
                    else:
                        correlations[metric] = None
                except Exception as e:
                    logger.warning("Correlation failed for %s: %s", metric, e)
                    correlations[metric] = None

        # Filter out None
        return {k: v for k, v in correlations.items() if v is not None}

    # ════════════════════════════════════════════════════════════════════
    # Surprise detection
    # ════════════════════════════════════════════════════════════════════

    def _detect_surprises(self, stats: Dict[str, Any]) -> str:
        """Detect counter-intuitive patterns."""
        surprises = []

        # Rule 1: Score 90+ underperforms 70-80
        wr_90 = stats.get("WinRate_90_plus")
        wr_70_80 = stats.get("WinRate_70_80")
        if isinstance(wr_90, (int, float)) and isinstance(wr_70_80, (int, float)):
            if wr_90 < wr_70_80 - 10:
                surprises.append(f"Score 90+ underperforms 70-80 ({wr_90}% vs {wr_70_80}%)")

        # Rule 2: WinRate variance > 30% across tiers
        tier_rates = [stats.get(f"WinRate_{t}") for t in ["60_70", "70_80", "80_90", "90_plus"]]
        tier_rates = [r for r in tier_rates if isinstance(r, (int, float))]
        if tier_rates and (max(tier_rates) - min(tier_rates)) > 30:
            surprises.append(f"High variance between tiers ({min(tier_rates)}% to {max(tier_rates)}%)")

        # Rule 3: Strong correlation (|corr| > 0.4)
        for metric, corr in stats.get("correlations", {}).items():
            if abs(corr) > 0.4:
                direction = "positive" if corr > 0 else "negative"
                surprises.append(f"{metric} has strong {direction} correlation ({corr:.2f})")
                break  # one is enough

        if not surprises:
            return "No surprises this period"
        return " | ".join(surprises[:2])

    # ════════════════════════════════════════════════════════════════════
    # Recommendation
    # ════════════════════════════════════════════════════════════════════

    def _build_recommendation(self, stats: Dict[str, Any], tier: str) -> str:
        """Pipe-separated structured recommendation."""
        if tier == TIER_INSUFFICIENT:
            return f"INSUFFICIENT_DATA: n={stats['TotalTrades']}, need ≥10"

        parts = []

        # PRIMARY: best tier
        tier_rates = stats.get("tier_rates_raw", {})
        best_tier = None
        best_wr = -1
        for label, wr in tier_rates.items():
            if isinstance(wr, (int, float)) and wr > best_wr:
                best_wr = wr
                best_tier = label

        if best_tier:
            parts.append(f"PRIMARY: Sweet spot is {best_tier.replace('_', '-')} ({best_wr}% WR)")

        # SECONDARY: strongest predictor
        if stats.get("StrongestPredictor"):
            parts.append(f"SECONDARY: {stats['StrongestPredictor']} strongest predictor")

        # ACTION
        actions = []
        wr_60_70 = tier_rates.get("60_70")
        wr_90 = tier_rates.get("90_plus")

        if isinstance(wr_60_70, (int, float)) and wr_60_70 < 40:
            actions.append("Consider raising AGENT_MIN_SCORE to 65")
        if isinstance(wr_90, (int, float)) and wr_90 < 50:
            actions.append("Score 90+ may be noise — investigate")

        if actions:
            parts.append(f"ACTION: {'; '.join(actions)}")
        else:
            parts.append("ACTION: Continue collecting data")

        return " | ".join(parts)

    # ════════════════════════════════════════════════════════════════════
    # Suggestions (weekly only)
    # ════════════════════════════════════════════════════════════════════

    def _generate_suggestions(
        self,
        stats: Dict[str, Any],
        period: str,
        confidence: str,
    ) -> List[List[Any]]:
        """Generate 0-5 suggestions as 14-column rows."""
        suggestions = []
        now = datetime.now(PERU_TZ)
        date_str = now.strftime("%Y-%m-%d")

        tier_rates = stats.get("tier_rates_raw", {})
        correlations = stats.get("correlations", {})

        # Suggestion 1: 60-70 tier underperforming → raise threshold
        wr_60_70 = tier_rates.get("60_70")
        if isinstance(wr_60_70, (int, float)) and wr_60_70 < 50:
            suggestions.append(self._make_suggestion(
                date_str, period, SUGGESTION_THRESHOLD, confidence,
                description=f"60-70 score tier has {wr_60_70}% win rate (below 50%)",
                reasoning=(
                    f"Of {stats['TotalTrades']} trades, 60-70 underperforms. "
                    f"Raising minimum score may improve quality."
                ),
                affected="AGENT_MIN_SCORE",
                current="60",
                proposed="65",
                sample_size=stats["TotalTrades"],
            ))

        # Suggestion 2: Strong correlation → adjust weight
        for metric, corr in correlations.items():
            if abs(corr) > 0.3:
                direction = "increase" if abs(corr) > 0.4 else "consider increasing"
                suggestions.append(self._make_suggestion(
                    date_str, period, SUGGESTION_WEIGHT, confidence,
                    description=f"{metric} has strong correlation ({corr:.2f})",
                    reasoning=(
                        f"Pearson correlation of {corr:.2f} suggests {metric} is a "
                        f"strong predictor. Consider increasing its weight in the score formula."
                    ),
                    affected=f"WEIGHT_{metric}",
                    current="current_weight",
                    proposed=f"{direction}_weight",
                    sample_size=stats["TotalTrades"],
                ))
                if len(suggestions) >= 3:
                    break  # max 3 metric suggestions

        # Suggestion 3: Score 90+ underperforming
        wr_90 = tier_rates.get("90_plus")
        if isinstance(wr_90, (int, float)) and wr_90 < 50:
            suggestions.append(self._make_suggestion(
                date_str, period, SUGGESTION_OBSERVATION, confidence,
                description=f"Score 90+ has only {wr_90}% win rate",
                reasoning=(
                    "High scores may indicate over-extended pumps with continued momentum. "
                    "Investigate if this tier should be excluded or have separate rules."
                ),
                affected="HIGH_SCORE_HANDLING",
                current="treated_same",
                proposed="investigate",
                sample_size=stats["TotalTrades"],
            ))

        # Cap at 5 suggestions
        return suggestions[:5]

    def _make_suggestion(
        self,
        date: str, period: str, sugg_type: str, confidence: str,
        description: str, reasoning: str,
        affected: str, current: str, proposed: str,
        sample_size: int,
    ) -> List[Any]:
        """Build a 14-column suggestion row."""
        return [
            f"SUG-{uuid.uuid4().hex[:12]}",  # 1. SuggestionID
            date,                              # 2. GeneratedDate
            period,                            # 3. WeekOf
            sugg_type,                         # 4. Type
            description,                       # 5. Description
            reasoning,                         # 6. Reasoning
            confidence,                        # 7. Confidence
            affected,                          # 8. AffectedMetric
            current,                           # 9. CurrentValue
            proposed,                          # 10. ProposedValue
            "PENDING",                         # 11. Status
            "",                                # 12. UserResponse
            "",                                # 13. ResponseDate
            sample_size,                       # 14. SampleSize
        ]
