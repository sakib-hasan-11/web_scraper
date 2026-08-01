"""
Enhanced contact extraction with normalization and validation.

Normalizes phone numbers to E.164 format.
Validates email addresses.
Tracks confidence scores.
"""

import logging
import re
from phonenumbers import parse as parse_phone, format_number, PhoneNumberFormat, NumberParseException

from app.confidence_engine import (
    ExtractionSource,
    ConfidenceScore,
    score_phone,
    score_email,
)

logger = logging.getLogger(__name__)


def normalize_phone(phone: str, country: str = "US") -> tuple[str | None, bool]:
    """
    Normalize phone to E.164 format.

    Args:
        phone: Raw phone string
        country: ISO country code (default US)

    Returns:
        (formatted_phone, is_valid) or (None, False) if invalid
    """
    if not phone:
        return None, False

    try:
        # Parse with country context
        parsed = parse_phone(phone, region=country)

        # Check if valid
        if not parsed or not isinstance(parsed.country_code, int):
            return None, False

        # Format to E.164 (e.g., +1234567890)
        formatted = format_number(parsed, PhoneNumberFormat.E164)
        return formatted, True

    except (NumberParseException, Exception) as e:
        logger.debug(f"Failed to parse phone '{phone}': {e}")
        return None, False


def extract_phones_enhanced(soup, html: str) -> list[ConfidenceScore]:
    """
    Extract and normalize phone numbers with confidence scores.

    Args:
        soup: BeautifulSoup object
        html: Full HTML content

    Returns:
        List of ConfidenceScore objects
    """
    scores = []

    # 1. Extract tel: links (highest confidence)
    tel_links = soup.find_all("a", href=re.compile(r"^tel:"))
    for link in tel_links:
        phone = link.get("href", "").replace("tel:", "").strip()
        if phone:
            normalized, is_valid = normalize_phone(phone)
            if normalized:
                score = score_phone(normalized, ExtractionSource.TEL, is_normalized=True)
                scores.append(score)

    # 2. Extract structured data (schema.org)
    schema_phones = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict) and "telephone" in data:
                tel = data["telephone"]
                if isinstance(tel, list):
                    schema_phones.extend(tel)
                else:
                    schema_phones.append(tel)
        except:
            pass

    for phone in schema_phones:
        if phone:
            normalized, is_valid = normalize_phone(phone)
            if normalized:
                score = score_phone(normalized, ExtractionSource.SCHEMA, is_normalized=True)
                scores.append(score)

    # 3. Regex patterns (footer priority)
    phone_patterns = [
        r"\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})",  # US
        r"\+[1-9]\d{1,14}",  # E.164 format
        r"(?:phone|tel|contact):\s*([+\d\s\-()]+)",  # Labeled
    ]

    for pattern in phone_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            raw_phone = match.group(0) if len(match.groups()) == 0 else match.group(1)
            if raw_phone:
                # Check if in footer
                in_footer = raw_phone in soup.find("footer").get_text() if soup.find("footer") else False
                source = ExtractionSource.FOOTER if in_footer else ExtractionSource.REGEX

                normalized, is_valid = normalize_phone(raw_phone)
                if normalized:
                    score = score_phone(normalized, source, is_normalized=True)
                    scores.append(score)

    # Deduplicate by normalized value
    seen = set()
    unique_scores = []
    for score in scores:
        if score.value not in seen:
            seen.add(score.value)
            unique_scores.append(score)

    return unique_scores


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email string

    Returns:
        True if valid format
    """
    # RFC 5322 simplified
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def extract_emails_enhanced(soup, html: str) -> list[ConfidenceScore]:
    """
    Extract and validate email addresses with confidence scores.

    Args:
        soup: BeautifulSoup object
        html: Full HTML content

    Returns:
        List of ConfidenceScore objects
    """
    scores = []

    # 1. Extract mailto: links (highest confidence)
    mailto_links = soup.find_all("a", href=re.compile(r"^mailto:"))
    for link in mailto_links:
        email = link.get("href", "").replace("mailto:", "").strip().lower()
        if email and validate_email(email):
            score = score_email(email, ExtractionSource.MAILTO)
            scores.append(score)

    # 2. Extract structured data
    schema_emails = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict) and "email" in data:
                email = data["email"]
                if isinstance(email, list):
                    schema_emails.extend(email)
                else:
                    schema_emails.append(email)
        except:
            pass

    for email in schema_emails:
        if email:
            email = email.lower()
            if validate_email(email):
                score = score_email(email, ExtractionSource.SCHEMA)
                scores.append(score)

    # 3. Regex patterns
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    for match in re.finditer(email_pattern, html):
        email = match.group(0).lower()

        # Check if in footer
        in_footer = email in soup.find("footer").get_text() if soup.find("footer") else False
        source = ExtractionSource.FOOTER if in_footer else ExtractionSource.REGEX

        if validate_email(email):
            score = score_email(email, source)
            scores.append(score)

    # Deduplicate
    seen = set()
    unique_scores = []
    for score in scores:
        if score.value not in seen:
            seen.add(score.value)
            unique_scores.append(score)

    return unique_scores
