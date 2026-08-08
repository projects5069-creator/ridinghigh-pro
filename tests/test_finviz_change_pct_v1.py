"""finviz renamed the screener header 'Change' → 'Change %' (2026-08-07).

Measured live on 2026-08-08 against the real screener page:

    th row:  ['No.', 'Ticker', ..., 'P/E', 'Price', 'Change %', 'Volume']
    NUMBER_COL (finvizfinance 1.3.0 constants): has 'Change', NOT 'Change %'

Two consequences, both fatal to the scan path on 2026-08-07 (482 runs, zero
tickers, a full lost trading day):

  1. The df column is now named 'Change %', so both consumers —
     auto_scanner.fetch_finviz:350 and dashboard.fetch_finviz_data:236 —
     die on sort_values(by='Change') (KeyError, swallowed, "No stocks").
  2. The renamed column dropped out of the library's numeric-conversion set,
     so its values arrive as raw strings ('19.63%') instead of the fraction
     floats (0.1963) that analyze_ticker's float()*100 contract expects.

Both call sites route every page through utils.SanitizedOverview._get_table
(§10 single funnel — same reason TASK-238 lives there), so the normalization
is pinned there: header name back to 'Change', values through number_covert.

The fixture mirrors the caller exactly (finvizfinance 1.3.0 base.py:137-153):
rows include the header tr, each body row carries the leading 'No.' td that
_get_table strips, and num_col_index is what the library computes today —
the change column absent, because 'Change %' is not in NUMBER_COL.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils  # noqa: E402

bs4 = pytest.importorskip("bs4")
from bs4 import BeautifulSoup  # noqa: E402


# Header shape captured live 2026-08-08 (after finviz's rename).
HEADER_NEW = ["Ticker", "Company", "Sector", "Industry", "Country",
              "Market Cap", "P/E", "Price", "Change %", "Volume"]
# The pre-2026-08-07 shape, kept as a revert guard.
HEADER_OLD = ["Ticker", "Company", "Sector", "Industry", "Country",
              "Market Cap", "P/E", "Price", "Change", "Volume"]


def _rows(header, change_cell):
    """Build the tr list exactly as the library hands it to _get_table."""
    ths = "".join(f"<th>{h}</th>" for h in ["No."] + header)
    tds = "".join([
        "<td>1</td>",
        '<td><a class="tab-link">TTC</a></td>',
        "<td>TenTen Corp</td>", "<td>Technology</td>", "<td>Software</td>",
        "<td>USA</td>", "<td>12.5M</td>", "<td>-</td>", "<td>3.46</td>",
        f"<td>{change_cell}</td>", "<td>4,628,702</td>",
    ])
    html = f"<table><tr>{ths}</tr><tr>{tds}</tr></table>"
    return BeautifulSoup(html, "html.parser").find("table").find_all("tr")


def _num_col_index(header):
    """What base.py:148 computes: indexes of headers found in NUMBER_COL —
    hand-built here (not imported) so the test runs under 0.14.6 and 1.3.0
    alike. Today that set matches 'Market Cap', 'Price', 'Volume', 'Change' —
    and NOT 'Change %', which is precisely the bug."""
    numeric = {"Market Cap", "Price", "Volume", "Change"}
    return [i for i, h in enumerate(header) if h in numeric]


def test_change_pct_header_is_normalized_to_change_fraction():
    ov = utils.SanitizedOverview()
    df = ov._get_table(_rows(HEADER_NEW, "19.63%"), None,
                       _num_col_index(HEADER_NEW), HEADER_NEW)
    assert "Change" in df.columns, f"columns: {list(df.columns)}"
    assert "Change %" not in df.columns
    val = df["Change"].iloc[0]
    assert isinstance(val, float), f"Change stayed {type(val).__name__}: {val!r}"
    assert val == pytest.approx(0.1963)
    # the consumers' first move — must not raise
    df.sort_values(by="Change", ascending=False)


def test_legacy_change_header_contract_unchanged():
    ov = utils.SanitizedOverview()
    df = ov._get_table(_rows(HEADER_OLD, "19.63%"), None,
                       _num_col_index(HEADER_OLD), HEADER_OLD)
    assert "Change" in df.columns
    assert df["Change"].iloc[0] == pytest.approx(0.1963)
    assert df["Ticker"].iloc[0] == "TTC"


def test_ticker_sanitization_survives_the_rename():
    ov = utils.SanitizedOverview()
    df = ov._get_table(_rows(HEADER_NEW, "19.63%"), None,
                       _num_col_index(HEADER_NEW), HEADER_NEW)
    assert df["Ticker"].iloc[0] == "TTC"
