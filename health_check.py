#!/usr/bin/env python3
"""
RidingHigh Pro - System Health Check
Runs deep validation across all sheets and reports issues.

Usage:
    python3 health_check.py          # full check
    python3 health_check.py --quiet  # only warnings/errors

Returns:
    run() -> list[str]  (importable from dashboard)
"""

import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, __import__("os").path.expanduser("~/RidingHighPro"))
import pytz
import sheets_manager
from gsheets_sync import load_post_analysis_from_sheets

PERU_TZ = pytz.timezone("America/Lima")


def _trading_days_before(date_str: str, n: int = 5) -> list:
    """Return the n trading days (weekdays) strictly after date_str."""
    return sheets_manager.trading_days_after(date_str, n)


def _is_missing(val) -> bool:
    if val is None:
        return True
    return str(val).strip() in ("", "nan", "None", "NaN")


def _is_market_open(now=None) -> bool:
    if now is None:
        now = datetime.now(PERU_TZ)
    return now.weekday() < 5 and 8 * 60 + 30 <= now.hour * 60 + now.minute <= 15 * 60


def _all_settled(scan_date: str, n: int = 5) -> bool:
    """True if at least n trading days after scan_date have fully closed."""
    try:
        days = _trading_days_before(scan_date, n)
        now = datetime.now(PERU_TZ)
        today = now.date()
        for d in days:
            day = datetime.strptime(d, "%Y-%m-%d").date()
            if day > today:
                return False
            if day == today and now.hour < 15:
                return False
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Individual check functions — each returns list[str] of result lines
# ─────────────────────────────────────────────────────────────────────────────

def check_post_analysis(gc, timeline_dates: set) -> list:
    lines = []
    lines.append("── Post Analysis ──────────────────────────────────")

    df = load_post_analysis_from_sheets()
    if df.empty:
        lines.append("❌ post_analysis: ריק לחלוטין")
        return lines

    lines.append(f"✅ post_analysis: {len(df)} שורות | {df['ScanDate'].min()} → {df['ScanDate'].max()}")

    critical = 0
    warnings = 0

    for date, grp in df.groupby("ScanDate"):
        n = len(grp)
        issues = []
        warn_items = []

        # Score > 0
        score_zero = (pd.to_numeric(grp["Score"], errors="coerce").fillna(0) == 0).sum()
        if score_zero:
            issues.append(f"Score=0 ({score_zero}/{n})")

        # ScanChange% > 0
        sc = pd.to_numeric(grp.get("ScanChange%", pd.Series(dtype=float)), errors="coerce")
        sc_bad = (sc.fillna(0) == 0).sum()
        if sc_bad == n:
            warn_items.append(f"ScanChange%=0 (כל {n})")
        elif sc_bad:
            warn_items.append(f"ScanChange%=0 ({sc_bad}/{n})")

        # Score_v2 not None
        if "Score_v2" in grp.columns:
            sv2_missing = grp["Score_v2"].apply(_is_missing).sum()
            if sv2_missing:
                warn_items.append(f"Score_v2 חסר ({sv2_missing}/{n})")

        # IntraHigh — only check dates that exist in timeline_live
        if date in timeline_dates:
            intra_missing = grp["IntraHigh"].apply(_is_missing).sum() if "IntraHigh" in grp.columns else n
            if intra_missing == n:
                issues.append(f"IntraHigh חסר לכולם")
            elif intra_missing:
                warn_items.append(f"IntraHigh חסר ({intra_missing}/{n})")

        # TP10_Hit + MaxDrop% — only after 5 settled trading days
        if _all_settled(date, 5):
            for field in ["TP10_Hit", "MaxDrop%"]:
                if field in grp.columns:
                    missing = grp[field].apply(_is_missing).sum()
                    if missing == n:
                        issues.append(f"{field} חסר לכולם")
                    elif missing:
                        warn_items.append(f"{field} חסר ({missing}/{n})")

        if issues:
            critical += 1
            lines.append(f"  ❌ {date} ({n} מניות): {' | '.join(issues)}")
        elif warn_items:
            warnings += 1
            lines.append(f"  ⚠️  {date} ({n} מניות): {' | '.join(warn_items)}")
        else:
            lines.append(f"  ✅ {date} ({n} מניות)")

    return lines, critical, warnings


def check_timeline_live(gc) -> tuple:
    lines = []
    lines.append("── Timeline Live ───────────────────────────────────")
    critical = 0
    warnings = 0

    ws = sheets_manager.get_worksheet("timeline_live", gc=gc)
    if ws is None:
        lines.append("❌ timeline_live: לא נמצא")
        return lines, 1, 0

    data = ws.get_all_values()
    if len(data) <= 1:
        lines.append("❌ timeline_live: ריק")
        return lines, 1, 0

    tl = pd.DataFrame(data[1:], columns=data[0])
    tl["Score"] = pd.to_numeric(tl["Score"], errors="coerce")
    total = len(tl)
    dates = sorted(tl["Date"].unique())
    lines.append(f"✅ timeline_live: {total} שורות | תאריכים: {', '.join(dates[-3:])}")

    now = datetime.now(PERU_TZ)
    today = now.strftime("%Y-%m-%d")

    # Check today's data if market is open or just closed
    if now.weekday() < 5:
        today_rows = tl[tl["Date"] == today]
        if today_rows.empty:
            if _is_market_open(now):
                lines.append(f"  ⚠️  אין נתונים מהיום ({today}) — שוק פתוח")
                warnings += 1
            else:
                lines.append(f"  ⚠️  אין נתונים מהיום ({today})")
                warnings += 1
        else:
            lines.append(f"  ✅ היום ({today}): {len(today_rows)} שורות")

    # EntryScore check for Score>=70
    high_score = tl[tl["Score"] >= 70]
    if not high_score.empty and "EntryScore" in tl.columns:
        entry_missing = high_score["EntryScore"].apply(_is_missing).sum()
        if entry_missing:
            pct = entry_missing / len(high_score) * 100
            msg = f"  ⚠️  EntryScore חסר ל-{entry_missing}/{len(high_score)} מניות עם Score≥70 ({pct:.0f}%)"
            if pct > 50:
                lines.append(msg.replace("⚠️", "❌"))
                critical += 1
            else:
                lines.append(msg)
                warnings += 1
        else:
            lines.append(f"  ✅ EntryScore: קיים לכל {len(high_score)} מניות Score≥70")

    return lines, critical, warnings, set(dates)


def check_portfolio(gc) -> tuple:
    lines = []
    lines.append("── Portfolio ───────────────────────────────────────")
    critical = 0
    warnings = 0

    ws = sheets_manager.get_worksheet("portfolio", gc=gc)
    if ws is None:
        lines.append("❌ portfolio: לא נמצא")
        return lines, 1, 0

    data = ws.get_all_values()
    if len(data) <= 1:
        lines.append("⚠️  portfolio: ריק")
        return lines, 0, 1

    df = pd.DataFrame(data[1:], columns=data[0])
    lines.append(f"✅ portfolio: {len(df)} שורות")

    if "Status" in df.columns:
        empty_status = (df["Status"].str.strip() == "").sum()
        if empty_status:
            lines.append(f"  ⚠️  {empty_status} שורות עם Status ריק")
            warnings += 1

    if "EntryPrice" in df.columns:
        bad_price = (pd.to_numeric(df["EntryPrice"], errors="coerce").fillna(0) <= 0).sum()
        if bad_price:
            lines.append(f"  ❌ {bad_price} שורות עם EntryPrice <= 0")
            critical += 1
        else:
            lines.append(f"  ✅ כל EntryPrice > 0")

    return lines, critical, warnings


def check_score_tracker(gc) -> tuple:
    lines = []
    lines.append("── Score Tracker ───────────────────────────────────")
    critical = 0
    warnings = 0

    ws = sheets_manager.get_worksheet("score_tracker", gc=gc)
    if ws is None:
        lines.append("❌ score_tracker: לא נמצא")
        return lines, 1, 0

    data = ws.get_all_values()
    if len(data) <= 1:
        lines.append("⚠️  score_tracker: ריק")
        return lines, 0, 1

    df = pd.DataFrame(data[1:], columns=data[0])
    total = len(df)

    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    date_col = next((c for c in ["Date", "ScanDate", "date"] if c in df.columns), None)
    if date_col:
        today_rows = df[df[date_col] == today]
        if today_rows.empty and datetime.now(PERU_TZ).weekday() < 5:
            lines.append(f"  ⚠️  אין נתונים מהיום ({today}) ב-score_tracker")
            warnings += 1
        else:
            lines.append(f"✅ score_tracker: {total} שורות | היום: {len(today_rows)}")
    else:
        lines.append(f"✅ score_tracker: {total} שורות")

    return lines, critical, warnings


def check_live_trades(gc) -> tuple:
    lines = []
    lines.append("── Live Trades ─────────────────────────────────────")
    critical = 0
    warnings = 0

    ws = sheets_manager.get_worksheet("live_trades", gc=gc)
    if ws is None:
        lines.append("⚠️  live_trades: לא נמצא")
        return lines, 0, 1

    data = ws.get_all_values()
    if len(data) <= 1:
        lines.append("✅ live_trades: ריק (אין עסקאות פתוחות)")
        return lines, 0, 0

    df = pd.DataFrame(data[1:], columns=data[0])
    total = len(df)
    lines.append(f"✅ live_trades: {total} שורות")

    today = datetime.now(PERU_TZ).date()
    cutoff = today - timedelta(days=5)

    status_col = next((c for c in ["Status", "status"] if c in df.columns), None)
    date_col = next((c for c in ["ScanDate", "EntryDate", "Date", "date"] if c in df.columns), None)

    if status_col and date_col:
        pending = df[df[status_col].str.strip().str.lower().isin(["pending", ""])]
        if not pending.empty:
            old_pending = []
            for _, row in pending.iterrows():
                try:
                    d = datetime.strptime(str(row[date_col])[:10], "%Y-%m-%d").date()
                    if d <= cutoff:
                        old_pending.append(f"{row.get('Ticker','?')} ({row[date_col][:10]})")
                except Exception:
                    pass
            if old_pending:
                lines.append(f"  ⚠️  {len(old_pending)} Pending ישנות (5+ ימים): {', '.join(old_pending[:5])}")
                warnings += 1
            else:
                lines.append(f"  ✅ {len(pending)} Pending — כולן בטווח תקין")

    return lines, critical, warnings


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(quiet: bool = False) -> list:
    """
    Run all health checks. Returns list of output lines.
    quiet=True suppresses ✅ lines (only warnings/errors).
    """
    output = []
    now_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d %H:%M:%S")
    output.append(f"=== RidingHigh Health Check — {now_str} Peru ===")
    output.append("")

    try:
        gc = sheets_manager._get_gc()
        if gc is None:
            output.append("❌ CRITICAL: לא ניתן להתחבר ל-Google Sheets")
            return output
    except Exception as e:
        output.append(f"❌ CRITICAL: שגיאת auth — {e}")
        return output

    total_critical = 0
    total_warnings = 0

    # 1. Timeline (first — need dates set for post_analysis check)
    result = check_timeline_live(gc)
    tl_lines, tl_crit, tl_warn, timeline_dates = result
    total_critical += tl_crit
    total_warnings += tl_warn
    for line in tl_lines:
        if not quiet or not line.startswith("  ✅"):
            output.append(line)
    output.append("")

    # 2. Post analysis
    result = check_post_analysis(gc, timeline_dates)
    pa_lines, pa_crit, pa_warn = result
    total_critical += pa_crit
    total_warnings += pa_warn
    for line in pa_lines:
        if not quiet or not line.startswith("  ✅"):
            output.append(line)
    output.append("")

    # 3. Portfolio
    pf_lines, pf_crit, pf_warn = check_portfolio(gc)
    total_critical += pf_crit
    total_warnings += pf_warn
    for line in pf_lines:
        if not quiet or not line.startswith("  ✅"):
            output.append(line)
    output.append("")

    # 4. Score tracker
    st_lines, st_crit, st_warn = check_score_tracker(gc)
    total_critical += st_crit
    total_warnings += st_warn
    for line in st_lines:
        if not quiet or not line.startswith("  ✅"):
            output.append(line)
    output.append("")

    # 5. Live trades
    lt_lines, lt_crit, lt_warn = check_live_trades(gc)
    total_critical += lt_crit
    total_warnings += lt_warn
    for line in lt_lines:
        if not quiet or not line.startswith("  ✅"):
            output.append(line)
    output.append("")

    # Summary
    output.append("=" * 51)
    summary_icon = "✅" if total_critical == 0 and total_warnings == 0 else ("❌" if total_critical > 0 else "⚠️")
    output.append(f"{summary_icon} סיכום: {total_critical} בעיות קריטיות, {total_warnings} אזהרות")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RidingHigh System Health Check")
    parser.add_argument("--quiet", action="store_true", help="Show only warnings and errors")
    args = parser.parse_args()

    lines = run(quiet=args.quiet)
    print("\n".join(lines))
