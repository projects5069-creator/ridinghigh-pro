"""
monthly_rotation.py
───────────────────
Pre-creates all Google Sheets for the NEXT calendar month and commits the
updated sheets_config.json back to git so every subsequent GitHub Actions
run finds the IDs without re-creating duplicates.

Also copies Open portfolio positions from the current month into the next
month's portfolio sheet so trades that span the month boundary continue
to be tracked.

Usage:
    python monthly_rotation.py            # live run
    python monthly_rotation.py --dry-run  # print what would happen, change nothing
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_manager


# ── helpers ───────────────────────────────────────────────────────────────────

def _next_month_key() -> str:
    now = datetime.utcnow()
    if now.month == 12:
        return f"{now.year + 1}-01"
    return f"{now.year}-{now.month + 1:02d}"


def _current_month_key() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _already_done(month_key: str) -> bool:
    """True if sheets_config.json already has full entries for month_key."""
    config = sheets_manager._load_config()
    if month_key not in config:
        return False
    return all(name in config[month_key] for name in sheets_manager.SHEET_NAMES)


def _copy_open_portfolio(gc, from_month: str, to_month: str, dry_run: bool):
    """
    Copy rows where Status == 'Open' from current-month portfolio
    into next-month portfolio, so trades that span the boundary keep running.
    Skips rows that already exist in the target (by PositionKey or Ticker+Date).
    """
    print(f"\n[Rotation] Copying Open portfolio positions {from_month} → {to_month}...")

    ws_src = sheets_manager.get_worksheet("portfolio", month=from_month, gc=gc)
    if not ws_src:
        print("[Rotation] ⚠️  Could not open source portfolio sheet")
        return

    src_data = ws_src.get_all_values()
    if len(src_data) <= 1:
        print("[Rotation] Source portfolio is empty — nothing to copy")
        return

    headers = src_data[0]
    rows    = src_data[1:]

    # Find Status column
    status_idx = headers.index("Status") if "Status" in headers else None
    open_rows  = [r for r in rows if status_idx is not None and
                  len(r) > status_idx and r[status_idx].strip() == "Open"]

    if not open_rows:
        print("[Rotation] No Open positions to carry over")
        return

    print(f"[Rotation] Found {len(open_rows)} Open positions to copy")
    if dry_run:
        for r in open_rows:
            print(f"  DRY-RUN would copy: {r[:5]}")
        return

    ws_dst = sheets_manager.get_worksheet("portfolio", month=to_month, gc=gc)
    if not ws_dst:
        print("[Rotation] ⚠️  Could not open destination portfolio sheet")
        return

    dst_data = ws_dst.get_all_values()

    if len(dst_data) <= 1:
        # Destination empty — write headers + open rows
        ws_dst.update("A1", [headers] + open_rows)
        print(f"[Rotation] ✅ Wrote {len(open_rows)} rows + headers to {to_month}/portfolio")
    else:
        # Destination has data — append only rows not already present
        dst_keys = set(r[0] for r in dst_data[1:]) if dst_data[1:] else set()
        new_rows = [r for r in open_rows if r[0] not in dst_keys]
        if new_rows:
            ws_dst.append_rows(new_rows)
            print(f"[Rotation] ✅ Appended {len(new_rows)} new Open rows to {to_month}/portfolio")
        else:
            print("[Rotation] All Open positions already present in destination")


def _git_commit_push(dry_run: bool):
    """Commit sheets_config.json and push to origin/main."""
    config_path = sheets_manager.CONFIG_PATH
    print(f"\n[Rotation] Committing {config_path}...")

    if dry_run:
        print("  DRY-RUN: would run git add / commit / push")
        return

    repo_root = os.path.dirname(os.path.abspath(__file__))

    def run(cmd):
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️  {' '.join(cmd)} failed:\n{result.stderr.strip()}")
        else:
            out = result.stdout.strip()
            if out:
                print(f"  {out}")
        return result.returncode

    run(["git", "config", "user.email", "rotation-bot@ridinghigh.pro"])
    run(["git", "config", "user.name",  "RidingHigh Rotation Bot"])
    run(["git", "add", config_path])

    msg = f"Monthly rotation: add sheets for {_next_month_key()}"
    rc  = run(["git", "commit", "-m", msg])
    if rc == 0:
        push_rc = run(["git", "push"])
        if push_rc == 0:
            print("[Rotation] ✅ sheets_config.json committed and pushed")
        else:
            print("[Rotation] ⚠️  Push failed — config was committed locally but not pushed")
    else:
        print("[Rotation] ℹ️  Nothing to commit (sheets_config.json already up to date)")


# ── main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False):
    banner = "DRY-RUN " if dry_run else ""
    print(f"{'='*55}")
    print(f"  RidingHigh Monthly Rotation  {banner}")
    print(f"{'='*55}")

    current_key = _current_month_key()
    next_key    = _next_month_key()
    print(f"Current month : {current_key}")
    print(f"Next month    : {next_key}")

    # ── Idempotency check ─────────────────────────────────────────────────────
    if _already_done(next_key):
        print(f"\n✅ Already rotated — {next_key} fully present in sheets_config.json")
        print("   Nothing to do.")
        return

    print(f"\n[Rotation] {next_key} not found in config — proceeding...")

    if dry_run:
        print("\n[DRY-RUN] Would create the following sheets in Google Drive:")
        for name in sheets_manager.SHEET_NAMES:
            print(f"  RH-{next_key}-{name}")
        print(f"\n[DRY-RUN] Would copy Open portfolio positions from {current_key} → {next_key}")
        print(f"[DRY-RUN] Would git commit + push sheets_config.json")
        print("\n[DRY-RUN] sheets_config.json would gain:")
        print(json.dumps({next_key: {n: "<new-id>" for n in sheets_manager.SHEET_NAMES}}, indent=2))
        return

    # ── Create all sheets for next month ──────────────────────────────────────
    print(f"\n[Rotation] Creating sheets for {next_key}...")
    try:
        new_cfg = sheets_manager._ensure_month(next_key)
    except Exception as e:
        print(f"[Rotation] ❌ Failed to create sheets: {e}")
        sys.exit(1)

    print(f"\n[Rotation] Created sheets:")
    for name, sid in new_cfg.items():
        print(f"  {name}: {sid}")

    # ── Copy Open portfolio positions ─────────────────────────────────────────
    try:
        gc = sheets_manager._get_gc()
        _copy_open_portfolio(gc, current_key, next_key, dry_run=False)
    except Exception as e:
        print(f"[Rotation] ⚠️  Portfolio copy failed (non-fatal): {e}")

    # ── Commit + push sheets_config.json ──────────────────────────────────────
    _git_commit_push(dry_run=False)

    print(f"\n{'='*55}")
    print(f"  ✅ Rotation complete — {next_key} is ready")
    print(f"{'='*55}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would happen without making any changes")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
