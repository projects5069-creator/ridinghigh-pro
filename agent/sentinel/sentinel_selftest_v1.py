"""
agent/sentinel/sentinel_selftest_v1.py
───────────────────────────────────────
Sentinel self-test harness (read-only, no side effects).
Feeds every check valid + intentionally-corrupted data and verifies
the returned decision matches expectation. Required by PK v2.18 before
switching SENTINEL_MODE shadow→active.

Does NOT touch config, check code, Sheets, or SENTINEL_MODE.
Run: python3 -m agent.sentinel.sentinel_selftest_v1
"""
import sys, os, time
from datetime import datetime, timedelta
import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PERU = pytz.timezone("America/Lima")

# ── fake data_provider injected via market_state ──────────────────
class _GoodProvider:
    def get_latest_bar(self, ticker):
        return {"open": 10.0, "high": 10.5, "low": 9.8, "close": 10.0}

class _DeadProvider:
    def get_latest_bar(self, ticker):
        raise RuntimeError("simulated provider outage")

def _scan_time_minutes_ago(mins):
    t = datetime.now(PERU) - timedelta(minutes=mins)
    return t.strftime("%H:%M")

# ── test runner ───────────────────────────────────────────────────
RESULTS = []

def _run(name, expected, fn):
    try:
        res = fn()
        got = res.decision
        ok = (got == expected)
    except Exception as e:
        got = f"EXCEPTION: {e}"
        ok = False
    RESULTS.append((name, expected, got, ok))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name:<38} expected={expected:<6} got={got}")

def main():
    print("=" * 68)
    print("SENTINEL SELF-TEST v1 —", datetime.now(PERU).strftime("%Y-%m-%d %H:%M Peru"))
    print("=" * 68)

    from agent.sentinel.checks.completeness import check_completeness
    from agent.sentinel.checks.price_sanity import check_price_sanity
    from agent.sentinel.checks.price_freshness import check_price_freshness, clear_cache
    from agent.sentinel.checks.scan_freshness import check_scan_freshness
    from agent.sentinel.checks.position_sync import check_position_sync
    from agent.sentinel.checks import provider_heartbeat as ph
    from agent.sentinel.checks import quota_health as qh

    good_signal = {"ticker": "TEST", "score": 75, "price": 5.0,
                   "mxv": -200, "run_up": 12.0, "atrx": 1.5, "rsi": 88,
                   "high": 5.2, "low": 4.8,
                   "scan_time": _scan_time_minutes_ago(1)}
    good_ms = {"data_provider": _GoodProvider()}

    print("\n── completeness ──")
    _run("completeness / valid", "ALLOW",
         lambda: check_completeness(good_signal, {}))
    bad = dict(good_signal); bad.pop("mxv")
    _run("completeness / missing mxv", "BLOCK",
         lambda: check_completeness(bad, {}))

    print("\n── price_sanity ──")
    _run("price_sanity / valid", "ALLOW",
         lambda: check_price_sanity(good_signal, {}))
    bad = dict(good_signal); bad["price"] = 50000.0; bad["high"] = 50001; bad["low"] = 49999
    _run("price_sanity / price 50000", "BLOCK",
         lambda: check_price_sanity(bad, {}))
    bad = dict(good_signal); bad["high"] = 4.0; bad["low"] = 6.0
    _run("price_sanity / OHLC inverted", "BLOCK",
         lambda: check_price_sanity(bad, {}))

    print("\n── price_freshness ──")
    clear_cache()
    _run("price_freshness / valid (delta~0)", "ALLOW",
         lambda: check_price_freshness({"ticker": "TEST", "price": 10.0}, good_ms))
    clear_cache()
    _run("price_freshness / delta 10%", "WARN",
         lambda: check_price_freshness({"ticker": "TEST", "price": 11.0}, good_ms))
    clear_cache()

    print("\n── scan_freshness ──")
    _run("scan_freshness / valid (1 min)", "ALLOW",
         lambda: check_scan_freshness({"ticker": "TEST", "scan_time": _scan_time_minutes_ago(1)}, {}))
    _run("scan_freshness / aging (7 min)", "WARN",
         lambda: check_scan_freshness({"ticker": "TEST", "scan_time": _scan_time_minutes_ago(7)}, {}))
    _run("scan_freshness / stale (12 min)", "BLOCK",
         lambda: check_scan_freshness({"ticker": "TEST", "scan_time": _scan_time_minutes_ago(12)}, {}))

    print("\n── position_sync ──")
    _run("position_sync / valid (3 ent, 3 open)", "ALLOW",
         lambda: check_position_sync({"open_position_count": 3}, today_enters=3))
    _run("position_sync / 3 ent, 0 open", "BLOCK",
         lambda: check_position_sync({"open_position_count": 0}, today_enters=3))

    print("\n── provider_heartbeat ──")
    ph.reset()
    _run("provider_heartbeat / alive", "ALLOW",
         lambda: ph.check_provider_heartbeat({"data_provider": _GoodProvider()}))
    ph.reset()
    dead_ms = {"data_provider": _DeadProvider()}
    ph.check_provider_heartbeat(dead_ms)
    ph.check_provider_heartbeat(dead_ms)
    _run("provider_heartbeat / 3 failures", "BLOCK",
         lambda: ph.check_provider_heartbeat(dead_ms))
    ph.reset()

    print("\n── quota_health ──")
    qh.reset()
    for _ in range(10): qh.record_write()
    _run("quota_health / 10 writes", "ALLOW",
         lambda: qh.check_quota_health())
    qh.reset()
    for _ in range(65): qh.record_write()
    _run("quota_health / 65 writes", "BLOCK",
         lambda: qh.check_quota_health())
    qh.reset()

    print("\n" + "=" * 68)
    total = len(RESULTS)
    passed = sum(1 for _, _, _, ok in RESULTS if ok)
    block_ok = sum(1 for _, exp, got, ok in RESULTS if exp == "BLOCK" and ok)
    print(f"RESULT: {passed}/{total} tests passed | {block_ok} checks fire BLOCK correctly")
    if passed == total:
        print("STATUS: ALL PASS — Sentinel checks verified.")
    else:
        print("STATUS: FAILURES PRESENT — do NOT switch to active.")
        for name, exp, got, ok in RESULTS:
            if not ok:
                print(f"  FAILED: {name} (expected {exp}, got {got})")
    print("=" * 68)
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
