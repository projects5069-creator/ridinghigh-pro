"""
agent/dashboard/trade_history_page.py
──────────────────────────────────────
Trade History — audit trail of all positions opened by the agent.

Sections:
1. KPI Summary (total trades, wins, losses, open, win rate, total P&L)
2. All Trades table (with live price for OPEN positions)
3. Cumulative P&L chart (plotly)
4. Win Rate by Ticker breakdown
5. Near-miss SKIPs (high-score skipped candidates)
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
    render_regime_banner,
    PERU_TZ,
)

logger = logging.getLogger("agent.dashboard.trade_history")

OPEN_STATUSES = ["OPEN", "DRY_RUN_OPEN"]
CLOSED_STATUSES = ["CLOSED", "DRY_RUN_CLOSED"]


# ── Data loaders ─────────────────────────────────────────────────

@st.cache_data(ttl=300)
def _load_decision_log_all() -> pd.DataFrame:
    """Load full decision_log (TTL 300s — heavier query)."""
    try:
        from agent.dashboard._data_loaders import _get_worksheet
        ws = _get_worksheet("decision_log")
        if ws is None:
            return pd.DataFrame()
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame()
    except Exception as e:
        logger.error("Failed to load full decision_log: %s", e)
        return pd.DataFrame()


@st.cache_data(ttl=120)
def _fetch_live_prices(tickers: tuple) -> dict:
    """Fetch current prices via yfinance. Cached 120s."""
    import yfinance as yf
    out = {}
    if not tickers:
        return out
    try:
        data = yf.download(
            list(tickers), period="1d", interval="1m",
            progress=False, group_by="ticker", auto_adjust=False,
        )
        for tk in tickers:
            try:
                if len(tickers) == 1:
                    closes = data["Close"].dropna()
                else:
                    closes = data[tk]["Close"].dropna()
                if len(closes) > 0:
                    out[tk] = float(closes.iloc[-1])
            except (KeyError, IndexError):
                pass
    except Exception:
        pass
    return out


# ── Helpers ──────────────────────────────────────────────────────

def _status_badge(row) -> str:
    reason = str(row.get("ExitReason", "")).upper()
    status = str(row.get("Status", "")).upper()
    if "TP" in reason:
        return "🟢 TP_HIT"
    if "SL" in reason:
        return "🔴 SL_HIT"
    if "EOD" in reason:
        return "🟡 EOD_CLOSED"
    if status in [s.upper() for s in OPEN_STATUSES]:
        return "⏳ OPEN"
    return reason or status


def _exit_reason_normalized(row) -> str:
    reason = str(row.get("ExitReason", "")).upper()
    if "TP" in reason:
        return "TP_HIT"
    if "SL" in reason:
        return "SL_HIT"
    if "EOD" in reason:
        return "EOD_CLOSED"
    status = str(row.get("Status", "")).upper()
    if status in [s.upper() for s in OPEN_STATUSES]:
        return "OPEN"
    return reason or status


def _hold_duration(row) -> str:
    """Compute hold duration as 'Xd Yh' format."""
    try:
        entry_date = str(row.get("EntryDate", ""))
        entry_time = str(row.get("EntryTime", ""))
        entry_str = f"{entry_date} {entry_time}".strip()
        if not entry_date:
            return ""

        # Parse entry
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                entry_dt = datetime.strptime(entry_str, fmt)
                break
            except ValueError:
                continue
        else:
            return ""

        # End: ExitDate/ExitTime if closed, else now
        status = str(row.get("Status", "")).upper()
        if status in [s.upper() for s in OPEN_STATUSES]:
            end_dt = datetime.now(PERU_TZ).replace(tzinfo=None)
        else:
            exit_date = str(row.get("ExitDate", ""))
            exit_time = str(row.get("ExitTime", ""))
            exit_str = f"{exit_date} {exit_time}".strip()
            if not exit_date:
                return ""
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    end_dt = datetime.strptime(exit_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return ""

        delta = end_dt - entry_dt
        total_hours = int(delta.total_seconds() // 3600)
        days = total_hours // 24
        hours = total_hours % 24
        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h"
    except Exception:
        return ""


# ── Filter logic ─────────────────────────────────────────────────

def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render filter widgets and return filtered DataFrame."""
    col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1])

    with col1:
        time_filter = st.selectbox(
            "Time", ["All time", "Last 30d", "Last 7d", "Today"],
            index=0, key="th_time_filter",
        )

    # Ticker list
    tickers_available = sorted(df["Ticker"].dropna().unique().tolist()) if "Ticker" in df.columns else []
    with col2:
        ticker_filter = st.multiselect(
            "Ticker", tickers_available, default=[], key="th_ticker_filter",
        )

    with col3:
        status_options = ["All", "TP_HIT", "SL_HIT", "EOD_CLOSED", "OPEN"]
        status_filter = st.selectbox(
            "Status", status_options, index=0, key="th_status_filter",
        )

    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="th_refresh"):
            st.cache_data.clear()
            st.rerun()

    filtered = df.copy()

    # Time filter
    if time_filter != "All time" and "EntryDate" in filtered.columns:
        now = datetime.now(PERU_TZ)
        if time_filter == "Today":
            cutoff = now.strftime("%Y-%m-%d")
            filtered = filtered[filtered["EntryDate"] == cutoff]
        elif time_filter == "Last 7d":
            cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            filtered = filtered[filtered["EntryDate"] >= cutoff]
        elif time_filter == "Last 30d":
            cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            filtered = filtered[filtered["EntryDate"] >= cutoff]

    # Ticker filter
    if ticker_filter:
        filtered = filtered[filtered["Ticker"].isin(ticker_filter)]

    # Status filter
    if status_filter != "All":
        filtered["_exit_norm"] = filtered.apply(_exit_reason_normalized, axis=1)
        filtered = filtered[filtered["_exit_norm"] == status_filter]
        filtered = filtered.drop(columns=["_exit_norm"])

    return filtered


# ── Sections ─────────────────────────────────────────────────────

def _render_kpis(df: pd.DataFrame):
    """Section 1: KPI summary metrics."""
    total = len(df)
    is_open = df.apply(lambda r: str(r.get("Status", "")).upper() in [s.upper() for s in OPEN_STATUSES], axis=1) if not df.empty else pd.Series(dtype=bool)
    open_count = is_open.sum() if not df.empty else 0
    closed_df = df[~is_open] if not df.empty else df

    # Wins / Losses from RealizedPnL
    wins = 0
    losses = 0
    if not closed_df.empty and "RealizedPnL" in closed_df.columns:
        pnl = pd.to_numeric(closed_df["RealizedPnL"], errors="coerce")
        wins = int((pnl > 0).sum())
        losses = int((pnl < 0).sum())

    closed_count = len(closed_df)
    win_rate = (wins / closed_count * 100) if closed_count > 0 else 0.0

    # Total P&L: realized (closed) + unrealized (open)
    total_pnl = 0.0
    if not closed_df.empty and "RealizedPnL" in closed_df.columns:
        total_pnl += pd.to_numeric(closed_df["RealizedPnL"], errors="coerce").sum()
    if not df.empty and "UnrealizedPnL" in df.columns:
        open_pnl = pd.to_numeric(df[is_open]["UnrealizedPnL"], errors="coerce").sum()
        total_pnl += open_pnl

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("🎯 Total Trades", total)
    col2.metric("✅ Wins", f"{wins} ({wins/closed_count*100:.0f}%)" if closed_count else str(wins))
    col3.metric("❌ Losses", f"{losses} ({losses/closed_count*100:.0f}%)" if closed_count else str(losses))
    col4.metric("⏳ Open", int(open_count))
    col5.metric("📊 Win Rate", f"{win_rate:.1f}%" if closed_count else "—")
    col6.metric("💰 Total P&L", f"${total_pnl:+,.2f}")


def _render_trades_table(df: pd.DataFrame):
    """Section 2: All trades table with live prices for OPEN."""
    if df.empty:
        st.info("No trades match the current filters.")
        return

    display = df.copy()

    # Fetch live prices for open positions
    open_mask = display.apply(
        lambda r: str(r.get("Status", "")).upper() in [s.upper() for s in OPEN_STATUSES], axis=1
    )
    open_tickers = tuple(display[open_mask]["Ticker"].dropna().unique().tolist())
    live_prices = _fetch_live_prices(open_tickers) if open_tickers else {}

    def _current_price(row):
        status = str(row.get("Status", "")).upper()
        if status in [s.upper() for s in OPEN_STATUSES]:
            cp = pd.to_numeric(row.get("CurrentPrice", 0), errors="coerce")
            if cp and cp > 0:
                return cp
            return live_prices.get(str(row.get("Ticker", "")).strip().upper(), 0)
        return pd.to_numeric(row.get("ExitPrice", 0), errors="coerce")

    def _pnl_dollar(row):
        status = str(row.get("Status", "")).upper()
        if status in [s.upper() for s in OPEN_STATUSES]:
            entry = pd.to_numeric(row.get("EntryPrice", 0), errors="coerce")
            qty = pd.to_numeric(row.get("Quantity", 0), errors="coerce")
            curr = row.get("_current_price", 0)
            if entry and curr and qty:
                return (entry - curr) * qty
            return pd.to_numeric(row.get("UnrealizedPnL", 0), errors="coerce")
        return pd.to_numeric(row.get("RealizedPnL", 0), errors="coerce")

    def _pnl_pct(row):
        status = str(row.get("Status", "")).upper()
        if status in [s.upper() for s in OPEN_STATUSES]:
            entry = pd.to_numeric(row.get("EntryPrice", 0), errors="coerce")
            curr = row.get("_current_price", 0)
            if entry and curr:
                return (entry - curr) / entry * 100
            return pd.to_numeric(row.get("UnrealizedPnLPct", 0), errors="coerce")
        return pd.to_numeric(row.get("RealizedPnLPct", 0), errors="coerce")

    # Compute columns
    display["Status_Badge"] = display.apply(_status_badge, axis=1)
    display["_current_price"] = display.apply(_current_price, axis=1)
    display["HoldDuration"] = display.apply(_hold_duration, axis=1).fillna("—").replace("", "—")
    pnl_dollar_raw = display.apply(_pnl_dollar, axis=1).round(2)
    pnl_pct_raw = display.apply(_pnl_pct, axis=1).round(2)

    # Format P&L columns as strings to avoid mixed-type Arrow errors
    display["P&L $"] = pnl_dollar_raw.apply(
        lambda v: f"${v:+,.2f}" if pd.notna(v) and v != 0 else "—"
    )
    display["P&L %"] = pnl_pct_raw.apply(
        lambda v: f"{v:+.2f}%" if pd.notna(v) and v != 0 else "—"
    )

    # Format price columns as strings
    def _fmt_price(series, allow_zero=True):
        return pd.to_numeric(series, errors="coerce").apply(
            lambda v: f"${v:.2f}" if pd.notna(v) and (allow_zero or v != 0) else "—"
        )

    if "EntryPrice" in display.columns:
        display["EntryPrice"] = _fmt_price(display["EntryPrice"])
    if "TPPrice" in display.columns:
        display["TPPrice"] = _fmt_price(display["TPPrice"])
    if "SLPrice" in display.columns:
        display["SLPrice"] = _fmt_price(display["SLPrice"])
    if "ExitPrice" in display.columns:
        display["ExitPrice"] = _fmt_price(display["ExitPrice"], allow_zero=False)

    # Format Quantity as string
    if "Quantity" in display.columns:
        display["Quantity"] = pd.to_numeric(display["Quantity"], errors="coerce").apply(
            lambda v: str(int(v)) if pd.notna(v) else "—"
        )

    # Fill NaN/empty in remaining text columns to ensure uniform string dtype
    for col in ("EntryDate", "EntryTime", "ExitDate", "ExitTime", "ExitReason"):
        if col in display.columns:
            display[col] = display[col].fillna("—").replace("", "—").astype(str)

    # Rename for display — drop original Status first to avoid duplicates
    if "Status" in display.columns:
        display = display.drop(columns=["Status"])
    display = display.rename(columns={"Status_Badge": "Status"})

    cols_to_show = [
        c for c in [
            "Status", "EntryDate", "EntryTime", "Ticker",
            "EntryPrice", "Quantity", "TPPrice", "SLPrice",
            "ExitDate", "ExitTime", "ExitPrice", "ExitReason",
            "HoldDuration", "P&L $", "P&L %",
        ] if c in display.columns
    ]

    # Sort newest first
    if "EntryDate" in display.columns:
        display = display.sort_values(
            ["EntryDate", "EntryTime"] if "EntryTime" in display.columns else ["EntryDate"],
            ascending=False,
        )

    # Bullet-proof: rebuild DataFrame from scratch as pure string dict
    # Some object columns (timestamps, mixed pd.NA/np.nan/None) still trip Arrow
    # even after fillna+astype. This rebuild forces a clean str-only schema.
    safe_data = {}
    for col in cols_to_show:
        if col not in display.columns:
            continue
        vals = []
        for v in display[col].tolist():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                vals.append("—")
            else:
                s = str(v)
                if s.lower() in ("nan", "none", "nat", ""):
                    vals.append("—")
                else:
                    vals.append(s)
        safe_data[col] = vals

    display_safe = pd.DataFrame(safe_data)
    st.dataframe(display_safe, use_container_width=True, hide_index=True)


def _render_cumulative_pnl(df: pd.DataFrame):
    """Section 3: Cumulative P&L line chart (closed positions only)."""
    if df.empty:
        st.info("No closed trades to chart.")
        return

    # Filter to closed only
    closed = df[~df.apply(
        lambda r: str(r.get("Status", "")).upper() in [s.upper() for s in OPEN_STATUSES], axis=1
    )].copy()

    if closed.empty or "RealizedPnL" not in closed.columns:
        st.info("No closed trades to chart.")
        return

    closed["RealizedPnL"] = pd.to_numeric(closed["RealizedPnL"], errors="coerce").fillna(0)

    # Sort by exit date
    if "ExitDate" in closed.columns:
        closed = closed.sort_values(
            ["ExitDate", "ExitTime"] if "ExitTime" in closed.columns else ["ExitDate"]
        )

    closed["CumulativePnL"] = closed["RealizedPnL"].cumsum()
    closed["ExitReason_Norm"] = closed.apply(_exit_reason_normalized, axis=1)

    try:
        import plotly.graph_objects as go

        fig = go.Figure()

        # Line
        fig.add_trace(go.Scatter(
            x=closed["ExitDate"],
            y=closed["CumulativePnL"],
            mode="lines+markers",
            line=dict(color="gray", width=2),
            marker=dict(
                color=closed["ExitReason_Norm"].map({
                    "TP_HIT": "green",
                    "SL_HIT": "red",
                    "EOD_CLOSED": "orange",
                }).fillna("gray"),
                size=8,
            ),
            text=closed.apply(
                lambda r: f"{r.get('Ticker', '')} {r.get('ExitReason', '')} ${r.get('RealizedPnL', 0):+.2f}",
                axis=1,
            ),
            hovertemplate="%{text}<br>Cumulative: $%{y:+,.2f}<extra></extra>",
        ))

        # Color fill
        fig.add_trace(go.Scatter(
            x=closed["ExitDate"],
            y=closed["CumulativePnL"],
            fill="tozeroy",
            fillcolor="rgba(0,200,0,0.1)" if closed["CumulativePnL"].iloc[-1] >= 0 else "rgba(200,0,0,0.1)",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

        fig.update_layout(
            title="Cumulative P&L over time",
            xaxis_title="Exit Date",
            yaxis_title="Cumulative P&L ($)",
            yaxis_tickprefix="$",
            hovermode="x unified",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("plotly not installed — chart unavailable.")


def _render_win_rate_by_ticker(df: pd.DataFrame):
    """Section 4: Win Rate by Ticker grouped table."""
    if df.empty:
        st.info("No trades to analyze.")
        return

    df = df.copy()
    df["_is_open"] = df.apply(
        lambda r: str(r.get("Status", "")).upper() in [s.upper() for s in OPEN_STATUSES], axis=1
    )
    df["RealizedPnL"] = pd.to_numeric(df.get("RealizedPnL", pd.Series(dtype=float)), errors="coerce").fillna(0)

    rows = []
    for ticker, group in df.groupby("Ticker"):
        total = len(group)
        open_count = group["_is_open"].sum()
        closed = group[~group["_is_open"]]
        closed_pnl = pd.to_numeric(closed["RealizedPnL"], errors="coerce")
        wins = int((closed_pnl > 0).sum())
        losses = int((closed_pnl < 0).sum())
        closed_count = len(closed)
        win_rate = (wins / closed_count * 100) if closed_count > 0 else 0.0
        net_pnl = closed_pnl.sum()

        # Avg hold duration
        durations = group.apply(_hold_duration, axis=1)
        avg_dur = durations.mode().iloc[0] if not durations.empty and durations.iloc[0] else ""

        rows.append({
            "Ticker": ticker,
            "Trades": total,
            "Wins": wins,
            "Losses": losses,
            "Open": int(open_count),
            "Win Rate %": f"{win_rate:.1f}%",
            "Net P&L $": round(net_pnl, 2),
            "Avg Hold": avg_dur,
        })

    if not rows:
        st.info("No ticker data to display.")
        return

    result = pd.DataFrame(rows).sort_values("Net P&L $", ascending=False)
    st.dataframe(result, use_container_width=True, hide_index=True)


def _render_near_miss_skips(time_filter: str):
    """Section 5: Near-miss SKIPs (Score >= 60)."""
    log_df = _load_decision_log_all()

    if log_df.empty:
        st.info("No decision log data available.")
        return

    # Filter to SKIPs
    if "Action" not in log_df.columns:
        st.info("No Action column in decision_log.")
        return

    skips = log_df[log_df["Action"].astype(str).str.upper() == "SKIP"].copy()

    if skips.empty:
        st.info("No SKIP decisions found.")
        return

    # Score filter >= 60
    if "Score" in skips.columns:
        skips["Score"] = pd.to_numeric(skips["Score"], errors="coerce")
        skips = skips[skips["Score"] >= 60]

    if skips.empty:
        st.info("No near-miss SKIPs (Score >= 60) found.")
        return

    # Time filter
    if "Timestamp" in skips.columns:
        now = datetime.now(PERU_TZ)
        if time_filter == "Today":
            today_str = now.strftime("%Y-%m-%d")
            skips = skips[skips["Timestamp"].astype(str).str.startswith(today_str)]
        elif time_filter == "Last 7d":
            cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            skips = skips[skips["Timestamp"].astype(str) >= cutoff]
        elif time_filter == "Last 30d":
            cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            skips = skips[skips["Timestamp"].astype(str) >= cutoff]

    if skips.empty:
        st.info("No near-miss SKIPs in the selected time range.")
        return

    # Build Why column (SkipReason or Reason)
    if "SkipReason" in skips.columns:
        skips["Why"] = skips["SkipReason"]
    elif "Reason" in skips.columns:
        skips["Why"] = skips["Reason"]
    else:
        skips["Why"] = ""

    # Extract time from Timestamp
    if "Timestamp" in skips.columns:
        skips["Time"] = skips["Timestamp"].astype(str).str[11:16]
    else:
        skips["Time"] = ""

    skips = skips.sort_values("Score", ascending=False).head(50)

    cols = [c for c in ["Time", "Ticker", "Score", "Why"] if c in skips.columns]
    st.dataframe(skips[cols], use_container_width=True, hide_index=True)


# ── Main render ──────────────────────────────────────────────────

def render_trade_history():
    """Main entry point for Trade History page."""
    st.title("📊 Trade History")
    st.caption("Audit trail — all positions opened by the agent")

    # ── Market Regime Banner (display only) ──────────────────
    render_regime_banner()

    # Load data
    portfolio_df = load_paper_portfolio()

    if portfolio_df.empty:
        st.warning("No paper_portfolio data found. The agent hasn't opened any positions yet.")
        return

    # ── Filters ──
    filtered_df = _apply_filters(portfolio_df)

    # Track time filter for SKIPs section
    time_filter = st.session_state.get("th_time_filter", "All time")

    st.divider()

    # ── Section 1: KPIs ──
    _render_kpis(filtered_df)

    st.divider()

    # ── Section 2: All Trades Table ──
    st.subheader("📋 All Trades")
    _render_trades_table(filtered_df)

    st.divider()

    # ── Section 3: Cumulative P&L ──
    st.subheader("📈 Cumulative P&L")
    _render_cumulative_pnl(filtered_df)

    st.divider()

    # ── Section 4: Win Rate by Ticker ──
    st.subheader("🎯 Win Rate by Ticker")
    _render_win_rate_by_ticker(filtered_df)

    st.divider()

    # ── Section 5: Near-miss SKIPs ──
    st.subheader("⚠️ Near-miss SKIPs (Score ≥ 60)")
    _render_near_miss_skips(time_filter)
