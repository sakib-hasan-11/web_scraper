"""
Page selector — extracts internal links from HTML and filters them to only
keep pages that are likely to contain useful business information.

Does NOT crawl. Does NOT extract data. Only selects URLs.
"""

import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.constants.keywords import IMPORTANT_SLUGS, IGNORE_SLUGS

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


def _url_contains_important_slug(url: str) -> bool:
    """Return True if any important slug appears in the URL path."""
    path = urlparse(url).path.lower()
    segments = path.strip("/").split("/")
    for segment in segments:
        for slug in IMPORTANT_SLUGS:
            if slug in segment:
                return True
    return False


def _url_contains_ignored_slug(url: str) -> bool:
    """Return True if any ignore slug appears in the URL path."""
    path = urlparse(url).path.lower()
    segments = path.strip("/").split("/")
    for segment in segments:
        for slug in IGNORE_SLUGS:
            if slug in segment:
                return True
    return False


def filter_important_pages(urls: list[str], max_pages: int = 10) -> list[str]:
    """
    Filter a list of internal URLs to keep only the most relevant pages.

    Priority: important slugs first, ignored slugs discarded, capped at max_pages.

    Args:
        urls: List of internal absolute URLs.
        max_pages: Maximum number of pages to return.

    Returns:
        Filtered, deduplicated list of important page URLs.
    """
    important: list[str] = []

    for url in urls:
        if _url_contains_ignored_slug(url):
            continue
        if _url_contains_important_slug(url):
            important.append(url)

    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for url in important:
        if url not in seen:
            seen.add(url)
            result.append(url)

    logger.info("Selected %d important pages (max %d)", len(result[:max_pages]), max_pages)
    return result[:max_pages]
