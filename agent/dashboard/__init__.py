"""
agent/dashboard package
────────────────────────
Streamlit dashboard pages for the agent.

Page 9 (Live Agent): operational view of agent state.
Page 10 (Score Brain): analytical view of score performance.

Both pages registered in main dashboard.py via the navigation radio.
"""

from agent.dashboard.live_agent_page import render_live_agent
from agent.dashboard.score_brain_page import render_score_brain

__all__ = ["render_live_agent", "render_score_brain"]
