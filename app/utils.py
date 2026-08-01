"""
URL validation and normalisation utilities.
"""

import re
import logging
from urllib.parse import urlparse, urlunparse

import tldextract

logger = logging.getLogger(__name__)

# Reject anything that looks like a bare IP address
_IP_RE = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"
)


def normalize_url(url: str) -> str:
    """
    Normalize a raw URL string into a canonical HTTPS URL.

    - Strips whitespace
    - Adds https:// scheme if missing
    - Lowercases the netloc
    - Removes trailing slashes from path

    Args:
        url: Raw URL string from the user.

    Returns:
        Normalized URL string.
    """
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    # Upgrade http → https
    scheme = "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""

    return urlunparse((scheme, netloc, path, "", "", ""))


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate that a URL is safe to crawl.

    Rejects:
    - localhost / loopback addresses
    - Bare IP addresses
    - URLs with no recognisable registered domain

    Args:
        url: Normalized URL string.

    Returns:
        (is_valid, error_message) — error_message is empty when valid.
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""

    # Reject localhost
    if host in ("localhost", "127.0.0.1", "::1"):
        return False, f"Localhost URLs are not allowed: {host}"

    # Reject bare IP addresses
    if _IP_RE.match(host):
        return False, f"IP address URLs are not allowed: {host}"

    # Require a registered domain
    ext = tldextract.extract(url)
    if not ext.domain or not ext.suffix:
        return False, f"Could not extract a valid domain from URL: {url}"

    return True, ""
