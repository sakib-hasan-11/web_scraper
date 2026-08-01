"""
Email extractor.

Extracts email addresses from:
- Visible text (regex scan)
- mailto: links

Validates addresses using email-validator.
Deduplicates results.
"""

import re
import logging
from email_validator import validate_email, EmailNotValidError
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Broad pattern to find candidate email strings
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)


def _is_valid_email(address: str) -> bool:
    """Return True if the address passes email-validator checks."""
    try:
        validate_email(address, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def extract_emails(html: str, soup: BeautifulSoup, url: str) -> list[str]:
    """
    Extract and validate unique email addresses from a page.

    Args:
        html: Raw HTML string.
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Sorted list of unique, validated email addresses.
    """
    candidates: set[str] = set()

    # 1. mailto links
    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        if href.lower().startswith("mailto:"):
            address = href[7:].split("?")[0].strip()
            if address:
                candidates.add(address.lower())

    # 2. Visible text regex scan
    for match in _EMAIL_RE.finditer(html):
        candidates.add(match.group(0).lower())

    # Validate
    valid = [e for e in candidates if _is_valid_email(e)]

    if valid:
        logger.debug("Found %d email(s) on %s", len(valid), url)

    return sorted(valid)
