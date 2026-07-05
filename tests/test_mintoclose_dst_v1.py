"""enrich_post_analysis._min_to_close must be DST-aware.

MinToClose = minutes between peak-score time (Peru) and market close.
Close = 16:00 ET (America/New_York, DST-aware). Hardcoding "15:00" Peru
only holds in summer/EDT; winter/EST close is 16:00 Peru -> the old code
undercounts by 60 min. Mirror of utils.is_day_complete / auto_scanner.
is_snapshot_time (TASK-223). RULE #10.  TASK-231.

Ground-truth (verified vs live pytz): peak 14:00 Peru ->
  summer 2026-07-06 (EDT, 16:00 ET = 15:00 Peru): 60 min
  winter 2026-01-06 (EST, 16:00 ET = 16:00 Peru): 120 min
"""
import enrich_post_analysis as ep


def test_summer_edt_close_is_1500_peru():
    assert ep._min_to_close("14:00:00", "2026-07-06") == "60"


def test_winter_est_close_is_1600_peru():
    assert ep._min_to_close("14:00:00", "2026-01-06") == "120"


def test_dst_delta_is_60_min_same_peak():
    summer = int(ep._min_to_close("14:00:00", "2026-07-06"))
    winter = int(ep._min_to_close("14:00:00", "2026-01-06"))
    assert winter - summer == 60


def test_peak_after_close_clamps_to_zero():
    assert ep._min_to_close("16:30:00", "2026-07-06") == "0"
