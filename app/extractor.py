"""
Extraction orchestrator.

Runs all independent extractors against a single crawled page
and returns the aggregated raw results.

Each extractor receives (html, soup, url) and returns structured data.
This module has NO knowledge of how results are merged across pages.
"""

import logging
from bs4 import BeautifulSoup

from app.crawler import CrawledPage
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

    Args:
        page: A successfully crawled page with html content.

    Returns:
        Dictionary containing raw results from every extractor.
        Keys: emails, phones, social, metadata, company, services,
              forms, technology, schema, url.
    """
    if not page.success or not page.html:
        logger.warning("Skipping extraction for failed page: %s", page.url)
        return {}

    soup = BeautifulSoup(page.html, "lxml")

    return {
        "url": page.url,
        "emails": extract_emails(page.html, soup, page.url),
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
