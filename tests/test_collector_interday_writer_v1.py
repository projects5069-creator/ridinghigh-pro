"""TASK-182 §0 writer-hardening — post_analysis_collector must write
InterdayArtifact as a STRING ('True'/'False'), not a bare Python bool.

Root cause: a bool column unioned with legacy NaN rows in
save_post_analysis_to_sheets up-casts to float64 (True->1.0), then
gsheets_sync's .fillna('').astype(str) renders '1.0'/'0.0' into the sheet —
which the old _coerce_bool read as False (the §0 bug). Writing str(bool) keeps
the column object-dtype, so it never up-casts. Defense-in-depth: the reader
(_coerce_bool, fixed in a2bd740) already tolerates '1.0', but the writer should
not produce it. Source-guard is RED on the pre-fix collector, GREEN after.
"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _collector_src():
    return open(os.path.join(_REPO, "post_analysis_collector.py"), encoding="utf-8").read()


def test_collector_writes_interday_artifact_as_string():
    """Production guard: the row dict must wrap the bool in str()."""
    src = _collector_src()
    assert '"InterdayArtifact": str(interday_is_artifact)' in src, \
        "collector must write str(interday_is_artifact) (object-dtype, no float up-cast)"
    assert '"InterdayArtifact": interday_is_artifact,' not in src, \
        "bare bool still written -> will up-cast to '1.0'/'0.0' on union with legacy NaN"


def test_str_bool_roundtrips_through_coerce_bool():
    """The hardened writer emits 'True'/'False'; the reader must round-trip them.
    (The live up-cast that produced '1.0'/'0.0' lives in the union path and is
    evidenced by the TASK-182 dry-run — 13x'0.0' + 1x'1.0' — not reproduced here;
    str() guarantees object-dtype so no downstream float-coercion can occur.)"""
    from cross_month_loaders import _coerce_bool
    written = pd.Series([str(True), str(False)])     # what the hardened collector writes
    assert _coerce_bool(written).tolist() == [True, False]
