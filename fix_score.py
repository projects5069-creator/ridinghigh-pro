#!/usr/bin/env python3
"""
Replaces calculate_score() in auto_scanner.py with fixed version.
Fixes: ATRX formula, Gap direction, Float% removed, PriceToHigh direction.
"""

import re

path = '/Users/adilevy/RidingHighPro/auto_scanner.py'

OLD = '''def calculate_score(metrics):
    score = 0
    try:
        if metrics['mxv'] < 0:
            score += min(abs(metrics['mxv']) / 50, 1) * 20
    except: pass
    try:
        if metrics['price_to_52w_high'] > 0:
            score += min(metrics['price_to_52w_high'] / 100, 1) * 10
    except: pass
    try:
        if metrics['price_to_high'] < 0:
            score += min(abs(metrics['price_to_high']) / 10, 1) * 15
    except: pass
    try:
        score += min(metrics['rel_vol'] / 2, 1) * 15
    except: pass
    try:
        if metrics['rsi'] > 80: score += 15
        else: score += (metrics['rsi'] / 80) * 15
    except: pass
    try:
        score += min(metrics['atrx'] / 15, 1) * 10
    except: pass
    try:
        if metrics['run_up'] > 0:
            score += min(metrics['run_up'] / 50, 1) * 5
    except: pass
    try:
        score += min(metrics['float_pct'] / 10, 1) * 5
    except: pass
    try:
        score += min(abs(metrics['gap']) / 20, 1) * 3
    except: pass
    try:
        score += min(abs(metrics['vwap_dist']) / 15, 1) * 2
    except: pass
    return round(score, 2)'''

NEW = '''def calculate_score(metrics):
    score = 0

    # MxV — 20% — more negative = stronger pump signal
    try:
        if metrics['mxv'] < 0:
            score += min(abs(metrics['mxv']) / 50, 1) * 20
    except: pass

    # PriceTo52WHigh — 10% — above 52w high = extended
    try:
        if metrics['price_to_52w_high'] > 0:
            score += min(metrics['price_to_52w_high'] / 100, 1) * 10
    except: pass

    # PriceToHigh — 10% — FIXED: reward stocks NEAR intraday high (still pumping)
    try:
        if metrics['price_to_high'] > -10:
            score += min((10 + metrics['price_to_high']) / 10, 1) * 10
    except: pass

    # REL_VOL — 15% — higher relative volume = more unusual activity
    try:
        score += min(metrics['rel_vol'] / 2, 1) * 15
    except: pass

    # RSI — 10% — overbought = short candidate
    try:
        if metrics['rsi'] > 80: score += 10
        else: score += (metrics['rsi'] / 80) * 10
    except: pass

    # ATRX — 15% — FIXED: today's range / ATR = how many times bigger than normal
    try:
        score += min(metrics['atrx'] / 3, 1) * 15
    except: pass

    # RunUp — 15% — FIXED: reward stocks that rose from open (pump in progress)
    try:
        if metrics['run_up'] > 0:
            score += min(metrics['run_up'] / 50, 1) * 15
    except: pass

    # Float% — REMOVED (was volume/shares, not real float%)

    # Gap — 5% — FIXED: small gap = no catalyst = better short
    try:
        if metrics['gap'] < 15:
            score += min((15 - metrics['gap']) / 15, 1) * 5
    except: pass

    # VWAP — 5% — price above VWAP = extended
    try:
        if metrics['vwap_dist'] > 0:
            score += min(metrics['vwap_dist'] / 15, 1) * 5
    except: pass

    return round(score, 2)'''

with open(path, 'r') as f:
    content = f.read()

if OLD not in content:
    print("❌ לא מצאתי את הפונקציה המקורית — בדוק שהקובץ נכון")
else:
    new_content = content.replace(OLD, NEW)
    with open(path, 'w') as f:
        f.write(new_content)
    print("✅ calculate_score() עודכן בהצלחה!")
    print("\nאימות — הפונקציה החדשה:")
    import subprocess
    result = subprocess.run(['sed', '-n', '172,225p', path], capture_output=True, text=True)
    print(result.stdout)
