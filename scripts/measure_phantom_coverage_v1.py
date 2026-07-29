#!/usr/bin/env python3
"""
measure_phantom_coverage_v1.py — TASK-240 / TASK-241 measurement, READ-ONLY
──────────────────────────────────────────────────────────────────────────
Quantifies the unsupervised 2026-07-05 → 2026-07-28 window: how far the finviz
doubled-letter ticker corruption (TASK-238) spread, whether daily coverage has
holes, whether MxV — the only live gate signal — was collected complete, and
what the 83 open paper positions actually are.

Hard rules this script obeys:
  • READ-ONLY. No ws.update, no append, no Drive write. Ever.
  • ONE get_all_values per (tab, month). Results are cached to a local JSON
    snapshot so repeated subcommand invocations cost zero extra Sheets reads —
    iterating reads is what produces the 429 storms.
  • Header-aware only. Columns are resolved by name; a missing name prints
    COL_NOT_FOUND=<name> and the affected metric is skipped. Never guess an
    index — the paper_portfolio 2026-07 misalignment (TASK-217) came from
    positional writes.
  • Trading days come from utils.is_trading_day (holiday-aware), never
    weekday() < 5.

Phantom detection is deliberately reported at two levels, never merged:
  CANDIDATE = ticker[0] == ticker[1]. This also catches legitimate symbols
              (AAPL, AA, LLY), so it is an upper bound, not an answer.
  CONFIRMED = CANDIDATE and ticker[1:] appears as a real ticker elsewhere in
              the data. That is the doubled-first-letter signature.

Usage:
    python3 scripts/measure_phantom_coverage_v1.py --headers
    python3 scripts/measure_phantom_coverage_v1.py --phantom
    python3 scripts/measure_phantom_coverage_v1.py --coverage
    python3 scripts/measure_phantom_coverage_v1.py --metrics
    python3 scripts/measure_phantom_coverage_v1.py --positions
    python3 scripts/measure_phantom_coverage_v1.py --decisions
    python3 scripts/measure_phantom_coverage_v1.py --refresh   # drop the cache
"""

import argparse
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config          # noqa: E402
import sheets_manager  # noqa: E402
import utils           # noqa: E402

MONTH = "2026-07"
WINDOW_START = date(2026, 7, 5)
WINDOW_END = date(2026, 7, 28)

TABS = ["post_analysis", "daily_snapshots", "paper_portfolio", "decision_log"]

CACHE_PATH = os.path.join(tempfile.gettempdir(), "rh_measure_cache_2026-07.json")

_MEM = {}


# ── batched, cached reads ─────────────────────────────────────────────────────

def _load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)


def read_all():
    """Return {tab: [[...]]}. Exactly one Sheets read per tab, then cached."""
    global _MEM
    if _MEM:
        return _MEM

    cache = _load_cache()
    missing = [t for t in TABS if t not in cache]

    if missing:
        gc = sheets_manager._get_gc()
        if gc is None:
            print("FATAL: no Google credentials")
            sys.exit(1)
        for tab in missing:
            try:
                ws = sheets_manager.get_worksheet(tab, month=MONTH, gc=gc)
                cache[tab] = ws.get_all_values() if ws is not None else []
                print(f"  READ / {tab} / {len(cache[tab])} row(s) incl. header")
            except Exception as exc:
                print(f"  READ / {tab} / FAIL: {exc}")
                cache[tab] = []
        _save_cache(cache)
        print(f"  CACHE / {CACHE_PATH} / written ({len(TABS)} tab(s))")

    _MEM = cache
    return _MEM


def col(header, *names):
    """Resolve the first matching column name. None + a printed note if absent."""
    for name in names:
        if name in header:
            return header.index(name)
    print(f"  COL_NOT_FOUND={names[0]}  (tried {list(names)})")
    return None


def rows_of(tab):
    data = read_all().get(tab, [])
    if not data:
        return [], []
    return data[0], data[1:]


# ── phantom classification ────────────────────────────────────────────────────

def _all_tickers():
    """Every ticker string seen anywhere in the four tabs, for the CONFIRMED test."""
    seen = set()
    for tab in TABS:
        header, rows = rows_of(tab)
        if not header:
            continue
        idx = None
        for name in ("Ticker", "ticker", "Symbol"):
            if name in header:
                idx = header.index(name)
                break
        if idx is None:
            continue
        for r in rows:
            if len(r) > idx:
                t = r[idx].strip().upper()
                if t:
                    seen.add(t)
    return seen


def classify(ticker, universe):
    """Return 'CONFIRMED' | 'CANDIDATE' | 'CLEAN'."""
    t = (ticker or "").strip().upper()
    if len(t) < 2 or t[0] != t[1]:
        return "CLEAN"
    return "CONFIRMED" if t[1:] in universe else "CANDIDATE"


# ── subcommands ───────────────────────────────────────────────────────────────

def cmd_headers():
    for tab in TABS:
        header, rows = rows_of(tab)
        print(f"\n--- {tab} ({MONTH}) — {len(rows)} data row(s), {len(header)} column(s)")
        for i, h in enumerate(header):
            print(f"   [{i:>2}] {h!r}")


def cmd_phantom():
    universe = _all_tickers()
    print(f"UNIVERSE_DISTINCT_TICKERS={len(universe)}")

    detail = defaultdict(lambda: {"count": 0, "dates": []})

    for tab, date_names in (("post_analysis", ("ScanDate", "Date", "scan_date")),
                            ("daily_snapshots", ("ScanDate", "Date", "scan_date"))):
        header, rows = rows_of(tab)
        print(f"\n--- {tab} ({MONTH}) ---")
        if not header:
            print("   EMPTY_OR_UNREADABLE")
            continue
        ti = col(header, "Ticker", "ticker", "Symbol")
        di = col(header, *date_names)
        if ti is None:
            continue

        per_day = defaultdict(lambda: Counter())
        for r in rows:
            if len(r) <= ti:
                continue
            tk = r[ti].strip().upper()
            day = r[di].strip()[:10] if (di is not None and len(r) > di) else "(no-date)"
            kind = classify(tk, universe)
            per_day[day]["total"] += 1
            if kind == "CANDIDATE":
                per_day[day]["candidate"] += 1
            elif kind == "CONFIRMED":
                per_day[day]["confirmed"] += 1
                d = detail[tk]
                d["count"] += 1
                d["dates"].append(day)

        print(f"   {'date':<12} {'total':>6} {'cand':>6} {'confirmed':>10} {'conf%':>7}")
        for day in sorted(per_day):
            c = per_day[day]
            pct = 100.0 * c["confirmed"] / c["total"] if c["total"] else 0.0
            print(f"   {day:<12} {c['total']:>6} {c['candidate']:>6} "
                  f"{c['confirmed']:>10} {pct:>6.1f}%")
        tot = sum(c["total"] for c in per_day.values())
        cnd = sum(c["candidate"] for c in per_day.values())
        cnf = sum(c["confirmed"] for c in per_day.values())
        print(f"   {'TOTAL':<12} {tot:>6} {cnd:>6} {cnf:>10} "
              f"{(100.0*cnf/tot if tot else 0):>6.1f}%")

    print(f"\n--- CONFIRMED distinct symbols ({len(detail)}) ---")
    print(f"   {'symbol':<10} {'stripped':<10} {'count':>6}  first_date   last_date")
    for sym in sorted(detail, key=lambda s: -detail[s]["count"]):
        d = detail[sym]
        days = sorted(x for x in d["dates"] if x and x != "(no-date)")
        print(f"   {sym:<10} {sym[1:]:<10} {d['count']:>6}  "
              f"{(days[0] if days else '-'):<12} {(days[-1] if days else '-')}")


def _window_trading_days():
    out, cur = [], WINDOW_START
    while cur <= WINDOW_END:
        if utils.is_trading_day(cur):
            out.append(cur.isoformat())
        cur = date.fromordinal(cur.toordinal() + 1)
    return out


def cmd_coverage():
    trading = _window_trading_days()
    print(f"TRADING_DAYS={len(trading)}  ({WINDOW_START} .. {WINDOW_END})")
    print(f"  {trading}")

    for tab in ("post_analysis", "daily_snapshots"):
        header, rows = rows_of(tab)
        print(f"\n--- {tab} ---")
        if not header:
            print("   EMPTY_OR_UNREADABLE")
            continue
        di = col(header, "ScanDate", "Date", "scan_date")
        if di is None:
            continue
        per_day = Counter()
        for r in rows:
            if len(r) > di and r[di].strip():
                per_day[r[di].strip()[:10]] += 1

        present = [d for d in trading if d in per_day]
        missing = [d for d in trading if d not in per_day]
        print(f"   PRESENT={len(present)}  MISSING={len(missing)}")
        print(f"   MISSING_DAYS={missing}")
        counts = [per_day[d] for d in present]
        if counts:
            counts_sorted = sorted(counts)
            med = counts_sorted[len(counts_sorted) // 2]
            thin = [d for d in present if per_day[d] < med * 0.5]
            print(f"   ROWS_PER_DAY median={med} min={min(counts)} max={max(counts)}")
            print(f"   THIN_DAYS(<50% of median)={thin}")
        print(f"   {'date':<12} rows")
        for d in trading:
            mark = "" if d in per_day else "   <-- MISSING"
            print(f"   {d:<12} {per_day.get(d, 0)}{mark}")
        outside = sorted(d for d in per_day if d not in set(trading))
        if outside:
            print(f"   DATES_OUTSIDE_WINDOW={outside}")


def cmd_metrics():
    header, rows = rows_of("post_analysis")
    print(f"--- post_analysis ({MONTH}) — MxV completeness ---")
    if not header:
        print("   EMPTY_OR_UNREADABLE")
        return
    di = col(header, "ScanDate", "Date", "scan_date")
    mi = col(header, "MxV", "MXV", "MxVolume")
    si = col(header, "Score")

    if mi is None:
        print("   cannot measure MxV — column absent")
    else:
        per_day = defaultdict(lambda: Counter())
        for r in rows:
            day = r[di].strip()[:10] if (di is not None and len(r) > di) else "(no-date)"
            v = r[mi].strip() if len(r) > mi else ""
            per_day[day]["rows"] += 1
            if v == "":
                per_day[day]["blank"] += 1
            else:
                per_day[day]["present"] += 1
                try:
                    if float(v) == 0.0:
                        per_day[day]["zero"] += 1
                except ValueError:
                    per_day[day]["nonnumeric"] += 1

        print(f"   {'date':<12} {'rows':>6} {'present':>8} {'blank':>6} {'zero':>6} "
              f"{'nonnum':>7} {'blank%':>7}")
        for day in sorted(per_day):
            c = per_day[day]
            pct = 100.0 * c["blank"] / c["rows"] if c["rows"] else 0.0
            print(f"   {day:<12} {c['rows']:>6} {c['present']:>8} {c['blank']:>6} "
                  f"{c['zero']:>6} {c['nonnumeric']:>7} {pct:>6.1f}%")
        tot = sum(c["rows"] for c in per_day.values())
        blk = sum(c["blank"] for c in per_day.values())
        print(f"   TOTAL rows={tot} blank={blk} blank_pct="
              f"{(100.0*blk/tot if tot else 0):.1f}%")

    print(f"\n--- SCORE_WRITE_FROZEN={config.SCORE_WRITE_FROZEN} "
          f"(expectation: Score column empty) ---")
    if si is None:
        print("   Score column absent — nothing to check")
    else:
        nonempty = [r[si].strip() for r in rows if len(r) > si and r[si].strip()]
        print(f"   rows_with_nonempty_Score={len(nonempty)} / {len(rows)}")
        if nonempty:
            print(f"   sample={nonempty[:10]}")


def _trading_days_between(d0, d1):
    if d0 > d1:
        return 0
    n, cur = 0, d0
    while cur <= d1:
        if utils.is_trading_day(cur):
            n += 1
        cur = date.fromordinal(cur.toordinal() + 1)
    return n


def cmd_positions():
    header, rows = rows_of("paper_portfolio")
    print(f"--- paper_portfolio ({MONTH}) — {len(rows)} data row(s) ---")
    if not header:
        print("   EMPTY_OR_UNREADABLE")
        return

    sti = col(header, "Status")
    tki = col(header, "Ticker")
    edi = col(header, "EntryDate")

    if sti is None:
        return
    print(f"   STATUS_DISTRIBUTION={dict(Counter(r[sti].strip() for r in rows if len(r) > sti))}")

    exit_cols = [h for h in header if h.lower().startswith("exit")]
    print(f"   EXIT_COLUMNS={exit_cols}")

    open_rows = [r for r in rows if len(r) > sti and r[sti].strip() == "DRY_RUN_OPEN"]
    print(f"   DRY_RUN_OPEN={len(open_rows)}")
    if not open_rows:
        return

    for h in exit_cols:
        i = header.index(h)
        blank = sum(1 for r in open_rows if len(r) <= i or not r[i].strip())
        print(f"   {h}: blank_in_open={blank}/{len(open_rows)}")

    universe = _all_tickers()
    today = utils.get_peru_time().date()
    max_hold = config.MAX_HOLDING_DAYS
    print(f"   MAX_HOLDING_DAYS(from config)={max_hold}  today={today}")

    per_date = Counter()
    ages, over, phantom_open, clean_open, cand_open = [], 0, [], [], []

    for r in open_rows:
        tk = r[tki].strip().upper() if (tki is not None and len(r) > tki) else ""
        ed = r[edi].strip()[:10] if (edi is not None and len(r) > edi) else ""
        per_date[ed] += 1
        try:
            d0 = datetime.strptime(ed, "%Y-%m-%d").date()
            age = _trading_days_between(d0, today) - 1  # entry day itself not held-through
        except ValueError:
            age = None
        if age is not None:
            ages.append(age)
            if age > max_hold:
                over += 1
        kind = classify(tk, universe)
        (phantom_open if kind == "CONFIRMED"
         else cand_open if kind == "CANDIDATE" else clean_open).append((tk, ed, age))

    print(f"\n   OPEN_BY_ENTRY_DATE:")
    for d in sorted(per_date):
        print(f"     {d or '(blank)':<12} {per_date[d]}")

    if ages:
        print(f"\n   AGE_IN_TRADING_DAYS min={min(ages)} max={max(ages)} "
              f"median={sorted(ages)[len(ages)//2]}")
    print(f"   OVER_MAX_HOLDING_DAYS={over}/{len(open_rows)}  "
          f"({100.0*over/len(open_rows):.1f}%)")

    print(f"\n   OPEN_ON_CONFIRMED_PHANTOM={len(phantom_open)}")
    for tk, ed, age in sorted(phantom_open):
        print(f"     {tk:<10} entry={ed} age_td={age}")
    print(f"   OPEN_ON_CANDIDATE_ONLY={len(cand_open)} "
          f"{sorted(set(t for t, _, _ in cand_open))}")
    print(f"   OPEN_ON_CLEAN_TICKER={len(clean_open)} "
          f"{sorted(set(t for t, _, _ in clean_open))}")


def cmd_decisions():
    header, rows = rows_of("decision_log")
    print(f"--- decision_log ({MONTH}) — {len(rows)} data row(s) ---")
    if not header:
        print("   EMPTY_OR_UNREADABLE")
        return

    ai = col(header, "Action", "Decision")
    # decision_log dates its rows via Timestamp, not a Date column.
    di = col(header, "Timestamp", "Date", "DecisionDate", "ScanDate")
    tki = col(header, "Ticker")
    if ai is None:
        return

    print(f"   ACTION_DISTRIBUTION="
          f"{dict(Counter(r[ai].strip() for r in rows if len(r) > ai))}")

    universe = _all_tickers()
    per_day = defaultdict(lambda: Counter())
    enter_phantom, enter_clean = [], []

    for r in rows:
        act = r[ai].strip().upper() if len(r) > ai else ""
        day = r[di].strip()[:10] if (di is not None and len(r) > di) else "(no-date)"
        per_day[day][act] += 1
        if act == "ENTER" and tki is not None and len(r) > tki:
            tk = r[tki].strip().upper()
            if classify(tk, universe) == "CONFIRMED":
                enter_phantom.append((day, tk))
            else:
                enter_clean.append((day, tk))

    print(f"\n   {'date':<12} {'ENTER':>6} {'SKIP':>6} {'other':>6}")
    for day in sorted(per_day):
        c = per_day[day]
        other = sum(v for k, v in c.items() if k not in ("ENTER", "SKIP"))
        print(f"   {day:<12} {c.get('ENTER', 0):>6} {c.get('SKIP', 0):>6} {other:>6}")

    total_enter = len(enter_phantom) + len(enter_clean)
    print(f"\n   ENTER_TOTAL={total_enter}")
    print(f"   ENTER_ON_CONFIRMED_PHANTOM={len(enter_phantom)} "
          f"({100.0*len(enter_phantom)/total_enter if total_enter else 0:.1f}%)")
    for day, tk in sorted(enter_phantom):
        print(f"     {day}  {tk}")


def main():
    p = argparse.ArgumentParser(description="TASK-240/241 read-only measurement")
    p.add_argument("--headers", action="store_true")
    p.add_argument("--phantom", action="store_true")
    p.add_argument("--coverage", action="store_true")
    p.add_argument("--metrics", action="store_true")
    p.add_argument("--positions", action="store_true")
    p.add_argument("--decisions", action="store_true")
    p.add_argument("--refresh", action="store_true", help="drop the local cache")
    a = p.parse_args()

    if a.refresh and os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
        print(f"CACHE_CLEARED {CACHE_PATH}")

    if a.headers:
        cmd_headers()
    if a.phantom:
        cmd_phantom()
    if a.coverage:
        cmd_coverage()
    if a.metrics:
        cmd_metrics()
    if a.positions:
        cmd_positions()
    if a.decisions:
        cmd_decisions()


if __name__ == "__main__":
    main()
