"""
Feature detection system.

Detects business-critical features on pages:
  - Contact form
  - Booking system
  - Live chat
  - Pricing information
  - Multiple locations
  - Team page
  - FAQ
  - Careers
  - WhatsApp button
  - Social links
  - Analytics
  - CRM
  - Marketing pixels

Returns boolean feature flags.
"""

import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Patterns to detect features
FEATURE_PATTERNS = {
    # Contact form
    "contact_form": [
        r'<form[^>]*class=["\'].*contact',
        r'<form[^>]*id=["\'].*contact',
        r'contact-form',
        r'enquiry-form',
        r'inquiry-form',
        r'message-form',
    ],

    # Booking system
    "booking": [
        r'book\s+(an?\s+)?appointment',
        r'schedule\s+appointment',
        r'reserve\s+(a\s+)?slot',
        r'booking\.com',
        r'calendly',
        r'acuity',
        r'setmore',
        r'class=["\'].*book',
        r'id=["\'].*book',
    ],

    # Live chat
    "live_chat": [
        r'intercom',
        r'zendesk',
        r'freshdesk',
        r'drift',
        r'olark',
        r'livechat',
        r'crisp\.chat',
        r'gorgias',
        r'class=["\'].*chat',
        r'id=["\'].*chat',
    ],

    # Pricing
    "pricing": [
        r'<section[^>]*id=["\']pricing',
        r'<div[^>]*class=["\']pricing',
        r'\$\d+',  # Dollar amounts
        r'pricing table',
        r'price\s+list',
        r'subscription\s+plan',
    ],

    # Team/Staff
    "team": [
        r'<section[^>]*id=["\']team',
        r'<div[^>]*class=["\']team',
        r'meet\s+(the\s+)?team',
        r'our\s+leadership',
        r'staff\s+members',
    ],

    # FAQ
    "faq": [
        r'<section[^>]*id=["\']faq',
        r'<div[^>]*class=["\']faq',
        r'frequently\s+asked\s+questions',
        r'accordion',
    ],

    # Careers
    "careers": [
        r'<a[^>]*href=["\'][^"\']*careers',
        r'<a[^>]*href=["\'][^"\']*jobs',
        r'join\s+our\s+team',
        r'we.{0,10}?hiring',
    ],

    # WhatsApp
    "whatsapp": [
        r'wa\.me',
        r'whatsapp',
        r'class=["\'].*whatsapp',
        r'id=["\'].*whatsapp',
    ],

    # Analytics
    "analytics": [
        r'google-analytics',
        r'gtag\.js',
        r'_gat\.',
        r'_ga\.',
    ],

    # CRM tools
    "crm": [
        r'hubspot',
        r'salesforce',
        r'pipedrive',
        r'zoho',
    ],

    # Marketing pixels
    "marketing_pixels": [
        r'facebook\.com/tr',
        r'facebook.com/ads',
        r'pixel\.quantserve',
        r'google\.com/ads',
        r'doubleclick',
    ],

    # Multiple locations
    "multiple_locations": [
        r'multiple\s+location',
        r'locations?\s+worldwide',
        r'global\s+presence',
        r'international',
    ],

    # Social links
    "social_links": [
        r'(facebook|instagram|twitter|linkedin|youtube)',
    ],
}


def detect_contact_form(html: str, soup: BeautifulSoup) -> bool:
    """Detect presence of contact form."""
    try:
        # Look for form elements
        forms = soup.find_all("form")
        for form in forms:
            form_html = str(form).lower()
            # Check for contact-related form
            if any(keyword in form_html for keyword in ["contact", "message", "inquiry", "email"]):
                return True

            # Check for input fields typical of contact forms
            inputs = form.find_all(["input", "textarea"])
            if len(inputs) >= 2:  # At least 2 fields
                return True

        # Pattern matching
        html_lower = html.lower()
        for pattern in FEATURE_PATTERNS["contact_form"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting contact form: %s", exc)

    return False


def detect_booking_system(html: str, soup: BeautifulSoup) -> bool:
    """Detect booking/appointment system."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["booking"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

        # Check for common booking systems in scripts
        scripts = soup.find_all("script")
        script_content = " ".join([s.string or "" for s in scripts if s.string]).lower()

        if any(keyword in script_content for keyword in ["calendly", "acuity", "setmore", "booking"]):
            return True

    except Exception as exc:
        logger.debug("Error detecting booking system: %s", exc)

    return False


def detect_live_chat(html: str, soup: BeautifulSoup) -> bool:
    """Detect live chat widget."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["live_chat"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

        # Check scripts for chat services
        scripts = soup.find_all("script")
        script_content = " ".join([s.string or "" for s in scripts if s.string]).lower()

        if any(keyword in script_content for keyword in ["intercom", "zendesk", "drift", "olark"]):
            return True

    except Exception as exc:
        logger.debug("Error detecting live chat: %s", exc)

    return False


def detect_pricing(html: str, soup: BeautifulSoup) -> bool:
    """Detect pricing information."""
    try:
        html_lower = html.lower()

        # Look for pricing section
        pricing_sections = soup.find_all(["section", "div"], id=re.compile(r"pricing", re.IGNORECASE))
        if pricing_sections:
            return True

        # Pattern matching
        for pattern in FEATURE_PATTERNS["pricing"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting pricing: %s", exc)

    return False


def detect_team_page(html: str, soup: BeautifulSoup) -> bool:
    """Detect team/staff section."""
    try:
        html_lower = html.lower()

        # Look for team section
        team_sections = soup.find_all(["section", "div"], id=re.compile(r"team|staff", re.IGNORECASE))
        if team_sections:
            return True

        # Pattern matching
        for pattern in FEATURE_PATTERNS["team"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting team page: %s", exc)

    return False


def detect_faq(html: str, soup: BeautifulSoup) -> bool:
    """Detect FAQ section."""
    try:
        html_lower = html.lower()

        # Look for FAQ section
        faq_sections = soup.find_all(["section", "div"], id=re.compile(r"faq", re.IGNORECASE))
        if faq_sections:
            return True

        # Pattern matching
        for pattern in FEATURE_PATTERNS["faq"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting FAQ: %s", exc)

    return False


def detect_careers(html: str, soup: BeautifulSoup) -> bool:
    """Detect careers/jobs page."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["careers"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting careers: %s", exc)

    return False


def detect_whatsapp(html: str, soup: BeautifulSoup) -> bool:
    """Detect WhatsApp link/button."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["whatsapp"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting WhatsApp: %s", exc)

    return False


def detect_analytics(html: str, soup: BeautifulSoup) -> bool:
    """Detect analytics tools."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["analytics"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting analytics: %s", exc)

    return False


def detect_crm(html: str, soup: BeautifulSoup) -> bool:
    """Detect CRM tools."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["crm"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting CRM: %s", exc)

    return False


def detect_marketing_pixels(html: str, soup: BeautifulSoup) -> bool:
    """Detect marketing/tracking pixels."""
    try:
        html_lower = html.lower()

        for pattern in FEATURE_PATTERNS["marketing_pixels"]:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True

    except Exception as exc:
        logger.debug("Error detecting marketing pixels: %s", exc)

    return False


def detect_social_links(html: str, soup: BeautifulSoup) -> bool:
    """Detect social media links."""
    try:
        # Look for links to social platforms
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "").lower()
            if any(platform in href for platform in ["facebook", "instagram", "twitter", "linkedin", "youtube", "tiktok"]):
                return True

    except Exception as exc:
        logger.debug("Error detecting social links: %s", exc)

    return False


def detect_all_features(html: str) -> dict[str, bool]:
    """
    Detect all features on a page.

    Args:
        html: Page HTML

    Returns:
        Dict of feature flags (bool values)
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    features = {
        "has_contact_form": detect_contact_form(html, soup),
        "has_booking": detect_booking_system(html, soup),
        "has_live_chat": detect_live_chat(html, soup),
        "has_pricing": detect_pricing(html, soup),
        "has_team_page": detect_team_page(html, soup),
        "has_faq": detect_faq(html, soup),
        "has_careers": detect_careers(html, soup),
        "has_whatsapp": detect_whatsapp(html, soup),
        "has_analytics": detect_analytics(html, soup),
        "has_crm": detect_crm(html, soup),
        "has_marketing_pixels": detect_marketing_pixels(html, soup),
        "has_social_links": detect_social_links(html, soup),
    }

    logger.info("Detected features: %s", {k: v for k, v in features.items() if v})

    return features


def aggregate_features(all_features: list[dict[str, bool]]) -> dict[str, bool]:
    """
    Aggregate features from multiple pages.

    Returns True if feature is found on ANY page.

    Args:
        all_features: List of feature dicts from each page

    Returns:
        Dict with aggregated features (True if found on any page)
    """
    aggregated = {}

    if not all_features:
        return aggregated

    # Get all feature keys from first page
    keys = all_features[0].keys()

    # For each feature, return True if found on ANY page
    for key in keys:
        aggregated[key] = any(page.get(key, False) for page in all_features)

    return aggregated
