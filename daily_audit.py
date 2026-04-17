#!/usr/bin/env python3
"""
daily_audit.py - RidingHigh Pro Daily System Audit
====================================================

Comprehensive daily audit of the entire RidingHigh Pro system.
Runs 7 categories of checks and produces a detailed report.

Categories:
    1. CODE    - Syntax, duplicates, inline formulas, hardcoded values
    2. DATA    - Sheet contents, broken rows, cross-sheet consistency
    3. SYSTEM  - Backups, file sizes, imports
    4. METRICS - Correlations, distributions
    5. TESTS   - Run all unit tests
    6. GITHUB  - Actions status (if logs available)
    7. SECURITY - Check for exposed credentials, TODO/FIXME

Usage:
    python3 daily_audit.py                    # Full audit
    python3 daily_audit.py --quick            # Fast checks only (skip Sheet data)
    python3 daily_audit.py --section code     # Only run specific section
    python3 daily_audit.py --output file.txt  # Write to file

Exit codes:
    0 - No critical issues found
    1 - Warnings found (review recommended)
    2 - Critical issues found (action required)

Designed to run:
    - Daily at 07:00 Peru time (before market opens)
    - Via cron or GitHub Actions
    - Takes ~5-60 minutes depending on --quick flag
"""

import os
import sys
import re
import ast
import json
import argparse
import subprocess
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

# Configuration
HOME = os.path.expanduser("~")
PROJECT_DIR = os.path.join(HOME, "RidingHighPro")
SEVERITY_ICONS = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
    "INFO":     "ℹ️",
}


# ═══════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════

class AuditReport:
    """Collects findings from all audit sections."""
    
    def __init__(self):
        self.sections = {}
        self.findings = defaultdict(list)  # {severity: [finding, ...]}
        self.start_time = datetime.now()
    
    def add(self, section, severity, message, details=None):
        """Add a finding to the report."""
        self.findings[severity].append({
            "section": section,
            "message": message,
            "details": details or "",
        })
    
    def section_summary(self, section_name, stats):
        """Record summary stats for a section."""
        self.sections[section_name] = stats
    
    def has_critical(self):
        return len(self.findings["CRITICAL"]) > 0
    
    def has_warnings(self):
        return (len(self.findings["HIGH"]) > 0 or 
                len(self.findings["MEDIUM"]) > 0)
    
    def print_report(self, output=None):
        """Print formatted report to stdout or file."""
        out = []
        
        # Header
        duration = (datetime.now() - self.start_time).total_seconds()
        out.append("=" * 70)
        out.append(f"🔬 RidingHigh Pro - Daily Audit Report")
        out.append(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Peru")
        out.append(f"   Duration: {duration:.1f}s")
        out.append("=" * 70)
        
        # Section summaries
        out.append("\n📋 Section Summary:")
        for section, stats in self.sections.items():
            out.append(f"  {section}: {stats}")
        
        # Findings by severity
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        for severity in severity_order:
            findings = self.findings[severity]
            if not findings:
                continue
            
            icon = SEVERITY_ICONS[severity]
            out.append(f"\n{icon} {severity} ({len(findings)} findings):")
            for f in findings:
                out.append(f"  [{f['section']}] {f['message']}")
                if f['details']:
                    for line in f['details'].split('\n'):
                        out.append(f"    {line}")
        
        # Final verdict
        out.append("\n" + "=" * 70)
        if self.has_critical():
            out.append("🔴 CRITICAL ISSUES FOUND - Action required!")
        elif self.has_warnings():
            out.append("🟡 Warnings found - Review recommended")
        else:
            out.append("✅ System is healthy - No significant issues")
        out.append("=" * 70)
        
        text = "\n".join(out)
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Report written to {output}")
        else:
            print(text)
        
        return text


def read_file_safe(filepath):
    """Read file, return lines list or None."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception:
        return None


def strip_comments(line):
    """Strip # comments (basic - ignores # inside strings)."""
    in_string = False
    quote = None
    for i, c in enumerate(line):
        if c in ('"', "'") and (i == 0 or line[i-1] != '\\'):
            if not in_string:
                in_string = True
                quote = c
            elif c == quote:
                in_string = False
        elif c == '#' and not in_string:
            return line[:i]
    return line


def get_core_files():
    """List of core production files to audit."""
    return [
        "auto_scanner.py",
        "dashboard.py",
        "post_analysis_collector.py",
        "enrich_post_analysis.py",
        "backfill_ohlc.py",
        "formulas.py",
        "utils.py",
        "config.py",
        "sheets_manager.py",
        "gsheets_sync.py",
        "backup_manager.py",
        "monthly_rotation.py",
        "data_logger.py",
        "health_check.py",
    ]


# ═══════════════════════════════════════════════════════════════════════
# Section 1: CODE Audit
# ═══════════════════════════════════════════════════════════════════════

def audit_code(report, verbose=False):
    """Audit code quality across all source files."""
    print("\n🔍 [CODE] Auditing source files...")
    
    core_files = get_core_files()
    files_lines = {}
    
    # Load all files
    for filename in core_files:
        filepath = os.path.join(PROJECT_DIR, filename)
        lines = read_file_safe(filepath)
        if lines:
            files_lines[filepath] = lines
    
    # 1.1 Syntax check
    syntax_errors = []
    for filepath in files_lines:
        try:
            with open(filepath, 'r') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            syntax_errors.append((os.path.basename(filepath), str(e)))
    
    for filename, err in syntax_errors:
        report.add("CODE", "CRITICAL", f"Syntax error in {filename}", err)
    
    # 1.2 Inline formulas (the ATRX/MxV bugs we saw before)
    # These patterns are what SHOULD be using formulas.py
    formula_patterns = {
        "ATRX wrong formula": r"atrx\s*=\s*\(atr\s*/\s*price\)\s*\*\s*100",
        "MxV inline": r"\(market_cap\s*-\s*price\s*\*\s*volume\)",
        "Float% wrong formula": r"float_pct\s*=\s*\(?volume\s*/\s*shares_outstanding",
        "RunUp inline": r"run_up\s*=\s*\(price\s*-.*Open.*\)\s*/.*Open.*100",
    }
    
    inline_findings = defaultdict(list)
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        if filename in ("formulas.py", "test_formulas.py"):
            continue
        for ln, line in enumerate(lines, 1):
            clean = strip_comments(line)
            if "calculate_" in clean:
                continue  # it's using formulas
            for name, pattern in formula_patterns.items():
                if re.search(pattern, clean):
                    inline_findings[name].append(f"{filename}:{ln}")
    
    for name, locations in inline_findings.items():
        report.add("CODE", "CRITICAL" if "wrong" in name else "HIGH",
                   f"Inline formula: {name}",
                   "\n".join(locations))
    
    # 1.3 Function duplicates
    func_locations = defaultdict(list)
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        for ln, line in enumerate(lines, 1):
            match = re.match(r'\s*def\s+(\w+)\s*\(', line)
            if match:
                func_name = match.group(1)
                if func_name.startswith('_') or func_name in ('main', '__init__', 'run'):
                    continue
                func_locations[func_name].append((filename, ln))
    
    duplicates = {name: locs for name, locs in func_locations.items() if len(locs) > 1}
    for name, locs in list(duplicates.items())[:10]:
        locations_str = ", ".join([f"{f}:{ln}" for f, ln in locs])
        report.add("CODE", "MEDIUM", f"Duplicate function: {name}()", locations_str)
    
    # 1.4 Hardcoded values
    hardcoded_patterns = {
        "Hardcoded score threshold (60)": r"score\s*>=\s*60|Score\s*>=\s*60",
        "Hardcoded score threshold (70)": r"score\s*>=\s*70|Score\s*>=\s*70",
        "Hardcoded score threshold (85)": r"score\s*>=\s*85|Score\s*>=\s*85",
        "Hardcoded date 2026": r"['\"]2026-\d{2}-\d{2}['\"]",
    }
    
    hc_counts = defaultdict(int)
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        if filename in ("config.py", "test_formulas.py", "test_utils.py"):
            continue
        for ln, line in enumerate(lines, 1):
            clean = strip_comments(line)
            for name, pattern in hardcoded_patterns.items():
                if re.search(pattern, clean):
                    hc_counts[name] += 1
    
    for name, count in hc_counts.items():
        severity = "MEDIUM" if count > 5 else "LOW"
        report.add("CODE", severity, f"{name}: {count} occurrences")
    
    # 1.5 TODO/FIXME/HACK
    todo_count = 0
    for filepath, lines in files_lines.items():
        for ln, line in enumerate(lines, 1):
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX|BUG)', line, re.IGNORECASE):
                todo_count += 1
    
    if todo_count > 0:
        report.add("CODE", "LOW", f"{todo_count} TODO/FIXME markers in code")
    
    report.section_summary("CODE", f"{len(files_lines)} files checked, "
                                   f"{len(syntax_errors)} syntax errors, "
                                   f"{sum(len(v) for v in inline_findings.values())} inline formulas, "
                                   f"{len(duplicates)} function duplicates")


# ═══════════════════════════════════════════════════════════════════════
# Section 2: DATA Audit (requires Google Sheets)
# ═══════════════════════════════════════════════════════════════════════

def audit_data(report, quick=False):
    """Audit data in Google Sheets for consistency and quality."""
    print("\n📊 [DATA] Auditing Google Sheets data...")
    
    if quick:
        report.add("DATA", "INFO", "Skipped in --quick mode")
        report.section_summary("DATA", "Skipped (--quick)")
        return
    
    try:
        sys.path.insert(0, PROJECT_DIR)
        import sheets_manager
        from datetime import datetime, timedelta
        import pytz
        
        PERU_TZ = pytz.timezone("America/Lima")
        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        
        gc = sheets_manager._get_gc()
        
        # 2.1 Check timeline_live for broken scores
        ws = sheets_manager.get_worksheet("timeline_live", gc=gc)
        data = ws.get_all_values()
        
        if not data:
            report.add("DATA", "HIGH", "timeline_live is EMPTY!")
            return
        
        headers = data[0]
        rows = data[1:]
        
        # Check for scores out of 0-100 range
        score_col = headers.index("Score") if "Score" in headers else -1
        broken_scores = 0
        if score_col >= 0:
            for row in rows:
                if len(row) > score_col:
                    try:
                        s = float(row[score_col])
                        if s < 0 or s > 100:
                            broken_scores += 1
                    except (ValueError, TypeError):
                        pass
        
        if broken_scores > 0:
            report.add("DATA", "HIGH",
                       f"timeline_live: {broken_scores} rows with Score outside [0,100]")
        
        # Check for today's data
        today_rows = sum(1 for r in rows if r and r[0].startswith(today))
        if today_rows == 0:
            now = datetime.now(PERU_TZ)
            # Only warn if during/after market hours
            if now.hour >= 9:
                report.add("DATA", "HIGH",
                           f"timeline_live: NO data for today ({today})")
        
        report.section_summary("DATA",
            f"timeline_live: {len(rows)} total rows, "
            f"{today_rows} today, "
            f"{broken_scores} broken scores")
        
    except Exception as e:
        report.add("DATA", "HIGH", "Failed to audit sheets", str(e)[:200])
        report.section_summary("DATA", f"ERROR: {type(e).__name__}")


# ═══════════════════════════════════════════════════════════════════════
# Section 3: SYSTEM Audit
# ═══════════════════════════════════════════════════════════════════════

def audit_system(report):
    """Audit system state: backups, files, structure."""
    print("\n⚙️  [SYSTEM] Auditing system state...")
    
    # 3.1 Check for required files
    required = [
        "auto_scanner.py", "dashboard.py", "post_analysis_collector.py",
        "formulas.py", "utils.py", "config.py",
        "sheets_config.json", "google_credentials.json",
        "test_formulas.py", "test_utils.py",
    ]
    
    missing = []
    for f in required:
        if not os.path.exists(os.path.join(PROJECT_DIR, f)):
            missing.append(f)
    
    if missing:
        report.add("SYSTEM", "CRITICAL",
                   f"{len(missing)} required files missing",
                   "\n".join(missing))
    
    # 3.2 Check for BEFORE_ backups (should be cleaned up eventually)
    backup_files = []
    for f in os.listdir(PROJECT_DIR):
        if "BEFORE" in f or "_v1_BACKUP" in f:
            backup_files.append(f)
    
    if len(backup_files) > 10:
        report.add("SYSTEM", "LOW",
                   f"{len(backup_files)} backup files in project dir",
                   "Consider moving to גיבוי זמני/")
    
    # 3.3 Check dashboard.py size
    dash_path = os.path.join(PROJECT_DIR, "dashboard.py")
    if os.path.exists(dash_path):
        size_kb = os.path.getsize(dash_path) / 1024
        lines = len(read_file_safe(dash_path) or [])
        if lines > 4000:
            report.add("SYSTEM", "LOW",
                       f"dashboard.py is very large: {lines} lines, {size_kb:.0f}KB")
    
    # 3.4 Verify imports work
    import_errors = []
    for module in ["formulas", "utils", "config"]:
        try:
            sys.path.insert(0, PROJECT_DIR)
            __import__(module)
        except Exception as e:
            import_errors.append(f"{module}: {e}")
    
    for err in import_errors:
        report.add("SYSTEM", "CRITICAL", f"Import failed: {err}")
    
    report.section_summary("SYSTEM",
        f"{len(required)-len(missing)}/{len(required)} files present, "
        f"{len(backup_files)} backups, "
        f"{len(import_errors)} import errors")


# ═══════════════════════════════════════════════════════════════════════
# Section 4: METRICS Audit (optional - uses data)
# ═══════════════════════════════════════════════════════════════════════

def audit_metrics(report, quick=False):
    """Analyze metric correlations and distributions."""
    print("\n📈 [METRICS] Analyzing metric quality...")
    
    if quick:
        report.add("METRICS", "INFO", "Skipped in --quick mode")
        report.section_summary("METRICS", "Skipped")
        return
    
    try:
        sys.path.insert(0, PROJECT_DIR)
        import sheets_manager
        import pandas as pd
        
        # Load post_analysis
        gc = sheets_manager._get_gc()
        ws = sheets_manager.get_worksheet("post_analysis", gc=gc)
        data = ws.get_all_values()
        
        if not data or len(data) < 10:
            report.add("METRICS", "INFO", "post_analysis has insufficient data")
            return
        
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Convert to numeric (ignore errors)
        for col in ["Score", "MaxDrop%", "MxV", "RunUp", "ATRX", "REL_VOL"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Filter complete rows
        if "MaxDrop%" in df.columns and "Score" in df.columns:
            complete = df.dropna(subset=["MaxDrop%", "Score"])
            
            if len(complete) >= 20:
                # Check Score correlation with MaxDrop
                corr = complete["Score"].corr(complete["MaxDrop%"])
                if abs(corr) < 0.1:
                    report.add("METRICS", "MEDIUM",
                               f"Score-MaxDrop correlation is weak (r={corr:.3f})",
                               "Score may not be predictive. Consider v3.")
                else:
                    report.add("METRICS", "INFO",
                               f"Score-MaxDrop correlation: r={corr:.3f}")
                
                report.section_summary("METRICS",
                    f"{len(complete)} complete rows, "
                    f"Score r={corr:.3f}")
            else:
                report.section_summary("METRICS", f"{len(complete)} rows (need 20+)")
    
    except Exception as e:
        report.add("METRICS", "MEDIUM", "Failed to audit metrics", str(e)[:200])
        report.section_summary("METRICS", f"ERROR: {type(e).__name__}")


# ═══════════════════════════════════════════════════════════════════════
# Section 5: TESTS Audit
# ═══════════════════════════════════════════════════════════════════════

def audit_tests(report):
    """Run all unit tests."""
    print("\n🧪 [TESTS] Running unit tests...")
    
    test_files = ["test_formulas.py", "test_utils.py"]
    
    for test_file in test_files:
        filepath = os.path.join(PROJECT_DIR, test_file)
        if not os.path.exists(filepath):
            report.add("TESTS", "HIGH", f"{test_file} not found")
            continue
        
        try:
            result = subprocess.run(
                [sys.executable, filepath],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Extract passed/total from output
                match = re.search(r'Results:\s*(\d+)/(\d+)\s*passed', result.stdout)
                if match:
                    passed, total = match.groups()
                    report.add("TESTS", "INFO",
                               f"{test_file}: {passed}/{total} passed")
                else:
                    report.add("TESTS", "INFO", f"{test_file}: passed")
            else:
                report.add("TESTS", "HIGH",
                           f"{test_file}: FAILED",
                           result.stdout[-500:] if result.stdout else result.stderr[-500:])
        except Exception as e:
            report.add("TESTS", "HIGH", f"{test_file}: exception", str(e))
    
    report.section_summary("TESTS", f"{len(test_files)} test files run")


# ═══════════════════════════════════════════════════════════════════════
# Section 6: GITHUB Audit (optional)
# ═══════════════════════════════════════════════════════════════════════

def audit_github(report):
    """Check GitHub Actions status via git log."""
    print("\n🐙 [GITHUB] Checking git status...")
    
    try:
        # Check uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        uncommitted = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        if uncommitted > 0:
            report.add("GITHUB", "LOW",
                       f"{uncommitted} uncommitted changes in git")
        
        # Last commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s (%ar)"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            last_commit = result.stdout.strip()
            report.add("GITHUB", "INFO", f"Last commit: {last_commit}")
        
        report.section_summary("GITHUB", f"{uncommitted} uncommitted")
        
    except Exception as e:
        report.add("GITHUB", "LOW", "Git check failed", str(e)[:200])
        report.section_summary("GITHUB", "git unavailable")


# ═══════════════════════════════════════════════════════════════════════
# Section 7: SECURITY Audit
# ═══════════════════════════════════════════════════════════════════════

def audit_security(report):
    """Check for exposed credentials, sensitive info."""
    print("\n🔒 [SECURITY] Checking for exposed credentials...")
    
    sensitive_patterns = {
        "Hardcoded API key": r"api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
        "Hardcoded password": r"password\s*=\s*['\"][^'\"]{8,}['\"]",
        "Hardcoded token": r"token\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
        "Hardcoded secret": r"secret\s*=\s*['\"][^'\"]{8,}['\"]",
        "Google creds in code": r"google_credentials\.json.*=.*['\"]",
    }
    
    issues = []
    core_files = get_core_files()
    
    for filename in core_files:
        filepath = os.path.join(PROJECT_DIR, filename)
        lines = read_file_safe(filepath)
        if not lines:
            continue
        
        for ln, line in enumerate(lines, 1):
            clean = strip_comments(line)
            for pattern_name, pattern in sensitive_patterns.items():
                if re.search(pattern, clean, re.IGNORECASE):
                    issues.append(f"{filename}:{ln} - {pattern_name}")
    
    for issue in issues:
        report.add("SECURITY", "CRITICAL", "Potential credential exposure", issue)
    
    # Check .gitignore
    gitignore_path = os.path.join(PROJECT_DIR, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            gitignore = f.read()
        if "google_credentials.json" not in gitignore:
            report.add("SECURITY", "CRITICAL",
                       "google_credentials.json not in .gitignore!")
    else:
        report.add("SECURITY", "HIGH", ".gitignore not found")
    
    report.section_summary("SECURITY", f"{len(issues)} potential issues")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="RidingHigh Pro Daily Audit")
    parser.add_argument("--quick", action="store_true",
                        help="Fast checks only (skip data audit)")
    parser.add_argument("--section", choices=["code", "data", "system", "metrics",
                                              "tests", "github", "security"],
                        help="Run only specific section")
    parser.add_argument("--output", help="Write report to file")
    args = parser.parse_args()
    
    print(f"\n{'=' * 70}")
    print(f"🔬 RidingHigh Pro - Daily Audit")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mode: {'QUICK' if args.quick else 'FULL'}")
    if args.section:
        print(f"   Section: {args.section.upper()} only")
    print(f"{'=' * 70}")
    
    report = AuditReport()
    
    sections_to_run = [args.section] if args.section else [
        "code", "data", "system", "metrics", "tests", "github", "security"
    ]
    
    if "code" in sections_to_run:
        audit_code(report)
    if "data" in sections_to_run:
        audit_data(report, quick=args.quick)
    if "system" in sections_to_run:
        audit_system(report)
    if "metrics" in sections_to_run:
        audit_metrics(report, quick=args.quick)
    if "tests" in sections_to_run:
        audit_tests(report)
    if "github" in sections_to_run:
        audit_github(report)
    if "security" in sections_to_run:
        audit_security(report)
    
    # Print report
    report.print_report(output=args.output)
    
    # Exit code
    if report.has_critical():
        sys.exit(2)
    elif report.has_warnings():
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
