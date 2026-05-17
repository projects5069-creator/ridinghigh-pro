"""
Critic Agent — reviews completed trades and produces factual summaries.

Reads paper_portfolio + decision_log to assess each closed trade's
outcome, then generates win/loss stats split by data quality.
"""
from agent.critic.critic_v1 import CriticAgent

__all__ = ["CriticAgent"]
