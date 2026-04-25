#!/usr/bin/env python3
"""
generate_project_state.py
=========================
Generates PROJECT_STATE.md - a live snapshot of the RidingHigh Pro system.

Auto-runs after every git commit via .git/hooks/post-commit.
Manual run: python3 generate_project_state.py

Sections:
1. Header (timestamp, branch, commit)
2. Recent commits (last 5)
3. Open issues count (from OPEN_ISSUES.md)
4. GitHub Actions status (last 5 workflow runs)
5. Google Sheets stats (rows, last date per sheet) — slow, ~30-60s
6. System health flags

Exit codes:
  0 — success
  1 — fatal error (e.g., not in repo)
  2 — partial success (some data missed but file written)
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = REPO_ROOT / "PROJECT_STATE.md"
SHEETS_CONFIG = REPO_ROOT / "sheets_config.json"
OPEN_ISSUES = REPO_ROOT / "OPEN_ISSUES.md"
CREDENTIALS = REPO_ROOT / "google_credentials.json"

# GitHub config — read from env or fallback to known repo
GITHUB_REPO = os.environ.get("GITHUB_REPO", "projects5069-creator/ridinghigh-pro")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # optional but recommended

PERU_TZ = "America/Lima"

# ============================================================================
# HELPERS
# ============================================================================

def now_peru():
    """Return current Peru time as formatted string."""
    try:
        import pytz
        peru = pytz.timezone(PERU_TZ)
        return datetime.now(peru).strftime("%Y-%m-%d %H:%M:%S %Z")
    except ImportError:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")


def run_git(*args):
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


# ============================================================================
# SECTION GENERATORS
# ============================================================================

def section_header():
    """Top header with current timestamp + git context."""
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    commit = run_git("rev-parse", "--short", "HEAD") or "unknown"
    msg = run_git("log", "-1", "--pretty=%s") or "unknown"

    return f"""# RidingHigh Pro — Project State
*Auto-generated. Do not edit manually.*

**Generated:** {now_peru()}
**Branch:** `{branch}`
**Latest commit:** `{commit}` — {msg}

---
"""


def section_recent_commits():
    """Last 5 commits."""
    log = run_git("log", "--oneline", "-5", "--decorate")
    if not log:
        return "## 📜 Recent commits\n_(unable to read git log)_\n\n---\n"

    lines = log.splitlines()
    body = "\n".join(f"- `{line}`" for line in lines)
    return f"""## 📜 Recent commits (last 5)

{body}

---
"""


def section_open_issues():
    """Count and summarize open issues from OPEN_ISSUES.md."""
    if not OPEN_ISSUES.exists():
        return "## 📋 Open issues\n_OPEN_ISSUES.md not found_\n\n---\n"

    content = OPEN_ISSUES.read_text(encoding="utf-8")

    # Count by severity using emoji markers in section headers
    # Look for "## 🔴 STILL OPEN", "## 🟠 STILL OPEN", etc.
    sections = {
        "🔴 Critical": 0,
        "🟠 Important": 0,
        "🟡 Medium": 0,
        "🟢 Low": 0,
    }

    current_section = None
    for line in content.splitlines():
        # Detect "## 🔴 STILL OPEN - Critical" style headers
        if line.startswith("## ") and "STILL OPEN" in line:
            for key in sections:
                emoji = key.split()[0]
                if emoji in line:
                    current_section = key
                    break
            else:
                current_section = None
        elif current_section and re.match(r"^### #\d+", line):
            sections[current_section] += 1

    total = sum(sections.values())
    by_severity = "\n".join(f"- {k}: **{v}**" for k, v in sections.items())

    return f"""## 📋 Open issues — {total} total

{by_severity}

_See `OPEN_ISSUES.md` for full list_

---
"""


def section_github_actions():
    """Latest workflow runs via GitHub API (no auth needed for public)."""
    try:
        import urllib.request
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=5"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if GITHUB_TOKEN:
            req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        runs = data.get("workflow_runs", [])[:5]
        if not runs:
            return "## ⚙️ GitHub Actions\n_No recent runs_\n\n---\n"

        rows = ["| Workflow | Status | Conclusion | Started |", "|---|---|---|---|"]
        for run in runs:
            name = run.get("name", "?")
            status = run.get("status", "?")
            conclusion = run.get("conclusion", "—") or "—"
            started = run.get("run_started_at", "?")[:16].replace("T", " ")
            emoji = "✅" if conclusion == "success" else ("❌" if conclusion == "failure" else "⏳")
            rows.append(f"| {name} | {status} | {emoji} {conclusion} | {started} UTC |")

        return f"""## ⚙️ GitHub Actions — last 5 runs

{chr(10).join(rows)}

---
"""
    except Exception as e:
        return f"## ⚙️ GitHub Actions\n_Failed to query: {e}_\n\n---\n"


def section_sheets_stats():
    """Read row counts and last dates from each Google Sheet — SLOW (~30-60s)."""
    if not SHEETS_CONFIG.exists():
        return "## 📊 Google Sheets\n_sheets_config.json not found_\n\n---\n"
    if not CREDENTIALS.exists():
        return "## 📊 Google Sheets\n_google_credentials.json not found — skipped_\n\n---\n"

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return "## 📊 Google Sheets\n_gspread not installed — `pip install gspread google-auth`_\n\n---\n"

    try:
        config = json.loads(SHEETS_CONFIG.read_text())
        # Get the most recent month key
        month_key = sorted(config.keys())[-1]
        sheets = config[month_key]

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(str(CREDENTIALS), scopes=scopes)
        gc = gspread.authorize(creds)

        rows = ["| Sheet | Total rows | Last date | Status |", "|---|---|---|---|"]

        for name, sheet_id in sheets.items():
            try:
                ws = gc.open_by_key(sheet_id).sheet1
                values = ws.get_all_values()
                total = max(0, len(values) - 1)  # minus header
                last_date = "—"
                if total > 0 and values[-1]:
                    # First column usually has date
                    last_date = values[-1][0][:10] if values[-1][0] else "—"
                status = "✅" if total > 0 else "⚠️ empty"
                rows.append(f"| {name} | {total:,} | {last_date} | {status} |")
            except Exception as e:
                rows.append(f"| {name} | ? | ? | ❌ {str(e)[:30]} |")

        return f"""## 📊 Google Sheets — month `{month_key}`

{chr(10).join(rows)}

---
"""
    except Exception as e:
        return f"## 📊 Google Sheets\n_Error: {e}_\n\n---\n"


def section_health():
    """Quick system health checks."""
    flags = []

    # Check critical files exist
    critical_files = [
        "auto_scanner.py", "post_analysis_collector.py", "dashboard.py",
        "sheets_manager.py", "config.py", "formulas.py", "utils.py",
    ]
    for f in critical_files:
        if not (REPO_ROOT / f).exists():
            flags.append(f"❌ Missing critical file: `{f}`")

    # Check for uncommitted changes
    status = run_git("status", "--porcelain")
    if status:
        n_changes = len(status.splitlines())
        flags.append(f"⚠️ {n_changes} uncommitted file(s)")

    # Check sheets_config has current month
    try:
        import pytz
        peru = pytz.timezone(PERU_TZ)
        current_month = datetime.now(peru).strftime("%Y-%m")
        config = json.loads(SHEETS_CONFIG.read_text())
        if current_month not in config:
            flags.append(f"⚠️ sheets_config.json missing entry for `{current_month}`")
    except Exception:
        pass

    if not flags:
        return "## 🩺 Health\n✅ All checks passed.\n\n---\n"

    body = "\n".join(f"- {f}" for f in flags)
    return f"""## 🩺 Health

{body}

---
"""


def section_footer():
    return """## ℹ️ How this file is generated

This file is auto-generated by `generate_project_state.py`.
It runs automatically after every `git commit` via `.git/hooks/post-commit`.

To run manually:
```bash
cd ~/RidingHighPro && python3 generate_project_state.py
```

To disable auto-update temporarily:
```bash
chmod -x .git/hooks/post-commit
```
"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    if not (REPO_ROOT / ".git").exists():
        print("ERROR: Not a git repository", file=sys.stderr)
        return 1

    print(f"[generate_project_state] writing to {OUTPUT_FILE}")
    print("[generate_project_state] this may take 30-60s for Sheets stats...")

    sections = [
        section_header(),
        section_recent_commits(),
        section_open_issues(),
        section_github_actions(),
        section_sheets_stats(),
        section_health(),
        section_footer(),
    ]

    OUTPUT_FILE.write_text("\n".join(sections), encoding="utf-8")
    print(f"[generate_project_state] ✅ done — {OUTPUT_FILE.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
