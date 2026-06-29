"""TASK-207 AC#2 — dry-run fidelity: report only tabs actually missing from config.

RED: the current dry-run branch prints "Would create" for ALL AGENT_SHEET_NAMES,
ignoring the per-sheet config-skip that the LIVE run performs. With 15/16 already
in sheets_config, a faithful dry-run must list exactly ONE would-create tab
(shadow_gate_events), not 16.

Offline: the dry-run branch returns before drive_oauth is built, so no Google
calls happen and no credentials are needed.
"""
import importlib

cs = importlib.import_module("agent.setup.create_agent_sheets")

TEST_MONTH = "2026-06"
MISSING = "shadow_gate_events"


def _config_15_of_16():
    """sheets_config with every AGENT_SHEET_NAMES tab present EXCEPT shadow_gate_events."""
    present = {n: f"id-{n}" for n in cs.AGENT_SHEET_NAMES if n != MISSING}
    return {TEST_MONTH: present}


def _listed_tabs(out):
    """Tabs the dry-run reported it would create.

    The dry-run lists each tab on its own line as:
        RH-2026-06-<name> (<n> columns)
    so a tab is "listed" iff that exact prefix (name + trailing space) appears.
    Trailing space disambiguates prefixes (e.g. borrow_data vs borrow_coverage).
    """
    prefix = f"RH-{TEST_MONTH}-"
    lines = out.splitlines()
    return [n for n in cs.AGENT_SHEET_NAMES
            if any(f"{prefix}{n} " in ln for ln in lines)]


def test_dryrun_reports_only_missing_tab(monkeypatch, capsys):
    monkeypatch.setattr(cs.sheets_manager, "_load_config", lambda: _config_15_of_16())

    cs.create_agent_sheets(TEST_MONTH, dry_run=True)
    out = capsys.readouterr().out

    listed = _listed_tabs(out)
    assert listed == [MISSING], (
        f"faithful dry-run should list only the missing tab [{MISSING}]; "
        f"got {len(listed)}: {listed}"
    )
