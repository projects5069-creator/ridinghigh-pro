"""
agent/dashboard/sentinel_events_page.py
─────────────────────────────────────────
Sentinel Events — what Data Sentinel caught.

Reads sentinel_events sheet, shows:
1. KPI Summary (total BLOCKs, WARNs, clean days, last event)
2. Events table (recent BLOCK/WARN)
3. Breakdown by Component (which check fired)
4. Breakdown by Message (which reason)
"""

import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd

from agent.dashboard._data_loaders import _get_worksheet, PERU_TZ

logger = logging.getLogger("agent.dashboard.sentinel_events")


@st.cache_data(ttl=120)
def _load_sentinel_events() -> pd.DataFrame:
    """Load sentinel_events (all rows are Sentinel events). TTL 120s."""
    try:
        ws = _get_worksheet("sentinel_events")
        if ws is None:
            return pd.DataFrame()
        records = ws.get_all_records()
        df = pd.DataFrame(records) if records else pd.DataFrame()
        if df.empty or "EventType" not in df.columns:
            return pd.DataFrame()
        # Filter to Sentinel events only
        df = df[df["EventType"].astype(str).str.startswith("SENTINEL_")].copy()
        return df
    except Exception as e:
        logger.error("Failed to load sentinel events: %s", e)
        return pd.DataFrame()


def _render_kpis(df: pd.DataFrame) -> None:
    """Top KPI row."""
    total = len(df)
    blocks = len(df[df["EventType"] == "SENTINEL_BLOCK"]) if not df.empty else 0
    warns = len(df[df["EventType"] == "SENTINEL_WARN"]) if not df.empty else 0

    # Clean days = days since last event
    last_event = "—"
    days_clean = "—"
    if not df.empty and "Timestamp" in df.columns:
        try:
            ts = pd.to_datetime(df["Timestamp"], errors="coerce").dropna()
            if len(ts) > 0:
                last = ts.max()
                last_event = last.strftime("%Y-%m-%d %H:%M")
                now = datetime.now(PERU_TZ).replace(tzinfo=None)
                days_clean = f"{(now - last.tz_localize(None)).days}d"
        except Exception:
            pass

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛑 BLOCKs", blocks)
    c2.metric("⚠️ WARNs", warns)
    c3.metric("📊 Total Events", total)
    c4.metric("🕐 Last Event", last_event)


def _render_events_table(df: pd.DataFrame) -> None:
    """Recent events table."""
    if df.empty:
        st.info("אין events עדיין — Data Sentinel רץ ב-shadow mode ולא תפס כלום, "
                "או שהסוכן עוד לא רץ מאז שהחיווט נוסף.")
        return
    show = df.copy()
    # Most recent first
    if "Timestamp" in show.columns:
        show = show.iloc[::-1]
    # Clean string display
    cols = ["Timestamp", "EventType", "Severity", "Component", "Message", "ActionTaken"]
    cols = [c for c in cols if c in show.columns]
    display = show[cols].astype(str)
    st.dataframe(display, use_container_width=True, hide_index=True)


def _render_breakdown(df: pd.DataFrame) -> None:
    """Breakdown by Component and Message."""
    if df.empty:
        return
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**לפי בדיקה (Component)**")
        if "Component" in df.columns:
            counts = df["Component"].value_counts()
            st.dataframe(counts.reset_index().rename(
                columns={"index": "Component", "Component": "Count"}),
                use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**לפי סיבה (Message)**")
        if "Message" in df.columns:
            counts = df["Message"].value_counts()
            st.dataframe(counts.reset_index().rename(
                columns={"index": "Message", "Message": "Count"}),
                use_container_width=True, hide_index=True)


def render_sentinel_events() -> None:
    """Main entry — Sentinel Events page."""
    st.title("🛡️ Sentinel Events")
    st.caption("מה ש-Data Sentinel תפס. כרגע ב-shadow mode — events מתועדים אך לא חוסמים.")

    df = _load_sentinel_events()

    st.divider()
    _render_kpis(df)

    st.divider()
    with st.expander("📋 Events Table", expanded=True):
        _render_events_table(df)

    st.divider()
    with st.expander("📊 Breakdown", expanded=True):
        _render_breakdown(df)

    st.divider()
    st.caption("Data Sentinel — 7 checks (4 per-signal + 3 system). "
               "SENTINEL_MODE='shadow' → אחרי כמה ימי shadow נקיים, מעבר ל-'active'.")
