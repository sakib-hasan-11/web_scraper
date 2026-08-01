"""
Company information extractor.

Attempts to extract:
- Company name (from og:site_name, title, or prominent heading)
- Tagline (short hero text or meta description)
- Mission / About paragraph (longer descriptive text block)

This is heuristic-based, not LLM-based.
"""

import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Sections likely to contain "about" content
_ABOUT_SECTION_IDS = re.compile(
    r"about|mission|vision|story|who-we-are|company", re.IGNORECASE
)


def _get_og_site_name(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", property="og:site_name")
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def _get_title_based_name(soup: BeautifulSoup) -> str:
    """Try to infer company name from <title> tag (text before separator)."""
    title_tag = soup.find("title")
    if not title_tag:
        return ""
    title = title_tag.get_text(strip=True)
    # Title often: "Company Name | Tagline" or "Company Name - Page"
    for sep in ("|", "–", "—", "-"):
        if sep in title:
            return title.split(sep)[0].strip()
    return title.strip()


def _find_about_paragraph(soup: BeautifulSoup) -> str:
    """
    Look for a descriptive paragraph inside about/mission sections.

    Heuristic: find elements with about-related IDs/classes, take first <p>.
    """
    for tag in soup.find_all(id=_ABOUT_SECTION_IDS):
        p = tag.find("p")
        if p:
            text = p.get_text(strip=True)
            if len(text) > 40:
                return text

    for tag in soup.find_all(class_=_ABOUT_SECTION_IDS):
        p = tag.find("p")
        if p:
            text = p.get_text(strip=True)
            if len(text) > 40:
                return text

    return ""


def extract_company_info(html: str, soup: BeautifulSoup, url: str) -> dict:
    """
    Extract company name, tagline, and description from a page.

    Args:
        html: Raw HTML string (unused, kept for consistent extractor signature).
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Dictionary with keys: name, tagline, description.
    """
    name = _get_og_site_name(soup) or _get_title_based_name(soup)

    # Tagline: og:description or meta description (short)
    og_desc_tag = soup.find("meta", property="og:description")
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})

    tagline = ""
    if og_desc_tag and og_desc_tag.get("content"):
        tagline = og_desc_tag["content"].strip()
    elif meta_desc_tag and meta_desc_tag.get("content"):
        tagline = meta_desc_tag["content"].strip()

    description = _find_about_paragraph(soup)

    return {
        "name": name,
        "tagline": tagline,
        "description": description,
    }
