"""
agent/dashboard/live_agent_page.py
───────────────────────────────────
Page 9: Live Agent — operational view.

Sections:
A. Status banner (mode, market open/closed)
B. Today's KPIs (positions, PnL, decisions count)
C. Open positions table
D. Today's decisions table
E. Emergency stop (logs to system_events; M10 adds halt logic)
"""

import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd

from agent.dashboard._data_loaders import (
    load_paper_portfolio,
    load_decision_log_today,
    log_emergency_stop,
    PERU_TZ,
)

try:
    from config import AGENT_DRY_RUN, AGENT_LIVE_PAPER
except ImportError:
    AGENT_DRY_RUN = True
    AGENT_LIVE_PAPER = False

logger = logging.getLogger("agent.dashboard.live_agent")

OPEN_STATUSES = ["OPEN", "DRY_RUN_OPEN"]


def render_live_agent():
    """Main entry — Page 9."""
    st.title("🤖 Live Agent")

    # Manual refresh button
    if st.button("🔄 Refresh data", key="agent_refresh_top"):
        st.cache_data.clear()
        st.rerun()

    # ── Section A: Status Banner ─────────────────────────────
    _render_status_banner()

    st.divider()

    # ── Section B: Today's KPIs ───────────────────────────────
    portfolio_df = load_paper_portfolio()
    decisions_df = load_decision_log_today()

    _render_kpis(portfolio_df, decisions_df)

    st.divider()

    # ── Section C: Open Positions ─────────────────────────────
    st.subheader("📂 Open Positions")
    _render_open_positions(portfolio_df)

    st.divider()

    # ── Section C2: Today's Trades Summary ──────────────────
    st.subheader("📊 Today's Trades")
    _render_today_trades(portfolio_df)

    st.divider()

    # ── Section D: Today's Decisions ─────────────────────────
    st.subheader("📜 Today's Decisions")
    _render_today_decisions(decisions_df)

    st.divider()

    # ── Section E: Emergency Stop ────────────────────────────
    _render_emergency_stop()


def _render_status_banner():
    """Mode banner + market status."""
    now = datetime.now(PERU_TZ)
    market_open = (
        now.weekday() < 5
        and 8 * 60 + 30 <= now.hour * 60 + now.minute <= 15 * 60
    )

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if AGENT_DRY_RUN:
            st.warning("🧪 **DRY RUN MODE** — Simulated trades only, no real Alpaca calls")
        elif AGENT_LIVE_PAPER:
            st.success("🟢 **LIVE PAPER MODE** — Real Alpaca paper trades")
        else:
            st.error("🔴 **DISABLED** — Agent halted")

    with col2:
        market_icon = "🟢" if market_open else "🔴"
        market_text = "Market Open" if market_open else "Market Closed"
        st.info(f"{market_icon} {market_text}")

    with col3:
        st.info(f"🕐 {now.strftime('%H:%M Peru')}")


def _render_kpis(portfolio_df: pd.DataFrame, decisions_df: pd.DataFrame):
    """KPI metric cards."""
    col1, col2, col3, col4 = st.columns(4)

    # Open positions
    open_count = 0
    if not portfolio_df.empty and "Status" in portfolio_df.columns:
        open_count = portfolio_df["Status"].isin(OPEN_STATUSES).sum()
    col1.metric("📂 Open Positions", open_count)

    # Today's PnL (closed positions today)
    today_pnl = 0.0
    positions_closed_today = 0
    positions_with_pnl = 0
    if not portfolio_df.empty:
        today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        if "ExitDate" in portfolio_df.columns and "RealizedPnL" in portfolio_df.columns:
            today_closed = portfolio_df[portfolio_df["ExitDate"] == today_str]
            positions_closed_today = len(today_closed)
            pnl_numeric = pd.to_numeric(today_closed["RealizedPnL"], errors="coerce")
            positions_with_pnl = pnl_numeric.notna().sum()
            today_pnl = pnl_numeric.sum()
    col2.metric("💰 Today's P&L", f"${today_pnl:.2f}",
                delta=f"{positions_closed_today} closed" if positions_closed_today else None)

    # Today's decisions
    decisions_count = len(decisions_df) if not decisions_df.empty else 0
    col3.metric("📜 Decisions Today", decisions_count)

    # ENTER decisions today
    enters_count = 0
    if not decisions_df.empty and "Action" in decisions_df.columns:
        enters_count = (decisions_df["Action"] == "ENTER").sum()
    col4.metric("🎯 ENTER Today", enters_count)

    # Warning if positions closed but PnL missing
    if positions_closed_today > 0 and positions_with_pnl == 0:
        st.caption(f"⚠️ {positions_closed_today} position(s) closed today but PnL data missing")


def _render_open_positions(df: pd.DataFrame):
    """Open positions table."""
    if df.empty or "Status" not in df.columns:
        st.info("No open positions. Agent is waiting for signals.")
        return

    open_df = df[df["Status"].isin(OPEN_STATUSES)].copy()
    if open_df.empty:
        st.info("No open positions. Agent is waiting for signals.")
        return

    cols_to_show = [
        c for c in [
            "Ticker", "EntryDate", "EntryTime", "EntryPrice",
            "Quantity", "CurrentPrice", "UnrealizedPnLPct", "Status",
        ] if c in open_df.columns
    ]
    st.dataframe(open_df[cols_to_show], use_container_width=True, hide_index=True)


def _render_today_decisions(df: pd.DataFrame):
    """Today's decisions table — combines Reason+SkipReason into one Why column."""
    if df.empty:
        st.info("No decisions yet today. Agent will activate when scanner finds signals.")
        return

    display_df = df.copy()

    # Combine Reason (for ENTER) + SkipReason (for SKIP/REJECTED) into one column
    if "Action" in display_df.columns:
        def _combined_reason(row):
            if row.get("Action") == "ENTER":
                return row.get("Reason", "")
            return row.get("SkipReason", "")
        display_df["Why"] = display_df.apply(_combined_reason, axis=1)

    cols_to_show = [
        c for c in [
            "Timestamp", "Ticker", "AgentMode", "Action", "Score", "Why",
        ] if c in display_df.columns
    ]

    if not cols_to_show:
        st.dataframe(display_df.head(20), use_container_width=True, hide_index=True)
        return

    if "Timestamp" in display_df.columns:
        display_df = display_df.sort_values("Timestamp", ascending=False)

    st.dataframe(display_df[cols_to_show].head(50), use_container_width=True, hide_index=True)


def _render_today_trades(df: pd.DataFrame):
    """Render today's trades table — combined view of open + closed positions from today."""
    today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    if df.empty:
        st.info("No trades today yet.")
        return

    # Filter to today's trades: EntryDate == today OR (still open from previous days)
    today_mask = df.get("EntryDate", pd.Series(dtype=str)) == today_str
    today_df = df[today_mask].copy()

    if today_df.empty:
        st.info("No trades today yet. Agent is waiting for signals.")
        return

    # ── Stats row ──
    total = len(today_df)
    open_count = today_df["Status"].isin(OPEN_STATUSES).sum() if "Status" in today_df.columns else 0
    closed_df = today_df[~today_df["Status"].isin(OPEN_STATUSES)] if "Status" in today_df.columns else today_df.iloc[0:0]

    wins = 0
    losses = 0
    realized_pnl = 0.0
    if not closed_df.empty and "RealizedPnL" in closed_df.columns:
        pnl_num = pd.to_numeric(closed_df["RealizedPnL"], errors="coerce")
        wins = (pnl_num > 0).sum()
        losses = (pnl_num < 0).sum()
        realized_pnl = pnl_num.sum()

    closed_count = len(closed_df)
    win_rate = (wins / closed_count * 100) if closed_count > 0 else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🎯 Trades", total)
    col2.metric("✅ Wins", int(wins))
    col3.metric("❌ Losses", int(losses))
    col4.metric("⏳ Open", int(open_count))
    col5.metric("📊 Win Rate", f"{win_rate:.1f}%" if closed_count else "—")

    # ── Trades table ──
    display_df = today_df.copy()

    # Compute P&L column (Realized if closed, Unrealized otherwise)
    def _pnl_value(row):
        status = str(row.get("Status", "")).upper()
        if status in [s.upper() for s in OPEN_STATUSES]:
            return pd.to_numeric(row.get("UnrealizedPnL", 0), errors="coerce")
        return pd.to_numeric(row.get("RealizedPnL", 0), errors="coerce")

    def _pnl_pct(row):
        status = str(row.get("Status", "")).upper()
        if status in [s.upper() for s in OPEN_STATUSES]:
            return pd.to_numeric(row.get("UnrealizedPnLPct", 0), errors="coerce")
        return pd.to_numeric(row.get("RealizedPnLPct", 0), errors="coerce")

    def _status_badge(row):
        reason = str(row.get("ExitReason", "")).upper()
        status = str(row.get("Status", "")).upper()
        if "TP" in reason:
            return "🟢 TP_HIT"
        if "SL" in reason:
            return "🔴 SL_HIT"
        if "EOD" in reason or "EOD_CLOSE" in reason:
            return "🟡 EOD_CLOSED"
        if status in [s.upper() for s in OPEN_STATUSES]:
            return "⏳ OPEN"
        return reason or status

    display_df["P&L $"] = display_df.apply(_pnl_value, axis=1).round(2)
    display_df["P&L %"] = display_df.apply(_pnl_pct, axis=1).round(2)
    display_df["Status"] = display_df.apply(_status_badge, axis=1)

    cols_to_show = [
        c for c in [
            "Ticker", "EntryTime", "EntryPrice", "Quantity",
            "TPPrice", "SLPrice", "ExitTime", "ExitPrice",
            "P&L $", "P&L %", "Status",
        ] if c in display_df.columns
    ]

    if "EntryTime" in display_df.columns:
        display_df = display_df.sort_values("EntryTime", ascending=False)

    st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)


def _render_emergency_stop():
    """Emergency stop with confirmation dialog."""
    st.subheader("🚨 Emergency Stop")
    st.caption("Halts all agent activity. Logged to system_events. M10 adds real halt logic.")

    if st.button("🚨 EMERGENCY STOP", type="primary", key="emergency_stop_btn"):
        st.session_state["es_confirm_dialog"] = True

    if st.session_state.get("es_confirm_dialog"):
        st.warning("⚠️ **Confirm Emergency Stop**")
        confirm = st.text_input("Type 'STOP' to confirm:", key="es_confirm_input")
        reason = st.text_input("Reason (optional):", key="es_reason_input")

        col1, col2 = st.columns(2)
        if col1.button("✅ Confirm Stop", key="es_confirm_btn"):
            if confirm.upper().strip() == "STOP":
                success = log_emergency_stop(reason=reason or "no reason given")
                if success:
                    st.success("🚨 Emergency stop logged. M10 will pick up the signal.")
                    st.session_state["es_confirm_dialog"] = False
                else:
                    st.error("Failed to log emergency stop. Check connectivity.")
            else:
                st.error("Confirmation text didn't match. Type 'STOP' exactly.")

        if col2.button("❌ Cancel", key="es_cancel_btn"):
            st.session_state["es_confirm_dialog"] = False
            st.rerun()
