"""
Services extractor.

Attempts to extract service names, product names, and solution offerings
from headings and list items on services/solutions pages.

Strategy:
- Prioritise content inside sections with relevant IDs/classes.
- Collect H2, H3 headings and <li> items that look like service names.
- Skip generic navigation labels.
"""

import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Sections likely to contain service listings
_SERVICE_SECTION_RE = re.compile(
    r"service|solution|product|offering|what-we-do|capabilities", re.IGNORECASE
)

# Navigation containers to ignore
_NAV_TAGS = {"nav", "header", "footer"}

# Skip generic phrases that are not service names
_SKIP_PHRASES = {
    "home", "about", "contact", "blog", "login", "get started",
    "learn more", "read more", "click here", "sign up", "sign in",
    "menu", "close", "open", "search", "back",
}


def _is_nav_child(tag) -> bool:
    """Return True if tag is inside a nav/header/footer."""
    for parent in tag.parents:
        if parent.name in _NAV_TAGS:
            return True
    return False


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_services(html: str, soup: BeautifulSoup, url: str) -> list[str]:
    """
    Extract service/product names from a page.

    Args:
        html: Raw HTML string (unused, kept for consistent extractor signature).
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Deduplicated list of service name strings.
    """
    services: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        cleaned = _clean_text(text)
        lower = cleaned.lower()
        if (
            cleaned
            and 3 < len(cleaned) < 100
            and lower not in _SKIP_PHRASES
            and cleaned not in seen
        ):
            seen.add(cleaned)
            services.append(cleaned)

    # 1. Look inside service-related sections first
    priority_tags = (
        soup.find_all(id=_SERVICE_SECTION_RE) +
        soup.find_all(class_=_SERVICE_SECTION_RE)
    )

    for section in priority_tags:
        for heading in section.find_all(["h2", "h3", "h4"]):
            if not _is_nav_child(heading):
                add(heading.get_text())
        for li in section.find_all("li"):
            if not _is_nav_child(li) and not li.find(["ul", "li"]):
                add(li.get_text())

    # 2. Fall back to all h2/h3 if nothing found yet
    if not services:
        for heading in soup.find_all(["h2", "h3"]):
            if not _is_nav_child(heading):
                add(heading.get_text())

    if services:
        logger.debug("Extracted %d service(s) from %s", len(services), url)

    return services
