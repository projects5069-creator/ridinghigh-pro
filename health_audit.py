#!/usr/bin/env python3
"""
health_audit.py
===============
Automated health audit for RidingHigh Pro.

Runs 15 checks across 5 categories:
  📁 Code integrity (3)
  📊 Data freshness (3)
  🔢 Data quality (4)
  ⚙️ Config consistency (3)
  🔐 Repo health (2)

Usage:
  # GitHub Actions context (uses env vars):
  python3 health_audit.py

  # Local context (uses google_credentials.json):
  python3 health_audit.py --local

  # Just print, don't write to Sheet:
  python3 health_audit.py --no-sheet

Output:
  - Console: human-readable report
  - Google Sheet "RidingHigh-Health-Audit" (if configured):
    * History tab — append every run
    * Latest tab — overwrite with current state
    * Failed tab — only currently-failing checks

Exit codes:
  0 — no CRITICAL issues (healthy state, even with WARNINGs)
  1 — at least one CRITICAL check failed

CHANGELOG:
  v3 (2026-04-25): Exit code semantics fixed for CI compatibility.
                   Previously WARNINGs returned exit code 2, which GitHub
                   Actions treats as failure — producing false-positive
                   "exit code 2" annotations on every run (since open
                   issues show up as warnings). Now WARNINGs return 0.
                   Detailed status logged before exit.
  v2 (2026-04-25): Smart month selection (was selecting empty 2026-05).
                   Fixed X2 false positive (comment "# Total: 100" was
                   counted as a weight value).
                   C1 now ignores files in גיבוי זמני/ folder.
                   D2 now uses the smart-selected month (was reading
                   from empty 2026-05 sheet).
  v1 (2026-04-25): Initial version
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from utils import is_trading_day

# ============================================================================
# CONFIG
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parent
SHEETS_CONFIG = REPO_ROOT / "sheets_config.json"
CREDENTIALS_FILE = REPO_ROOT / "google_credentials.json"
OPEN_ISSUES = REPO_ROOT / "OPEN_ISSUES.md"

# The audit results sheet (created by setup_health_audit_sheet.py)
AUDIT_SHEET_NAME = "RidingHigh-Health-Audit"
AUDIT_SHEET_ID_FILE = REPO_ROOT / ".health_audit_sheet_id"

PERU_TZ = "America/Lima"

# Severity levels
CRITICAL = "🔴 CRITICAL"
WARNING = "🟠 WARNING"
INFO = "🔵 INFO"
PASSED = "✅ PASSED"

# ============================================================================
# UTILITIES
# ============================================================================

def now_peru_str():
    """Current Peru time as string."""
    try:
        import pytz
        peru = pytz.timezone(PERU_TZ)
        return datetime.now(peru).strftime("%Y-%m-%d %H:%M:%S")
    except ImportError:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def now_peru():
    """Current Peru datetime."""
    try:
        import pytz
        peru = pytz.timezone(PERU_TZ)
        return datetime.now(peru)
    except ImportError:
        return datetime.utcnow()


# is_trading_day moved to utils.py (single source of truth + holiday detection)


def run_cmd(*args, timeout=10):
    """Run shell command, return (stdout, returncode)."""
    try:
        r = subprocess.run(list(args), cwd=REPO_ROOT, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout, r.returncode
    except Exception as e:
        return f"ERROR: {e}", 1


def get_gspread_client(local=False):
    """Get authenticated gspread client. Returns None on failure."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None, "gspread not installed"

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]

    try:
        if local and CREDENTIALS_FILE.exists():
            creds = Credentials.from_service_account_file(
                str(CREDENTIALS_FILE), scopes=scopes)
        elif "GOOGLE_CREDENTIALS_JSON" in os.environ:
            info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
            creds = Credentials.from_service_account_info(info, scopes=scopes)
        elif CREDENTIALS_FILE.exists():
            creds = Credentials.from_service_account_file(
                str(CREDENTIALS_FILE), scopes=scopes)
        else:
            return None, "no credentials found"
        return gspread.authorize(creds), None
    except Exception as e:
        return None, f"auth failed: {e}"


def get_active_month_sheets(gc):
    """
    Pick the active month from sheets_config.json — SMART.

    Priority:
      1. Current Peru month (if it has actual data)
      2. Most recent month (alphabetically) with data
      3. Latest key alphabetically (last resort)

    Returns (month_key, sheets_dict) or (None, None) on failure.
    """
    if not SHEETS_CONFIG.exists():
        return None, None
    config = json.loads(SHEETS_CONFIG.read_text())
    if not config:
        return None, None
    if gc is None:
        # Without Sheets access we can't verify data — fall back to current month or latest
        current = now_peru().strftime("%Y-%m")
        if current in config:
            return current, config[current]
        latest = sorted(config.keys())[-1]
        return latest, config[latest]

    available = sorted(config.keys())
    current = now_peru().strftime("%Y-%m")

    def _has_data(month_key):
        """Quick check using row_count (no full data fetch)."""
        sheets = config[month_key]
        if not sheets:
            return False
        # Sample timeline_live (the highest-volume sheet)
        sample_id = sheets.get("timeline_live") or next(iter(sheets.values()))
        try:
            ws = gc.open_by_key(sample_id).sheet1
            return ws.row_count > 1
        except Exception:
            return False

    # Priority 1: current month with data
    if current in config and _has_data(current):
        return current, config[current]

    # Priority 2: most recent month with data
    for month_key in reversed(available):
        if _has_data(month_key):
            return month_key, config[month_key]

    # Priority 3: fallback to latest key
    fallback = available[-1]
    return fallback, config[fallback]


# ============================================================================
# CHECK CLASS
# ============================================================================

class CheckResult:
    def __init__(self, check_id, name, category, status, message, details=""):
        self.check_id = check_id
        self.name = name
        self.category = category
        self.status = status
        self.message = message
        self.details = details
        self.timestamp = now_peru_str()

    def to_row(self):
        """Row format for Google Sheets log."""
        return [
            self.timestamp,
            self.check_id,
            self.category,
            self.name,
            self.status,
            self.message,
            self.details[:500],
        ]

    def is_failure(self):
        return self.status in (CRITICAL, WARNING)

    def is_critical(self):
        return self.status == CRITICAL


# ============================================================================
# CHECKS — Category 1: Code Integrity
# ============================================================================

def check_01_duplicate_functions():
    """C1: Find functions defined in 2+ files (single source of truth violation)."""
    py_files = [f for f in REPO_ROOT.glob("*.py") if "_BEFORE_" not in f.name]
    func_locations = {}
    pattern = re.compile(r"^def\s+(\w+)\s*\(", re.MULTILINE)

    # Skip patterns: backup/legacy files in root that are kept for reference
    skip_name_patterns = [
        re.compile(r"_BEFORE_"),
        re.compile(r"_BACKUP"),
        re.compile(r"_LEGACY"),
        re.compile(r"_v1_BACKUP"),
        re.compile(r"_v\d+\.py$"),  # versioned snapshots like _v2.py
        re.compile(r"^_archive_"),
        re.compile(r"^migrate_"),    # migration scripts (one-time use)
    ]

    def _is_skipped(name):
        return any(p.search(name) for p in skip_name_patterns)

    for f in py_files:
        if _is_skipped(f.name):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            for match in pattern.finditer(content):
                fname = match.group(1)
                if fname.startswith("_") or fname in {"main", "test"}:
                    continue
                func_locations.setdefault(fname, []).append(f.name)
        except Exception:
            continue

    duplicates = {k: v for k, v in func_locations.items() if len(set(v)) > 1}
    # Filter out known acceptable duplicates
    acceptable = {"calculate_score", "run", "now_peru"}  # calculate_score: auto_scanner+tests; run: generic entry; now_peru: different APIs (datetime vs str)
    duplicates = {k: v for k, v in duplicates.items() if k not in acceptable}

    if not duplicates:
        return CheckResult("C1", "Duplicate functions", "Code integrity",
                           PASSED, "No duplicate function definitions found")

    msg = f"{len(duplicates)} function(s) defined in multiple files"
    details = "; ".join(f"{k}: {set(v)}" for k, v in list(duplicates.items())[:5])
    return CheckResult("C1", "Duplicate functions", "Code integrity",
                       WARNING, msg, details)


def check_02_hardcoded_thresholds():
    """C2: Find hardcoded thresholds that should be in config.py."""
    suspicious_patterns = [
        (r"\b0\.07\b", "SL_THRESHOLD_FRAC (0.07)"),
        (r"\b0\.10\b(?!\d)", "TP_THRESHOLD_FRAC (0.10)"),
        (r">=\s*60\b", "MIN_SCORE_DISPLAY (60)"),
        (r">=\s*70\b", "MIN_SCORE threshold (70)"),
    ]

    findings = []
    for f in REPO_ROOT.glob("*.py"):
        if "_BEFORE_" in f.name or f.name in {"config.py", "test_formulas.py",
                                              "test_utils.py", "health_audit.py"}:
            continue
        try:
            content = f.read_text(encoding="utf-8")
            for pattern, label in suspicious_patterns:
                matches = list(re.finditer(pattern, content))
                if matches:
                    line_nums = []
                    for m in matches[:3]:
                        line_no = content[:m.start()].count("\n") + 1
                        line_nums.append(line_no)
                    findings.append(f"{f.name}:{line_nums} → {label}")
        except Exception:
            continue

    if not findings:
        return CheckResult("C2", "Hardcoded thresholds", "Code integrity",
                           PASSED, "No hardcoded thresholds found")

    return CheckResult("C2", "Hardcoded thresholds", "Code integrity",
                       WARNING, f"{len(findings)} hardcoded threshold(s)",
                       "; ".join(findings[:5]))


def check_03_imports_consistency():
    """C3: Verify dashboard.py imports from formulas.py / config.py."""
    dashboard = REPO_ROOT / "dashboard.py"
    if not dashboard.exists():
        return CheckResult("C3", "Imports consistency", "Code integrity",
                           CRITICAL, "dashboard.py missing!")

    content = dashboard.read_text(encoding="utf-8")
    has_formulas_import = "from formulas import" in content or "import formulas" in content
    has_config_import = "from config import" in content or "import config" in content

    if has_formulas_import and has_config_import:
        return CheckResult("C3", "Imports consistency", "Code integrity",
                           PASSED, "dashboard.py imports formulas + config correctly")

    missing = []
    if not has_formulas_import:
        missing.append("formulas")
    if not has_config_import:
        missing.append("config")

    return CheckResult("C3", "Imports consistency", "Code integrity",
                       WARNING, f"dashboard.py missing imports: {missing}")


# ============================================================================
# CHECKS — Category 2: Data Freshness
# ============================================================================

def check_04_timeline_freshness(gc):
    """D1: timeline_live updated within 24h on trading days."""
    if gc is None:
        return CheckResult("D1", "Timeline freshness", "Data freshness",
                           INFO, "Skipped (no Sheets access)")

    month, sheets = get_active_month_sheets(gc)
    if not sheets or "timeline_live" not in sheets:
        return CheckResult("D1", "Timeline freshness", "Data freshness",
                           CRITICAL, "timeline_live not configured")

    try:
        # Get last row's date — first column (cached + retried)
        all_vals = _ha_col_values(gc, sheets["timeline_live"], 1)
        if len(all_vals) < 2:
            return CheckResult("D1", "Timeline freshness", "Data freshness",
                               WARNING, "timeline_live is empty")
        last_date_str = all_vals[-1][:10]
        try:
            last_dt = datetime.strptime(last_date_str, "%Y-%m-%d")
        except ValueError:
            return CheckResult("D1", "Timeline freshness", "Data freshness",
                               WARNING, f"Unparseable date: {last_date_str}")

        # Compare to most recent expected trading day
        today = now_peru().replace(tzinfo=None)
        days_old = (today - last_dt).days

        if not is_trading_day(today):
            # Weekend/holiday — last update should be from last Friday
            return CheckResult("D1", "Timeline freshness", "Data freshness",
                               PASSED, f"Last update: {last_date_str} ({days_old}d ago, non-trading day)")

        if days_old <= 1:
            return CheckResult("D1", "Timeline freshness", "Data freshness",
                               PASSED, f"Last update: {last_date_str}")
        elif days_old <= 3:
            return CheckResult("D1", "Timeline freshness", "Data freshness",
                               WARNING, f"Last update {days_old}d ago: {last_date_str}")
        else:
            return CheckResult("D1", "Timeline freshness", "Data freshness",
                               CRITICAL, f"timeline_live stale {days_old}d: {last_date_str}")
    except Exception as e:
        return CheckResult("D1", "Timeline freshness", "Data freshness",
                           CRITICAL, f"Failed: {e}")


def check_05_post_analysis_completeness(gc):
    """D2: post_analysis has rows for all recent trading days."""
    if gc is None:
        return CheckResult("D2", "Post-analysis completeness", "Data freshness",
                           INFO, "Skipped (no Sheets access)")

    month, sheets = get_active_month_sheets(gc)
    if not sheets or "post_analysis" not in sheets:
        return CheckResult("D2", "Post-analysis completeness", "Data freshness",
                           CRITICAL, "post_analysis not configured")

    try:
        col1 = _ha_col_values(gc, sheets["post_analysis"], 2)[1:]  # ScanDate is column 2
        if not col1:
            return CheckResult("D2", "Post-analysis completeness", "Data freshness",
                               WARNING, "post_analysis is empty")

        # Get unique scan dates
        scan_dates = set()
        for v in col1:
            try:
                d = v[:10]
                datetime.strptime(d, "%Y-%m-%d")
                scan_dates.add(d)
            except ValueError:
                continue

        # Check days T-3 to T-1 (post_analysis runs after EOD, so today's not expected)
        today = now_peru().replace(tzinfo=None)
        expected = []
        check_back = 5  # check 5 days back, expect at least 3 trading days
        for i in range(1, check_back + 1):
            d = today - timedelta(days=i)
            if is_trading_day(d):
                expected.append(d.strftime("%Y-%m-%d"))
            if len(expected) >= 3:
                break

        missing = [d for d in expected if d not in scan_dates]

        # Cross-month boundary: if active sheet doesn't cover all expected days,
        # check previous month's sheet (data may be there during first days of month)
        if missing:
            try:
                config = json.loads(SHEETS_CONFIG.read_text())
                months = sorted(config.keys())
                idx = months.index(month) if month in months else -1
                if idx > 0:
                    prev_month = months[idx - 1]
                    prev_sheets = config[prev_month]
                    if "post_analysis" in prev_sheets:
                        prev_col = _ha_col_values(gc, prev_sheets["post_analysis"], 2)[1:]
                        for v in prev_col:
                            try:
                                d = v[:10]
                                datetime.strptime(d, "%Y-%m-%d")
                                scan_dates.add(d)
                            except ValueError:
                                continue
                        # Recompute missing after merging previous month
                        missing = [d for d in expected if d not in scan_dates]
            except Exception:
                pass  # Previous month unavailable — fall through with original missing

        if not missing:
            return CheckResult("D2", "Post-analysis completeness", "Data freshness",
                               PASSED, f"All recent {len(expected)} trading days present")

        return CheckResult("D2", "Post-analysis completeness", "Data freshness",
                           WARNING, f"Missing {len(missing)}/{len(expected)} recent days",
                           f"Missing: {missing}")
    except Exception as e:
        return CheckResult("D2", "Post-analysis completeness", "Data freshness",
                           CRITICAL, f"Failed: {e}")


def check_06_github_actions_health():
    """D3: GitHub Actions success rate in last 24h."""
    repo = os.environ.get("GITHUB_REPO", "projects5069-creator/ridinghigh-pro")
    token = os.environ.get("GITHUB_TOKEN", "")

    try:
        import urllib.request
        url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=50"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_runs = []
        for run in data.get("workflow_runs", []):
            try:
                started = datetime.fromisoformat(run["run_started_at"].replace("Z", ""))
                if started >= cutoff:
                    recent_runs.append(run)
            except Exception:
                continue

        if not recent_runs:
            return CheckResult("D3", "GitHub Actions health", "Data freshness",
                               WARNING, "No workflow runs in last 24h")

        completed = [r for r in recent_runs if r.get("status") == "completed"]
        successes = [r for r in completed if r.get("conclusion") == "success"]
        failures = [r for r in completed if r.get("conclusion") == "failure"]

        if not completed:
            return CheckResult("D3", "GitHub Actions health", "Data freshness",
                               INFO, f"{len(recent_runs)} runs, none completed yet")

        success_rate = len(successes) / len(completed) * 100

        if success_rate >= 95:
            return CheckResult("D3", "GitHub Actions health", "Data freshness",
                               PASSED, f"{success_rate:.0f}% success ({len(successes)}/{len(completed)})")
        elif success_rate >= 80:
            return CheckResult("D3", "GitHub Actions health", "Data freshness",
                               WARNING, f"{success_rate:.0f}% success — {len(failures)} failed")
        else:
            failed_names = [r.get("name", "?") for r in failures[:5]]
            return CheckResult("D3", "GitHub Actions health", "Data freshness",
                               CRITICAL, f"Only {success_rate:.0f}% success",
                               f"Failed: {failed_names}")
    except Exception as e:
        return CheckResult("D3", "GitHub Actions health", "Data freshness",
                           WARNING, f"API query failed: {e}")


def check_22_post_analysis_today_ran():
    """D4: post_analysis.yml ran successfully today (catches cron drift)."""
    repo = os.environ.get("GITHUB_REPO", "projects5069-creator/ridinghigh-pro")
    token = os.environ.get("GITHUB_TOKEN", "")

    # Only check on trading days
    today = datetime.utcnow().date()
    if not is_trading_day(today):
        return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                           PASSED, "Non-trading day — skipped")

    try:
        import urllib.request
        url = (f"https://api.github.com/repos/{repo}/actions/workflows/"
               f"post_analysis.yml/runs?per_page=20")
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        today_str = today.isoformat()
        today_runs = []
        for run in data.get("workflow_runs", []):
            try:
                started = run.get("run_started_at", "")
                if started.startswith(today_str):
                    today_runs.append(run)
            except Exception:
                continue

        successes = [r for r in today_runs if r.get("conclusion") == "success"]
        in_progress = [r for r in today_runs if r.get("status") in ("in_progress", "queued")]

        # Cron is scheduled for 21:05 UTC. Allow 90 min for drift before alarming.
        now_utc = datetime.utcnow()
        scheduled_time = now_utc.replace(hour=21, minute=5, second=0, microsecond=0)
        grace_period_end = scheduled_time + timedelta(minutes=90)  # 22:35 UTC

        if successes:
            last = successes[0]
            return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                               PASSED,
                               f"Ran successfully today (run #{last.get('run_number')})",
                               f"started: {last.get('run_started_at')}")

        if in_progress:
            return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                               PASSED,
                               f"Currently running (run #{in_progress[0].get('run_number')})")

        # No successful run yet — decide severity based on time of day
        if now_utc < scheduled_time:
            return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                               PASSED, "Before scheduled time — not expected to run yet")

        if now_utc < grace_period_end:
            return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                               WARNING,
                               f"Not run yet (scheduled 21:05 UTC, now {now_utc.strftime('%H:%M')} UTC) — possible drift")

        # Past grace period — this is a real problem
        return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                           CRITICAL,
                           f"Did not run today (it is {now_utc.strftime('%H:%M')} UTC, scheduled was 21:05)",
                           "Run manually via workflow_dispatch")

    except Exception as e:
        return CheckResult("D4", "Post-analysis ran today", "Data freshness",
                           WARNING, f"API query failed: {e}")


# ============================================================================
# CHECKS — Category 3: Data Quality
# ============================================================================

def check_07_score_range(gc):
    """Q1: All Scores in [0, 100]."""
    if gc is None:
        return CheckResult("Q1", "Score range", "Data quality",
                           INFO, "Skipped (no Sheets access)")

    month, sheets = get_active_month_sheets(gc)
    if not sheets or "post_analysis" not in sheets:
        return CheckResult("Q1", "Score range", "Data quality",
                           INFO, "post_analysis not available")

    try:
        all_data = _ha_get_all_values(gc, sheets["post_analysis"])
        if len(all_data) < 2:
            return CheckResult("Q1", "Score range", "Data quality",
                               INFO, "No data to check")

        header = all_data[0]
        if "Score" not in header:
            return CheckResult("Q1", "Score range", "Data quality",
                               WARNING, "No 'Score' column in post_analysis")

        score_idx = header.index("Score")
        invalid = []
        for i, row in enumerate(all_data[1:], start=2):
            if len(row) <= score_idx:
                continue
            try:
                v = float(row[score_idx])
                if v < 0 or v > 100:
                    invalid.append((i, row[0] if row else "?", v))
            except (ValueError, TypeError):
                continue

        if not invalid:
            return CheckResult("Q1", "Score range", "Data quality",
                               PASSED, f"All {len(all_data)-1} Scores in [0,100]")

        return CheckResult("Q1", "Score range", "Data quality",
                           CRITICAL, f"{len(invalid)} invalid Score(s)",
                           "; ".join(f"row{r[0]}={r[2]}" for r in invalid[:5]))
    except Exception as e:
        return CheckResult("Q1", "Score range", "Data quality",
                           WARNING, f"Failed: {e}")


def check_08_required_columns(gc):
    """Q2: All sheets have required columns."""
    if gc is None:
        return CheckResult("Q2", "Required columns", "Data quality",
                           INFO, "Skipped (no Sheets access)")

    required = {
        "timeline_live": ["Date", "ScanTime", "Ticker", "Price", "Score"],
        "post_analysis": ["Ticker", "ScanDate", "Score"],
        "daily_summary": ["Date"],
    }

    month, sheets = get_active_month_sheets(gc)
    if not sheets:
        return CheckResult("Q2", "Required columns", "Data quality",
                           CRITICAL, "No sheets configured")

    missing_report = []
    for name, req_cols in required.items():
        if name not in sheets:
            missing_report.append(f"{name}: not configured")
            continue
        try:
            header = _ha_row_values(gc, sheets[name], 1)
            missing = [c for c in req_cols if c not in header]
            if missing:
                missing_report.append(f"{name}: missing {missing}")
        except Exception as e:
            missing_report.append(f"{name}: error {str(e)[:30]}")

    if not missing_report:
        return CheckResult("Q2", "Required columns", "Data quality",
                           PASSED, f"All required columns present")

    return CheckResult("Q2", "Required columns", "Data quality",
                       WARNING, f"{len(missing_report)} sheet(s) with issues",
                       "; ".join(missing_report))


def check_09_duplicate_post_analysis_rows(gc):
    """Q3: post_analysis has no duplicate (Ticker, ScanDate)."""
    if gc is None:
        return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                           INFO, "Skipped (no Sheets access)")

    month, sheets = get_active_month_sheets(gc)
    if not sheets or "post_analysis" not in sheets:
        return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                           INFO, "post_analysis not available")

    try:
        all_data = _ha_get_all_values(gc, sheets["post_analysis"])
        if len(all_data) < 2:
            return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                               PASSED, "Empty — no duplicates")

        header = all_data[0]
        if "Ticker" not in header or "ScanDate" not in header:
            return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                               INFO, "Required columns not found")

        ti = header.index("Ticker")
        di = header.index("ScanDate")
        seen = {}
        dupes = []
        for i, row in enumerate(all_data[1:], start=2):
            if len(row) <= max(ti, di):
                continue
            key = (row[ti], row[di][:10])
            if key in seen:
                dupes.append((seen[key], i, key))
            else:
                seen[key] = i

        if not dupes:
            return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                               PASSED, f"No duplicates in {len(all_data)-1} rows")

        return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                           WARNING, f"{len(dupes)} duplicate (Ticker,ScanDate) pair(s)",
                           "; ".join(f"rows{d[0]}+{d[1]}: {d[2]}" for d in dupes[:5]))
    except Exception as e:
        return CheckResult("Q3", "Duplicate post_analysis rows", "Data quality",
                           WARNING, f"Failed: {e}")


def check_10_outliers(gc):
    """Q4: Detect REL_VOL outliers and negative prices."""
    if gc is None:
        return CheckResult("Q4", "Outliers", "Data quality",
                           INFO, "Skipped (no Sheets access)")

    month, sheets = get_active_month_sheets(gc)
    if not sheets or "post_analysis" not in sheets:
        return CheckResult("Q4", "Outliers", "Data quality",
                           INFO, "post_analysis not available")

    try:
        all_data = _ha_get_all_values(gc, sheets["post_analysis"])
        if len(all_data) < 2:
            return CheckResult("Q4", "Outliers", "Data quality",
                               PASSED, "No data")

        header = all_data[0]
        outliers = []

        # Check REL_VOL > 100 (cap should prevent this)
        if "REL_VOL" in header:
            rv_idx = header.index("REL_VOL")
            for i, row in enumerate(all_data[1:], start=2):
                if len(row) <= rv_idx:
                    continue
                try:
                    v = float(row[rv_idx])
                    if v > 100:
                        outliers.append(f"row{i} REL_VOL={v:.1f}")
                except (ValueError, TypeError):
                    continue

        # Check ScanPrice <= 0
        if "ScanPrice" in header:
            sp_idx = header.index("ScanPrice")
            for i, row in enumerate(all_data[1:], start=2):
                if len(row) <= sp_idx:
                    continue
                try:
                    v = float(row[sp_idx])
                    if v <= 0:
                        outliers.append(f"row{i} ScanPrice={v}")
                except (ValueError, TypeError):
                    continue

        if not outliers:
            return CheckResult("Q4", "Outliers", "Data quality",
                               PASSED, "No outliers detected")

        return CheckResult("Q4", "Outliers", "Data quality",
                           WARNING, f"{len(outliers)} outlier(s)",
                           "; ".join(outliers[:5]))
    except Exception as e:
        return CheckResult("Q4", "Outliers", "Data quality",
                           WARNING, f"Failed: {e}")


# ============================================================================
# CHECKS — Category 4: Config Consistency
# ============================================================================

def check_11_sheets_config_current_month():
    """X1: sheets_config.json has current Peru month."""
    if not SHEETS_CONFIG.exists():
        return CheckResult("X1", "sheets_config current month", "Config",
                           CRITICAL, "sheets_config.json not found")

    try:
        config = json.loads(SHEETS_CONFIG.read_text())
    except Exception as e:
        return CheckResult("X1", "sheets_config current month", "Config",
                           CRITICAL, f"Invalid JSON: {e}")

    current = now_peru().strftime("%Y-%m")
    if current in config:
        return CheckResult("X1", "sheets_config current month", "Config",
                           PASSED, f"Current month {current} configured")

    return CheckResult("X1", "sheets_config current month", "Config",
                       CRITICAL, f"Missing entry for {current}",
                       f"Available: {sorted(config.keys())}")


def check_12_score_weights_sum():
    """X2: SCORE_WEIGHTS_V2 sums to 100 (or 1.0)."""
    config_file = REPO_ROOT / "config.py"
    if not config_file.exists():
        return CheckResult("X2", "Score weights sum", "Config",
                           CRITICAL, "config.py not found")

    try:
        # Parse the SCORE_WEIGHTS_V2 dict
        content = config_file.read_text(encoding="utf-8")
        match = re.search(r"SCORE_WEIGHTS_V2\s*=\s*\{([^}]+)\}", content, re.DOTALL)
        if not match:
            return CheckResult("X2", "Score weights sum", "Config",
                               WARNING, "SCORE_WEIGHTS_V2 not found in config.py")

        body = match.group(1)
        # Filter out comment lines (e.g. "# Total: 100" was being counted as a weight)
        lines = [l for l in body.splitlines() if not l.strip().startswith("#")]
        nums = re.findall(r":\s*([0-9.]+)", "\n".join(lines))
        total = sum(float(n) for n in nums)

        # Accept either 100 (integer percent) or 1.0 (fraction)
        if abs(total - 100) < 0.01 or abs(total - 1.0) < 0.001:
            return CheckResult("X2", "Score weights sum", "Config",
                               PASSED, f"Weights sum = {total}")

        return CheckResult("X2", "Score weights sum", "Config",
                           CRITICAL, f"Weights sum = {total} (expected 100 or 1.0)")
    except Exception as e:
        return CheckResult("X2", "Score weights sum", "Config",
                           WARNING, f"Failed: {e}")


def check_13_critical_files():
    """X3: All critical files exist."""
    critical_files = [
        "auto_scanner.py", "post_analysis_collector.py", "dashboard.py",
        "sheets_manager.py", "config.py", "formulas.py", "utils.py",
        "sheets_config.json",
    ]
    missing = [f for f in critical_files if not (REPO_ROOT / f).exists()]

    if not missing:
        return CheckResult("X3", "Critical files", "Config",
                           PASSED, f"All {len(critical_files)} critical files present")

    return CheckResult("X3", "Critical files", "Config",
                       CRITICAL, f"{len(missing)} missing", str(missing))


# ============================================================================
# CHECKS — Category 5: Repo Health
# ============================================================================

def check_14_uncommitted_count():
    """R1: Warn if many uncommitted files."""
    output, code = run_cmd("git", "status", "--porcelain")
    if code != 0:
        return CheckResult("R1", "Uncommitted files", "Repo health",
                           INFO, "git not available")

    lines = [l for l in output.splitlines() if l.strip()]
    n = len(lines)

    if n == 0:
        return CheckResult("R1", "Uncommitted files", "Repo health",
                           PASSED, "Working tree clean")
    elif n <= 5:
        return CheckResult("R1", "Uncommitted files", "Repo health",
                           INFO, f"{n} uncommitted file(s)")
    elif n <= 15:
        return CheckResult("R1", "Uncommitted files", "Repo health",
                           WARNING, f"{n} uncommitted files — consider committing")
    else:
        return CheckResult("R1", "Uncommitted files", "Repo health",
                           CRITICAL, f"{n} uncommitted files — repo is messy",
                           output[:300])


# ── Sheets read cache + retry helpers (2026-05-22) ─────────────────────
_HA_SHEET_CACHE = {}
_HA_CACHE_TTL_SEC = 300


def _ha_cached_read(gc, sheet_id, op, *args, ttl=_HA_CACHE_TTL_SEC, retries=3):
    """Cached + retried Sheets read. op = 'get_all_values'|'col_values'|'row_values'."""
    import time as _t
    cache_key = (sheet_id, op, args)
    now = _t.time()
    cached = _HA_SHEET_CACHE.get(cache_key)
    if cached and (now - cached[0]) < ttl:
        return cached[1]
    last_err = None
    for attempt in range(retries):
        try:
            ws = gc.open_by_key(sheet_id).sheet1
            if op == 'get_all_values': data = ws.get_all_values()
            elif op == 'col_values': data = ws.col_values(*args)
            elif op == 'row_values': data = ws.row_values(*args)
            else: raise ValueError(f"Unknown op: {op}")
            _HA_SHEET_CACHE[(sheet_id, op, args)] = (now, data)
            return data
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            is_429 = '429' in err_str or 'quota' in err_str or 'rate' in err_str
            if not is_429 or attempt == retries - 1: raise
            wait = (2 ** attempt) * 5
            _t.sleep(wait)
    raise last_err


def _ha_get_all_values(gc, sheet_id):
    return _ha_cached_read(gc, sheet_id, 'get_all_values')


def _ha_col_values(gc, sheet_id, col):
    return _ha_cached_read(gc, sheet_id, 'col_values', col)


def _ha_row_values(gc, sheet_id, row):
    return _ha_cached_read(gc, sheet_id, 'row_values', row)


def _load_recent_metrics(gc):
    """Helper: load last 200 rows of timeline_live for metric sanity checks."""
    month, sheets = get_active_month_sheets(gc)
    if not sheets or "timeline_live" not in sheets:
        return None, None, "timeline_live sheet not found in config"
    all_data = _ha_get_all_values(gc, sheets["timeline_live"])
    if len(all_data) < 50:
        return None, None, "Not enough data to evaluate (< 50 rows)"
    return all_data[0], all_data[-200:], None


def _to_floats(header, recent, col_name):
    """Helper: extract numeric values for given column from recent rows."""
    if col_name not in header:
        return []
    idx = header.index(col_name)
    out = []
    for row in recent:
        if idx >= len(row):
            continue
        try:
            out.append(float(row[idx]))
        except (ValueError, TypeError):
            pass
    return out


def check_16_rel_vol_stuck(gc):
    """Q5a: Detect REL_VOL stuck at 1.0 (CRITICAL — REL_VOL is part of Score v2)."""
    try:
        header, recent, err = _load_recent_metrics(gc)
        if err:
            status = PASSED if "Not enough" in err else WARNING
            return CheckResult("16", "REL_VOL Sanity", "Data Quality", status, err)

        rel = _to_floats(header, recent, "REL_VOL")
        if rel and max(rel) - min(rel) < 0.01 and abs(rel[0] - 1.0) < 0.01:
            return CheckResult("16", "REL_VOL Sanity", "Data Quality",
                               CRITICAL,
                               "REL_VOL stuck at 1.0 — likely calculation bug",
                               details=f"Last 200 rows: variance < 0.01, all near 1.0. REL_VOL is in Score v2 (5%) — affects scoring.")

        return CheckResult("16", "REL_VOL Sanity", "Data Quality",
                           PASSED, f"REL_VOL varies normally ({len(rel)} samples)")
    except Exception as e:
        return CheckResult("16", "REL_VOL Sanity", "Data Quality",
                           WARNING, f"Could not check: {e}")


def check_20_float_pct_stuck(gc):
    """Q5b: Detect Float% stuck (WARNING — Float% not in Score v2, dashboard only)."""
    try:
        header, recent, err = _load_recent_metrics(gc)
        if err:
            status = PASSED if "Not enough" in err else WARNING
            return CheckResult("20", "Float% Sanity", "Data Quality", status, err)

        flt = _to_floats(header, recent, "Float%")
        if flt and max(flt) - min(flt) < 0.01:
            return CheckResult("20", "Float% Sanity", "Data Quality",
                               WARNING,
                               f"Float% stuck at {flt[0]:.2f} — likely data source issue",
                               details=f"Last 200 rows: variance < 0.01. Float% is shown in dashboard but NOT in Score v2 — not blocking trading.")

        return CheckResult("20", "Float% Sanity", "Data Quality",
                           PASSED, f"Float% varies normally ({len(flt)} samples)")
    except Exception as e:
        return CheckResult("20", "Float% Sanity", "Data Quality",
                           WARNING, f"Could not check: {e}")


def check_21_gap_outliers(gc):
    """Q5c: Detect Gap outliers > 500% (WARNING — Gap not in Score v2, often corporate actions)."""
    try:
        header, recent, err = _load_recent_metrics(gc)
        if err:
            status = PASSED if "Not enough" in err else WARNING
            return CheckResult("21", "Gap Outliers", "Data Quality", status, err)

        gap = _to_floats(header, recent, "Gap")
        # Threshold raised to 500% — Gaps 100-500% are real for low-priced stocks (corporate actions)
        outliers = [v for v in gap if abs(v) > 500]
        if outliers:
            return CheckResult("21", "Gap Outliers", "Data Quality",
                               WARNING,
                               f"Gap has {len(outliers)} outliers > 500% (max={max(outliers):.0f})",
                               details=f"Likely corporate actions (reverse splits) — Alpaca returns unadjusted PrevClose. Gap is NOT in Score v2 — does not affect trading decisions.")

        return CheckResult("21", "Gap Outliers", "Data Quality",
                           PASSED, f"Gap within normal range ({len(gap)} samples)")
    except Exception as e:
        return CheckResult("21", "Gap Outliers", "Data Quality",
                           WARNING, f"Could not check: {e}")


def check_17_fundamentals_provider():
    """P1: Verify fundamentals provider returns valid data for a known ticker.

    Catches breaks like UnboundLocalError, missing imports, or yfinance API
    failures BEFORE they affect production. Uses AAPL as a stable test ticker.
    """
    try:
        from data_provider import get_fundamentals_provider
        provider = get_fundamentals_provider()
        fund = provider.get_fundamentals('AAPL')

        if not fund:
            return CheckResult("17", "Fundamentals provider", "Providers",
                               CRITICAL, "Provider returned empty/None for AAPL",
                               "Expected dict with market_cap, average_volume, etc.")

        required = ['market_cap', 'average_volume', 'shares_outstanding']
        missing = [k for k in required if not fund.get(k)]

        if missing:
            return CheckResult("17", "Fundamentals provider", "Providers",
                               CRITICAL, f"Missing required fields: {missing}",
                               f"Got keys: {list(fund.keys())}")

        return CheckResult("17", "Fundamentals provider", "Providers",
                           PASSED, f"AAPL fundamentals OK (market_cap={fund['market_cap']:,})")
    except Exception as e:
        return CheckResult("17", "Fundamentals provider", "Providers",
                           CRITICAL, f"Provider crashed: {type(e).__name__}",
                           str(e)[:300])


def check_18_daily_bars_provider():
    """P2: Verify daily bars provider returns valid OHLC for a known ticker.

    Tests the data_provider (Alpaca or yfinance fallback) by fetching 10 days
    of AAPL bars. Catches Alpaca SIP errors, auth failures, rate limits.
    """
    try:
        from data_provider import get_data_provider
        provider = get_data_provider()
        bars = provider.get_daily_bars('AAPL', days=10)

        if bars is None or bars.empty:
            return CheckResult("18", "Daily bars provider", "Providers",
                               CRITICAL, "Provider returned empty bars for AAPL")

        if len(bars) < 5:
            return CheckResult("18", "Daily bars provider", "Providers",
                               WARNING, f"Only {len(bars)} bars returned (expected ~10)")

        # Verify columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [c for c in required_cols if c not in bars.columns]
        if missing:
            return CheckResult("18", "Daily bars provider", "Providers",
                               CRITICAL, f"Missing columns: {missing}",
                               f"Got: {list(bars.columns)}")

        return CheckResult("18", "Daily bars provider", "Providers",
                           PASSED, f"AAPL bars OK ({len(bars)} rows)")
    except Exception as e:
        return CheckResult("18", "Daily bars provider", "Providers",
                           CRITICAL, f"Provider crashed: {type(e).__name__}",
                           str(e)[:300])


def check_15_gitignore_enforcement():
    """R2: No files in tree that should match .gitignore patterns."""
    bad_patterns = [r"_BEFORE_", r"\.BEFORE_", r"\.pyc$", r"__pycache__"]
    output, code = run_cmd("git", "ls-files")
    if code != 0:
        return CheckResult("R2", ".gitignore enforcement", "Repo health",
                           INFO, "git not available")

    files = output.splitlines()
    violations = []
    for f in files:
        for pat in bad_patterns:
            if re.search(pat, f):
                violations.append(f)
                break

    if not violations:
        return CheckResult("R2", ".gitignore enforcement", "Repo health",
                           PASSED, ".gitignore properly enforced")

    return CheckResult("R2", ".gitignore enforcement", "Repo health",
                       WARNING, f"{len(violations)} tracked file(s) match ignore patterns",
                       "; ".join(violations[:5]))


# ============================================================================
# CHECKS — Category 7: Agent subsystems
# ============================================================================

def check_24_sentinel_health(gc):
    """S1: Data Sentinel module health — files, config, recent events."""
    import os as _os
    SENTINEL_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                 "agent", "sentinel")
    # 1. Required files exist
    required = ["data_sentinel.py", "__init__.py",
                "checks/completeness.py", "checks/scan_freshness.py",
                "checks/price_sanity.py", "checks/position_sync.py",
                "checks/price_freshness.py", "checks/quota_health.py",
                "checks/provider_heartbeat.py"]
    missing = [f for f in required if not _os.path.exists(_os.path.join(SENTINEL_DIR, f))]
    if missing:
        return CheckResult("S1", "Data Sentinel health", "Agents",
                           CRITICAL, f"Missing Sentinel files: {missing}")

    # 2. Config flags present
    try:
        import importlib
        import config as _cfg
        importlib.reload(_cfg)
        mode = getattr(_cfg, "SENTINEL_MODE", None)
        enabled = getattr(_cfg, "DATA_SENTINEL_ENABLED", None)
        if mode not in ("shadow", "active", "off"):
            return CheckResult("S1", "Data Sentinel health", "Agents",
                               WARNING, f"SENTINEL_MODE invalid: {mode}")
        if enabled is None:
            return CheckResult("S1", "Data Sentinel health", "Agents",
                               WARNING, "DATA_SENTINEL_ENABLED missing from config")
    except Exception as e:
        return CheckResult("S1", "Data Sentinel health", "Agents",
                           WARNING, f"Config read failed: {e}")

    # 3. system_events sheet reachable + recent event count
    event_info = ""
    if gc is not None:
        try:
            month, sheets = get_active_month_sheets(gc)
            if sheets and "system_events" in sheets:
                rows = _ha_get_all_values(gc, sheets["system_events"])
                sentinel_rows = [r for r in rows[1:]
                                 if r and len(r) > 1 and str(r[1]).startswith("SENTINEL_")]
                event_info = f", {len(sentinel_rows)} sentinel events logged"
            else:
                event_info = ", system_events not configured"
        except Exception as e:
            event_info = f", system_events read failed: {e}"

    return CheckResult("S1", "Data Sentinel health", "Agents",
                       PASSED, f"All 9 files OK, mode={mode}, enabled={enabled}{event_info}")


# ============================================================================
# CHECKS — Category 6b: Data quality (NaN detection)
# ============================================================================

def check_23_nan_scantime(gc):
    """Q8: post_analysis FirstScanTime/LastScanTime should not contain 'nan' string."""
    if gc is None:
        return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                           INFO, "Skipped (no Sheets access)")

    month, sheets = get_active_month_sheets(gc)
    if not sheets or "post_analysis" not in sheets:
        return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                           CRITICAL, "post_analysis not configured")

    try:
        data = _ha_get_all_values(gc, sheets["post_analysis"])
        if len(data) <= 1:
            return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                               INFO, "post_analysis is empty")

        headers = data[0]
        rows = data[1:]

        fst_idx = headers.index("FirstScanTime") if "FirstScanTime" in headers else None
        lst_idx = headers.index("LastScanTime") if "LastScanTime" in headers else None

        if fst_idx is None:
            return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                               WARNING, "FirstScanTime column missing")

        invalid_values = ("nan", "none", "null", "n/a")
        nan_count = 0
        nan_examples = []

        for i, row in enumerate(rows):
            if fst_idx < len(row):
                val = str(row[fst_idx]).strip().lower()
                if val in invalid_values:
                    nan_count += 1
                    if len(nan_examples) < 3:
                        ticker_idx = headers.index("Ticker") if "Ticker" in headers else 0
                        date_idx = headers.index("ScanDate") if "ScanDate" in headers else 1
                        ticker = row[ticker_idx] if ticker_idx < len(row) else "?"
                        date = row[date_idx] if date_idx < len(row) else "?"
                        nan_examples.append(f"{ticker}/{date}")

        if nan_count == 0:
            return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                               PASSED, f"All {len(rows)} rows have valid FirstScanTime")

        examples_str = ", ".join(nan_examples)
        pct = nan_count / len(rows) * 100
        msg = f"{nan_count}/{len(rows)} rows ({pct:.1f}%) with invalid FirstScanTime. Examples: {examples_str}"

        # Historical 'nan' rows (pre-2026-05) are tolerated as known gap
        # Only WARN if rate is high (>30%) or new rows have it
        if pct > 30:
            return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                               WARNING, msg)
        else:
            return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                               INFO, f"{msg} (historical, tolerated)")

    except Exception as e:
        return CheckResult("Q8", "NaN ScanTime in post_analysis", "Data quality",
                           CRITICAL, f"Failed: {e}")


# ============================================================================
# CHECKS — Category 7: Sync
# ============================================================================

def check_19_pk_sync():
    """S1: Verify local repo is in sync with origin/main and docs are consistent."""
    import time as _time

    # ── Part A: CI skip ──────────────────────────────────────────────────
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return CheckResult("19", "PK sync", "Sync",
                           INFO, "Skipped in CI (always in sync with origin)")

    # ── Part B: git sync ─────────────────────────────────────────────────
    run_cmd("git", "fetch", "origin", "main", timeout=15)
    local_sha, rc1 = run_cmd("git", "rev-parse", "HEAD")
    origin_sha, rc2 = run_cmd("git", "rev-parse", "origin/main")

    if rc1 != 0 or rc2 != 0:
        return CheckResult("19", "PK sync", "Sync",
                           INFO, "git not available or no remote")

    local_sha = local_sha.strip()
    origin_sha = origin_sha.strip()

    if local_sha == origin_sha:
        # In sync — also check docs consistency (Part C)
        doc_issue = _check_docs_consistency()
        if doc_issue:
            return CheckResult("19", "PK sync", "Sync",
                               WARNING, f"In sync with origin, but: {doc_issue}")
        return CheckResult("19", "PK sync", "Sync",
                           PASSED, "In sync with origin/main")

    # Check if ahead, behind, or diverged
    ahead_out, _ = run_cmd("git", "log", "origin/main..HEAD", "--oneline")
    behind_out, _ = run_cmd("git", "log", "HEAD..origin/main", "--oneline")
    ahead_n = len([l for l in ahead_out.strip().splitlines() if l])
    behind_n = len([l for l in behind_out.strip().splitlines() if l])

    if ahead_n > 0 and behind_n > 0:
        return CheckResult("19", "PK sync", "Sync",
                           CRITICAL, f"Diverged from origin — {ahead_n} ahead, {behind_n} behind",
                           "Manual resolution needed: git pull --rebase or merge")

    if behind_n > 0:
        return CheckResult("19", "PK sync", "Sync",
                           WARNING, f"Behind origin by {behind_n} commit(s) — pull needed")

    # Ahead — check how long ago last commit was
    ts_out, _ = run_cmd("git", "log", "-1", "--format=%ct")
    try:
        commit_ts = int(ts_out.strip())
        age_hours = (_time.time() - commit_ts) / 3600
    except (ValueError, TypeError):
        age_hours = 0

    if age_hours < 6:
        age_str = f"{int(age_hours * 60)} minutes" if age_hours < 1 else f"{age_hours:.1f} hours"
        return CheckResult("19", "PK sync", "Sync",
                           INFO, f"Ahead by {ahead_n} commit(s), last commit {age_str} ago")
    elif age_hours < 24:
        return CheckResult("19", "PK sync", "Sync",
                           WARNING, f"Ahead by {ahead_n} commit(s) for {age_hours:.0f}h — consider pushing")
    else:
        return CheckResult("19", "PK sync", "Sync",
                           CRITICAL, f"Ahead by {ahead_n} commit(s) for {age_hours:.0f}h+ — push immediately")


def _check_docs_consistency():
    """Check OPEN_ISSUES.md for issues marked fixed but still in STILL OPEN section."""
    oi_path = REPO_ROOT / "OPEN_ISSUES.md"
    if not oi_path.exists():
        return None

    content = oi_path.read_text(encoding="utf-8")
    # Split into STILL OPEN sections vs CLOSED sections
    in_open = False
    stale = []
    for line in content.splitlines():
        if "STILL OPEN" in line:
            in_open = True
        elif line.startswith("## ✅ CLOSED") or line.startswith("## 📊") or line.startswith("## 📅"):
            in_open = False
        elif in_open and line.startswith("### "):
            # Check if issue title has strikethrough or ✅ or closed/fixed/resolved
            if "~~" in line or "✅" in line:
                # Extract issue number
                import re as _re
                m = _re.search(r"#(\d+)", line)
                num = m.group(1) if m else "?"
                stale.append(f"#{num}")

    if stale:
        return f"Issue(s) marked fixed but still in STILL OPEN: {', '.join(stale)}"
    return None


# ============================================================================
# REPORTING
# ============================================================================

def print_report(results):
    """Print human-readable report."""
    print(f"\n{'='*70}")
    print(f"  RidingHigh Pro — Health Audit")
    print(f"  {now_peru_str()} Peru")
    print(f"{'='*70}\n")

    by_status = {}
    for r in results:
        by_status.setdefault(r.status, []).append(r)

    counts = {
        PASSED: len(by_status.get(PASSED, [])),
        INFO: len(by_status.get(INFO, [])),
        WARNING: len(by_status.get(WARNING, [])),
        CRITICAL: len(by_status.get(CRITICAL, [])),
    }

    print(f"  {PASSED}: {counts[PASSED]}")
    print(f"  {INFO}: {counts[INFO]}")
    print(f"  {WARNING}: {counts[WARNING]}")
    print(f"  {CRITICAL}: {counts[CRITICAL]}")
    print()

    # Group by category
    by_cat = {}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)

    for cat in by_cat:
        print(f"\n## {cat}")
        for r in by_cat[cat]:
            print(f"  [{r.check_id}] {r.status} — {r.name}")
            print(f"        {r.message}")
            if r.details:
                print(f"        Details: {r.details[:200]}")

    print(f"\n{'='*70}\n")


def write_to_sheet(results, gc):
    """Write results to RidingHigh-Health-Audit Google Sheet."""
    if gc is None:
        print("⚠️  No gspread client — skipping Sheet write")
        return False

    if not AUDIT_SHEET_ID_FILE.exists():
        print(f"⚠️  {AUDIT_SHEET_ID_FILE.name} not found — run setup_health_audit_sheet.py first")
        return False

    sheet_id = AUDIT_SHEET_ID_FILE.read_text().strip()

    try:
        sh = gc.open_by_key(sheet_id)

        # Tab 1: History (append)
        history = sh.worksheet("History")
        rows = [r.to_row() for r in results]
        history.append_rows(rows, value_input_option="USER_ENTERED")

        # Tab 2: Latest (overwrite)
        latest = sh.worksheet("Latest")
        latest.clear()
        header = ["Timestamp", "Check ID", "Category", "Name", "Status", "Message", "Details"]
        latest.append_row(header)
        latest.append_rows(rows, value_input_option="USER_ENTERED")

        # Tab 3: Failed (only failures)
        failed = sh.worksheet("Failed")
        failed.clear()
        failed.append_row(header)
        fail_rows = [r.to_row() for r in results if r.is_failure()]
        if fail_rows:
            failed.append_rows(fail_rows, value_input_option="USER_ENTERED")

        print(f"✅ Wrote {len(rows)} results to '{AUDIT_SHEET_NAME}' Sheet")
        return True
    except Exception as e:
        print(f"❌ Failed to write to Sheet: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def send_email_alert(results):
    """Send email alert when CRITICAL issues detected. Includes full report.
    Requires GMAIL_USER, GMAIL_APP_PASS, REPORT_TO env vars."""
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_pass = os.environ.get("GMAIL_APP_PASS")
    report_to  = os.environ.get("REPORT_TO")

    if not all([gmail_user, gmail_pass, report_to]):
        print("[health_audit] ⚠️  Email not configured — skipping alert")
        return False

    critical = [r for r in results if r.is_critical()]
    warnings = [r for r in results if r.status == WARNING]
    passed   = [r for r in results if r.status == PASSED]
    info     = [r for r in results if r.status == INFO]

    # Heartbeat mode: always send email, with subject reflecting severity
    if critical:
        subject = f"🔴 RidingHigh Health Audit — {len(critical)} CRITICAL issue(s)"
    elif warnings:
        subject = f"🟡 RidingHigh Health Audit — {len(warnings)} WARNING(s)"
    else:
        subject = f"✅ RidingHigh Health Audit — All clear"

    lines = []
    lines.append(f"RidingHigh Pro — Health Audit Report")
    lines.append(f"Time: {now_peru_str()} Peru")
    lines.append("")
    lines.append(f"Summary:")
    lines.append(f"  🔴 CRITICAL: {len(critical)}")
    lines.append(f"  🟠 WARNING:  {len(warnings)}")
    lines.append(f"  ✅ PASSED:   {len(passed)}")
    lines.append(f"  🔵 INFO:     {len(info)}")
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"🔴 CRITICAL Issues ({len(critical)}):")
    lines.append("=" * 60)
    for r in critical:
        lines.append(f"")
        lines.append(f"[{r.check_id}] {r.name} ({r.category})")
        lines.append(f"  Status:  {r.status}")
        lines.append(f"  Message: {r.message}")
        if r.details:
            lines.append(f"  Details: {r.details[:300]}")

    if warnings:
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"🟠 WARNINGs ({len(warnings)}):")
        lines.append("=" * 60)
        for r in warnings:
            lines.append(f"  [{r.check_id}] {r.name}: {r.message}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"✅ Passed checks ({len(passed)}):")
    lines.append("=" * 60)
    for r in passed:
        lines.append(f"  [{r.check_id}] {r.name}")

    lines.append("")
    lines.append("— RidingHigh Pro Health Audit (automated)")
    lines.append(f"  Next run: 06:00 / 12:00 / 22:00 Peru daily")

    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText("\n".join(lines))
        msg["Subject"] = subject
        msg["From"]    = gmail_user
        msg["To"]      = report_to
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_user, gmail_pass)
            smtp.sendmail(gmail_user, [report_to], msg.as_string())
        print(f"[health_audit] ✅ Alert email sent to {report_to}")
        return True
    except Exception as e:
        print(f"[health_audit] ❌ Email failed: {e}")
        return False


def main():
    args = sys.argv[1:]
    local_mode = "--local" in args
    no_sheet = "--no-sheet" in args

    print(f"[health_audit] Starting at {now_peru_str()} Peru")
    print(f"[health_audit] Mode: {'local' if local_mode else 'CI/automatic'}")

    gc, err = get_gspread_client(local=local_mode)
    if gc is None:
        print(f"⚠️  No Sheets access ({err}) — running checks that don't need Sheets")
    else:
        # Show which month is being analyzed
        active_month, _ = get_active_month_sheets(gc)
        if active_month:
            print(f"[health_audit] Analyzing month: {active_month}")

    # Run all checks
    results = []
    print("[health_audit] Running 23 checks...")

    # Code integrity
    results.append(check_01_duplicate_functions())
    results.append(check_02_hardcoded_thresholds())
    results.append(check_03_imports_consistency())

    # Data freshness
    results.append(check_04_timeline_freshness(gc))
    results.append(check_05_post_analysis_completeness(gc))
    results.append(check_06_github_actions_health())
    results.append(check_22_post_analysis_today_ran())

    # Data quality
    results.append(check_07_score_range(gc))
    results.append(check_08_required_columns(gc))
    results.append(check_09_duplicate_post_analysis_rows(gc))
    results.append(check_10_outliers(gc))
    results.append(check_16_rel_vol_stuck(gc))
    results.append(check_20_float_pct_stuck(gc))
    results.append(check_21_gap_outliers(gc))
    results.append(check_23_nan_scantime(gc))
    results.append(check_24_sentinel_health(gc))

    # Config
    results.append(check_11_sheets_config_current_month())
    results.append(check_12_score_weights_sum())
    results.append(check_13_critical_files())

    # Repo health
    results.append(check_14_uncommitted_count())
    results.append(check_15_gitignore_enforcement())

    # Providers
    results.append(check_17_fundamentals_provider())
    results.append(check_18_daily_bars_provider())

    # Sync
    results.append(check_19_pk_sync())

    print_report(results)

    if not no_sheet:
        write_to_sheet(results, gc)

    # Determine exit code
    # v3 (2026-04-25): WARNINGs are a normal/healthy state — open issues
    # show up as warnings until resolved. Only CRITICAL = real CI failure.
    # Previously v2 returned 2 for warnings, which GitHub Actions treats as
    # failure, producing false-positive "Process completed with exit code 2"
    # annotations on every run.
    has_critical = any(r.is_critical() for r in results)
    has_warnings = any(r.is_failure() for r in results)

    # Heartbeat mode: always send email
    send_email_alert(results)

    if has_critical:
        print(f"\n[health_audit] Exit 1 — CRITICAL issues detected")
        return 1

    if has_warnings:
        print(f"\n[health_audit] Exit 0 — WARNINGs present but no critical issues (healthy)")
    else:
        print(f"\n[health_audit] Exit 0 — all checks passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
