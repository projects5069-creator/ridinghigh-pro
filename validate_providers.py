#!/usr/bin/env python3
"""
validate_providers.py - A/B comparison of Alpaca vs yfinance
================================================================

Runs both providers on the same set of tickers and compares the prices.
Produces a detailed report:
  - Tickers where prices match (within tolerance)
  - Tickers with small differences
  - Tickers with significant differences (investigate)

This is the validation gate before switching DATA_PROVIDER from
yfinance to alpaca in production.

Usage:
    python3 validate_providers.py
    python3 validate_providers.py --tickers AAPL,MSFT,TSLA
    python3 validate_providers.py --days 30 --tolerance 0.5
    python3 validate_providers.py --output report.md
    python3 validate_providers.py --use-post-analysis  # Use real RidingHigh tickers

Created: 2026-04-25 (Issue #9)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# ── Project imports ─────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_provider import get_data_provider, reset_providers


# ════════════════════════════════════════════════════════════════════════
# Default ticker list — diverse mix (large/mid/small cap, different sectors)
# ════════════════════════════════════════════════════════════════════════

DEFAULT_TICKERS = [
    # Large cap tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META",
    # Large cap other
    "TSLA", "JPM", "V", "WMT",
    # Mid cap
    "F", "AMD", "INTC", "GE", "DIS",
    # Small / volatile (the kind we typically scan)
    "PLTR", "RIVN", "LCID", "SOFI", "HOOD",
    # ETFs (sanity)
    "SPY", "QQQ", "IWM",
]


# ════════════════════════════════════════════════════════════════════════
# Comparison helpers
# ════════════════════════════════════════════════════════════════════════

def compare_bars(bars_a, bars_b, tolerance_pct: float) -> Dict:
    """
    Compare two daily-bar DataFrames.
    
    Returns:
        Dict with:
          - total_a, total_b (number of bars)
          - matched_dates (intersection)
          - close_diffs: list of {date, close_a, close_b, diff_pct}
          - max_diff_pct
          - all_within_tolerance (bool)
    """
    result = {
        "total_a": len(bars_a),
        "total_b": len(bars_b),
        "matched_dates": 0,
        "close_diffs": [],
        "max_diff_pct": 0.0,
        "all_within_tolerance": True,
    }
    
    if bars_a.empty or bars_b.empty:
        result["all_within_tolerance"] = False
        return result
    
    # Normalize dates for matching
    def to_date(idx):
        if hasattr(idx, "date"):
            return idx.date()
        return idx
    
    dates_a = {to_date(d): bars_a.iloc[i] for i, d in enumerate(bars_a.index)}
    dates_b = {to_date(d): bars_b.iloc[i] for i, d in enumerate(bars_b.index)}
    
    common_dates = sorted(set(dates_a) & set(dates_b))
    result["matched_dates"] = len(common_dates)
    
    for d in common_dates:
        close_a = float(dates_a[d]["close"])
        close_b = float(dates_b[d]["close"])
        if close_a == 0:
            continue
        diff_pct = abs(close_a - close_b) / close_a * 100
        result["close_diffs"].append({
            "date": str(d),
            "close_a": round(close_a, 2),
            "close_b": round(close_b, 2),
            "diff_pct": round(diff_pct, 3),
        })
        if diff_pct > result["max_diff_pct"]:
            result["max_diff_pct"] = diff_pct
        if diff_pct > tolerance_pct:
            result["all_within_tolerance"] = False
    
    result["max_diff_pct"] = round(result["max_diff_pct"], 3)
    return result


def classify_ticker(comparison: Dict, tolerance_pct: float) -> str:
    """Bucket a ticker into one of: identical / minor / significant / failed."""
    if comparison["matched_dates"] == 0:
        return "failed"
    
    max_diff = comparison["max_diff_pct"]
    if max_diff < 0.01:
        return "identical"
    if max_diff < tolerance_pct:
        return "minor"
    return "significant"


# ════════════════════════════════════════════════════════════════════════
# Report writers
# ════════════════════════════════════════════════════════════════════════

def write_markdown_report(results: List[Dict], path: Path, args) -> None:
    """Write a human-readable Markdown report."""
    buckets = {"identical": [], "minor": [], "significant": [], "failed": []}
    for r in results:
        buckets[r["bucket"]].append(r)
    
    total = len(results)
    pct_clean = (len(buckets["identical"]) + len(buckets["minor"])) / total * 100 if total else 0
    
    lines = [
        f"# Provider Validation Report",
        f"*Generated: {datetime.now().isoformat(timespec='seconds')}*",
        f"",
        f"## Configuration",
        f"- Tickers tested: **{total}**",
        f"- Days back: **{args.days}**",
        f"- Tolerance: **{args.tolerance}%**",
        f"- Provider A: **{args.provider_a}**",
        f"- Provider B: **{args.provider_b}**",
        f"",
        f"## Summary",
        f"- ✅ Identical:   **{len(buckets['identical'])}** ({len(buckets['identical'])/total*100:.0f}%)",
        f"- 🟢 Minor:       **{len(buckets['minor'])}** ({len(buckets['minor'])/total*100:.0f}%)",
        f"- 🟡 Significant: **{len(buckets['significant'])}** ({len(buckets['significant'])/total*100:.0f}%)",
        f"- 🔴 Failed:      **{len(buckets['failed'])}** ({len(buckets['failed'])/total*100:.0f}%)",
        f"",
        f"**Overall: {pct_clean:.1f}% of tickers within tolerance.**",
        f"",
    ]
    
    if pct_clean >= 95:
        lines.append("> ✅ **VERDICT: Providers agree. Safe to switch DATA_PROVIDER.**")
    elif pct_clean >= 80:
        lines.append("> 🟡 **VERDICT: Mostly aligned. Investigate significant cases before switching.**")
    else:
        lines.append("> 🔴 **VERDICT: Too many disagreements. Do NOT switch yet.**")
    lines.append("")
    
    # Detail tables for each bucket
    for bucket_name in ["significant", "failed", "minor"]:
        bucket = buckets[bucket_name]
        if not bucket:
            continue
        emoji = {"significant": "🟡", "failed": "🔴", "minor": "🟢"}[bucket_name]
        lines.append(f"## {emoji} {bucket_name.title()} ({len(bucket)})")
        lines.append("")
        lines.append("| Ticker | Bars A | Bars B | Matched | Max diff % |")
        lines.append("|--------|--------|--------|---------|-----------|")
        for r in bucket:
            c = r["comparison"]
            lines.append(
                f"| {r['ticker']} | {c['total_a']} | {c['total_b']} | "
                f"{c['matched_dates']} | {c['max_diff_pct']:.3f} |"
            )
        lines.append("")
    
    # Top 5 worst offenders detail
    lines.append("## Top 5 worst differences")
    lines.append("")
    worst = sorted(results, key=lambda r: -r["comparison"]["max_diff_pct"])[:5]
    for r in worst:
        diffs = sorted(r["comparison"]["close_diffs"], key=lambda d: -d["diff_pct"])[:3]
        lines.append(f"### {r['ticker']} (max diff: {r['comparison']['max_diff_pct']:.2f}%)")
        lines.append("")
        lines.append(f"| Date | {args.provider_a} close | {args.provider_b} close | Diff % |")
        lines.append("|------|----------|----------|--------|")
        for d in diffs:
            lines.append(f"| {d['date']} | {d['close_a']} | {d['close_b']} | {d['diff_pct']:.3f} |")
        lines.append("")
    
    path.write_text("\n".join(lines))
    print(f"📄 Report written to: {path}")


# ════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tickers", default=None, help="Comma-separated list (overrides default)")
    p.add_argument("--days", type=int, default=30, help="Days of history to compare")
    p.add_argument("--tolerance", type=float, default=0.5, help="% diff tolerance")
    p.add_argument("--output", default="provider_validation_report.md")
    p.add_argument("--provider-a", default="alpaca")
    p.add_argument("--provider-b", default="yfinance")
    p.add_argument("--use-post-analysis", action="store_true",
                   help="Use real tickers from post_analysis sheet instead of defaults")
    args = p.parse_args()
    
    # Resolve ticker list
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    elif args.use_post_analysis:
        tickers = _load_post_analysis_tickers()
        if not tickers:
            print("⚠️  Could not load tickers from post_analysis, using defaults")
            tickers = DEFAULT_TICKERS
    else:
        tickers = DEFAULT_TICKERS
    
    print("=" * 70)
    print(f"Provider Validation: {args.provider_a} vs {args.provider_b}")
    print(f"Tickers: {len(tickers)}    Days: {args.days}    Tolerance: {args.tolerance}%")
    print("=" * 70)
    
    # Initialize both providers
    reset_providers()
    try:
        prov_a = get_data_provider(force_provider=args.provider_a)
        print(f"✅ Provider A ({args.provider_a}): {prov_a.name}")
    except Exception as e:
        print(f"❌ Provider A failed to initialize: {e}")
        return 1
    
    try:
        prov_b = get_data_provider(force_provider=args.provider_b)
        print(f"✅ Provider B ({args.provider_b}): {prov_b.name}")
    except Exception as e:
        print(f"❌ Provider B failed to initialize: {e}")
        return 1
    print()
    
    # Compare ticker by ticker
    results = []
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker:6} ... ", end="", flush=True)
        try:
            bars_a = prov_a.get_daily_bars(ticker, days=args.days)
            bars_b = prov_b.get_daily_bars(ticker, days=args.days)
            comp = compare_bars(bars_a, bars_b, args.tolerance)
            bucket = classify_ticker(comp, args.tolerance)
            results.append({
                "ticker": ticker,
                "comparison": comp,
                "bucket": bucket,
            })
            emoji = {"identical": "✅", "minor": "🟢", "significant": "🟡", "failed": "🔴"}[bucket]
            print(f"{emoji} {bucket:11} (max_diff={comp['max_diff_pct']:.3f}%, "
                  f"{comp['matched_dates']} matched dates)")
        except Exception as e:
            print(f"❌ error: {e}")
            results.append({
                "ticker": ticker,
                "comparison": {"total_a": 0, "total_b": 0, "matched_dates": 0,
                               "close_diffs": [], "max_diff_pct": 0.0,
                               "all_within_tolerance": False},
                "bucket": "failed",
            })
    
    print()
    
    # Write report
    write_markdown_report(results, Path(args.output), args)
    
    # Also save raw JSON for programmatic use
    json_path = Path(args.output).with_suffix(".json")
    json_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"📊 JSON written to:    {json_path}")
    
    # Summary verdict
    total = len(results)
    clean = sum(1 for r in results if r["bucket"] in ("identical", "minor"))
    pct = clean / total * 100 if total else 0
    
    print()
    print("=" * 70)
    if pct >= 95:
        print(f"✅ {pct:.1f}% within tolerance — Providers agree, safe to switch.")
        return 0
    elif pct >= 80:
        print(f"🟡 {pct:.1f}% within tolerance — Mostly aligned, investigate before switch.")
        return 0
    else:
        print(f"🔴 {pct:.1f}% within tolerance — Too many disagreements, do NOT switch.")
        return 2


def _load_post_analysis_tickers(limit: int = 30) -> List[str]:
    """Load tickers from post_analysis Sheet (recent unique)."""
    try:
        import json as _json
        import gspread
        from google.oauth2.service_account import Credentials
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("google_credentials.json", scopes=scopes)
        gc = gspread.authorize(creds)
        config = _json.load(open("sheets_config.json"))
        
        # Find a month with data
        for month in sorted(config.keys(), reverse=True):
            sheet_id = config[month].get("post_analysis")
            if not sheet_id:
                continue
            try:
                ws = gc.open_by_key(sheet_id).sheet1
                vals = ws.get_all_values()
                if len(vals) > 1:
                    headers = vals[0]
                    if "Ticker" in headers:
                        tcol = headers.index("Ticker")
                        tickers = list({row[tcol] for row in vals[1:] if len(row) > tcol and row[tcol]})
                        return sorted(tickers)[:limit]
            except Exception:
                continue
        return []
    except Exception as e:
        print(f"⚠️  Could not load from post_analysis: {e}")
        return []


if __name__ == "__main__":
    sys.exit(main())
