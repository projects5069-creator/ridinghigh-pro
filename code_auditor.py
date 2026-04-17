"""
code_auditor.py - RidingHigh Pro Deep Code Auditor
===================================================

בודק את כל הקבצים בפרויקט ומחפש:
- נוסחאות inline שעוקפות את formulas.py
- פונקציות מקומיות שמחקות את formulas.py
- כפילויות קוד
- Scores מחושבים ללא שימוש ב-calculate_score
- הערכים hardcoded (תאריכים, thresholds)
- תנאי is_cloud() - איפה קוד רץ מקומית
- ייבואים כפולים
- פונקציות שמוגדרות יותר מפעם אחת

Read-only - לא עושה שינויים.

Usage:
    python3 code_auditor.py
"""
import os
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════

HOME = os.path.expanduser("~")
PROJECT_DIR = os.path.join(HOME, "RidingHighPro")

# Files to audit (main production files)
CORE_FILES = [
    "auto_scanner.py",
    "dashboard.py",
    "post_analysis_collector.py",
    "formulas.py",
    "sheets_manager.py",
    "gsheets_sync.py",
    "enrich_post_analysis.py",
    "backfill_ohlc.py",
    "backup_manager.py",
    "monthly_rotation.py",
    "data_logger.py",
    "health_check.py",
    "score_tracker_sync.py",  # should be in quarantine
    "config.py",
]

# Backup files to skip
SKIP_PATTERNS = [
    "_BEFORE_",
    "_backup",
    "backup_",
    "גיבוי",
    ".pyc",
]


# ═══════════════════════════════════════════════════════════════════════
# Patterns to detect
# ═══════════════════════════════════════════════════════════════════════

FORMULA_PATTERNS = {
    "MxV inline": [
        r"market_cap\s*-\s*\(?price\s*\*\s*volume",
        r"mkt_cap\s*-\s*price\s*\*\s*volume",
        r"\(mc\s*-\s*\(?pr\s*\*\s*vol",
    ],
    "RunUp inline": [
        r"\(price\s*-\s*current\[.Open.\]\)\s*/\s*current\[.Open.\]\s*\)\s*\*\s*100",
        r"\(price\s*-\s*open_price\)\s*/\s*open_price\s*\)\s*\*\s*100",
        r"\(pr\s*-\s*op\)\s*/\s*op\s*\)\s*\*\s*100",
    ],
    "ATRX inline (ratio)": [
        r"\(current\[.High.\]\s*-\s*current\[.Low.\]\)\s*/\s*atr",
        r"\(high\s*-\s*low\)\s*/\s*atr",
        r"\(h\s*-\s*l\)\s*/\s*atr",
    ],
    "ATRX inline (WRONG - percentage)": [
        r"\(atr\s*/\s*price\)\s*\*\s*100",
    ],
    "Gap inline": [
        r"\(current\[.Open.\]\s*-\s*previous\[.Close.\]\)\s*/\s*previous\[.Close.\]",
        r"\(open_price\s*-\s*prev_close\)\s*/\s*prev_close",
        r"\(op\s*-\s*pc\)\s*/\s*pc",
    ],
    "VWAP inline": [
        r"\(price\s*/\s*vwap",
        r"\(pr\s*/\s*vp",
    ],
    "REL_VOL inline (without cap)": [
        r"rel_vol\s*=\s*volume\s*/\s*avg",
        r"REL_VOL_calc.*=.*vol\s*/\s*avg_vol",
    ],
    "Float% inline (wrong - Turnover)": [
        r"float_pct\s*=\s*\(?volume\s*/\s*shares_outstanding",
    ],
    "Float% inline (correct)": [
        r"float_pct\s*=\s*\(?float_shares\s*/\s*shares_outstanding",
        r"float_pct\s*=\s*\(?fs\s*/\s*shares_outstanding",
    ],
}


HARDCODED_PATTERNS = {
    "Hardcoded date (2026)": r"['\"]2026-\d{2}-\d{2}['\"]",
    "Hardcoded date (2025)": r"['\"]2025-\d{2}-\d{2}['\"]",
    "Hardcoded SL threshold (7%)": r"SL.*=\s*7|0\.07.*SL|sl.*7\.0",
    "Hardcoded SL threshold (10%)": r"SL.*=\s*10|0\.10.*SL|sl.*10\.0",
    "Hardcoded TP threshold (10%)": r"TP.*=\s*10|0\.10.*TP",
    "Hardcoded Score threshold (60)": r"score\s*[><=]+\s*60|Score\s*>=\s*60",
    "Hardcoded Score threshold (70)": r"score\s*[><=]+\s*70|Score\s*>=\s*70",
    "TODO/FIXME/HACK": r"#\s*(TODO|FIXME|XXX|HACK|BUG)",
}


# ═══════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════

def should_skip(filename):
    """Skip backup files."""
    return any(pattern in filename for pattern in SKIP_PATTERNS)


def read_file(filepath):
    """Read file, return lines with line numbers."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        return None


def strip_comments(line):
    """Strip Python comments from line."""
    # Simple: strip everything after # (not perfect but good enough)
    if '#' in line:
        # Don't strip # inside strings (basic check)
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


# ═══════════════════════════════════════════════════════════════════════
# Audit functions
# ═══════════════════════════════════════════════════════════════════════

def audit_formulas(files_lines):
    """Detect inline formulas that should use formulas.py."""
    findings = defaultdict(list)
    
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        if filename == "formulas.py":
            continue  # formulas.py is source of truth
        if filename == "test_formulas.py":
            continue  # tests contain formula patterns by design
        
        for ln, line in enumerate(lines, 1):
            clean = strip_comments(line).strip()
            if not clean:
                continue
            
            for formula_name, patterns in FORMULA_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, clean):
                        # Skip calculate_* function calls
                        if "calculate_" in clean:
                            continue
                        # Skip formulas.py itself
                        findings[formula_name].append({
                            "file": filename,
                            "line": ln,
                            "code": clean[:100]
                        })
                        break  # one match per line
    
    return findings


def audit_function_definitions(files_lines):
    """Find functions defined in multiple files (potential duplicates)."""
    func_locations = defaultdict(list)
    
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        for ln, line in enumerate(lines, 1):
            # Match function definitions
            match = re.match(r'\s*def\s+(\w+)\s*\(', line)
            if match:
                func_name = match.group(1)
                # Skip common helpers and privates
                if func_name.startswith('_') or func_name in ('main', '__init__'):
                    continue
                func_locations[func_name].append((filename, ln))
    
    # Return only functions defined in multiple files
    duplicates = {name: locs for name, locs in func_locations.items() 
                  if len(locs) > 1}
    return duplicates


def audit_imports(files_lines):
    """Find duplicate imports in same file."""
    findings = defaultdict(list)
    
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        imports_seen = defaultdict(list)
        
        for ln, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Normalize
                normalized = re.sub(r'\s+', ' ', stripped)
                imports_seen[normalized].append(ln)
        
        for imp, lines_list in imports_seen.items():
            if len(lines_list) > 1:
                findings[filename].append({
                    "import": imp,
                    "lines": lines_list
                })
    
    return findings


def audit_hardcoded(files_lines):
    """Find hardcoded values that might be bugs."""
    findings = defaultdict(list)
    
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        if filename == "test_formulas.py":
            continue  # tests have hardcoded values by design
        
        for ln, line in enumerate(lines, 1):
            clean = strip_comments(line).strip()
            if not clean:
                continue
            
            for pattern_name, pattern in HARDCODED_PATTERNS.items():
                if re.search(pattern, clean):
                    findings[pattern_name].append({
                        "file": filename,
                        "line": ln,
                        "code": clean[:100]
                    })
    
    return findings


def audit_cloud_local_divergence(files_lines):
    """Find is_cloud() checks that might hide local-only code paths."""
    findings = []
    
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        for ln, line in enumerate(lines, 1):
            if 'is_cloud()' in line or 'is_cloud ' in line:
                # Get context (the check)
                context = line.strip()[:120]
                findings.append({
                    "file": filename,
                    "line": ln,
                    "code": context
                })
    
    return findings


def audit_score_calculations(files_lines):
    """Find Score calculations that don't use calculate_score()."""
    findings = []
    
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        if filename in ("formulas.py", "test_formulas.py"):
            continue
        
        for ln, line in enumerate(lines, 1):
            clean = strip_comments(line).strip()
            # Look for score += patterns (inline score calculation)
            if re.search(r'score\s*\+=\s*min\(', clean):
                if 'calculate_score' not in clean:
                    findings.append({
                        "file": filename,
                        "line": ln,
                        "code": clean[:100]
                    })
    
    return findings


def audit_file_sizes(files_lines):
    """Report file sizes - unusually large files may have duplicates."""
    sizes = []
    for filepath, lines in files_lines.items():
        filename = os.path.basename(filepath)
        size_kb = os.path.getsize(filepath) / 1024
        sizes.append((filename, len(lines), size_kb))
    return sorted(sizes, key=lambda x: -x[2])


# ═══════════════════════════════════════════════════════════════════════
# Report functions
# ═══════════════════════════════════════════════════════════════════════

def print_section(title, icon="🔍"):
    print(f"\n{'='*70}")
    print(f"{icon} {title}")
    print(f"{'='*70}")


def print_findings(findings, title, icon="⚠️"):
    if not findings:
        print(f"  ✅ לא נמצאו ממצאים")
        return
    
    print(f"\n  {icon} {title}:")
    for key, items in findings.items():
        if isinstance(items, list) and items:
            print(f"\n    🔸 {key}: {len(items)} ממצאים")
            for item in items[:5]:  # show up to 5
                if isinstance(item, dict):
                    print(f"       {item.get('file', '?')}:{item.get('line', '?')}")
                    print(f"         {item.get('code', '')[:80]}")
                else:
                    print(f"       {item}")
            if len(items) > 5:
                print(f"       ... ועוד {len(items) - 5}")


# ═══════════════════════════════════════════════════════════════════════
# Main audit
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("="*70)
    print("🔬 RidingHigh Pro - Deep Code Auditor")
    print("="*70)
    
    # Load all files
    print(f"\n📂 Scanning {PROJECT_DIR}")
    
    files_lines = {}
    for filename in CORE_FILES:
        filepath = os.path.join(PROJECT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠️  {filename}: not found")
            continue
        if should_skip(filepath):
            continue
        lines = read_file(filepath)
        if lines:
            files_lines[filepath] = lines
            print(f"  ✅ {filename}: {len(lines)} lines")
    
    if not files_lines:
        print("\n❌ No files to audit!")
        sys.exit(1)
    
    # Run audits
    print_section("1. Formula Duplications", "📐")
    formulas_findings = audit_formulas(files_lines)
    print_findings(formulas_findings, "נוסחאות inline (לא דרך formulas.py)")
    
    print_section("2. Function Duplicates (across files)", "🔁")
    func_dups = audit_function_definitions(files_lines)
    if func_dups:
        print(f"\n  ⚠️  {len(func_dups)} פונקציות מוגדרות ביותר מקובץ אחד:")
        for name, locs in list(func_dups.items())[:15]:
            locations_str = ", ".join([f"{f}:{ln}" for f, ln in locs])
            print(f"    🔸 {name}(): {locations_str}")
    else:
        print(f"\n  ✅ אין כפילויות פונקציות")
    
    print_section("3. Duplicate Imports (same file)", "📦")
    import_dups = audit_imports(files_lines)
    if import_dups:
        for file, imports in import_dups.items():
            print(f"\n  ⚠️  {file}:")
            for imp in imports:
                print(f"    🔸 {imp['import']}")
                print(f"       lines: {imp['lines']}")
    else:
        print(f"\n  ✅ אין ייבואים כפולים")
    
    print_section("4. Hardcoded Values", "🔧")
    hc_findings = audit_hardcoded(files_lines)
    print_findings(hc_findings, "ערכים hardcoded")
    
    print_section("5. is_cloud() Divergence", "☁️")
    cloud_findings = audit_cloud_local_divergence(files_lines)
    if cloud_findings:
        print(f"\n  מופעים של is_cloud() בקוד ({len(cloud_findings)}):")
        for f in cloud_findings[:10]:
            print(f"    {f['file']}:{f['line']}: {f['code'][:70]}")
    else:
        print(f"\n  ✅ אין שימושי is_cloud()")
    
    print_section("6. Score Calculations Not Using formulas", "🎯")
    score_findings = audit_score_calculations(files_lines)
    if score_findings:
        print(f"\n  ⚠️  {len(score_findings)} חישובי Score inline:")
        for f in score_findings[:15]:
            print(f"    {f['file']}:{f['line']}: {f['code'][:70]}")
    else:
        print(f"\n  ✅ כל חישובי Score מבוססי formulas")
    
    print_section("7. File Sizes", "📏")
    sizes = audit_file_sizes(files_lines)
    print(f"\n  {'File':<40} {'Lines':>8} {'KB':>8}")
    print(f"  {'-'*40} {'-'*8} {'-'*8}")
    for name, lines, kb in sizes[:10]:
        print(f"  {name:<40} {lines:>8} {kb:>8.1f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════════
    print_section("🏁 FINAL SUMMARY", "🎯")
    
    # Count total issues
    formula_count = sum(len(v) for v in formulas_findings.values())
    hardcoded_count = sum(len(v) for v in hc_findings.values())
    
    total_issues = (
        formula_count +
        len(func_dups) +
        sum(len(v) for v in import_dups.values()) +
        hardcoded_count +
        len(score_findings)
    )
    
    print(f"\n  🔸 נוסחאות inline שעוקפות formulas.py: {formula_count}")
    print(f"  🔸 כפילויות פונקציות: {len(func_dups)}")
    print(f"  🔸 ייבואים כפולים: {sum(len(v) for v in import_dups.values())}")
    print(f"  🔸 ערכים hardcoded: {hardcoded_count}")
    print(f"  🔸 is_cloud() מופעים: {len(cloud_findings)}")
    print(f"  🔸 Score inline: {len(score_findings)}")
    print(f"\n  📊 סה\"כ נקודות לבדיקה: {total_issues}")
    
    if total_issues == 0:
        print(f"\n  🎉 הקוד נקי לחלוטין!")
    elif total_issues < 10:
        print(f"\n  ✅ הקוד במצב טוב - רק {total_issues} נקודות לבדיקה")
    else:
        print(f"\n  ⚠️  יש {total_issues} נקודות שדורשות בדיקה")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
