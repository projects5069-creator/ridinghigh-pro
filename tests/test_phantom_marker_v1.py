"""TASK-246: is_confirmed_phantom, the universe-based phantom test.

Why the universe and not the string
-----------------------------------
Measured live on 2026-07-29 against the real finviz screener HTML: the logo
placeholder letter inside the ticker cell was being concatenated onto the symbol,
so the feed produced

    feed value   real ticker
    AAMIX        AMIX
    AA           A            (Agilent)
    AAA          AA           (Alcoa)

A string rule cannot separate the last two. Stripping the doubled first character
turns Alcoa's real AA into A; leaving short symbols alone leaves Agilent broken.
So the test asks the data, not the shape: a value is a confirmed phantom only when
its first character is doubled AND the remainder is itself a ticker seen in the
same dataset. That is the CONFIRMED rule from
scripts/measure_phantom_coverage_v1.py, promoted here so the marker tool and any
loader read one implementation (rule 10, single source of truth).

Mirrors the is_interday_artifact / flag_interday_artifact_chain precedent in
formulas.py: pure, scalar, no pandas, no IO.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formulas import is_confirmed_phantom  # noqa: E402


# The six confirmed phantoms actually measured in 2026-07, with their true symbol.
MEASURED_PHANTOMS = [
    ("AAMIX", "AMIX"),
    ("VVEEE", "VEEE"),
    ("IINLF", "INLF"),
    ("DDFNS", "DFNS"),
    ("TTC", "TC"),
    ("AADVB", "ADVB"),
]

# Real symbols that start with a repeated letter. A shape-based rule destroys these.
REAL_DOUBLED = ["AA", "AAPL", "III", "TTOO", "MMM", "CCJ", "WW"]


@pytest.mark.parametrize("feed_value,true_symbol", MEASURED_PHANTOMS)
def test_measured_phantoms_are_confirmed(feed_value, true_symbol):
    universe = {true_symbol, "SPY", "QQQ"}
    assert is_confirmed_phantom(feed_value, universe) is True


@pytest.mark.parametrize("symbol", REAL_DOUBLED)
def test_real_doubled_symbols_are_not_phantoms(symbol):
    """In the universe as themselves, with their stripped form absent."""
    universe = {symbol, "SPY", "QQQ"}
    assert is_confirmed_phantom(symbol, universe) is False


def test_the_case_that_kills_a_string_rule():
    """Agilent arrives as AA and Alcoa as AAA. Only the universe separates them.

    Universe holds A and AA as real symbols. Then:
      AA  -> stripped A  is real -> phantom of Agilent
      AAA -> stripped AA is real -> phantom of Alcoa
    and with a universe that does NOT contain the stripped form, AA is left alone.
    """
    universe_with_both = {"A", "AA", "SPY"}
    assert is_confirmed_phantom("AA", universe_with_both) is True
    assert is_confirmed_phantom("AAA", universe_with_both) is True

    # Same input string, different universe, opposite verdict. This is the whole point.
    universe_alcoa_only = {"AA", "SPY"}
    assert is_confirmed_phantom("AA", universe_alcoa_only) is False


def test_stripped_form_absent_from_universe_is_not_confirmed():
    """Doubled first letter but no evidence: candidate, not confirmed."""
    assert is_confirmed_phantom("AAZZZ", {"SPY", "QQQ"}) is False


def test_hyphenated_symbol_measured_live():
    """AAAC-U appeared in the feed; the real symbol is AAC-U."""
    assert is_confirmed_phantom("AAAC-U", {"AAC-U"}) is True
    assert is_confirmed_phantom("AAC-U", {"AAC-U"}) is False


def test_case_and_whitespace_are_normalised():
    assert is_confirmed_phantom("  aamix  ", {"AMIX"}) is True
    assert is_confirmed_phantom("aamix", {"amix"}) is True


def test_single_letter_is_never_a_phantom():
    assert is_confirmed_phantom("A", {"A"}) is False


def test_empty_and_none_are_never_phantoms():
    assert is_confirmed_phantom("", {"A"}) is False
    assert is_confirmed_phantom(None, {"A"}) is False
    assert is_confirmed_phantom("   ", {"A"}) is False


def test_empty_universe_never_confirms():
    assert is_confirmed_phantom("AAMIX", set()) is False
    assert is_confirmed_phantom("AAMIX", None) is False


def test_non_doubled_never_confirms_even_if_stripped_is_real():
    """ABCD stripped is BCD; without the doubled first letter it is not the bug."""
    assert is_confirmed_phantom("ABCD", {"BCD"}) is False


def test_accepts_any_container_for_the_universe():
    """The marker tool passes a set; a loader may pass a list or dict keys."""
    assert is_confirmed_phantom("AAMIX", ["AMIX"]) is True
    assert is_confirmed_phantom("AAMIX", {"AMIX": 1}.keys()) is True


def test_returns_a_real_bool_not_a_truthy_value():
    """Callers write the result into a sheet cell, so the type matters."""
    assert isinstance(is_confirmed_phantom("AAMIX", {"AMIX"}), bool)
    assert isinstance(is_confirmed_phantom("AAPL", {"AAPL"}), bool)


# ── second layer: the three-way tier ─────────────────────────────────────────
# One bool is not enough to act on. Of the 83 stuck open positions, 67 have a
# corroborating symbol in the data and 16 do not, and the two groups deserve
# different treatment: the first is proven, the second is likely but unproven.

from formulas import classify_phantom_tier  # noqa: E402

CONFIRMED = "PHANTOM_CONFIRMED"
SUSPECT = "PHANTOM_SUSPECT"
CLEAN = "CLEAN"

# The six suspects measured in paper_portfolio on 2026-07-30. Their stripped
# forms (ATPC, BIYA, PAVS, STKH, VSA, WLDS) never appeared in the July universe.
MEASURED_SUSPECTS = ["AATPC", "BBIYA", "PPAVS", "SSTKH", "VVSA", "WWLDS"]


@pytest.mark.parametrize("feed_value,true_symbol", MEASURED_PHANTOMS)
def test_tier_confirmed_for_measured_phantoms(feed_value, true_symbol):
    assert classify_phantom_tier(feed_value, {true_symbol, "SPY"}) == CONFIRMED


@pytest.mark.parametrize("symbol", MEASURED_SUSPECTS)
def test_tier_suspect_when_stripped_form_is_absent(symbol):
    assert classify_phantom_tier(symbol, {"SPY", "QQQ", "AMIX"}) == SUSPECT


@pytest.mark.parametrize("symbol", REAL_DOUBLED)
def test_tier_suspect_for_real_doubled_symbols_too(symbol):
    """A real doubled-letter symbol is SUSPECT, not CLEAN — and that is correct.

    This test asserted CLEAN until 2026-08-03. It could not be satisfied, and the
    attempt to satisfy it would have broken the classifier. The rule it implied was
    "the symbol is itself in the universe", and mark_phantom_rows_v1.build_universe
    is defined as "every ticker seen anywhere in the loaded tabs" — so in production
    the symbol under test is ALWAYS in the universe, including a corrupted one.
    Under that rule PHANTOM_SUSPECT becomes unreachable and SSTKH / WWLDS classify
    as CLEAN, though STKH and WLDS both appeared in the live scan of 2026-08-03,
    proving them phantoms.

    The asymmetry decides it. A wrong SUSPECT costs one legitimate row excluded
    from a research sample. A wrong CLEAN costs a stuck position counted as a real
    trade. Nothing is deleted and no metric is rewritten either way — the tier only
    writes a mark that research filters on.

    Separating AAPL from AAMIX needs an authoritative list of tradable symbols,
    which the string and this universe cannot supply. utils.validate_stock_data
    already returns "NO_DATA" when the provider had no price for a row: that is the
    corroborating signal, it is offline and pure, and it belongs in a layer above
    formulas — not inside it.
    """
    assert classify_phantom_tier(symbol, {symbol, "SPY"}) == SUSPECT


def test_tier_clean_for_ordinary_symbol():
    assert classify_phantom_tier("MSFT", {"MSFT", "SPY"}) == CLEAN


def test_the_universe_is_point_in_time():
    """The property that makes a marking run a judgement, not a permanent truth.

    Same ticker, same code, opposite verdict, because the universe grew. This is
    not a defect: the July universe went from 497 distinct tickers on 29/7 to 543
    on 30/7 and confirmed counts rose with it.
    """
    ticker = "AATPC"
    before = {"SPY", "QQQ"}
    assert classify_phantom_tier(ticker, before) == SUSPECT

    after = before | {"ATPC"}          # the stripped form is scanned for the first time
    assert classify_phantom_tier(ticker, after) == CONFIRMED


def test_tier_agrees_with_is_confirmed_phantom_and_does_not_duplicate_it():
    """The bool and the tier must never disagree on the confirmed case."""
    for feed_value, true_symbol in MEASURED_PHANTOMS:
        u = {true_symbol}
        assert is_confirmed_phantom(feed_value, u) is True
        assert classify_phantom_tier(feed_value, u) == CONFIRMED
    for symbol in MEASURED_SUSPECTS:
        u = {"SPY"}
        assert is_confirmed_phantom(symbol, u) is False
        assert classify_phantom_tier(symbol, u) == SUSPECT


def test_tier_hyphenated_symbol():
    assert classify_phantom_tier("AAAC-U", {"AAC-U"}) == CONFIRMED
    assert classify_phantom_tier("AAAC-U", {"SPY"}) == SUSPECT
    # AAC-U doubles its first character too, so it is SUSPECT on shape alone —
    # same verdict as the REAL_DOUBLED case above, for the same reason.
    assert classify_phantom_tier("AAC-U", {"AAC-U"}) == SUSPECT


def test_tier_case_and_whitespace():
    assert classify_phantom_tier("  aamix  ", {"AMIX"}) == CONFIRMED
    assert classify_phantom_tier("  aatpc  ", {"SPY"}) == SUSPECT


def test_tier_single_letter_is_clean():
    assert classify_phantom_tier("A", {"A"}) == CLEAN


def test_tier_empty_and_none_are_clean():
    assert classify_phantom_tier("", {"A"}) == CLEAN
    assert classify_phantom_tier(None, {"A"}) == CLEAN
    assert classify_phantom_tier("   ", {"A"}) == CLEAN


def test_tier_empty_universe_downgrades_to_suspect_never_confirmed():
    """With no evidence nothing can be confirmed, but the shape is still odd."""
    assert classify_phantom_tier("AAMIX", set()) == SUSPECT
    assert classify_phantom_tier("AAMIX", None) == SUSPECT
    assert classify_phantom_tier("MSFT", set()) == CLEAN


def test_tier_returns_one_of_exactly_three_literals():
    allowed = {CONFIRMED, SUSPECT, CLEAN}
    for t, u in [("AAMIX", {"AMIX"}), ("AATPC", {"SPY"}), ("AAPL", {"AAPL"}),
                 ("", set()), (None, {"A"}), ("A", {"A"})]:
        assert classify_phantom_tier(t, u) in allowed


# ── third layer: the marker tool must act on BOTH tiers ──────────────────────
# The tool called is_confirmed_phantom alone, so it marked the 67 confirmed rows
# and left the 16 suspects with no mark at all. Those 16 are stuck positions that
# nothing explains, which is exactly the set a researcher must be able to exclude
# by rule. Wiring the tier in is what turns the classification into an action.

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from mark_phantom_rows_v1 import (  # noqa: E402
    plan_tab, build_universe,
    FLAG_COL, FLAG_VALUE, FLAG_VALUE_SUSPECT,
    PP_DATAQUALITY_VALUE, PP_DATAQUALITY_VALUE_SUSPECT,
)


def _post_analysis_fixture():
    """One sheet shaped like the real thing: a confirmed phantom, a suspect,
    a real symbol whose doubled form corroborates it, and an ordinary ticker."""
    return [
        ["Ticker", "ScanDate", "MxV"],
        ["AAMIX", "2026-07-16", "-300"],   # confirmed: AMIX is below
        ["AMIX",  "2026-07-14", "-250"],   # the corroborating real symbol
        ["AATPC", "2026-07-17", "-310"],   # suspect: ATPC never appears
        ["MSFT",  "2026-07-17", "-120"],   # clean, untouched
    ]


def test_marker_marks_confirmed_and_suspect_with_distinct_values():
    vals = _post_analysis_fixture()
    universe = build_universe({"post_analysis": vals})
    _header, hits, _note = plan_tab("post_analysis", vals, universe)

    by_ticker = {t: action for _row, t, _day, action in hits}
    assert by_ticker["AAMIX"] == f"{FLAG_COL}={FLAG_VALUE}"
    assert by_ticker["AATPC"] == f"{FLAG_COL}={FLAG_VALUE_SUSPECT}"
    assert FLAG_VALUE != FLAG_VALUE_SUSPECT, "research must be able to tell them apart"


def test_marker_never_marks_a_clean_row():
    vals = _post_analysis_fixture()
    universe = build_universe({"post_analysis": vals})
    _header, hits, _note = plan_tab("post_analysis", vals, universe)

    marked = {t for _row, t, _day, _action in hits}
    assert "MSFT" not in marked
    assert "AMIX" not in marked, "the real symbol the phantom was derived from stays clean"
    assert marked == {"AAMIX", "AATPC"}


def test_marker_covers_every_stuck_row_not_just_the_confirmed_ones():
    """The regression this wiring exists to prevent.

    Before 2026-08-03 the tool filtered on is_confirmed_phantom alone, so a sheet
    like this produced ONE hit and the suspect row was silently skipped. On the
    real July data that was 67 marked out of 83, with the 16 hardest rows left
    unexplained.
    """
    vals = _post_analysis_fixture()
    universe = build_universe({"post_analysis": vals})
    _header, hits, _note = plan_tab("post_analysis", vals, universe)
    assert len(hits) == 2, f"expected both tiers marked, got {hits}"


def test_marker_paper_portfolio_uses_the_existing_dataquality_column():
    """paper_portfolio is mode=exact with 25 columns, so no column may be added.

    The tier still has to survive that constraint: two distinct DataQuality values,
    written into the column that already exists.
    """
    vals = [
        ["Ticker", "EntryDate", "Status", "DataQuality"],
        ["AAMIX", "2026-07-16", "DRY_RUN_OPEN", ""],
        ["AMIX",  "2026-07-14", "DRY_RUN_CLOSED", ""],
        ["AATPC", "2026-07-17", "DRY_RUN_OPEN", ""],
    ]
    universe = build_universe({"paper_portfolio": vals})
    header, hits, _note = plan_tab("paper_portfolio", vals, universe)

    assert len(header) == 4, "no column may be added to paper_portfolio"
    by_ticker = {t: action for _row, t, _day, action in hits}
    assert by_ticker["AAMIX"] == f"DataQuality={PP_DATAQUALITY_VALUE}"
    assert by_ticker["AATPC"] == f"DataQuality={PP_DATAQUALITY_VALUE_SUSPECT}"
