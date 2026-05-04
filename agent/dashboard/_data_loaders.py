"""
agent/dashboard/_data_loaders.py
─────────────────────────────────
Cached data readers for agent dashboard pages.

Uses sheets_manager.get_worksheet() — same pattern as existing dashboard.

TTL strategy:
- 60s for live data (paper_portfolio, decision_log)
- 300s for analytics data (score_analytics, pending_suggestions)
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd

logger = logging.getLogger("agent.dashboard.data_loaders")

try:
    import pytz
    PERU_TZ = pytz.timezone("America/Lima")
except ImportError:
    from datetime import timezone
    PERU_TZ = timezone(timedelta(hours=-5))


def _get_worksheet(name: str):
    """Wrapper around sheets_manager — graceful fallback if unavailable."""
    try:
        import sheets_manager
        return sheets_manager.get_worksheet(name)
    except Exception as e:
        logger.error("Failed to get worksheet %s: %s", name, e)
        return None


@st.cache_data(ttl=60)
def load_paper_portfolio() -> pd.DataFrame:
    """Load paper_portfolio Sheet (TTL 60s — live data)."""
    ws = _get_worksheet("paper_portfolio")
    if ws is None:
        return pd.DataFrame()
    try:
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame()
    except Exception as e:
        logger.error("Failed to load paper_portfolio: %s", e)
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_decision_log_today() -> pd.DataFrame:
    """Load today's decision_log entries (TTL 60s)."""
    ws = _get_worksheet("decision_log")
    if ws is None:
        return pd.DataFrame()
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        if "Timestamp" in df.columns:
            df = df[df["Timestamp"].astype(str).str.startswith(today)]
        return df
    except Exception as e:
        logger.error("Failed to load decision_log: %s", e)
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_score_analytics_latest() -> Optional[Dict[str, Any]]:
    """Load latest score_analytics row (TTL 300s)."""
    ws = _get_worksheet("score_analytics")
    if ws is None:
        return None
    try:
        records = ws.get_all_records()
        if not records:
            return None
        df = pd.DataFrame(records)
        if "GeneratedAt" in df.columns:
            df = df.sort_values("GeneratedAt", ascending=False)
        return df.iloc[0].to_dict() if len(df) > 0 else None
    except Exception as e:
        logger.error("Failed to load score_analytics: %s", e)
        return None


@st.cache_data(ttl=300)
def load_pending_suggestions() -> pd.DataFrame:
    """Load pending_suggestions filtered to PENDING (TTL 300s)."""
    ws = _get_worksheet("pending_suggestions")
    if ws is None:
        return pd.DataFrame()
    try:
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        if "Status" in df.columns:
            df = df[df["Status"] == "PENDING"]
        return df
    except Exception as e:
        logger.error("Failed to load pending_suggestions: %s", e)
        return pd.DataFrame()


def update_suggestion_status(suggestion_id: str, status: str, response: str) -> bool:
    """
    Update a suggestion's Status atomically.

    Uses ws.find() to locate the row reliably (immune to empty rows or
    get_all_records() index drift).

    Args:
        suggestion_id: SUG-xxxxx
        status: "APPROVED" or "REJECTED"
        response: free-text user response

    Returns:
        True on success, False otherwise.
    """
    ws = _get_worksheet("pending_suggestions")
    if ws is None:
        return False
    try:
        # Find the row by SuggestionID — robust to empty rows and reordering
        cell = ws.find(suggestion_id)
        if cell is None:
            logger.warning("Suggestion %s not found in Sheet", suggestion_id)
            return False

        row_idx = cell.row
        now_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d %H:%M:%S")

        # Atomic update of Status (col K=11), UserResponse (col L=12), ResponseDate (col M=13)
        ws.update(
            f"K{row_idx}:M{row_idx}",
            [[status, response, now_str]],
            value_input_option="USER_ENTERED",
        )

        # Clear cache so user sees update on next render
        load_pending_suggestions.clear()
        return True
    except Exception as e:
        logger.error("Failed to update suggestion %s: %s", suggestion_id, e)
        return False


def log_emergency_stop(reason: str, source: str = "dashboard") -> bool:
    """
    Write EMERGENCY_STOP_REQUESTED event to system_events Sheet.

    M9 only logs — M10 will add real halt logic.
    """
    ws = _get_worksheet("system_events")
    if ws is None:
        return False
    try:
        now = datetime.now(PERU_TZ)
        # system_events schema (7 cols): Timestamp, EventType, Severity, Component, Message, Details, ActionTaken
        row = [
            now.isoformat(),
            "EMERGENCY_STOP_REQUESTED",
            "CRITICAL",
            source,
            f"User requested stop. Reason: {reason}",
            "",
            "LOGGED_PENDING_M10",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        logger.error("Failed to log emergency stop: %s", e)
        return False
