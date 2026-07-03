#!/usr/bin/env python3
"""TASK-62 + TASK-170 — unified closed-trade analysis (READ-ONLY, quota-cheap).

ONE batch read per (tab, month): paper_portfolio + decision_log, only for
months present in sheets_config (never auto-creates). In-memory join on
PositionID==DecisionID pulls MxV/ATRX (which live in decision_log, NOT
paper_portfolio). Then:

  PART 62  — win/loss segmentation of MxV & ATRX (mean+median+n).
  PART 170 — VIX-at-entry bucketed win-rate (<20 / 20-30 / >30).

VIX join is look-ahead-safe: uses the last ^VIX daily CLOSE strictly BEFORE
EntryDate (the close on the entry day is only known after entry). yfinance is
fetched ONCE for the whole date range. Raw output only — no verdict.
"""
import json
import os
import statistics as st
import sys
import time
from bisect import bisect_left

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sheets_manager as sm

CLOSED = {"CLOSED", "DRY_RUN_CLOSED"}
ALL_MONTHS = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]


def _num(x):
    """Parse a possibly-formatted numeric cell -> float or None."""
    if x is None:
        return None
    s = str(x).replace("$", "").replace(",", "").replace("%", "").strip()
    if s == "" or s.lower() in ("na", "none", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _read(tab, month, tries=3):
    for i in range(tries):
        try:
            return sm.get_sheet_records(tab, month=month) or []
        except Exception as e:
            if "429" in str(e) or "uota" in str(e).lower():
                wait = 5 * (2 ** i)  # 5,10,20
                sys.stderr.write(f"  [429] {tab} {month} -> backoff {wait}s\n")
                time.sleep(wait)
                continue
            sys.stderr.write(f"  [ERR] {tab} {month}: {type(e).__name__}: {str(e)[:60]}\n")
            return None
    sys.stderr.write(f"  [429] {tab} {month}: backoff exhausted -> STOP\n")
    return None


def main():
    cfg = json.load(open("sheets_config.json"))
    months = [m for m in ALL_MONTHS if m in cfg]

    pf, dl = [], []
    read_log = []
    for m in months:
        if "paper_portfolio" in cfg[m]:
            r = _read("paper_portfolio", m)
            if r is None:
                print(f"\n*** STOPPED on 429/err reading paper_portfolio {m}. Collected so far: pf={len(pf)} ***")
                return 2
            pf += r
            read_log.append(f"paper_portfolio {m}: {len(r)}")
            time.sleep(1.0)
        if "decision_log" in cfg[m]:
            r = _read("decision_log", m)
            if r is None:
                print(f"\n*** STOPPED on 429/err reading decision_log {m}. Collected so far: dl={len(dl)} ***")
                return 2
            dl += r
            read_log.append(f"decision_log {m}: {len(r)}")
            time.sleep(1.0)

    print("=== READ COVERAGE ===")
    for line in read_log:
        print("  " + line)
    print(f"  TOTAL: paper_portfolio={len(pf)} rows, decision_log={len(dl)} rows")

    # index decision_log by DecisionID -> MxV/ATRX
    dl_ix = {}
    for r in dl:
        did = str(r.get("DecisionID", "")).strip()
        if did:
            dl_ix[did] = r

    # closed trades
    closed = [r for r in pf if str(r.get("Status", "")).strip().upper() in CLOSED]
    matched, unmatched = [], 0
    for r in closed:
        pid = str(r.get("PositionID", "")).strip()
        d = dl_ix.get(pid)
        pnl = _num(r.get("RealizedPnL"))
        if d is None:
            unmatched += 1
            continue
        matched.append({
            "pid": pid,
            "pnl": pnl,
            "win": (pnl is not None and pnl > 0),
            "loss": (pnl is not None and pnl < 0),
            "mxv": _num(d.get("MxV")),
            "atrx": _num(d.get("ATRX")),
            "entry_date": str(r.get("EntryDate", "")).strip()[:10],
        })

    print(f"\n=== JOIN COVERAGE ===")
    print(f"  closed trades: {len(closed)}")
    print(f"  matched to decision_log: {len(matched)}")
    print(f"  unmatched (no decision_log row): {unmatched}")

    # ---- PART 62: win/loss MxV & ATRX ----
    def seg(rows, key):
        vals = [r[key] for r in rows if r[key] is not None]
        if not vals:
            return ("n=0", "-", "-")
        return (f"n={len(vals)}", round(st.mean(vals), 3), round(st.median(vals), 3))

    wins = [r for r in matched if r["win"]]
    losses = [r for r in matched if r["loss"]]
    print(f"\n=== PART 62 — per-trade MxV/ATRX by win/loss ===")
    print(f"  wins={len(wins)}  losses={len(losses)}  (zero/unparseable PnL excluded from both)")
    for metric in ("mxv", "atrx"):
        wn, wm, wmd = seg(wins, metric)
        ln, lm, lmd = seg(losses, metric)
        print(f"  {metric.upper():5} | WIN  {wn:<7} mean={wm} median={wmd}")
        print(f"  {metric.upper():5} | LOSS {ln:<7} mean={lm} median={lmd}")

    # ---- PART 170: VIX-at-entry bucket WR ----
    dated = [r for r in matched if r["entry_date"] and (r["win"] or r["loss"])]
    print(f"\n=== PART 170 — VIX-at-entry bucketed win-rate ===")
    if not dated:
        print("  no dated win/loss trades to bucket")
        _skills()
        return 0
    ds = sorted(r["entry_date"] for r in dated)
    lo, hi = ds[0], ds[-1]
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        start = (datetime.strptime(lo, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
        end = (datetime.strptime(hi, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
        h = yf.Ticker("^VIX").history(start=start, end=end)
        vix = [(idx.strftime("%Y-%m-%d"), float(row["Close"])) for idx, row in h.iterrows()]
    except Exception as e:
        print(f"  VIX fetch FAIL — {type(e).__name__}: {str(e)[:60]} (skipping 170)")
        _skills()
        return 0

    vdates = [d for d, _ in vix]

    def vix_before(entry):
        # last VIX close with date STRICTLY < entry (look-ahead safe)
        i = bisect_left(vdates, entry)
        return vix[i - 1][1] if i > 0 else None

    buckets = {"<20": [], "20-30": [], ">30": []}
    no_vix = 0
    for r in dated:
        v = vix_before(r["entry_date"])
        if v is None:
            no_vix += 1
            continue
        b = "<20" if v < 20 else ("20-30" if v <= 30 else ">30")
        buckets[b].append(r["win"])
    total = [r["win"] for r in dated]
    print(f"  VIX daily rows fetched: {len(vix)} ({lo}..{hi}); trades w/o prior-VIX: {no_vix}")
    for b in ("<20", "20-30", ">30"):
        arr = buckets[b]
        wr = f"{100*sum(arr)/len(arr):.1f}%" if arr else "-"
        print(f"  VIX {b:<6} n={len(arr):<4} WR={wr}")
    owr = f"{100*sum(total)/len(total):.1f}%" if total else "-"
    print(f"  OVERALL     n={len(total):<4} WR={owr}")
    _skills()
    return 0


def _skills():
    pass


if __name__ == "__main__":
    sys.exit(main())
