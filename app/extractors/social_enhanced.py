"""
Enhanced social link extraction.

Improves social link detection with better patterns.
Validates social URLs.
Tracks confidence scores.
"""

import logging
import re
from urllib.parse import urlparse

from app.confidence_engine import (
    ExtractionSource,
    ConfidenceScore,
    score_url,
)

logger = logging.getLogger(__name__)


# Social platform URL patterns
SOCIAL_PATTERNS = {
    "linkedin": [
        r"linkedin\.com/(?:company|in)/[\w-]+",
        r"linkedin\.com/.*",
    ],
    "facebook": [
        r"facebook\.com/[\w./-]+",
        r"fb\.(?:me|com)/[\w-]+",
    ],
    "twitter": [
        r"(?:twitter|x)\.com/[\w]+",
        r"x\.com/[\w]+",
    ],
    "instagram": [
        r"instagram\.com/[\w.]+",
    ],
    "youtube": [
        r"youtube\.com/(?:user|channel|c)/[\w-]+",
        r"youtube\.com/@[\w-]+",
        r"youtu\.be/[\w-]+",
    ],
    "tiktok": [
        r"tiktok\.com/@[\w.-]+",
    ],
    "github": [
        r"github\.com/[\w-]+",
    ],
    "whatsapp": [
        r"wa\.me/[\d]+",
        r"whatsapp\.com/.*",
    ],
    "telegram": [
        r"t\.me/[\w]+",
        r"telegram\.me/[\w]+",
    ],
    "discord": [
        r"discord\.(?:gg|com)/[\w-]+",
    ],
    "reddit": [
        r"reddit\.com/r/[\w-]+",
        r"reddit\.com/u/[\w-]+",
    ],
}


def extract_social_links_enhanced(html: str, soup) -> dict[str, ConfidenceScore]:
    """
    Extract social media links with validation.

    Args:
        html: Full HTML content
        soup: BeautifulSoup object

    Returns:
        Dictionary {platform: ConfidenceScore}
    """
    found_links = {}

    # 1. Extract from anchor tags (highest confidence)
    links = soup.find_all("a", href=True)
    for link in links:
        href = link.get("href", "").lower()
        if not href:
            continue

        # Try to match against patterns
        for platform, patterns in SOCIAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    # Found a match
                    if platform not in found_links:
                        score = score_url(href, ExtractionSource.VISIBLE)
                        found_links[platform] = score
                    break

    # 2. Look in footer (often has social links)
    footer = soup.find("footer")
    if footer:
        footer_links = footer.find_all("a", href=True)
        for link in footer_links:
            href = link.get("href", "").lower()
            if not href:
                continue

            for platform, patterns in SOCIAL_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        if platform not in found_links:
                            score = score_url(href, ExtractionSource.FOOTER)
                            found_links[platform] = score
                        break

    # 3. Look in header/nav
    nav = soup.find(re.compile(r"header|nav"))
    if nav:
        nav_links = nav.find_all("a", href=True)
        for link in nav_links:
            href = link.get("href", "").lower()
            if not href:
                continue

            for platform, patterns in SOCIAL_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        if platform not in found_links:
                            score = score_url(href, ExtractionSource.VISIBLE)
                            found_links[platform] = score
                        break

    # 4. Regex patterns in href attribute
    href_pattern = r'href=["\']([^"\']+)["\']'
    for match in re.finditer(href_pattern, html):
        href = match.group(1).lower()

        for platform, patterns in SOCIAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, href, re.IGNORECASE):
                    if platform not in found_links:
                        score = score_url(href, ExtractionSource.REGEX)
                        found_links[platform] = score
                    break

    return found_links


def validate_social_url(url: str, platform: str) -> bool:
    """
    Validate social media URL for specific platform.

    Args:
        url: URL to validate
        platform: Platform name

    Returns:
        True if valid
    """
    if not url or not url.startswith(("http://", "https://", "//")):
        return False

    url_lower = url.lower()

    # Check platform patterns
    if platform in SOCIAL_PATTERNS:
        patterns = SOCIAL_PATTERNS[platform]
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return True

    return False


def normalize_social_url(url: str, platform: str) -> str:
    """
    Normalize social media URL to standard format.

    Args:
        url: Raw URL
        platform: Platform name

    Returns:
        Normalized URL
    """
    if not url.startswith(("http://", "https://")):
        # Add protocol if missing
        url = "https://" + url.lstrip("//")

    # Ensure proper format
    if platform == "twitter":
        # Normalize twitter.com and x.com to x.com
        if "twitter.com" in url:
            url = url.replace("twitter.com", "x.com")
    elif platform == "whatsapp":
        # Normalize WhatsApp URLs
        if "wa.me" in url and not url.startswith("https://wa.me"):
            url = "https://wa.me" + url.split("wa.me")[1]

    return url


def merge_social_links(
    current: dict[str, str],
    new: dict[str, ConfidenceScore],
) -> dict[str, str]:
    """
    Merge social links, keeping highest confidence.

    Args:
        current: Previously found links {platform: url}
        new: Newly found links {platform: ConfidenceScore}

    Returns:
        Merged links {platform: url}
    """
    merged = current.copy()

    for platform, score in new.items():
        if platform not in merged:
            # Check if valid before adding
            if validate_social_url(score.value, platform):
                merged[platform] = normalize_social_url(score.value, platform)

    return merged
