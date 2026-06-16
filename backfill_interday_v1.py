"""TASK-182: one-time backfill of InterdayArtifact/InterdayArtifactPair on legacy
post_analysis rows (written before TASK-180's collector wiring, so the flag is blank).

Recomputes the split/halt flag from the D0-D5 close chain via the SAME detector the
collector uses (flag_interday_artifact_chain) -- single source of truth, no threshold
duplication. Non-destructive: rows that already carry a value are left untouched.
"""
import math
from formulas import flag_interday_artifact_chain


def _num(v):
    """Coerce a gspread string/number to float, or None if blank/NaN/non-numeric."""
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def backfill_interday_flags(df):
    """Return a copy of df with BLANK InterdayArtifact/Pair filled from D0-D5 closes."""
    df = df.copy()
    # columns load as string-dtype from Sheets; object dtype lets us assign bools cleanly
    for col in ("InterdayArtifact", "InterdayArtifactPair"):
        if col in df.columns:
            df[col] = df[col].astype(object)
    for idx in df.index:
        cur = str(df.at[idx, "InterdayArtifact"]).strip().lower() \
            if "InterdayArtifact" in df.columns else ""
        if cur in ("", "nan", "none"):
            closes = [_num(df.at[idx, "D0_Close"])] + \
                     [_num(df.at[idx, f"D{i}_Close"]) for i in range(1, 6)]
            is_art, pair = flag_interday_artifact_chain(closes)
            df.at[idx, "InterdayArtifact"] = is_art
            df.at[idx, "InterdayArtifactPair"] = pair
    return df
