"""TASK-87 — monthly Section C uses MEDIAN (robust), not mean, and re-adds mxv.

Root cause (recon): mxv is NOT polluted by sentinels — it is a heavy-tailed signed ratio
((mcap-price*vol)/mcap*100). Entered pumps cluster very negative with an extreme tail, so the
arithmetic MEAN is genuine but unrepresentative (May avg -1053 vs typical ~ -200/-400). The fix is
to report the MEDIAN for every Section C entry-metric and re-add mxv (previously dropped, mislabeled
"sentinel pollution"). Section C is descriptive/email-only — zero live impact.

build_monthly_detail is a pure @staticmethod -> tested directly, no Sheets.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.critic.critic_v1 import CriticAgent as Critic


def _win_trades_heavy_tailed():
    # EVERY metric has a heavy tail (4th row), so median != mean for each — the test then
    # genuinely locks median, not a symmetric fixture where median==mean:
    #   mxv          [-100,-200,-300,-12000] -> median -250.0   (mean -3150.0)
    #   run_up       [10,20,30,1000]         -> median 25.0     (mean 265.0)
    #   atrx         [1,2,3,100]             -> median 2.5      (mean 26.5)
    #   score_at_entry [60,61,62,600]        -> median 61.5     (mean 195.75)
    #   float_pct    [5,6,7,800]             -> median 6.5      (mean 204.5)
    return [
        {"verdict": "WIN", "mxv": -100, "run_up": 10, "atrx": 1.0, "float_pct": 5, "score_at_entry": 60, "ticker": "A"},
        {"verdict": "WIN", "mxv": -200, "run_up": 20, "atrx": 2.0, "float_pct": 6, "score_at_entry": 61, "ticker": "B"},
        {"verdict": "WIN", "mxv": -300, "run_up": 30, "atrx": 3.0, "float_pct": 7, "score_at_entry": 62, "ticker": "C"},
        {"verdict": "WIN", "mxv": -12000, "run_up": 1000, "atrx": 100.0, "float_pct": 800, "score_at_entry": 600, "ticker": "D"},
    ]


def test_section_c_re_adds_mxv_and_uses_median():
    d = Critic.build_monthly_detail(_win_trades_heavy_tailed())
    ew = d["entry_metrics_win"]
    assert "mxv" in ew                       # re-added (was dropped, mislabeled sentinel pollution)
    # median([-100,-200,-300,-12000]) = -250.0 (typical entered MxV); mean would be -3150 (tail-dragged).
    assert ew["mxv"] == -250.0


def test_section_c_run_up_is_median_not_mean():
    d = Critic.build_monthly_detail(_win_trades_heavy_tailed())
    # median([10,20,30,1000]) = 25.0 (typical); arithmetic mean would be 265.0 (dragged by 1000).
    assert d["entry_metrics_win"]["run_up"] == 25.0


def test_section_c_all_metrics_are_median():
    d = Critic.build_monthly_detail(_win_trades_heavy_tailed())
    ew = d["entry_metrics_win"]
    # atrx median([1,2,3,4]) = 2.5 ; score_at_entry median([60,61,62,63]) = 61.5
    assert ew["atrx"] == 2.5
    assert ew["score_at_entry"] == 61.5
    assert ew["float_pct"] == 6.5            # median([5,6,7,8])


def test_section_c_empty_group_metrics_none_including_mxv():
    d = Critic.build_monthly_detail([
        {"verdict": "WIN", "mxv": -100, "run_up": 10, "atrx": 1.0, "float_pct": 5, "score_at_entry": 60, "ticker": "A"},
    ])
    # no LOSS rows -> loss metrics all None, mxv included
    el = d["entry_metrics_loss"]
    assert el["mxv"] is None and el["run_up"] is None
