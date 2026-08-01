"""
Forms and contact widget extractor.

Detects the presence of:
- Contact forms
- Booking / appointment forms
- Newsletter signup forms
- Live chat widgets (Intercom, Zendesk, Drift, Crisp, Tawk.to)

Returns boolean flags only — does not parse form fields.
"""

import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Patterns to identify contact-intent forms
_CONTACT_FORM_RE = re.compile(
    r"contact|enquiry|inquiry|message|get.in.touch|reach.us", re.IGNORECASE
)

# Patterns to identify booking/appointment forms
_BOOKING_FORM_RE = re.compile(
    r"book|booking|appointment|schedule|calendly|acuity|demo", re.IGNORECASE
)

# Patterns to identify newsletter forms
_NEWSLETTER_RE = re.compile(
    r"newsletter|subscribe|mailing.list|sign.?up", re.IGNORECASE
)

# Chat widget script/src patterns
_CHAT_WIDGET_SIGNATURES = [
    "intercomcdn.com",
    "intercom.io",
    "zdassets.com",
    "zendesk.com",
    "js.driftt.com",
    "client.crisp.chat",
    "embed.tawk.to",
    "tawk.to",
]


def _has_form_with_pattern(soup: BeautifulSoup, pattern: re.Pattern) -> bool:
    """
    Return True if any <form> or its action/id/class matches the pattern,
    or if a nearby label/heading matches.
    """
    for form in soup.find_all("form"):
        action = form.get("action", "")
        form_id = form.get("id", "")
        form_class = " ".join(form.get("class", []))
        form_name = form.get("name", "")
        surrounding = action + form_id + form_class + form_name

        if pattern.search(surrounding):
            return True

        # Check preceding sibling heading or label
        prev = form.find_previous(["h1", "h2", "h3", "h4", "label", "legend"])
        if prev and pattern.search(prev.get_text()):
            return True

    # Also check for embedded iframes (Calendly, HubSpot forms)
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if pattern.search(src):
            return True

    return False


def _has_chat_widget(html: str) -> bool:
    """Return True if any known chat widget script signature is present."""
    html_lower = html.lower()
    return any(sig in html_lower for sig in _CHAT_WIDGET_SIGNATURES)


def extract_forms(html: str, soup: BeautifulSoup, url: str) -> dict:
    """
    Detect contact/booking/newsletter forms and chat widgets on a page.

    Args:
        html: Raw HTML string.
        soup: Parsed BeautifulSoup object.
        url: Source URL (used for logging context).

    Returns:
        Dictionary with boolean keys:
        contact_form, booking_form, newsletter_form, chat_widget, live_chat.
    """
    contact_form = _has_form_with_pattern(soup, _CONTACT_FORM_RE)
    booking_form = _has_form_with_pattern(soup, _BOOKING_FORM_RE)
    newsletter_form = _has_form_with_pattern(soup, _NEWSLETTER_RE)
    chat_widget = _has_chat_widget(html)

    logger.debug(
        "Forms on %s — contact:%s booking:%s newsletter:%s chat:%s",
        url, contact_form, booking_form, newsletter_form, chat_widget,
    )

    return {
        "contact_form": contact_form,
        "booking_form": booking_form,
        "newsletter_form": newsletter_form,
        "chat_widget": chat_widget,
        "live_chat": chat_widget,  # alias for response model
    }
