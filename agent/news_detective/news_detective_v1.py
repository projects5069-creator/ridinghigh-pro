"""
agent/news_detective/news_detective_v1.py
─────────────────────────────────────────
News Detective Agent v1 — SEC EDGAR filings + Finnhub company news.

Data sources:
  - SEC EDGAR submissions API (no API key, requires User-Agent header)
    Ticker→CIK mapping cached from company_tickers.json.
  - Finnhub company-news endpoint (requires FINNHUB_API_KEY env var)

Per-ticker caching:
  - First check of the day: immediate API calls to both sources.
  - Re-check after 1 hour: fresh API calls.
  - Within 1 hour: return cached result, no API calls.
  - Rate limiting: 0.5s delay between API calls (Finnhub allows 60/min).

Material news detection:
  - has_material_news = True if any 8-K filing in the last 7 days,
    or any S-1, 424B, or reverse-split filing in the last 30 days.

Returns a dict per ticker with: ticker, edgar_filings, finnhub_news,
has_material_news, checked_at, errors.
"""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz

logger = logging.getLogger("agent.news_detective")

_PERU_TZ = pytz.timezone("America/Lima")

# SEC EDGAR requires a descriptive User-Agent header
_EDGAR_USER_AGENT = "RidingHigh Pro research amihay.levy@gmail.com"

# Filing types we care about
_MATERIAL_FORM_TYPES = {"8-K", "8-K/A"}
_NOTABLE_FORM_TYPES = {"S-1", "S-1/A", "424B1", "424B2", "424B3", "424B4", "424B5"}

_CACHE_TTL_SECONDS = 3600  # 1 hour
_RATE_LIMIT_DELAY = 0.5    # seconds between API calls

# Module-level cache for ticker→CIK mapping (loaded once per process)
_ticker_to_cik: Optional[Dict[str, str]] = None


def _get_cik(ticker: str) -> Optional[str]:
    """Look up CIK for a ticker via SEC company_tickers.json (cached in-memory).

    Returns 10-digit zero-padded CIK string, or None if not found.
    """
    global _ticker_to_cik
    if _ticker_to_cik is None:
        url = "https://www.sec.gov/files/company_tickers.json"
        req = urllib.request.Request(url, headers={"User-Agent": _EDGAR_USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read())
        _ticker_to_cik = {}
        for entry in raw.values():
            tk = str(entry.get("ticker", "")).upper()
            cik = str(entry.get("cik_str", "")).zfill(10)
            _ticker_to_cik[tk] = cik
        logger.info("Loaded %d ticker→CIK mappings from SEC", len(_ticker_to_cik))

    return _ticker_to_cik.get(ticker.upper())


def _fetch_edgar_filings(ticker: str) -> List[Dict[str, str]]:
    """Fetch recent SEC EDGAR filings via the submissions API.

    Uses ticker→CIK mapping, then fetches filings.recent arrays.
    Filters to 8-K, S-1, 424B forms filed in the last 30 days.
    Returns list of dicts with keys: form_type, filed_date, sorted newest first.
    """
    cik = _get_cik(ticker)
    if not cik:
        raise ValueError(f"CIK not found for {ticker}")

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    req = urllib.request.Request(url, headers={"User-Agent": _EDGAR_USER_AGENT})

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])

    cutoff = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    filings = []
    for i, form in enumerate(forms):
        if i >= len(dates):
            break
        if dates[i] < cutoff:
            continue
        if form.startswith(("8-K", "S-1", "424B")):
            filings.append({
                "form_type": form,
                "filed_date": dates[i],
            })
        if len(filings) >= 20:
            break

    # Sort newest first
    filings.sort(key=lambda f: f["filed_date"], reverse=True)
    return filings


def _fetch_finnhub_news(ticker: str) -> List[Dict[str, Any]]:
    """Fetch recent company news from Finnhub.

    Requires FINNHUB_API_KEY environment variable.
    Returns list of dicts with keys: headline, date, source, sentiment.
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY not set")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    url = (
        f"https://finnhub.io/api/v1/company-news"
        f"?symbol={ticker}&from={week_ago}&to={today}&token={api_key}"
    )
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")

    with urllib.request.urlopen(req, timeout=10) as resp:
        articles = json.loads(resp.read())

    news = []
    for article in articles[:15]:
        news.append({
            "headline": article.get("headline", ""),
            "date": datetime.fromtimestamp(
                article.get("datetime", 0), tz=pytz.utc
            ).strftime("%Y-%m-%d %H:%M") if article.get("datetime") else "?",
            "source": article.get("source", ""),
            "sentiment": article.get("sentiment", None),
        })
    return news


def _has_material_news(edgar_filings: List[Dict], finnhub_news: List[Dict]) -> bool:
    """Determine if there's material news that could affect a trading decision.

    Returns True if:
      - Any 8-K filing in the last 7 days
      - Any S-1, 424B filing in the last 30 days (already filtered by fetch)
    """
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    for filing in edgar_filings:
        form = filing.get("form_type", "")
        filed = filing.get("filed_date", "")
        if form.startswith("8-K") and filed >= week_ago:
            return True
        if form.startswith(("S-1", "424B")):
            return True

    return False


class NewsDetectiveAgent:
    """Checks SEC EDGAR and Finnhub for material news on signal tickers."""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # ticker -> (check_timestamp, result_dict)

    def check_ticker(self, ticker: str) -> Dict[str, Any]:
        """Check a ticker for material news. Uses per-ticker cache (1h TTL).

        Returns dict with keys: ticker, edgar_filings, finnhub_news,
        has_material_news, checked_at, from_cache, errors.
        """
        ticker = ticker.upper().strip()
        now = datetime.now(_PERU_TZ)

        # Check cache
        cached = self._cache.get(ticker)
        if cached:
            cached_ts, cached_result = cached
            age_seconds = (now - cached_ts).total_seconds()
            if age_seconds < _CACHE_TTL_SECONDS:
                result = dict(cached_result)
                result["from_cache"] = True
                logger.info("Cache hit for %s (age=%ds)", ticker, int(age_seconds))
                return result

        # Cache miss — fetch from both sources
        errors = []
        edgar_filings = []
        finnhub_news = []

        # SEC EDGAR
        try:
            edgar_filings = _fetch_edgar_filings(ticker)
        except Exception as e:
            logger.warning("EDGAR fetch failed for %s: %s", ticker, e)
            errors.append(f"EDGAR: {e}")

        # Rate limit delay
        time.sleep(_RATE_LIMIT_DELAY)

        # Finnhub
        try:
            finnhub_news = _fetch_finnhub_news(ticker)
        except Exception as e:
            logger.warning("Finnhub fetch failed for %s: %s", ticker, e)
            errors.append(f"Finnhub: {e}")

        material = _has_material_news(edgar_filings, finnhub_news)

        result = {
            "ticker": ticker,
            "edgar_filings": edgar_filings,
            "finnhub_news": finnhub_news,
            "has_material_news": material,
            "checked_at": now.isoformat(),
            "from_cache": False,
            "errors": errors,
        }

        # Store in cache
        self._cache[ticker] = (now, result)
        logger.info("Fetched news for %s: %d filings, %d articles, material=%s",
                     ticker, len(edgar_filings), len(finnhub_news), material)

        return result
