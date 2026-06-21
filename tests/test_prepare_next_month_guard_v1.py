"""test_prepare_next_month_guard_v1.py — TASK-143 AC#3

Prevention root-guard for the monthly rotation. The 2026-07 orphan was created
when prepare_next_month ran against the WRONG root (RidingHigh-Data 1u330dP…)
instead of RidingHighPro (1mHSdsT…), and find_or_create_folder silently took
files[0] when a name-query returned more than one folder. These guards make a
wrong-root run and a duplicate-folder state fail-closed instead of silently
forking the data.

All tests use an in-memory MockDrive — no live Drive. Canonical roots verified
live 2026-06-21: RidingHighPro = 1mHSdsT…, RidingHigh-Data (bad) = 1u330dP….

RED: assert_correct_root / find_duplicate_month_folders / scan_orphan_root do not
exist yet, and find_or_create_folder still returns files[0] on a duplicate.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

import prepare_next_month as pnm

GOOD_ROOT = "1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh"   # RidingHighPro (canonical)
BAD_ROOT = "1u330dPMAVGRDaKaQ81_B9To9uYaSBCl2"    # RidingHigh-Data (orphan source)


# ── In-memory Drive double (mimics googleapiclient files().list/create) ───────
class _Req:
    def __init__(self, fn):
        self._fn = fn

    def execute(self):
        return self._fn()


class _Files:
    def __init__(self, drive):
        self.d = drive

    def list(self, q=None, fields=None):
        return _Req(lambda: self.d._do_list(q))

    def create(self, body=None, fields=None):
        return _Req(lambda: self.d._do_create(body))


class MockDrive:
    """folders: list of {"id","name","parents":[...]}."""
    def __init__(self, folders):
        self.folders = [dict(f) for f in folders]
        self.created = []

    def files(self):
        return _Files(self)

    def _do_list(self, q):
        import re
        q = q or ""
        name_m = re.search(r"name='([^']*)'", q)
        parent_m = re.search(r"'([^']*)' in parents", q)
        out = []
        for f in self.folders:
            if name_m and f["name"] != name_m.group(1):
                continue
            if parent_m and parent_m.group(1) not in f.get("parents", []):
                continue
            out.append({"id": f["id"], "name": f["name"]})
        return {"files": out}

    def _do_create(self, body):
        nid = f"new_{len(self.created)}"
        rec = {"id": nid, "name": body["name"], "parents": body["parents"]}
        self.created.append(rec)
        self.folders.append(rec)
        return {"id": nid}


# ── (a) root assert ───────────────────────────────────────────────────────────
def test_assert_correct_root_rejects_bad_root():
    try:
        pnm.assert_correct_root(BAD_ROOT)
        raised = False
    except Exception:
        raised = True
    assert raised, "assert_correct_root must reject the RidingHigh-Data root"


def test_assert_correct_root_accepts_canonical():
    pnm.assert_correct_root(GOOD_ROOT)  # must not raise


# ── (b) single-folder-per-month ───────────────────────────────────────────────
def test_find_or_create_folder_raises_on_duplicate():
    drive = MockDrive([
        {"id": "a", "name": "2026-08", "parents": [GOOD_ROOT]},
        {"id": "b", "name": "2026-08", "parents": [GOOD_ROOT]},
    ])
    try:
        pnm.find_or_create_folder(drive, "2026-08", GOOD_ROOT)
        raised = False
    except Exception:
        raised = True
    assert raised, "duplicate month folder must raise, not silently pick files[0]"


def test_find_or_create_folder_returns_existing_single():
    drive = MockDrive([{"id": "a", "name": "2026-08", "parents": [GOOD_ROOT]}])
    fid, created = pnm.find_or_create_folder(drive, "2026-08", GOOD_ROOT)
    assert fid == "a" and created is False
    assert drive.created == []  # no new folder created


# ── (c) post-rotation duplicate check (across roots) ──────────────────────────
def test_find_duplicate_month_folders_detects_cross_root():
    drive = MockDrive([
        {"id": "live", "name": "2026-07", "parents": [GOOD_ROOT]},
        {"id": "orphan", "name": "2026-07", "parents": [BAD_ROOT]},
    ])
    dups = pnm.find_duplicate_month_folders(drive, "2026-07")
    assert len(dups) == 2


# ── (d) orphan scan (advisory) ────────────────────────────────────────────────
def test_scan_orphan_root_reports_unknown():
    drive = MockDrive([
        {"id": "orphan", "name": "2026-07", "parents": [BAD_ROOT]},
    ])
    orphans = pnm.scan_orphan_root(drive, BAD_ROOT, known_ids={"live"})
    assert any(o["id"] == "orphan" for o in orphans)
