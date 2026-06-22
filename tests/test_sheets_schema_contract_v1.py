"""TASK-167 — SCHEMA.json contract + drift check (Layer-1, auto-safe, no gc).

The contract (SCHEMA.json) is a DERIVED artifact: scripts/generate_sheets_schema.py
builds it from the live code constants (AGENT_SHEET_HEADERS, TIMELINE_LIVE_COLS)
so code stays the §10 single source of truth. These tests prove:
  - the on-disk SCHEMA.json equals a fresh in-memory generation (round-trip) —
    catches a hand-edited or stale JSON;
  - each sheet's columns match the code constant they derive from;
  - post_analysis uses a required-subset contract (presence), with D6-D25 as
    forward-optional (decoupled from TASK-177);
  - the pure drift detector (_required_columns_result) flags missing/extra
    correctly without any live Sheets access.

Layer-2 (live gc read in health_audit.check_08) is code-only for now; its
live-verify is deferred to a quiet/post-EOD window (RULE #6). The pure logic
it delegates to is fully covered here by test #6.
"""
import importlib.util
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

# Derived-artifact generator (script-style import, project convention)
_spec = importlib.util.spec_from_file_location(
    "generate_sheets_schema",
    os.path.join(_REPO, "scripts", "generate_sheets_schema.py"))
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)

import health_audit
from agent.setup.create_agent_sheets import AGENT_SHEET_NAMES, AGENT_SHEET_HEADERS
from sheets_manager import TIMELINE_LIVE_COLS

SCHEMA_PATH = os.path.join(_REPO, "SCHEMA.json")


def _load_disk_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ── #1 file exists & parses ───────────────────────────────────────────────
def test_schema_file_exists_and_parses():
    assert os.path.exists(SCHEMA_PATH), "SCHEMA.json missing"
    data = _load_disk_schema()
    assert "sheets" in data and "_meta" in data


# ── #2 ROUND-TRIP: disk JSON == fresh in-memory generation (key guard) ─────
def test_roundtrip_code_to_json_matches():
    disk = _load_disk_schema()
    fresh = g.build_contract()
    assert disk == fresh, (
        "SCHEMA.json is stale or hand-edited — re-run "
        "scripts/generate_sheets_schema.py to regenerate")


# ── #3 agent sheets derive exactly from AGENT_SHEET_HEADERS ────────────────
def test_agent_sheets_match_constants():
    sheets = _load_disk_schema()["sheets"]
    for name in AGENT_SHEET_NAMES:
        assert name in sheets, f"{name} absent from contract"
        assert sheets[name]["mode"] == "exact"
        assert sheets[name]["columns"] == list(AGENT_SHEET_HEADERS[name])


# ── #4 timeline_live derives from TIMELINE_LIVE_COLS ───────────────────────
def test_timeline_matches_constant():
    tl = _load_disk_schema()["sheets"]["timeline_live"]
    assert tl["mode"] == "exact"
    assert tl["columns"] == list(TIMELINE_LIVE_COLS)


# ── #5 post_analysis = required-subset; D6-D25 forward-optional ────────────
def test_post_analysis_required_and_forward():
    pa = _load_disk_schema()["sheets"]["post_analysis"]
    assert pa["mode"] == "required_subset"
    for col in ("Ticker", "ScanDate", "Score", "ScanPrice", "score_version"):
        assert col in pa["required"]
    # D6-D25 must be forward-optional, NOT required (decouples 167 from 177)
    assert any(c.startswith("D6_") for c in pa["forward_optional"])
    assert all(not c.startswith("D6_") for c in pa["required"])


# ── #6 pure drift detector (no gc) ─────────────────────────────────────────
def test_drift_detector_pure():
    contract = {
        "alpha": {"mode": "exact", "columns": ["A", "B", "C"]},
        "beta": {"mode": "required_subset",
                 "required": ["X", "Y"], "forward_optional": ["Z6", "Z7"]},
    }
    # all good -> no issues
    clean = health_audit._required_columns_result(
        {"alpha": ["A", "B", "C"], "beta": ["X", "Y", "extra"]}, contract)
    assert clean == []

    # exact: missing a column -> issue mentions alpha + missing
    miss = health_audit._required_columns_result(
        {"alpha": ["A", "B"], "beta": ["X", "Y"]}, contract)
    assert any("alpha" in s and "missing" in s.lower() for s in miss)

    # exact: extra/unexpected column -> issue
    extra = health_audit._required_columns_result(
        {"alpha": ["A", "B", "C", "D"], "beta": ["X", "Y"]}, contract)
    assert any("alpha" in s for s in extra)

    # required_subset: missing a REQUIRED col -> issue
    req = health_audit._required_columns_result(
        {"alpha": ["A", "B", "C"], "beta": ["X"]}, contract)
    assert any("beta" in s and "missing" in s.lower() for s in req)

    # required_subset: missing only a forward_optional -> NO issue
    fwd = health_audit._required_columns_result(
        {"alpha": ["A", "B", "C"], "beta": ["X", "Y"]}, contract)
    assert fwd == []
