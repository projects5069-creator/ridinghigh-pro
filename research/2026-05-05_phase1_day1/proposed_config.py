# Generated from data analysis on 2026-05-05
# Based on N=140 records (binary), LR CV AUC=0.537
# WARNING: Sample size too small for reliable thresholds. Use with extreme caution.

AGENT_MIN_SCORE = None      # Score AUC=0.489 — not predictive, do not filter
AGENT_MXV_MAX   = None      # MxV AUC=0.478 — not predictive
AGENT_RUNUP_MIN = None      # RunUp AUC=0.565, but p=0.21 — insufficient evidence
AGENT_RELVOL_MIN= 4.22      # REL_VOL AUC=0.576, best F1 threshold (weak)
AGENT_HOUR_RANGE= (8, 9)    # Hour 8 TP rate=57.1%, Hour 9 TP rate=33.3%
AGENT_MIN_MCAP  = None      # MarketCap — direction unclear (LR says smaller=better)
AGENT_ATRX_MIN  = 3.52      # ATRX AUC=0.609 (best univariate, p=0.062)

# Additional (if implemented):
AGENT_MAX_RSI   = None      # RSI AUC=0.432, lower RSI=more TP, but weak signal
AGENT_SL_PCT    = 7         # Current SL at 7% rise — consider raising to 10-12%
AGENT_TP_PCT    = 10        # TP at 10% drop — seems working (79% hit rate without SL)
