"""
Extraction orchestrator.

Runs all independent extractors against a single crawled page
and returns the aggregated raw results.

Each extractor receives (html, soup, url) and returns structured data.
This module has NO knowledge of how results are merged across pages.

Phase 2: Now includes page classification and feature detection.
Phase 4+: Includes email quality filtering.
"""

import logging
from bs4 import BeautifulSoup

from app.crawler import CrawledPage
from app.page_classifier import classify_page
from app.feature_detector import detect_all_features
from app.email_quality_engine import get_verified_business_emails
from app.extractors.email import extract_emails
from app.extractors.phone import extract_phones
from app.extractors.social import extract_social_links
from app.extractors.metadata import extract_metadata
from app.extractors.company import extract_company_info
from app.extractors.services import extract_services
from app.extractors.forms import extract_forms
from app.extractors.technology import extract_technology
from app.extractors.schema import extract_schema

logger = logging.getLogger(__name__)


def extract_from_page(page: CrawledPage) -> dict:
    """
    Run all extractors against a single crawled page.

    Phase 2: Also includes page classification and feature detection.

    Args:
        page: A successfully crawled page with html content.

    Returns:
        Dictionary containing raw results from every extractor plus:
        - page_classification: Page type and confidence
        - features: Feature flags (has_booking, has_live_chat, etc.)
        Keys: url, page_classification, features, emails, phones, social,
              metadata, company, services, forms, technology, schema.
    """
    if not page.success or not page.html:
        logger.warning("Skipping extraction for failed page: %s", page.url)
        return {}

    soup = BeautifulSoup(page.html, "lxml")

    # Phase 2: Page Classification
    logger.info("Classifying page: %s", page.url)
    page_class = classify_page(page.url, page.html)
    logger.info("  → Type: %s (confidence: %.0f%%)", page_class["type"], page_class["confidence"] * 100)

    # Phase 2: Feature Detection
    logger.info("Detecting features on: %s", page.url)
    features = detect_all_features(page.html)

    # Extract all raw data
    raw_emails = extract_emails(page.html, soup, page.url)

    # Phase 4+: Filter emails with quality engine
    verified_emails = get_verified_business_emails(raw_emails)
    logger.info("  → Found %d emails, %d verified as business-relevant", len(raw_emails), len(verified_emails))

    return {
        "url": page.url,
        "page_classification": {
            "type": page_class["type"],
            "confidence": page_class["confidence"],
            "url_score": page_class["url_score"],
            "content_score": page_class["content_score"],
        },
        "features": features,
        "emails": verified_emails,  # Use quality-filtered emails
        "phones": extract_phones(page.html, soup, page.url),
        "social": extract_social_links(page.html, soup, page.url),
        "metadata": extract_metadata(page.html, soup, page.url),
        "company": extract_company_info(page.html, soup, page.url),
        "services": extract_services(page.html, soup, page.url),
        "forms": extract_forms(page.html, soup, page.url),
        "technology": extract_technology(page.html, soup, page.url),
        "schema": extract_schema(page.html, soup, page.url),
    }


def extract_from_pages(pages: list[CrawledPage]) -> list[dict]:
    """
    Run extraction across all crawled pages.

    Args:
        pages: List of crawled pages (may include failed ones).

    Returns:
        List of per-page extraction result dictionaries.
        Failed/empty pages are excluded.
    """
    results = []
    for page in pages:
        result = extract_from_page(page)
        if result:
            results.append(result)
    logger.info("Extracted data from %d page(s)", len(results))
    return results
