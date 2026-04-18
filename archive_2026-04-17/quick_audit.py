"""
Quick audit of post_analysis raw data quality.
No yfinance calls — reads only from the Google Sheet.

Usage:
  python quick_audit.py
"""
import pandas as pd
from gsheets_sync import load_post_analysis_from_sheets


def audit_row(row):
    """Run 5 sanity checks on a single row. Returns list of failure strings."""
    failures = []

    def safe(val):
        try:
            v = float(val)
            return v if pd.notna(v) else None
        except (TypeError, ValueError):
            return None

    price     = safe(row.get("ScanPrice"))
    atrx      = safe(row.get("ATRX"))
    atrx_calc = safe(row.get("ATRX_calc"))
    high      = safe(row.get("High_today_raw"))
    low       = safe(row.get("Low_today_raw"))
    open_p    = safe(row.get("Open_price_raw"))
    prev_cl   = safe(row.get("PrevClose_raw"))
    volume    = safe(row.get("Volume"))
    avg_vol   = safe(row.get("AvgVolume_raw"))
    atr14     = safe(row.get("ATR14_raw"))

    # If no raw data at all, flag as NO_DATA
    raw_fields = [high, low, open_p, avg_vol, atr14]
    if all(v is None or v == 0 for v in raw_fields):
        return ["NO_DATA"]

    # Check 1: ATRX vs ATRX_calc
    if atrx is not None and atrx_calc is not None and atrx_calc > 0:
        if abs(atrx - atrx_calc) > 0.01:
            failures.append(f"ATRX_mismatch({atrx:.2f}!={atrx_calc:.2f})")

    # Check 2: High_today_raw vs ScanPrice
    if high is not None and price is not None and price > 0:
        if high > 3 * price:
            failures.append(f"High_too_high({high:.2f} vs price {price:.2f})")

    # Check 3: Open_price_raw vs ScanPrice
    if open_p is not None and price is not None and price > 0:
        ratio = open_p / price
        if ratio > 2 or ratio < 0.5:
            failures.append(f"Open_outlier({open_p:.2f} vs price {price:.2f})")

    # Check 4: AvgVolume_raw sanity
    if avg_vol is not None and avg_vol > 0 and avg_vol < 1000:
        failures.append(f"AvgVol_tiny({avg_vol:.0f})")

    # Check 5: ATR14_raw vs Price
    if atr14 is not None and price is not None and price > 0:
        if atr14 > 0 and atr14 < 0.005 * price:
            failures.append(f"ATR_micro({atr14:.4f} vs price {price:.2f})")
        elif atr14 > 0.5 * price:
            failures.append(f"ATR_huge({atr14:.2f} vs price {price:.2f})")

    return failures


def classify(failures):
    if failures == ["NO_DATA"]:
        return "NO_DATA"
    if len(failures) >= 2:
        return "BROKEN"
    if len(failures) == 1:
        return "SUSPICIOUS"
    return "CLEAN"


def main():
    print("Loading post_analysis...")
    df = load_post_analysis_from_sheets()
    if df.empty:
        print("No data.")
        return
    print(f"Loaded {len(df)} rows\n")

    results = []
    for i, row in df.iterrows():
        failures = audit_row(row)
        status = classify(failures)
        results.append({
            "Ticker":   row.get("Ticker", "?"),
            "ScanDate": row.get("ScanDate", "?"),
            "Status":   status,
            "Failures": " | ".join(failures) if failures else "",
            "N_Fails":  len(failures) if failures != ["NO_DATA"] else 0,
        })

    report = pd.DataFrame(results)

    # ── Summary ──────────────────────────────────────────────────────
    print("=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)

    counts = report["Status"].value_counts()
    for status in ["CLEAN", "SUSPICIOUS", "BROKEN", "NO_DATA"]:
        n = counts.get(status, 0)
        pct = n / len(report) * 100
        print(f"  {status:<12}  {n:>4}  ({pct:.0f}%)")

    # ── By date ──────────────────────────────────────────────────────
    print(f"\nBreakdown by ScanDate:")
    print(f"  {'Date':<12} {'CLEAN':>6} {'SUSP':>6} {'BROKEN':>7} {'NO_DATA':>8} {'Total':>6}")
    print(f"  {'-'*50}")

    dates = sorted(report["ScanDate"].unique())
    for d in dates:
        day = report[report["ScanDate"] == d]
        cl = (day["Status"] == "CLEAN").sum()
        su = (day["Status"] == "SUSPICIOUS").sum()
        br = (day["Status"] == "BROKEN").sum()
        nd = (day["Status"] == "NO_DATA").sum()
        total = len(day)
        marker = "  ⚠" if br + su > total * 0.5 else ""
        print(f"  {d:<12} {cl:>6} {su:>6} {br:>7} {nd:>8} {total:>6}{marker}")

    # ── Top BROKEN details ───────────────────────────────────────────
    broken = report[report["Status"].isin(["BROKEN", "SUSPICIOUS"])].sort_values(
        "N_Fails", ascending=False)

    if not broken.empty:
        print(f"\nTop {min(10, len(broken))} problematic rows:")
        print(f"  {'Ticker':<8} {'ScanDate':<12} {'Status':<12} Failures")
        print(f"  {'-'*70}")
        for _, r in broken.head(10).iterrows():
            print(f"  {r['Ticker']:<8} {r['ScanDate']:<12} {r['Status']:<12} {r['Failures']}")

    # ── Failure type breakdown ───────────────────────────────────────
    all_failures = []
    for _, r in report.iterrows():
        if r["Failures"] and r["Status"] != "NO_DATA":
            for f in r["Failures"].split(" | "):
                # Extract check name (before the parenthesis)
                check_name = f.split("(")[0]
                all_failures.append(check_name)

    if all_failures:
        print(f"\nFailure type frequency:")
        for name, count in pd.Series(all_failures).value_counts().items():
            print(f"  {name:<20} {count:>4}")

    # ── Save CSV ─────────────────────────────────────────────────────
    report.to_csv("quick_audit_report.csv", index=False)
    print(f"\nFull report saved: quick_audit_report.csv")


if __name__ == "__main__":
    main()
