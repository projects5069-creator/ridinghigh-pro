#!/usr/bin/env python3
"""
Replaces calculate_score() in auto_scanner.py with final weights.
Removes: PriceToHigh, PriceTo52WHigh, Float%
Updates weights: MxV=30, RunUp=20, REL_VOL=20, RSI=10, ATRX=10, Gap=5, VWAP=5
"""

path = '/Users/adilevy/RidingHighPro/auto_scanner.py'

OLD = '''def calculate_score(metrics):
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

NEW = '''def calculate_score(metrics):
    score = 0

    # MxV — 30% — more negative = stronger pump signal
    try:
        if metrics['mxv'] < 0:
            score += min(abs(metrics['mxv']) / 50, 1) * 30
    except: pass

    # RunUp — 20% — rose from open = pump in progress
    try:
        if metrics['run_up'] > 0:
            score += min(metrics['run_up'] / 50, 1) * 20
    except: pass

    # REL_VOL — 20% — higher relative volume = more unusual activity
    try:
        score += min(metrics['rel_vol'] / 2, 1) * 20
    except: pass

    # RSI — 10% — overbought = short candidate
    try:
        if metrics['rsi'] > 80: score += 10
        else: score += (metrics['rsi'] / 80) * 10
    except: pass

    # ATRX — 10% — today range / ATR = how many times bigger than normal
    try:
        score += min(metrics['atrx'] / 3, 1) * 10
    except: pass

    # Gap — 5% — small gap = no catalyst = better short
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
    print("❌ לא מצאתי את הפונקציה — בדוק שהקובץ נכון")
else:
    new_content = content.replace(OLD, NEW)
    with open(path, 'w') as f:
        f.write(new_content)
    print("✅ calculate_score() עודכן בהצלחה!")
    import subprocess
    result = subprocess.run(['sed', '-n', '172,215p', path], capture_output=True, text=True)
    print(result.stdout)
