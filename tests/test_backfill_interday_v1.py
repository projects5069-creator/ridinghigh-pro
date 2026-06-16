"""TDD for TASK-182 backfill — backfill_interday_flags fills BLANK InterdayArtifact
from D0-D5 closes (non-destructive). RED: backfill_interday_v1 does not exist yet."""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (relocated to tests/)

from backfill_interday_v1 import backfill_interday_flags


def _row(art, d0, d1, d2, d3, d4, d5):
    return {"InterdayArtifact": art, "InterdayArtifactPair": "",
            "D0_Close": d0, "D1_Close": d1, "D2_Close": d2,
            "D3_Close": d3, "D4_Close": d4, "D5_Close": d5}


def test_fills_blank_artifact():
    # blank flag + a +400% D0->D1 jump (>100% threshold) -> should fill True, "D0->D1"
    df = pd.DataFrame([_row("", "1.0", "5.0", "5.1", "5.0", "5.2", "5.1")])
    out = backfill_interday_flags(df)
    assert bool(out.loc[0, "InterdayArtifact"]) is True
    assert out.loc[0, "InterdayArtifactPair"] == "D0->D1"


def test_fills_blank_normal():
    # blank flag + normal closes -> fill False, ""
    df = pd.DataFrame([_row("", "1.0", "1.05", "1.10", "1.08", "1.12", "1.15")])
    out = backfill_interday_flags(df)
    assert bool(out.loc[0, "InterdayArtifact"]) is False
    assert out.loc[0, "InterdayArtifactPair"] == ""


def test_preserves_already_filled():
    # already-valued (False) row whose closes WOULD trip -> must stay unchanged (non-destructive)
    df = pd.DataFrame([_row("False", "1.0", "5.0", "5.1", "5.0", "5.2", "5.1")])
    out = backfill_interday_flags(df)
    assert str(out.loc[0, "InterdayArtifact"]) == "False"
