"""
Evidence Aggregator V3.

Organizes extracted evidence by page type.

Philosophy:
  - No business logic
  - No inference or classification
  - Just group evidence by page type
  - Return raw structured data for LLM consumption
"""

import logging
from typing import Optional
from datetime import datetime

from app.models.evidence import (
    WebsiteEvidence,
    PageEvidence,
    CrawlMetadata,
    EvidenceItem,
    ScriptEvidence,
)

logger = logging.getLogger(__name__)


class EvidenceAggregator:
    """Aggregates raw extraction evidence from all pages."""

    def __init__(self, website_url: str):
        self.website_url = website_url
        self.pages_by_type = {
            "homepage": None,
            "about": None,
            "contact": None,
            "services": None,
            "team": None,
            "pricing": None,
            "locations": None,
            "faq": None,
            "booking": None,
        }
        self.other_pages = []
        self.technology_stack = {}
        self.pages_scanned = 0
        self.pages_extracted = 0

    def add_page_evidence(self, page_evidence: PageEvidence) -> None:
        """
        Add a page's evidence to the aggregation.

        Args:
            page_evidence: PageEvidence from extractor
        """
        self.pages_scanned += 1

        if not page_evidence or not page_evidence.url:
            logger.warning("Empty page evidence received")
            return

        page_type = page_evidence.page_type

        logger.info("Aggregating evidence for %s (type: %s)", page_evidence.url, page_type)

        # Organize by known page types
        if page_type in self.pages_by_type:
            if self.pages_by_type[page_type] is None:
                self.pages_by_type[page_type] = page_evidence
                self.pages_extracted += 1
            else:
                logger.info("  → Duplicate page type %s, keeping first occurrence", page_type)
        else:
            # Store other pages
            self.other_pages.append(page_evidence)
            self.pages_extracted += 1

        # Collect technology (no duplicate detection, just aggregate)
        if page_evidence.scripts:
            for script in page_evidence.scripts:
                tech_key = f"{script.category}:{script.name}"
                self.technology_stack[tech_key] = script

    def build_response(self, crawl_time_ms: int) -> WebsiteEvidence:
        """
        Build the final evidence response.

        Args:
            crawl_time_ms: Total crawl time in milliseconds

        Returns:
            WebsiteEvidence ready for API response
        """
        # Build response with only pages that exist
        response = WebsiteEvidence(
            website_url=self.website_url,
            homepage=self.pages_by_type.get("homepage"),
            about=self.pages_by_type.get("about"),
            contact=self.pages_by_type.get("contact"),
            services=self.pages_by_type.get("services"),
            team=self.pages_by_type.get("team"),
            pricing=self.pages_by_type.get("pricing"),
            locations=self.pages_by_type.get("locations"),
            faq=self.pages_by_type.get("faq"),
            booking=self.pages_by_type.get("booking"),
            other_pages=self.other_pages,
            technology=[script for script in self.technology_stack.values()],
            crawl=CrawlMetadata(
                pages_scanned=self.pages_scanned,
                pages_extracted=self.pages_extracted,
                crawl_time_ms=crawl_time_ms,
                discovery_method="sitemap + homepage crawl + internal links",
            ),
        )

        logger.info("Built response with %d pages (scanned: %d)", self.pages_extracted, self.pages_scanned)

        return response
