"""TASK-238: extract the finviz ticker from the DOM, never from a string guess.

Why this is not a string sanitizer
----------------------------------
Measured live 2026-07-29 against the real screener HTML: finviz now renders a
logo placeholder letter inside the ticker cell, so BeautifulSoup's col.text
concatenates it with the ticker. The library takes col.text raw, in 0.14.6
(overview.py:199) and in 1.3.0 (base.py:127) alike, so the version pin is
irrelevant to this bug.

The decisive observation is that the damage is not recoverable from the string:

    col.text   real ticker
    AA         A            (Agilent)
    AAA        AA           (Alcoa)
    AAAA       AAA
    AAMIX      AMIX

A rule that strips the doubled first character turns Alcoa's real "AA" into "A",
and a rule that leaves short symbols alone leaves Agilent broken. No string rule
separates them, so any heuristic here would trade a visible bug for a silent one.

The clean value is present in the DOM twice, on every row: the td carries
data-boxover-ticker, and the cell contains <a class="tab-link"> with the ticker
as its only text. These tests pin the extraction to those, in that order.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils  # noqa: E402

bs4 = pytest.importorskip("bs4")
from bs4 import BeautifulSoup  # noqa: E402


def _cell(html):
    return BeautifulSoup(html, "html.parser").find("td")


# Verbatim shape captured from the live page on 2026-07-29.
REAL_CELL = (
    '<td align="left" data-boxover-ticker="{t}" height="10">'
    '<span class="flex items-center gap-1 pl-0.5">'
    '<a class="company-ticker" href="stock?t={t}">'
    '<img alt="{t} logo" src="https://logo.finviz.com/{t}.svg"/>'
    '<span>{first}</span></a>'
    '<a class="tab-link" href="stock?t={t}">{t}</a></span></td>'
)


@pytest.mark.parametrize("ticker", [
    "AMIX", "BEG", "BEX", "DFNS", "EGG", "GMM", "VEEE", "INLF", "TC",
    # The cases a string rule cannot survive.
    "A", "AA", "AAA", "AAPL", "AAL", "BB", "CCJ", "MMM", "WW", "III", "TTOO",
    # Punctuation seen live.
    "AAC-U",
])
def test_extracts_true_ticker_from_real_cell_shape(ticker):
    td = _cell(REAL_CELL.format(t=ticker, first=ticker[0]))
    # Guard: this cell really does exhibit the bug via naive text extraction.
    assert td.text.strip() == ticker[0] + ticker
    assert utils.extract_finviz_ticker(td) == ticker


def test_prefers_attribute_over_link():
    td = _cell('<td data-boxover-ticker="AMIX">'
               '<a class="tab-link">WRONG</a></td>')
    assert utils.extract_finviz_ticker(td) == "AMIX"


def test_falls_back_to_tab_link_when_attribute_absent():
    td = _cell('<td><span><a class="company-ticker"><span>A</span></a>'
               '<a class="tab-link">AMIX</a></span></td>')
    assert utils.extract_finviz_ticker(td) == "AMIX"


def test_falls_back_to_plain_text_when_dom_is_flat():
    """Older markup with no logo span and no attribute must pass through."""
    td = _cell('<td>AMIX</td>')
    assert utils.extract_finviz_ticker(td) == "AMIX"


def test_empty_attribute_does_not_win():
    td = _cell('<td data-boxover-ticker="">'
               '<a class="tab-link">AMIX</a></td>')
    assert utils.extract_finviz_ticker(td) == "AMIX"


def test_whitespace_and_case_are_normalised():
    td = _cell('<td data-boxover-ticker="  amix  "></td>')
    assert utils.extract_finviz_ticker(td) == "AMIX"


def test_empty_cell_returns_empty_string():
    assert utils.extract_finviz_ticker(_cell("<td></td>")) == ""


def test_none_cell_returns_empty_string():
    assert utils.extract_finviz_ticker(None) == ""


def test_sanitized_overview_repairs_the_ticker_column():
    """The wiring point: one funnel, _get_table, shared by 0.14.6 and 1.3.0."""
    pytest.importorskip("finvizfinance")
    pytest.importorskip("pandas")
    import pandas as pd

    html = (
        "<table><tr><td>No.</td><td>Ticker</td><td>Price</td></tr>"
        "<tr><td>1</td>" + REAL_CELL.format(t="AMIX", first="A") +
        "<td>3.10</td></tr>"
        "<tr><td>2</td>" + REAL_CELL.format(t="A", first="A") +
        "<td>140.00</td></tr></table>"
    )
    rows = BeautifulSoup(html, "html.parser").find_all("tr")

    ov = utils.SanitizedOverview()
    df = ov._get_table(rows, pd.DataFrame([], columns=["Ticker", "Price"]),
                       [], ["Ticker", "Price"])

    assert list(df["Ticker"]) == ["AMIX", "A"], (
        "second row is Agilent: naive text gives 'AA', which is why a string "
        "rule cannot be used here"
    )


# ── hook guards ──────────────────────────────────────────────────────────────
# The extraction only works because SanitizedOverview overrides _get_table. If a
# future finvizfinance release moves that method, renames it, or changes its
# signature, the override stops applying and the corruption returns with no
# error raised anywhere. These three run offline and fail loudly in that case.

LIBRARY_GET_TABLE_SIGNATURE = "(self, rows, df, num_col_index, table_header, limit=-1)"


def test_override_resolves_to_utils_not_to_the_library():
    """Qualname is nested, so ask the module instead."""
    import inspect

    pytest.importorskip("finvizfinance")
    ov = utils.SanitizedOverview()
    module = inspect.getmodule(type(ov)._get_table)
    assert module is not None, "could not resolve the module of _get_table"
    assert module.__name__ == "utils", (
        f"_get_table resolved to {module.__name__}, not utils. The override is "
        f"no longer in the MRO and finviz tickers are being read raw again."
    )


def test_library_get_table_signature_is_what_the_override_expects():
    """0.14.6 defines it on Overview, 1.3.0 on Base, both with this signature."""
    import inspect

    pytest.importorskip("finvizfinance")
    from finvizfinance.screener.overview import Overview

    actual = str(inspect.signature(Overview._get_table))
    assert actual == LIBRARY_GET_TABLE_SIGNATURE, (
        f"finvizfinance changed _get_table from {LIBRARY_GET_TABLE_SIGNATURE} "
        f"to {actual}. utils.SanitizedOverview._get_table must be updated to "
        f"match, otherwise the ticker column silently reverts to col.text."
    )


def test_offline_end_to_end_ticker_column_stays_clean():
    """Fixed fixture, no network. Shape copied from the live page, 2026-07-29."""
    pytest.importorskip("finvizfinance")
    pytest.importorskip("pandas")
    import pandas as pd

    # AMIX is the plain corruption case. A and AA are the pair that proves a
    # string rule cannot work: they arrive as AA and AAA respectively.
    html = (
        "<table><tr><td>No.</td><td>Ticker</td><td>Price</td></tr>"
        + "".join(
            f"<tr><td>{i}</td>" + REAL_CELL.format(t=t, first=t[0])
            + f"<td>{p}</td></tr>"
            for i, (t, p) in enumerate(
                [("AMIX", "3.10"), ("A", "140.00"), ("AA", "31.50"),
                 ("VEEE", "2.40"), ("AAC-U", "10.05")], start=1)
        )
        + "</table>"
    )
    rows = BeautifulSoup(html, "html.parser").find_all("tr")

    ov = utils.SanitizedOverview()
    df = ov._get_table(rows, pd.DataFrame([], columns=["Ticker", "Price"]),
                       [], ["Ticker", "Price"])

    assert list(df["Ticker"]) == ["AMIX", "A", "AA", "VEEE", "AAC-U"]
    # And the naive path this replaced really would have been wrong.
    naive = [r.find_all("td")[1].text.strip() for r in rows[1:]]
    assert naive == ["AAMIX", "AA", "AAA", "VVEEE", "AAAC-U"]
