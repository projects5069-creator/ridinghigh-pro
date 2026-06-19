"""Task 1 — CORE_UNSAFE single source + matcher.

The auto-safe filter's correctness depends entirely on this list being the ONE
place the unsafe set is defined. These tests pin the reconciled set (2026-06-18):
orchestrator.py removed (does not exist); utils.py/data_provider.py/providers/**/
agent/** added; backfill_* and the Sheets/score writers covered.
"""
import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "overnight",
    ),
)

import core_unsafe  # noqa: E402


def test_confirmed_core_files_match():
    pats = core_unsafe.load_patterns()
    for f in [
        "formulas.py", "config.py", "sheets_manager.py", "gsheets_sync.py",
        "auto_scanner.py", "post_analysis_collector.py", "cross_month_loaders.py",
        "health_audit.py", "dashboard.py", "backup_manager.py",
        "utils.py", "data_provider.py",
    ]:
        assert core_unsafe.is_unsafe_path(f, pats), f


def test_glob_patterns_match():
    pats = core_unsafe.load_patterns()
    assert core_unsafe.is_unsafe_path("backfill_ohlc_v2.py", pats)       # backfill_*
    assert core_unsafe.is_unsafe_path("backfill_fundamentals.py", pats)
    assert core_unsafe.is_unsafe_path("providers/finviz.py", pats)        # providers/**
    assert core_unsafe.is_unsafe_path("agent/orchestrator_critic.py", pats)        # agent/**
    assert core_unsafe.is_unsafe_path("agent/notifications/email_sender.py", pats)  # nested


def test_score_and_sheets_writers_match():
    pats = core_unsafe.load_patterns()
    for f in ["score_backtest.py", "score_distribution.py", "sync_pk_to_sheet.py",
              "setup_health_audit_sheet.py", "setup_summaries_sheet.py"]:
        assert core_unsafe.is_unsafe_path(f, pats), f


def test_orchestrator_removed_and_safe_paths_pass():
    pats = core_unsafe.load_patterns()
    # orchestrator.py does not exist in the repo -> must NOT be listed
    assert not core_unsafe.is_unsafe_path("orchestrator.py", pats)
    # genuinely auto-safe targets must not be flagged
    assert not core_unsafe.is_unsafe_path("tests/test_helpers.py", pats)
    assert not core_unsafe.is_unsafe_path("scripts/overnight/build_report.py", pats)
    assert not core_unsafe.is_unsafe_path("README.md", pats)


def test_comments_and_blanks_ignored():
    pats = core_unsafe.load_patterns()
    assert all(not p.startswith("#") and p.strip() for p in pats)


def test_anchored_matches_absolute_and_worktree_paths():
    # Edit/Write tools pass absolute or worktree-relative paths; the anchored
    # matcher must catch core files regardless of prefix.
    pats = core_unsafe.load_patterns()
    assert core_unsafe.is_unsafe_anchored("/Users/adilevy/RidingHighPro/formulas.py", pats)
    assert core_unsafe.is_unsafe_anchored("../rh-night-T1/agent/x.py", pats)
    assert core_unsafe.is_unsafe_anchored("/tmp/wt/providers/finviz.py", pats)
    assert core_unsafe.is_unsafe_anchored("config.py", pats)            # plain relative still works


def test_matcher_is_case_insensitive():
    # APFS is case-insensitive: FORMULAS.PY writes the real formulas.py, so the
    # matcher must flag it regardless of case (else Edit("FORMULAS.PY") slips through).
    pats = core_unsafe.load_patterns()
    assert core_unsafe.is_unsafe_path("FORMULAS.PY", pats)
    assert core_unsafe.is_unsafe_anchored("/x/Config.PY", pats)
    assert core_unsafe.is_unsafe_anchored("/wt/AGENT/x.py", pats)


def test_anchored_safe_paths_not_flagged():
    pats = core_unsafe.load_patterns()
    assert not core_unsafe.is_unsafe_anchored("/Users/adilevy/RidingHighPro/tests/test_x.py", pats)
    assert not core_unsafe.is_unsafe_anchored("/Users/adilevy/RidingHighPro/scripts/overnight/build_report.py", pats)
    assert not core_unsafe.is_unsafe_anchored("tests/test_utils.py", pats)   # references utils, but isn't utils.py
    assert not core_unsafe.is_unsafe_anchored("README.md", pats)
