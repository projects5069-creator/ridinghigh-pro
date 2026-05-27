"""Unit tests for RiskSentinel v1 (daily P&L floor + buying-power buffer).

Self-contained — no live data/Sheets. Run: python3 test_risk_sentinel.py
"""
from types import SimpleNamespace
from datetime import datetime

import pytz

from agent.sentinel.risk_sentinel import RiskSentinel

PERU_TZ = pytz.timezone("America/Lima")
TODAY = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
CFG = SimpleNamespace(AGENT_COLD_START_DAILY_LOSS_ALERT_USD=200)


def _rs():
    return RiskSentinel(CFG)


# ── CHECK 4: daily realized P&L floor ──────────────────────────────────
def test_daily_loss_blocks_below_floor():
    pf = [{"Status": "SL_HIT", "ExitDate": TODAY, "RealizedPnL": -250}]
    r = _rs().check_entry("ABC", {"buying_power": 200000}, pf)
    assert r.allow is False and "DAILY_LOSS" in r.reason


def test_daily_loss_allows_above_floor():
    pf = [{"Status": "SL_HIT", "ExitDate": TODAY, "RealizedPnL": -150}]
    r = _rs().check_entry("ABC", {"buying_power": 200000}, pf)
    assert r.allow is True


def test_daily_loss_sums_today_only():
    pf = [
        {"Status": "SL_HIT", "ExitDate": "2026-01-01", "RealizedPnL": -999},  # other day, ignored
        {"Status": "TP_HIT", "ExitDate": TODAY, "RealizedPnL": -120},
        {"Status": "EOD_CLOSE", "ExitDate": TODAY, "RealizedPnL": -100},
    ]
    r = _rs().check_entry("ABC", {"buying_power": 200000}, pf)
    assert r.allow is False and "DAILY_LOSS" in r.reason  # today = -220 < -200


def test_daily_loss_ignores_open_positions():
    pf = [{"Status": "OPEN", "ExitDate": "", "UnrealizedPnL": -999, "EntryPrice": 10, "Quantity": 100}]
    r = _rs().check_entry("ABC", {"buying_power": 200000}, pf)
    assert r.allow is True  # open positions don't count as realized


# ── CHECK 5: buying-power buffer ───────────────────────────────────────
def test_buying_power_blocks_low_buffer():
    pf = [{"Status": "OPEN", "EntryPrice": 100, "Quantity": 100}]  # $10,000 deployed
    r = _rs().check_entry("ABC", {"buying_power": 500}, pf)        # 500/10500 = 4.8%
    assert r.allow is False and "BUYING_POWER" in r.reason


def test_buying_power_allows_high_buffer():
    pf = [{"Status": "OPEN", "EntryPrice": 10, "Quantity": 100}]   # $1,000 deployed
    r = _rs().check_entry("ABC", {"buying_power": 200000}, pf)
    assert r.allow is True


# ── edge cases ─────────────────────────────────────────────────────────
def test_allows_empty_portfolio():
    r = _rs().check_entry("ABC", {"buying_power": 200000}, [])
    assert r.allow is True


def test_allows_when_no_buying_power_field():
    r = _rs().check_entry("ABC", {}, [])
    assert r.allow is True  # account_value <= 0 -> skip buffer check


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception:
            print(f"  ❌ {t.__name__}")
            traceback.print_exc()
    print(f"\nResults: {passed}/{len(tests)} passed")
    raise SystemExit(0 if passed == len(tests) else 1)
