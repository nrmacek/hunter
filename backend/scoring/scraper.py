"""
Phase 7 scraper — collects qualitative text signals for AI scoring.

Strategy:
- Guess and fetch the firm's own website directly (most reliable source)
- DDG Lite searches with retry/backoff for supplemental signals
- Revenue and headcount data comes from the DB (already in firms table),
  not from scraping — those are passed as known_data to the AI scorer
"""

import time
import random
import logging
import re
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://duckduckgo.com/",
}

TIMEOUT = 12


def _get(url: str) -> str | None:
    """Fetch a URL via GET and return page text, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        logger.debug(f"GET failed for {url}: {e}")
    return None


def _ddg_search(query: str, retries: int = 2) -> str:
    """
    DuckDuckGo Lite search with retry on rate limit (202 response).
    Returns concatenated result snippets, or empty string.
    """
    for attempt in range(retries + 1):
        if attempt > 0:
            wait = 8 + attempt * 5
            logger.debug(f"DDG rate limited, waiting {wait}s before retry {attempt}")
            time.sleep(wait)

        try:
            session = requests.Session()
            # First hit the homepage to get cookies
            session.get("https://duckduckgo.com/", headers=HEADERS, timeout=TIMEOUT)
            time.sleep(1.5)

            resp = session.post(
                "https://lite.duckduckgo.com/lite/",
                data={"q": query},
                headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
                timeout=TIMEOUT,
            )
        except Exception as e:
            logger.debug(f"DDG request failed: {e}")
            continue

        if resp.status_code == 202:
            logger.debug(f"DDG returned 202 (rate limit) for: {query[:60]}")
            continue

        if resp.status_code != 200:
            logger.debug(f"DDG returned {resp.status_code} for: {query[:60]}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = []

        for td in soup.find_all("td", class_="result-snippet"):
            text = td.get_text(separator=" ", strip=True)
            if text:
                snippets.append(text)

        for a in soup.find_all("a", class_="result-link"):
            text = a.get_text(strip=True)
            if text and len(text) > 15:
                snippets.append(text)

        if snippets:
            return "\n".join(snippets[:25])

    return ""


def _guess_website_urls(firm_name: str) -> list[str]:
    """
    Generate likely domain candidates for a firm.
    e.g. "Gresham Smith" → greshamsmith.com, gresham-smith.com, etc.
    """
    # Normalize: lowercase, remove common legal suffixes
    name = firm_name.lower()
    for suffix in [" + ", " & ", " and ", ", inc", ", llc", ", ltd", ", pc",
                   " architects", " architecture", " engineering", " group",
                   " partners", " associates", " design", " studio", " consultants"]:
        name = name.replace(suffix, " ")

    words = re.findall(r"[a-z0-9]+", name)
    if not words:
        return []

    joined = "".join(words)
    hyphenated = "-".join(words)
    first_two = "".join(words[:2]) if len(words) >= 2 else joined
    first = words[0]

    candidates = [
        f"https://www.{joined}.com",
        f"https://{joined}.com",
        f"https://www.{hyphenated}.com",
        f"https://{hyphenated}.com",
        f"https://www.{first_two}.com",
        f"https://{first_two}.com",
        f"https://www.{first}andpartners.com",
    ]
    # Deduplicate
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def _fetch_firm_pages(base_url: str) -> str:
    """
    Fetch homepage + key subpages from the firm's website.
    Returns combined extracted text, capped to control token usage.
    """
    base = base_url.rstrip("/")
    pages_to_try = [
        base,
        f"{base}/about",
        f"{base}/about-us",
        f"{base}/services",
        f"{base}/markets",
        f"{base}/sectors",
        f"{base}/locations",
        f"{base}/offices",
    ]

    combined = []
    fetched = 0

    for page_url in pages_to_try:
        if fetched >= 4:
            break
        time.sleep(random.uniform(0.5, 1.0))
        html = _get(page_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if len(text) > 100:  # ignore blank/redirect pages
            combined.append(text[:2500])
            fetched += 1

    return "\n\n---\n\n".join(combined)


def _fetch_news_pages(base_url: str) -> str:
    """
    Fetch /news, /press, /newsroom, or /press-releases from the firm website.
    Returns extracted text capped to 2500 chars, or empty string if none found.
    """
    base = base_url.rstrip("/")
    news_slugs = ["/news", "/press", "/newsroom", "/press-releases",
                  "/news-events", "/media", "/insights"]

    for slug in news_slugs:
        time.sleep(random.uniform(0.4, 0.8))
        html = _get(base + slug)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if len(text) > 200:
            logger.debug(f"  News page found: {base + slug}")
            return text[:2500]

    return ""


def _ddg_news_search(query: str) -> str:
    """
    DDG search targeting press release and news sources for growth signals.
    Uses site-scoped query to hit BusinessWire, PRNewswire, and ENR.
    """
    news_query = (
        f"{query} "
        "(site:businesswire.com OR site:prnewswire.com OR site:enr.com "
        "OR site:architectmagazine.com OR site:bdcnetwork.com)"
    )
    return _ddg_search(news_query)


def _ddg_linkedin_jobs(firm_name: str) -> str:
    """
    Search for LinkedIn job posting signals via DDG.
    Returns snippets indicating hiring volume and active roles.
    """
    return _ddg_search(f'"{firm_name}" site:linkedin.com jobs hiring')


def _find_website_via_ddg(firm_name: str) -> str | None:
    """Try to find the firm's official website URL via DDG search."""
    query = f'"{firm_name}" official website architecture engineering'
    try:
        session = requests.Session()
        session.get("https://duckduckgo.com/", headers=HEADERS, timeout=TIMEOUT)
        time.sleep(1.5)
        resp = session.post(
            "https://lite.duckduckgo.com/lite/",
            data={"q": query},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return None
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    skip_domains = {
        "duckduckgo", "google", "linkedin", "facebook", "instagram", "twitter",
        "glassdoor", "indeed", "wikipedia", "yelp", "bbb", "youtube",
        "bloomberg", "enr", "zoominfo", "dnb", "manta", "craft.co", "comparably",
    }
    for a in soup.find_all("a", class_="result-link"):
        href = a.get("href", "")
        if not href.startswith("http"):
            continue
        try:
            domain = urlparse(href).netloc.lower().replace("www.", "")
            if not any(skip in domain for skip in skip_domains):
                return href
        except Exception:
            continue
    return None


def scrape_firm(firm_name: str, website_url: str | None = None) -> dict:
    """
    Collect qualitative text signals for a firm. Returns a dict with keys:
        overview, growth, industry_services, geography, website_url
    Revenue and employees are NOT scraped here — they come from the DB
    and are passed as known_data to the AI scorer.

    If website_url is provided (from user input), skip guessing/DDG lookup.
    """
    logger.info(f"Scraping: {firm_name}")

    # ── Step 1: Find and fetch the firm's website ──────────────────────────
    website_text = ""

    if website_url:
        # User provided the website — use it directly
        logger.info(f"  Using provided website: {website_url}")
        website_text = _fetch_firm_pages(website_url)
    else:
        # Try guessed URLs first (fast, no rate limit risk)
        for candidate in _guess_website_urls(firm_name):
            time.sleep(0.3)
            html = _get(candidate)
            if html and len(html) > 500:
                website_url = candidate
                logger.info(f"  Website found via guess: {candidate}")
                website_text = _fetch_firm_pages(candidate)
                break

        # Fall back to DDG if guessing failed
        if not website_url:
            time.sleep(2)
            website_url = _find_website_via_ddg(firm_name)
            if website_url:
                logger.info(f"  Website found via DDG: {website_url}")
                website_text = _fetch_firm_pages(website_url)
            else:
                logger.info(f"  No website found for {firm_name}")

    # ── Step 2: Fetch news/press page from website ────────────────────────
    news_text = ""
    if website_url:
        news_text = _fetch_news_pages(website_url)

    # ── Step 3: DDG searches for supplemental signals ─────────────────────
    time.sleep(random.uniform(2.5, 4.0))
    growth_ddg = _ddg_search(
        f'"{firm_name}" architecture engineering growth revenue ENR ranking 2023 2024 expansion'
    )

    time.sleep(random.uniform(3.0, 5.0))
    growth_news = _ddg_news_search(f'"{firm_name}"')

    time.sleep(random.uniform(3.0, 5.0))
    growth_jobs = _ddg_linkedin_jobs(firm_name)

    time.sleep(random.uniform(2.5, 4.0))
    overview = _ddg_search(
        f'"{firm_name}" architecture engineering firm offices locations employees'
    )

    growth_combined = "\n".join(filter(None, [
        growth_ddg,
        news_text,
        growth_news,
        growth_jobs,
    ]))

    return {
        "overview":          overview,
        "growth":            growth_combined,
        "industry_services": website_text,
        "geography":         overview + "\n" + website_text,
        "website_url":       website_url or "",
    }
