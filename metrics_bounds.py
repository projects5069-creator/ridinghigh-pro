"""Pure metric-bound helpers (no Streamlit, no I/O).

TASK-147 dual reporting: the headline WR excludes WHIPSAW (optimistic); the
pessimistic bound counts WHIPSAW as losses in the denominator. This is a
policy-layer aggregation only — the core classify_trade WIN/LOSS/WHIPSAW mapping
is untouched (WHIPSAW stays WHIPSAW upstream; it is only treated as a loss here,
for the pessimistic bound).
"""


def wr_bounds(n_win, n_loss, n_whip):
    """Return {'optimistic', 'pessimistic'} win-rate percentages.

    optimistic  = wins / (wins + losses)              * 100   # WHIPSAW excluded (headline)
    pessimistic = wins / (wins + losses + whipsaws)    * 100   # WHIPSAW-as-loss bound (TASK-147)

    Both default to 0.0 when their denominator is zero (no decided trades).
    pessimistic <= optimistic always (a larger denominator with the same numerator).
    """
    decided = n_win + n_loss
    opt = (n_win / decided * 100) if decided else 0.0
    denom_p = decided + n_whip
    pess = (n_win / denom_p * 100) if denom_p else 0.0
    return {"optimistic": opt, "pessimistic": pess}


def expectancy_bounds(decided_nets, whipsaw_as_loss_nets):
    """Return {'optimistic', 'pessimistic'} mean net-PnL FRACTION per trade (TASK-162).

    optimistic  = mean(decided_nets)                          # WIN/LOSS only, WHIPSAW excluded
    pessimistic = mean(decided_nets + whipsaw_as_loss_nets)   # WHIPSAW folded in as losses

    Inputs are lists of per-trade net fractions (from formulas.calculate_net_pnl);
    None entries are filtered. Empty -> 0.0. pessimistic <= optimistic (the WHIPSAW
    rows valued as losses pull the mean down). Policy-layer aggregation only — the
    core classify_trade / calculate_net_pnl logic is untouched.
    """
    dec = [x for x in decided_nets if x is not None]
    opt = (sum(dec) / len(dec)) if dec else 0.0
    alln = dec + [x for x in whipsaw_as_loss_nets if x is not None]
    pess = (sum(alln) / len(alln)) if alln else 0.0
    return {"optimistic": opt, "pessimistic": pess}
