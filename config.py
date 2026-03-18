#!/usr/bin/env python3
"""
Configuration - משקולות וערכי סף
"""

# משקולות (ניקוד מקסימלי)
WEIGHTS = {
    'MXV': 30,
    'REL_VOL': 20,
    'ATRX': 15,
    'GAP': 10,
    'RUN_UP': 10,
    'VWAP': 10,
    'RSI': 5,
}

# ערכי סף
THRESHOLDS = {
    'REL_VOL': 0.5,
    'ATRX': 0.15,
    'GAP': 10,
    'RUN_UP': 5,
    'VWAP': 0.2,
    'RSI': 80,
}

# צבעים
COLORS = {
    'HOT': '#ff4444',
    'WARM': '#ffaa00',
    'COOL': '#4444ff',
}
