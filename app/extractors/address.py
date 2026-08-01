"""
Address extraction module.

Extracts business addresses from pages.
Detects multiple locations.
Validates address format.
"""

import logging
import re
from bs4 import BeautifulSoup

from app.confidence_engine import (
    ExtractionSource,
    ConfidenceScore,
    score_text,
)

logger = logging.getLogger(__name__)


# US state abbreviations
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
}

# Common city/state/zip patterns
US_ADDRESS_PATTERN = r"""
    (\d+\s+[\w\s]+)\s+           # Street number and name
    ((?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way)\b)?\s*  # Optional street type
    ([A-Z]{2})\s+                 # State
    (\d{5})(?:-\d{4})?            # ZIP+4
"""


def extract_addresses(soup: BeautifulSoup, html: str) -> list[ConfidenceScore]:
    """
    Extract business addresses from HTML.

    Args:
        soup: BeautifulSoup object
        html: Full HTML content

    Returns:
        List of ConfidenceScore objects
    """
    scores = []

    # 1. Look for schema.org PostalAddress (highest confidence)
    schema_addresses = _extract_schema_addresses(soup)
    for addr in schema_addresses:
        score = score_text(addr, ExtractionSource.SCHEMA, min_length=10)
        scores.append(score)

    # 2. Look in <address> tags
    address_tags = soup.find_all("address")
    for tag in address_tags:
        addr_text = tag.get_text(separator=" ", strip=True)
        if len(addr_text) >= 10:
            score = score_text(addr_text, ExtractionSource.VISIBLE, min_length=10)
            scores.append(score)

    # 3. Look in footer (common location for addresses)
    footer = soup.find("footer")
    if footer:
        addresses = _find_addresses_in_text(footer.get_text())
        for addr in addresses:
            score = score_text(addr, ExtractionSource.FOOTER, min_length=10)
            scores.append(score)

    # 4. Look for contact sections
    contact_sections = soup.find_all(class_=re.compile(r"contact|address|location", re.I))
    for section in contact_sections:
        addresses = _find_addresses_in_text(section.get_text())
        for addr in addresses:
            score = score_text(addr, ExtractionSource.VISIBLE, min_length=10)
            scores.append(score)

    # 5. Regex pattern matching
    regex_addresses = _find_addresses_in_text(html)
    for addr in regex_addresses:
        score = score_text(addr, ExtractionSource.REGEX, min_length=10)
        scores.append(score)

    # Deduplicate (normalize whitespace)
    seen = set()
    unique_scores = []
    for score in scores:
        normalized = " ".join(score.value.split())
        if normalized not in seen:
            seen.add(normalized)
            unique_scores.append(score)

    return unique_scores


def _extract_schema_addresses(soup: BeautifulSoup) -> list[str]:
    """Extract addresses from JSON-LD schema."""
    addresses = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)

            # Check for PostalAddress
            if isinstance(data, dict):
                if data.get("@type") == "PostalAddress" and "streetAddress" in data:
                    addr_parts = []
                    if data.get("streetAddress"):
                        addr_parts.append(data["streetAddress"])
                    if data.get("addressLocality"):
                        addr_parts.append(data["addressLocality"])
                    if data.get("addressRegion"):
                        addr_parts.append(data["addressRegion"])
                    if data.get("postalCode"):
                        addr_parts.append(data["postalCode"])
                    if addr_parts:
                        addresses.append(", ".join(addr_parts))

                # Also check in contactPoint
                if "contactPoint" in data:
                    cp = data["contactPoint"]
                    if isinstance(cp, dict) and "address" in cp:
                        addr = cp["address"]
                        if isinstance(addr, dict):
                            addr_parts = []
                            if addr.get("streetAddress"):
                                addr_parts.append(addr["streetAddress"])
                            if addr.get("addressLocality"):
                                addr_parts.append(addr["addressLocality"])
                            if addr.get("addressRegion"):
                                addr_parts.append(addr["addressRegion"])
                            if addr.get("postalCode"):
                                addr_parts.append(addr["postalCode"])
                            if addr_parts:
                                addresses.append(", ".join(addr_parts))
        except:
            pass

    return addresses


def _find_addresses_in_text(text: str) -> list[str]:
    """
    Find address patterns in text.

    Simple pattern matching for US addresses.
    """
    addresses = []

    # Pattern: "123 Main St, City, ST 12345"
    pattern = r"(\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way|Place|Pl)?)\s*,?\s*([\w\s]+),?\s*([A-Z]{2})\s+(\d{5})"

    for match in re.finditer(pattern, text):
        street = match.group(1).strip()
        city = match.group(2).strip()
        state = match.group(3).strip()
        zipcode = match.group(4).strip()

        if state in US_STATES:
            addr = f"{street}, {city}, {state} {zipcode}"
            addresses.append(addr)

    return addresses


def count_locations(addresses: list[ConfidenceScore]) -> int:
    """
    Count distinct business locations.

    Args:
        addresses: List of extracted addresses

    Returns:
        Number of unique locations
    """
    if not addresses:
        return 0

    # Simple heuristic: different cities = different locations
    cities = set()
    for score in addresses:
        # Extract city (usually between second-to-last comma)
        parts = score.value.split(",")
        if len(parts) >= 2:
            cities.add(parts[-2].strip())

    return max(1, len(cities))
