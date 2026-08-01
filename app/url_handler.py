"""
Enhanced URL normalization and handling.

Responsibilities:
  - Normalize URLs (remove UTM params, tracking, fragments)
  - Extract root domain
  - Validate domain consistency
  - URL comparison and deduplication
"""

import logging
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from typing import Optional

logger = logging.getLogger(__name__)


# Common tracking and UTM parameters to remove
TRACKING_PARAMS = {
    # UTM params
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    # Facebook
    "fbclid",
    # Google Ads
    "gclid",
    "gclsrc",
    # Generic tracking
    "ref",
    "source",
    "campaign",
    "medium",
    "content",
}


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent comparison and crawling.

    Removes:
    - Fragments (#)
    - UTM and tracking parameters
    - Query strings if not essential

    Ensures:
    - http/https scheme
    - Lowercase domain
    - No trailing slash

    Args:
        url: Raw URL string

    Returns:
        Normalized URL
    """
    if not url:
        return ""

    url = url.strip()

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
    except Exception as exc:
        logger.warning("Failed to parse URL: %s — %s", url, exc)
        return url

    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Extract path and query
    path = parsed.path.rstrip("/")
    query_string = parsed.query

    # Filter tracking parameters
    if query_string:
        params = parse_qs(query_string, keep_blank_values=False)
        filtered_params = {
            k: v for k, v in params.items()
            if k.lower() not in TRACKING_PARAMS
        }

        # Reconstruct query string
        if filtered_params:
            # Flatten single-value lists
            flat_params = {k: v[0] if len(v) == 1 else v for k, v in filtered_params.items()}
            query_string = urlencode(flat_params, doseq=True)
        else:
            query_string = ""

    # Remove fragment entirely
    fragment = ""

    # Reconstruct URL
    normalized = urlunparse((scheme, netloc, path, "", query_string, fragment))

    # Remove trailing slash for consistency
    if normalized.endswith("/") and not normalized.endswith("://"):
        normalized = normalized.rstrip("/")

    return normalized


def extract_root_domain(url: str) -> str:
    """
    Extract root domain from URL.

    Examples:
        https://example.com/path -> https://example.com
        https://www.example.com/about -> https://example.com
        https://subdomain.example.com -> https://subdomain.example.com

    Args:
        url: Normalized URL

    Returns:
        Root domain URL
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()

        # Remove www prefix only if main domain
        if netloc.startswith("www."):
            netloc_without_www = netloc[4:]
            # Only remove www if it's at the main level (not a real subdomain)
            if netloc_without_www.count(".") >= 1:
                netloc = netloc_without_www

        return f"{scheme}://{netloc}"
    except Exception as exc:
        logger.warning("Failed to extract root domain from %s: %s", url, exc)
        return url


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same domain.

    Ignores www prefix.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if same domain, False otherwise
    """
    try:
        domain1 = extract_root_domain(url1)
        domain2 = extract_root_domain(url2)
        return domain1 == domain2
    except Exception as exc:
        logger.warning("Failed to compare domains: %s", exc)
        return False


def get_domain_name(url: str) -> str:
    """
    Extract domain name (netloc) from URL.

    Examples:
        https://example.com -> example.com
        https://www.example.com -> www.example.com

    Args:
        url: URL string

    Returns:
        Domain name (netloc)
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def url_path_depth(url: str) -> int:
    """
    Get the path depth of a URL.

    Examples:
        https://example.com -> 0
        https://example.com/ -> 0
        https://example.com/about -> 1
        https://example.com/about/team -> 2

    Args:
        url: URL string

    Returns:
        Path depth (number of segments)
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            return 0
        return len(path.split("/"))
    except Exception:
        return 0


def deduplicate_urls(urls: list[str]) -> list[str]:
    """
    Remove duplicate URLs while preserving order.

    Args:
        urls: List of URLs

    Returns:
        Deduplicated list in original order
    """
    seen = set()
    result = []
    for url in urls:
        normalized = normalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            result.append(url)
    return result
