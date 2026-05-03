"""
Data Quality Monitor — validates signal data before scoring/trading.

Catches corrupted, stale, or suspicious data from FINVIZ/Alpaca/yfinance
before it reaches the decision engine. Does NOT reject signals — only
flags them with a quality_score. The decision_logic module decides
whether to SKIP based on quality_score threshold.

5 quality checks:
1. ATRX > 50 — suspiciously high volatility (likely data error)
2. Change > 200% — extreme move (possible corporate action / bad data)
3. RSI outside 0-100 — broken indicator
4. Price < $0.01 — sub-penny / likely delisted
5. Volume negative or None — broken data feed

Used by: decision_logic.py (M3)
"""

from typing import Any


# Thresholds for quality checks
QUALITY_RULES = {
    "atrx_max_reasonable": 50.0,
    "change_pct_max": 200.0,
    "rsi_min": 0.0,
    "rsi_max": 100.0,
    "price_min": 0.01,
}


def validate(metrics: dict[str, Any]) -> dict:
    """
    Validate signal data quality.

    Args:
        metrics: dict containing at minimum:
            - atrx: float
            - change: float (percent)
            - rsi: float
            - price: float
            - volume: int/float

    Returns:
        dict with:
            - is_trustworthy: bool (True if quality_score >= 0.5)
            - quality_score: float 0.0-1.0 (starts at 1.0, -0.25 per flag)
            - flags: list[str] (names of failed checks)
            - flag_details: dict[str, str] (explanation per flag)
    """
    flags = []
    flag_details = {}

    # Check 1: ATRX suspiciously high
    atrx = metrics.get("atrx")
    if atrx is not None:
        try:
            if float(atrx) > QUALITY_RULES["atrx_max_reasonable"]:
                flags.append("SUSPICIOUS_ATRX")
                flag_details["SUSPICIOUS_ATRX"] = (
                    f"ATRX={atrx} exceeds max reasonable {QUALITY_RULES['atrx_max_reasonable']}"
                )
        except (TypeError, ValueError):
            flags.append("SUSPICIOUS_ATRX")
            flag_details["SUSPICIOUS_ATRX"] = f"ATRX not numeric: {atrx!r}"

    # Check 2: Change% extremely high
    change = metrics.get("change")
    if change is not None:
        try:
            if float(change) > QUALITY_RULES["change_pct_max"]:
                flags.append("SUSPICIOUS_CHANGE")
                flag_details["SUSPICIOUS_CHANGE"] = (
                    f"Change={change}% exceeds max {QUALITY_RULES['change_pct_max']}%"
                )
        except (TypeError, ValueError):
            flags.append("SUSPICIOUS_CHANGE")
            flag_details["SUSPICIOUS_CHANGE"] = f"Change not numeric: {change!r}"

    # Check 3: RSI outside valid range
    rsi = metrics.get("rsi")
    if rsi is not None:
        try:
            rsi_val = float(rsi)
            if rsi_val < QUALITY_RULES["rsi_min"] or rsi_val > QUALITY_RULES["rsi_max"]:
                flags.append("INVALID_RSI")
                flag_details["INVALID_RSI"] = (
                    f"RSI={rsi_val} outside valid range [0, 100]"
                )
        except (TypeError, ValueError):
            flags.append("INVALID_RSI")
            flag_details["INVALID_RSI"] = f"RSI not numeric: {rsi!r}"

    # Check 4: Price below minimum
    price = metrics.get("price")
    if price is not None:
        try:
            if float(price) < QUALITY_RULES["price_min"]:
                flags.append("INVALID_PRICE")
                flag_details["INVALID_PRICE"] = (
                    f"Price=${price} below minimum ${QUALITY_RULES['price_min']}"
                )
        except (TypeError, ValueError):
            flags.append("INVALID_PRICE")
            flag_details["INVALID_PRICE"] = f"Price not numeric: {price!r}"
    else:
        flags.append("INVALID_PRICE")
        flag_details["INVALID_PRICE"] = "Price is None/missing"

    # Check 5: Volume broken
    volume = metrics.get("volume")
    if volume is None:
        flags.append("INVALID_VOLUME")
        flag_details["INVALID_VOLUME"] = "Volume is None/missing"
    else:
        try:
            if float(volume) < 0:
                flags.append("INVALID_VOLUME")
                flag_details["INVALID_VOLUME"] = f"Volume={volume} is negative"
        except (TypeError, ValueError):
            flags.append("INVALID_VOLUME")
            flag_details["INVALID_VOLUME"] = f"Volume not numeric: {volume!r}"

    # Calculate quality score
    quality_score = max(0.0, 1.0 - len(flags) * 0.25)

    return {
        "is_trustworthy": quality_score >= 0.5,
        "quality_score": quality_score,
        "flags": flags,
        "flag_details": flag_details,
    }
