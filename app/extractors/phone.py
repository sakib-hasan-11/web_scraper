"""
Phone number extractor.

Extracts phone numbers from:
- tel: links
- Visible text (regex scan)

Normalises to E.164 format where possible.
Deduplicates results.
"""

import re
import logging
from bs4 import BeautifulSoup
import phonenumbers
from phonenumbers import PhoneNumberMatcher, PhoneNumberFormat

logger = logging.getLogger(__name__)

# Fallback regex for tel: links that phonenumbers may not parse directly
_TEL_RE = re.compile(r"tel:([\d\s\+\-\(\)\.]+)")


def _normalize_phone(number_str: str, region: str = "US") -> str | None:
    """
    Parse and normalise a phone number string to E.164.

    Args:
        number_str: Raw phone number string.
        region: Default region hint for parsing.

    Returns:
        E.164 formatted string, or None if unparseable.
    """
    try:
        parsed = phonenumbers.parse(number_str, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return None


def extract_phones(html: str, soup: BeautifulSoup, url: str) -> list[str]:
    """
    Extract and normalise unique phone numbers from a page.

    Args:
        html: Raw HTML string.
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Sorted list of unique E.164 phone numbers.
    """
    candidates: set[str] = set()

    # 1. tel: links
    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        if href.lower().startswith("tel:"):
            raw = href[4:].strip()
            normalised = _normalize_phone(raw)
            if normalised:
                candidates.add(normalised)

    # 2. PhoneNumberMatcher across visible text
    text = soup.get_text(separator=" ")
    for match in PhoneNumberMatcher(text, "US"):
        normalised = phonenumbers.format_number(match.number, PhoneNumberFormat.E164)
        candidates.add(normalised)

    if candidates:
        logger.debug("Found %d phone(s) on %s", len(candidates), url)

    return sorted(candidates)
