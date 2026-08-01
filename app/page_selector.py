"""
Page selector — extracts internal links from HTML and filters them to only
keep pages that are likely to contain useful business information.

Does NOT crawl. Does NOT extract data. Only selects URLs.

Uses intelligent page ranking instead of simple keyword matching.
"""

import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.page_ranker import rank_pages

logger = logging.getLogger(__name__)


def extract_internal_links(html: str, base_url: str) -> list[str]:
    """
    Parse HTML and return all unique internal links.

    Ignores: mailto, tel, javascript, anchors (#), and external domains.

    Args:
        html: Raw HTML of the page.
        base_url: The base URL of the site (used to resolve relative links).

    Returns:
        Sorted list of unique internal absolute URLs.
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc.lower()
    seen: set[str] = set()
    links: list[str] = []

    for tag in soup.find_all("a", href=True):
        href: str = tag["href"].strip()

        # Skip protocol-specific non-HTTP links
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue

        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)

        # Only keep http(s) links
        if parsed.scheme not in ("http", "https"):
            continue

        # Only keep internal links (same domain, ignoring www prefix)
        link_domain = parsed.netloc.lower().lstrip("www.")
        site_domain = base_domain.lstrip("www.")
        if link_domain != site_domain:
            continue

        # Normalise: drop fragment and query string, strip trailing slash
        clean = parsed._replace(fragment="", query="").geturl().rstrip("/")

        if clean not in seen and clean != base_url.rstrip("/"):
            seen.add(clean)
            links.append(clean)

    return sorted(links)


def filter_important_pages(urls: list[str], max_pages: int = 10) -> list[str]:
    """
    Filter and rank internal URLs by business importance.

    Uses intelligent page ranking based on URL patterns.
    Only returns pages with positive scores.

    Args:
        urls: List of internal absolute URLs.
        max_pages: Maximum number of pages to return.

    Returns:
        Ranked list of important page URLs (at most max_pages).
    """
    if not urls:
        logger.info("No URLs to filter")
        return []

    # Use intelligent page ranking
    ranked_urls = rank_pages(urls, max_pages=max_pages)

    logger.info(
        "Selected %d important pages (from %d total, max %d)",
        len(ranked_urls), len(urls), max_pages
    )
    return ranked_urls
