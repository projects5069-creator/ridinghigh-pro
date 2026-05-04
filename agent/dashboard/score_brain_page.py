"""
agent/dashboard/score_brain_page.py
────────────────────────────────────
Page 10: Score Brain — analytical view.

Sections:
A. Latest analytics KPIs
B. Win rate by tier (bar chart)
C. Metric correlations (horizontal bar chart)
D. Recommendation (formatted text)
E. Pending suggestions (table + Approve/Reject buttons)
"""

import sys
import os
import json
import math
import logging
from typing import Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from agent.dashboard._data_loaders import (
    load_score_analytics_latest,
    load_pending_suggestions,
    update_suggestion_status,
)

logger = logging.getLogger("agent.dashboard.score_brain")


def render_score_brain():
    """Main entry — Page 10."""
    st.title("🧠 Score Brain")

    # Manual refresh
    if st.button("🔄 Refresh data", key="brain_refresh_top"):
        st.cache_data.clear()
        st.rerun()

    latest = load_score_analytics_latest()

    if latest is None:
        st.warning("📊 No analytics data yet. Waiting for first postmortems and analytics runs.")
        st.info("Score Analytics runs daily at 16:30 Peru and weekly Saturday 18:00 Peru.")
        return

    # ── Section A: Latest KPIs ────────────────────────────────
    _render_latest_kpis(latest)

    st.divider()

    # ── Section B: Win Rate by Tier ──────────────────────────
    st.subheader("🎯 Win Rate by Score Tier")
    _render_tier_chart(latest)

    st.divider()

    # ── Section C: Correlations ──────────────────────────────
    st.subheader("🔗 Metric Correlations with PnL")
    _render_correlations_chart(latest)

    st.divider()

    # ── Section D: Recommendation ────────────────────────────
    st.subheader("💡 Recommendation")
    _render_recommendation(latest)

    st.divider()

    # ── Section E: Pending Suggestions ───────────────────────
    st.subheader("📬 Pending Suggestions")
    _render_pending_suggestions()


def _render_latest_kpis(stats: Dict[str, Any]):
    """4 KPI cards."""
    col1, col2, col3, col4 = st.columns(4)

    n = stats.get("SampleSize", 0)
    win_rate = stats.get("WinRate", 0)
    total_pnl = stats.get("TotalPnL", 0)
    avg_pnl = stats.get("AvgPnL", 0)

    col1.metric("📋 Sample Size", n, delta=stats.get("AnalysisType", ""))
    col2.metric("🎯 Win Rate", f"{win_rate}%")
    col3.metric("💰 Total PnL", f"{total_pnl}%")
    col4.metric("📊 Avg PnL", f"{avg_pnl}%")

    # Period + GeneratedAt
    period = stats.get("Period", "")
    generated = stats.get("GeneratedAt", "")
    if period or generated:
        st.caption(f"Period: {period} · Generated: {generated[:19] if generated else ''}")


def _render_tier_chart(stats: Dict[str, Any]):
    """Bar chart of win rate per tier."""
    tiers = []
    rates = []
    for label, key in [("60-70", "WinRate_60_70"), ("70-80", "WinRate_70_80"),
                        ("80-90", "WinRate_80_90"), ("90+", "WinRate_90_plus")]:
        val = stats.get(key)
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                continue
            tiers.append(label)
            rates.append(f)
        except (TypeError, ValueError):
            continue

    if not tiers:
        st.info("No tier data available yet.")
        return

    fig = go.Figure(data=[go.Bar(
        x=tiers, y=rates,
        text=[f"{r:.0f}%" for r in rates],
        textposition="auto",
        marker_color=["#FF6B6B" if r < 50 else "#FFD93D" if r < 70 else "#6BCB77" for r in rates],
    )])
    fig.update_layout(
        xaxis_title="Score Tier",
        yaxis_title="Win Rate (%)",
        yaxis_range=[0, 100],
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_correlations_chart(stats: Dict[str, Any]):
    """Horizontal bar chart of correlations sorted by |corr|."""
    metrics = ["MxV", "RunUp", "ATRX", "RSI", "TypicalPriceDist", "ScanChange", "REL_VOL"]
    pairs = []
    for m in metrics:
        val = stats.get(f"Corr_{m}")
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                continue
            pairs.append((m, f))
        except (TypeError, ValueError):
            continue

    if not pairs:
        st.info("No correlation data available yet.")
        return

    # Sort by absolute correlation
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    names = [p[0] for p in pairs]
    values = [p[1] for p in pairs]

    fig = go.Figure(data=[go.Bar(
        x=values, y=names, orientation="h",
        text=[f"{v:.2f}" for v in values],
        textposition="auto",
        marker_color=["#6BCB77" if v > 0 else "#FF6B6B" for v in values],
    )])
    fig.update_layout(
        xaxis_title="Pearson Correlation with PnL%",
        yaxis_title="Metric",
        xaxis_range=[-1, 1],
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_recommendation(stats: Dict[str, Any]):
    """Pipe-separated recommendation, parsed into sections."""
    rec = stats.get("Recommendation", "")
    if not rec:
        st.info("No recommendation yet.")
        return

    parts = [p.strip() for p in rec.split("|") if p.strip()]

    # Surprise finding
    surprise = stats.get("SurpriseFinding", "")
    if surprise and surprise != "No surprises this period":
        st.warning(f"⚠️ **Surprise:** {surprise}")

    for part in parts:
        if part.startswith("PRIMARY:"):
            st.success(f"🎯 **{part}**")
        elif part.startswith("SECONDARY:"):
            st.info(f"📊 **{part}**")
        elif part.startswith("ACTION:"):
            st.markdown(f"💡 **{part}**")
        else:
            st.markdown(part)


def _render_pending_suggestions():
    """Table of pending suggestions with approve/reject buttons."""
    df = load_pending_suggestions()

    if df.empty:
        st.info("No pending suggestions. Score Analytics generates suggestions weekly (Saturday 18:00 Peru).")
        return

    st.caption(f"{len(df)} suggestion(s) awaiting review")

    for idx, row in df.iterrows():
        sug_id = row.get("SuggestionID", "")
        sug_type = row.get("Type", "")
        description = row.get("Description", "")
        reasoning = row.get("Reasoning", "")
        confidence = row.get("Confidence", "")
        sample_size = row.get("SampleSize", "")

        with st.expander(f"📌 [{sug_type}] {description}", expanded=False):
            st.markdown(f"**Reasoning:** {reasoning}")
            st.caption(f"Confidence: {confidence} · Sample size: {sample_size} · ID: {sug_id}")

            col1, col2, col3 = st.columns([1, 1, 4])

            if col1.button("✅ Approve", key=f"approve_{idx}_{sug_id}"):
                if update_suggestion_status(sug_id, "APPROVED", "user_approved_via_dashboard"):
                    st.success(f"Approved: {sug_id}")
                    st.rerun()
                else:
                    st.error("Failed to update suggestion.")

            if col2.button("❌ Reject", key=f"reject_{idx}_{sug_id}"):
                if update_suggestion_status(sug_id, "REJECTED", "user_rejected_via_dashboard"):
                    st.success(f"Rejected: {sug_id}")
                    st.rerun()
                else:
                    st.error("Failed to update suggestion.")
