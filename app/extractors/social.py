"""
Social media link extractor.

Detects links to known social media platforms by matching hrefs
against a dictionary of known social domains.

Returns one canonical URL per platform (first found wins).
"""

import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from app.constants.keywords import SOCIAL_DOMAINS

logger = logging.getLogger(__name__)


def extract_social_links(html: str, soup: BeautifulSoup, url: str) -> dict[str, str]:
    """
    Detect social media profile URLs on a page.

    Args:
        html: Raw HTML string (unused, kept for consistent extractor signature).
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Dictionary mapping platform name → profile URL.
        Example: {"linkedin": "https://linkedin.com/company/acme"}
    """
    found: dict[str, str] = {}

    for tag in soup.find_all("a", href=True):
        href: str = tag["href"].strip()
        if not href.startswith("http"):
            continue

        parsed = urlparse(href)
        link_domain = parsed.netloc.lower().lstrip("www.")

        for social_domain, platform in SOCIAL_DOMAINS.items():
            if link_domain == social_domain or link_domain.endswith("." + social_domain):
                # Only keep the first occurrence per platform
                if platform not in found:
                    found[platform] = href
                break

    if found:
        logger.debug("Found social links on %s: %s", url, list(found.keys()))

    return found
