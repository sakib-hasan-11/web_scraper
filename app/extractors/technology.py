"""
Technology stack extractor.

Detects CMS, analytics tools, chat widgets, booking tools, and
payment processors by scanning raw HTML for known signatures.

All signatures are defined in app/constants/keywords.py to keep
detection logic separate from configuration.
"""

import logging
from bs4 import BeautifulSoup

from app.constants.keywords import TECH_SIGNATURES

logger = logging.getLogger(__name__)

# Map category name → response field name
_CATEGORY_MAP = {
    "cms": "cms",
    "analytics": "analytics",
    "widgets": "widgets",
    "booking": "booking",
}


def extract_technology(html: str, soup: BeautifulSoup, url: str) -> dict:
    """
    Detect technologies used on a page via HTML signature matching.

    Args:
        html: Raw HTML string (signatures are searched here).
        soup: Parsed BeautifulSoup object (unused, kept for consistent signature).
        url: Source URL (used for logging context).

    Returns:
        Dictionary with keys: cms (str), analytics (list), widgets (list), booking (list).
    """
    result: dict = {
        "cms": "",
        "analytics": [],
        "widgets": [],
        "booking": [],
    }
    html_lower = html.lower()

    for tech_name, category, signatures in TECH_SIGNATURES:
        if any(sig.lower() in html_lower for sig in signatures):
            field = _CATEGORY_MAP.get(category)
            if not field:
                continue

            if field == "cms":
                if not result["cms"]:  # First CMS wins
                    result["cms"] = tech_name
                    logger.debug("Detected CMS '%s' on %s", tech_name, url)
            else:
                if tech_name not in result[field]:
                    result[field].append(tech_name)
                    logger.debug("Detected %s '%s' on %s", category, tech_name, url)

    return result
