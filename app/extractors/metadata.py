"""
Metadata extractor.

Extracts SEO and Open Graph metadata from the page <head>:
- <title>
- <meta name="description">
- <html lang="...">
- First <h1>
- Open Graph tags (og:title, og:description, og:image)
- Twitter Card tags
- Canonical URL
"""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _meta_content(soup: BeautifulSoup, name: str) -> str:
    """Return content of a <meta name="..."> or <meta property="..."> tag."""
    tag = soup.find("meta", attrs={"name": name}) or soup.find(
        "meta", attrs={"property": name}
    )
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def extract_metadata(html: str, soup: BeautifulSoup, url: str) -> dict:
    """
    Extract page metadata from HTML head.

    Args:
        html: Raw HTML string (unused, kept for consistent extractor signature).
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Dictionary with keys: title, description, language, h1, h2s,
        og_title, og_description, og_image, canonical, twitter_title,
        twitter_description.
    """
    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Language
    html_tag = soup.find("html")
    language = ""
    if html_tag:
        language = html_tag.get("lang", "").strip()

    # H1
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else ""

    # H2s (collect up to 10)
    h2s = [tag.get_text(strip=True) for tag in soup.find_all("h2")][:10]

    # Canonical
    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    return {
        "title": title,
        "description": _meta_content(soup, "description"),
        "language": language,
        "h1": h1,
        "h2s": h2s,
        "og_title": _meta_content(soup, "og:title"),
        "og_description": _meta_content(soup, "og:description"),
        "og_image": _meta_content(soup, "og:image"),
        "canonical": canonical,
        "twitter_title": _meta_content(soup, "twitter:title"),
        "twitter_description": _meta_content(soup, "twitter:description"),
    }
