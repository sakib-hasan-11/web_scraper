"""
JSON-LD Schema.org extractor.

Parses embedded JSON-LD blocks and extracts structured data for:
- Organization
- LocalBusiness
- Person
- PostalAddress
- OpeningHoursSpecification
- Telephone, Email
"""

import json
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Schema types that contain useful business information
_USEFUL_TYPES = {
    "organization",
    "localbusiness",
    "person",
    "corporation",
    "professionalservice",
    "medicalorganization",
    "restaurant",
    "hotel",
    "store",
}


def _parse_json_ld_blocks(soup: BeautifulSoup) -> list[dict]:
    """Extract and parse all JSON-LD script blocks from a page."""
    blocks: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                blocks.append(data)
            elif isinstance(data, list):
                blocks.extend([d for d in data if isinstance(d, dict)])
        except (json.JSONDecodeError, TypeError) as exc:
            logger.debug("Failed to parse JSON-LD block: %s", exc)
    return blocks


def _extract_from_block(block: dict) -> dict:
    """Extract relevant fields from a single schema.org object."""
    schema_type = str(block.get("@type", "")).lower()

    result: dict = {
        "schema_type": block.get("@type", ""),
        "name": block.get("name", ""),
        "description": block.get("description", ""),
        "url": block.get("url", ""),
        "telephone": block.get("telephone", ""),
        "email": block.get("email", ""),
        "logo": "",
        "address": {},
        "opening_hours": [],
    }

    # Logo
    logo = block.get("logo")
    if isinstance(logo, str):
        result["logo"] = logo
    elif isinstance(logo, dict):
        result["logo"] = logo.get("url", "")

    # Address
    address = block.get("address")
    if isinstance(address, dict):
        result["address"] = {
            "street": address.get("streetAddress", ""),
            "city": address.get("addressLocality", ""),
            "region": address.get("addressRegion", ""),
            "postal_code": address.get("postalCode", ""),
            "country": address.get("addressCountry", ""),
        }

    # Opening hours
    hours = block.get("openingHoursSpecification", [])
    if isinstance(hours, dict):
        hours = [hours]
    if isinstance(hours, list):
        result["opening_hours"] = [
            {
                "day": h.get("dayOfWeek", ""),
                "opens": h.get("opens", ""),
                "closes": h.get("closes", ""),
            }
            for h in hours
            if isinstance(h, dict)
        ]

    return result


def extract_schema(html: str, soup: BeautifulSoup, url: str) -> list[dict]:
    """
    Extract all useful schema.org entities from a page.

    Args:
        html: Raw HTML string (unused, kept for consistent extractor signature).
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        List of extracted schema dictionaries. May be empty.
    """
    blocks = _parse_json_ld_blocks(soup)
    results: list[dict] = []

    for block in blocks:
        schema_type = str(block.get("@type", "")).lower()
        if schema_type in _USEFUL_TYPES:
            extracted = _extract_from_block(block)
            results.append(extracted)
            logger.debug(
                "Extracted JSON-LD '%s' from %s: name=%s",
                block.get("@type"), url, extracted.get("name"),
            )

    return results
