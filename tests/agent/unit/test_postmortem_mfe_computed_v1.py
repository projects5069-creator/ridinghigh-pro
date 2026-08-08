"""T-402 (Sprint 0) — PostmortemEngine must actually compute MFE/MAE.

C-09 measured MaxFavorable/MaxAdverse empty in 169/169 postmortems even though
the provider IS wired (orchestrator.py:657). Root cause found in Sprint 0 recon:
_compute_mfe_mae looks up bars["Low"]/bars["High"] while data_provider.
get_daily_bars returns lowercase columns ('low'/'high'), and passes end_date as
a str against a signature that declares Optional[datetime]. RED before fix.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import pandas as pd

from agent.analytics.postmortem_engine import PostmortemEngine


class FakeProvider:
    """Returns bars shaped exactly like data_provider.get_daily_bars does
    (lowercase OHLCV columns — measured in R27: cols=['open','high','low',
    'close','volume'])."""

    def __init__(self):
        self.received_end_date = "NOT_CALLED"

    def get_daily_bars(self, ticker, days=60, end_date=None):
        self.received_end_date = end_date
        return pd.DataFrame({
            "open":   [10.0, 9.5, 9.8],
            "high":   [10.6, 9.9, 10.1],
            "low":    [9.4, 8.7, 9.6],
            "close":  [9.5, 9.8, 10.0],
            "volume": [1000, 1200, 900],
        })


def test_mfe_mae_computed_with_real_provider_column_casing():
    eng = PostmortemEngine(data_provider=FakeProvider())
    mfe, mae = eng._compute_mfe_mae("SHPH", "2026-08-04", "2026-08-06", 10.0)
    assert mfe == 8.7, f"MFE (lowest low, short-favorable) expected 8.7, got {mfe!r}"
    assert mae == 10.6, f"MAE (highest high, short-adverse) expected 10.6, got {mae!r}"


def test_mfe_mae_passes_datetime_end_date_to_provider():
    fake = FakeProvider()
    eng = PostmortemEngine(data_provider=fake)
    eng._compute_mfe_mae("SHPH", "2026-08-04", "2026-08-06", 10.0)
    assert isinstance(fake.received_end_date, datetime), (
        "data_provider.get_daily_bars declares end_date: Optional[datetime]; "
        f"engine passed {type(fake.received_end_date).__name__}"
    )
