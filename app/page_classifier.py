"""
Enhanced page classification.

Classifies pages using multiple signals:
  - URL patterns (Phase 1)
  - Page title
  - H1 heading
  - Meta description
  - Navigation text
  - Body content patterns

Returns page type with confidence score.
"""

import logging
from bs4 import BeautifulSoup

from app.page_ranker import detect_page_type as detect_from_url, get_page_type

logger = logging.getLogger(__name__)

# Keywords for each page type (content-based)
CONTENT_KEYWORDS = {
    "contact": [
        "contact us", "get in touch", "reach out", "email us", "call us",
        "contact form", "send message", "inquiry", "support"
    ],
    "about": [
        "about us", "who we are", "our story", "company history", "our mission",
        "about company", "team history", "founded", "established"
    ],
    "services": [
        "services", "what we offer", "our services", "solutions", "offerings",
        "service offerings", "capabilities", "expertise"
    ],
    "team": [
        "team", "our team", "staff", "leadership", "management", "people",
        "meet our team", "team members", "employees"
    ],
    "pricing": [
        "pricing", "plans", "packages", "rates", "costs", "pricing plans",
        "our pricing", "price list", "subscription"
    ],
    "treatments": [
        "treatments", "procedures", "services offered", "medical procedures",
        "dental treatments", "therapy"
    ],
    "locations": [
        "locations", "offices", "branches", "our locations", "find us",
        "office locations", "store locations"
    ],
    "careers": [
        "careers", "jobs", "employment", "join us", "work with us",
        "job opportunities", "hiring", "positions"
    ],
    "faq": [
        "faq", "frequently asked questions", "q&a", "questions", "help",
        "support", "common questions"
    ],
}


def extract_page_text_signals(html: str, soup: BeautifulSoup) -> dict[str, str]:
    """
    Extract relevant text signals from page.

    Returns:
        Dict with: title, h1, meta_description, body_text
    """
    signals = {
        "title": "",
        "h1": "",
        "meta_description": "",
        "body_text": "",
    }

    try:
        # Title
        title_tag = soup.find("title")
        if title_tag:
            signals["title"] = title_tag.get_text(strip=True).lower()

        # H1
        h1_tag = soup.find("h1")
        if h1_tag:
            signals["h1"] = h1_tag.get_text(strip=True).lower()

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            signals["meta_description"] = meta_desc.get("content", "").lower()

        # Body text (first 500 chars)
        body_tag = soup.find("body")
        if body_tag:
            # Remove script and style tags
            for tag in body_tag(["script", "style", "nav"]):
                tag.decompose()
            signals["body_text"] = body_tag.get_text(strip=True).lower()[:1000]

    except Exception as exc:
        logger.warning("Error extracting page signals: %s", exc)

    return signals


def score_page_type_from_content(page_type: str, signals: dict[str, str]) -> float:
    """
    Score confidence based on content signals.

    Args:
        page_type: Page type to check (e.g., "contact", "about")
        signals: Dict with title, h1, meta_description, body_text

    Returns:
        Confidence score (0.0-1.0)
    """
    if page_type not in CONTENT_KEYWORDS:
        return 0.0

    keywords = CONTENT_KEYWORDS[page_type]
    matches = 0
    total_signals = 0

    for signal_name, signal_text in signals.items():
        if not signal_text:
            continue

        total_signals += 1

        for keyword in keywords:
            if keyword in signal_text:
                matches += 1
                break  # Count signal once if any keyword matches

    if total_signals == 0:
        return 0.0

    # Base confidence from matches
    base_confidence = matches / total_signals

    # Weight by signal importance
    signal_weights = {
        "title": 1.5,
        "h1": 1.3,
        "meta_description": 1.0,
        "body_text": 0.8,
    }

    weighted_matches = 0
    weighted_total = 0

    for signal_name, signal_text in signals.items():
        if not signal_text:
            continue

        weight = signal_weights.get(signal_name, 1.0)
        weighted_total += weight

        for keyword in keywords:
            if keyword in signal_text:
                weighted_matches += weight
                break

    if weighted_total == 0:
        return base_confidence

    return min(0.99, weighted_matches / weighted_total)


def classify_page(url: str, html: str) -> dict:
    """
    Classify a page using multiple signals.

    Args:
        url: Page URL
        html: Page HTML content

    Returns:
        Dict with:
          - type: Page type (e.g., "contact", "about")
          - confidence: Confidence score (0.0-1.0)
          - url_score: Confidence from URL
          - content_score: Confidence from content
          - reason: Explanation
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception as exc:
        logger.warning("Error parsing HTML for classification: %s", exc)
        soup = BeautifulSoup(html, "html.parser")

    # Step 1: Detect from URL
    url_type, url_confidence = detect_from_url(url)

    # Step 2: Extract content signals
    signals = extract_page_text_signals(html, soup)

    # Step 3: Score against all page types
    best_type = url_type
    best_confidence = url_confidence
    best_source = "url"

    for page_type in CONTENT_KEYWORDS.keys():
        content_confidence = score_page_type_from_content(page_type, signals)

        # Combined score (weighted: URL 60%, content 40%)
        combined = (url_confidence * 0.6) if page_type == url_type else 0
        combined += (content_confidence * 0.4)

        if combined > best_confidence:
            best_confidence = combined
            best_type = page_type
            best_source = "content"

    # Final confidence is weighted average
    final_confidence = (url_confidence * 0.5) + (
        score_page_type_from_content(best_type, signals) * 0.5
    )

    reason = f"Type: {best_type} (URL: {url_confidence:.0%}, Content: {score_page_type_from_content(best_type, signals):.0%})"

    return {
        "type": best_type,
        "confidence": min(0.99, max(0.0, final_confidence)),
        "url_score": url_confidence,
        "content_score": score_page_type_from_content(best_type, signals),
        "reason": reason,
    }
