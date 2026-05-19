"""
agent/sentinel/shadow_audit_v1.py
──────────────────────────────────
Shadow audit (read-only): runs every Sentinel check against TODAY's real
latest scan from timeline_live + real account_state, and reports the
would-be BLOCK/WARN/ALLOW distribution. Used to measure the real
false-positive BLOCK rate before switching SENTINEL_MODE shadow→active.

Does NOT modify config, check code, Sheets, or SENTINEL_MODE.
Run: python3 -m agent.sentinel.shadow_audit_v1
"""
import sys, os
from collections import Counter
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PERU = pytz.timezone("America/Lima")


def main():
    print("=" * 70)
    print("SENTINEL SHADOW AUDIT v1 —", datetime.now(PERU).strftime("%Y-%m-%d %H:%M Peru"))
    print("=" * 70)

    # 1. Real signals from today's latest scan (production code path)
    from agent.orchestrator import read_latest_signals, build_account_state
    signals = read_latest_signals()
    print(f"\nסיגנלים בסריקה האחרונה היום: {len(signals)}")
    if not signals:
        print("אין סיגנלים — אי אפשר לבצע audit. (השוק פתוח? יש סריקה היום?)")
        return 1

    # 2. Real data_provider for price_freshness / heartbeat
    data_provider = None
    try:
        from data_provider import get_data_provider
        data_provider = get_data_provider()
        print("data_provider: זמין")
    except Exception as e:
        print(f"data_provider: לא זמין ({e}) — price_freshness יחזיר WARN")
    market_state = {"data_provider": data_provider}

    # 3. Per-signal checks
    from agent.sentinel.checks.completeness import check_completeness
    from agent.sentinel.checks.scan_freshness import check_scan_freshness
    from agent.sentinel.checks.price_sanity import check_price_sanity
    from agent.sentinel.checks.price_freshness import check_price_freshness

    per_signal = [
        ("completeness", check_completeness),
        ("scan_freshness", check_scan_freshness),
        ("price_sanity", check_price_sanity),
        ("price_freshness", check_price_freshness),
    ]

    overall = Counter()          # worst decision per signal
    by_check = {n: Counter() for n, _ in per_signal}
    block_reasons = Counter()
    warn_reasons = Counter()
    block_examples = []

    for sig in signals:
        worst = "ALLOW"
        worst_reason = "OK"
        worst_check = "-"
        for cname, cfn in per_signal:
            try:
                r = cfn(sig, market_state)
                by_check[cname][r.decision] += 1
                if r.decision == "BLOCK":
                    if worst != "BLOCK":
                        worst, worst_reason, worst_check = "BLOCK", r.reason, cname
                    block_reasons[f"{cname}:{r.reason}"] += 1
                elif r.decision == "WARN":
                    warn_reasons[f"{cname}:{r.reason}"] += 1
                    if worst == "ALLOW":
                        worst, worst_reason, worst_check = "WARN", r.reason, cname
            except Exception as e:
                by_check[cname]["ERROR"] += 1
        overall[worst] += 1
        if worst == "BLOCK" and len(block_examples) < 8:
            block_examples.append((sig.get("ticker", "?"), worst_check, worst_reason,
                                   sig.get("price"), sig.get("scan_time")))

    # 4. System-level checks (once)
    print("\n── בדיקות מערכת ──")
    try:
        acct = build_account_state()
        today_enters = acct.get("cold_start_daily_used", 0)
        from agent.sentinel.checks.position_sync import check_position_sync
        from agent.sentinel.checks.quota_health import check_quota_health
        from agent.sentinel.checks.provider_heartbeat import check_provider_heartbeat
        ps = check_position_sync(acct, today_enters=today_enters)
        qh = check_quota_health()
        ph = check_provider_heartbeat(market_state)
        print(f"  position_sync     : {ps.decision:<6} ({ps.reason})")
        print(f"  quota_health      : {qh.decision:<6} ({qh.reason})")
        print(f"  provider_heartbeat: {ph.decision:<6} ({ph.reason})")
    except Exception as e:
        print(f"  שגיאה בבדיקות מערכת: {e}")

    # 5. Report
    n = len(signals)
    blocks = overall.get("BLOCK", 0)
    warns = overall.get("WARN", 0)
    allows = overall.get("ALLOW", 0)
    block_pct = blocks / n * 100 if n else 0

    print("\n" + "=" * 70)
    print(f"חלוקת החלטות על {n} סיגנלים אמיתיים (worst per signal):")
    print(f"  ALLOW: {allows:>4}  ({allows/n*100:.1f}%)")
    print(f"  WARN : {warns:>4}  ({warns/n*100:.1f}%)")
    print(f"  BLOCK: {blocks:>4}  ({block_pct:.1f}%)")

    print("\nפירוט לפי בדיקה (decision: count):")
    for cname, _ in per_signal:
        print(f"  {cname:<18}: {dict(by_check[cname])}")

    if block_reasons:
        print("\nסיבות BLOCK:")
        for reason, cnt in block_reasons.most_common():
            print(f"  {reason}: {cnt}")
    if warn_reasons:
        print("\nסיבות WARN:")
        for reason, cnt in warn_reasons.most_common():
            print(f"  {reason}: {cnt}")
    if block_examples:
        print("\nדוגמאות BLOCK (ticker, check, reason, price, scan_time):")
        for ex in block_examples:
            print(f"  {ex}")

    print("\n" + "=" * 70)
    print(f"שיעור BLOCK: {block_pct:.1f}%  (סף PK ל-active: < 5%)")
    if block_pct < 5:
        print("מסקנה: שיעור ה-BLOCK מתחת ל-5% — בטוח לשקול מעבר ל-active.")
    else:
        print("מסקנה: שיעור ה-BLOCK מעל 5% — לבדוק איזו בדיקה/סף אחראי לפני active.")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
