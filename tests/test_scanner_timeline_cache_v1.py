"""
test_scanner_timeline_cache_v1.py
──────────────────────────────────
TASK-58 Phase 2 (S1): the auto_scanner must read timeline_live through the
60s cache (get_sheet_values) instead of raw get_all_values, so the 4 reads
per run collapse to 2 (one pre-write, one post-write), with a MANDATORY
invalidate_cache("timeline_live") after the scan write.

Focused read-path test — no live FINVIZ / providers / Sheets. Stubs the
worksheet-open boundary and counts actual API fetches. Simulates the run
order: read@341 -> write+invalidate@421 -> read@522 -> read@744.

Run: python3 test_scanner_timeline_cache_v1.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (relocated to tests/)

import sheets_manager
from auto_scanner import _read_timeline_live  # RED until implemented

RESULTS = []


def _record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")


HEADER = ["Date", "ScanTime", "Ticker"]


def _install_fake(dataset, api_reads):
    """Stub get_worksheet to a fake ws that counts get_all_values calls.
    Uses the REAL get_sheet_values + cache. Returns restore()."""
    orig_gw = sheets_manager.get_worksheet

    class _FakeWS:
        def __init__(self, tab):
            self.tab = tab

        def get_all_values(self):
            api_reads[self.tab] = api_reads.get(self.tab, 0) + 1
            return [list(r) for r in dataset[self.tab]]

    sheets_manager.get_worksheet = lambda tab, month=None, gc=None: _FakeWS(tab)
    sheets_manager._sheet_values_cache.clear()
    return lambda: setattr(sheets_manager, "get_worksheet", orig_gw)


def test_timeline_read_path_two_reads_fresh():
    """read@341 -> write+invalidate@421 -> read@522 -> read@744:
    exactly 2 API reads; post-write reads see the new row; @744 is a cache hit."""
    api = {}
    data = {"timeline_live": [HEADER, ["2026-06-03", "9:00", "AAA"]]}
    restore = _install_fake(data, api)
    try:
        r1 = _read_timeline_live()                       # @341 (pre-write) — miss
        # @421: scanner appends this minute's row, then MUST invalidate
        data["timeline_live"].append(["2026-06-03", "9:01", "BBB"])
        sheets_manager.invalidate_cache("timeline_live")
        r2 = _read_timeline_live()                        # @522 (post-write) — miss (fresh)
        r3 = _read_timeline_live()                        # @744 — cache hit
    finally:
        restore()

    reads = api.get("timeline_live", 0)
    fresh = any("BBB" in row for row in r2)
    cache_hit = (r3 == r2)
    pre_write_no_bbb = not any("BBB" in row for row in r1)
    ok = reads == 2 and fresh and cache_hit and pre_write_no_bbb
    _record("timeline_read_path_two_reads_fresh", ok,
            f"api_reads={reads}, post_write_fresh={fresh}, cache_hit={cache_hit}")


def test_guard_missing_invalidate_is_stale():
    """Guard: WITHOUT invalidate after the write, the post-write read is a
    stale cache hit (misses this minute's row) and only 1 API read happens —
    proving invalidate-after-write is mandatory."""
    api = {}
    data = {"timeline_live": [HEADER, ["2026-06-03", "9:00", "AAA"]]}
    restore = _install_fake(data, api)
    try:
        _read_timeline_live()                             # miss
        data["timeline_live"].append(["2026-06-03", "9:01", "BBB"])
        # (intentionally NO invalidate)
        r_stale = _read_timeline_live()                   # cache hit -> stale
    finally:
        restore()
    reads = api.get("timeline_live", 0)
    is_stale = not any("BBB" in row for row in r_stale)
    ok = reads == 1 and is_stale  # demonstrates the failure mode
    _record("guard_missing_invalidate_is_stale", ok,
            f"api_reads={reads}, stale={is_stale}")


def run():
    print("=== test_scanner_timeline_cache_v1 ===")
    test_timeline_read_path_two_reads_fresh()
    test_guard_missing_invalidate_is_stale()
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f"\nResults: {passed}/{total} passed")
    if passed == total:
        print("✅ All scanner timeline-cache tests passed!")
        return 0
    print("❌ Some tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(run())
