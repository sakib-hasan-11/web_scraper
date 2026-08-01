"""
Evidence Cleaner V3.

Removes noise from extracted evidence.

Pipeline:
  Evidence → Cleaner → Clean Evidence → JSON Response

Responsibilities:
  - Remove empty objects
  - Deduplicate content
  - Remove boilerplate
  - Filter fake emails
  - Clean technology detection
  - Extract footer globally
  - Limit content volume
  - Optimize for LLM

NO architectural changes. NO new features. ONLY cleanup.
"""

import logging
import re
from typing import Optional, Any
from urllib.parse import urlparse

from app.models.evidence import (
    WebsiteEvidence,
    PageEvidence,
    EvidenceItem,
    CardEvidence,
    ParagraphEvidence,
    HeadingEvidence,
    SchemaEvidence,
    ScriptEvidence,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────

FAKE_EMAIL_DOMAINS = {
    "sentry.wixpress.com",
    "sentry-next.wixpress.com",
    "cloudflare.com",
    "googleusercontent.com",
    "localhost",
    "example.com",
    "test.com",
    "noreply",
    "no-reply",
    "donotreply",
}

BOILERPLATE_KEYWORDS = {
    "cookie",
    "privacy policy",
    "terms of service",
    "terms of use",
    "newsletter",
    "subscribe",
    "contact us",
    "get in touch",
    "follow us",
    "sitemap",
    "back to top",
    "marketing consent",
    "gdpr",
    "ccpa",
    "all rights reserved",
    "copyright",
    "unsubscribe",
    "contact details",
    "opening hours",
    "menu",
    "navigation",
}

EXCLUDED_PAGE_TYPES = {
    "unknown",  # Skip unknown pages
}

OPENING_HOURS_PATTERNS = [
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)",
    r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
    r"(\d{1,2}:\d{2}\s*(AM|PM|am|pm))",
    r"(\d{1,2}:\d{2})",
    r"(Closed|Open)",
    r"(9|10|11|12|13|14|15|16|17|18|19|20|21|22|23):\d{2}",
]


class EvidenceCleaner:
    """Cleans extracted evidence to remove noise and duplicates."""

    def __init__(self):
        self.seen_paragraphs = set()
        self.seen_headings = set()
        self.seen_emails = set()
        self.seen_phones = set()
        self.seen_social_links = set()
        self.seen_cards = set()
        self.global_footer = None
        self.global_technology = {}

    def clean_response(self, response: WebsiteEvidence) -> WebsiteEvidence:
        """
        Clean entire response.

        Args:
            response: WebsiteEvidence from aggregator

        Returns:
            Cleaned WebsiteEvidence
        """
        logger.info("Cleaning evidence response...")

        # Step 1: Extract footer globally (from contact or homepage)
        self.global_footer = self._extract_global_footer(response)

        # Step 2: Extract technology globally (from all pages)
        self.global_technology = self._extract_global_technology(response)

        # Step 3: Clean each page
        if response.homepage:
            response.homepage = self._clean_page(response.homepage, "homepage")

        if response.about:
            response.about = self._clean_page(response.about, "about")

        if response.contact:
            response.contact = self._clean_page(response.contact, "contact")

        if response.services:
            response.services = self._clean_page(response.services, "services")

        if response.team:
            response.team = self._clean_page(response.team, "team")

        if response.pricing:
            response.pricing = self._clean_page(response.pricing, "pricing")

        if response.locations:
            response.locations = self._clean_page(response.locations, "locations")

        if response.faq:
            response.faq = self._clean_page(response.faq, "faq")

        if response.booking:
            response.booking = self._clean_page(response.booking, "booking")

        # Step 4: Clean other pages
        cleaned_other = []
        for page in response.other_pages:
            if page.page_type not in EXCLUDED_PAGE_TYPES:
                cleaned = self._clean_page(page, page.page_type)
                if cleaned and self._has_meaningful_content(cleaned):
                    cleaned_other.append(cleaned)
        response.other_pages = cleaned_other

        # Step 5: Set global technology
        response.technology = list(self.global_technology.values())

        # Step 6: Remove empty pages
        response = self._remove_empty_pages(response)

        logger.info("Evidence cleaned successfully")
        return response

    # ────────────────────────────────────────────────────────────────────
    # Page Cleaning
    # ────────────────────────────────────────────────────────────────────

    def _clean_page(self, page: PageEvidence, page_type: str) -> Optional[PageEvidence]:
        """Clean a single page."""
        if not page or not page.url:
            return None

        # Ensure homepage is classified as homepage (root URL)
        parsed = urlparse(page.url)
        path = parsed.path.rstrip("/")
        
        if not path or path == "":
            # Root domain with no path = homepage
            page.page_type = "homepage"

        # Clean content
        page.title = self._clean_text(page.title, max_len=200)
        page.meta_title = self._clean_text(page.meta_title, max_len=200)
        page.meta_description = self._clean_text(page.meta_description, max_len=300)
        page.footer_text = None  # Remove (now global)

        # Clean arrays
        page.headings = self._clean_headings(page.headings)
        page.paragraphs = self._clean_paragraphs(page.paragraphs)
        page.lists = self._clean_lists(page.lists)
        page.tables = self._clean_tables(page.tables)
        page.cards = self._clean_cards(page.cards)

        # Clean contact evidence
        page.emails = self._clean_emails(page.emails)
        page.phones = self._clean_phones(page.phones)
        page.addresses = self._clean_addresses(page.addresses)
        page.opening_hours = self._clean_opening_hours(page.opening_hours)
        page.maps_links = self._clean_evidence_items(page.maps_links)

        # Clean forms and external
        page.social_links = self._clean_social_links(page.social_links)
        page.whatsapp_links = self._clean_evidence_items(page.whatsapp_links)
        page.calendar_links = self._clean_evidence_items(page.calendar_links)

        # Remove footer evidence (now global)
        page.footer_emails = []
        page.footer_phones = []
        page.footer_addresses = []
        page.footer_social_links = []
        page.copyright = None

        # Clean schema
        page.schema_data = self._clean_schema(page.schema_data)

        # Remove technology (now global)
        page.scripts = []

        return page

    # ────────────────────────────────────────────────────────────────────
    # Specific Cleaning Methods
    # ────────────────────────────────────────────────────────────────────

    def _clean_headings(self, headings: list[HeadingEvidence]) -> list[HeadingEvidence]:
        """Remove boilerplate, duplicates, limit to 20."""
        cleaned = []

        for heading in headings[:20]:  # Limit to 20
            text = heading.text.lower()

            # Skip boilerplate
            if any(keyword in text for keyword in BOILERPLATE_KEYWORDS):
                continue

            # Skip duplicates
            if text in self.seen_headings:
                continue

            if heading.text and len(heading.text) > 2:
                self.seen_headings.add(text)
                cleaned.append(heading)

        return cleaned

    def _clean_paragraphs(self, paragraphs: list[ParagraphEvidence]) -> list[ParagraphEvidence]:
        """Remove boilerplate, duplicates, limit to 10, enforce 50-800 chars."""
        cleaned = []

        for para in paragraphs[:30]:  # Process first 30
            text = para.text
            text_lower = text.lower()

            # Skip if too short or too long
            if len(text) < 50 or len(text) > 800:
                continue

            # Skip boilerplate
            if any(keyword in text_lower for keyword in BOILERPLATE_KEYWORDS):
                continue

            # Skip duplicates
            if text_lower in self.seen_paragraphs:
                continue

            self.seen_paragraphs.add(text_lower)
            cleaned.append(para)

            if len(cleaned) >= 10:  # Limit to 10
                break

        return cleaned

    def _clean_lists(self, lists: list) -> list:
        """Remove empty lists, limit to 5."""
        cleaned = []
        for lst in lists[:10]:
            if lst and lst.items and len(lst.items) > 0:
                cleaned.append(lst)
                if len(cleaned) >= 5:
                    break
        return cleaned

    def _clean_tables(self, tables: list) -> list:
        """Remove empty tables, limit to 3."""
        cleaned = []
        for table in tables[:5]:
            if table and (table.headers or table.rows) and table.rows:
                cleaned.append(table)
                if len(cleaned) >= 3:
                    break
        return cleaned

    def _clean_cards(self, cards: list[CardEvidence]) -> list[CardEvidence]:
        """Remove empty cards, deduplicate, limit to 15."""
        cleaned = []

        for card in cards[:30]:
            # Skip empty cards
            if not card.title and not card.subtitle and not card.description:
                continue

            # Create card fingerprint for deduplication
            fingerprint = f"{card.title}|{card.subtitle}|{card.description}".lower()
            if fingerprint in self.seen_cards:
                continue

            self.seen_cards.add(fingerprint)
            cleaned.append(card)

            if len(cleaned) >= 15:
                break

        return cleaned

    def _clean_emails(self, emails: list[EvidenceItem]) -> list[EvidenceItem]:
        """Remove fake emails, duplicates."""
        cleaned = []

        for email_item in emails:
            email = email_item.value.lower()

            # Skip fake emails
            if self._is_fake_email(email):
                continue

            # Skip duplicates
            if email in self.seen_emails:
                continue

            # Validate email format (basic)
            if not re.match(r"^[^@]+@[^@]+\.[a-z]{2,}$", email):
                continue

            self.seen_emails.add(email)
            cleaned.append(email_item)

        return cleaned

    def _clean_phones(self, phones: list[EvidenceItem]) -> list[EvidenceItem]:
        """Remove duplicates, invalid formats."""
        cleaned = []

        for phone_item in phones:
            phone = phone_item.value

            # Skip if too short
            if len(phone) < 6:
                continue

            # Skip duplicates
            if phone in self.seen_phones:
                continue

            self.seen_phones.add(phone)
            cleaned.append(phone_item)

        return cleaned

    def _clean_addresses(self, addresses: list[EvidenceItem]) -> list[EvidenceItem]:
        """Remove duplicates, very short addresses."""
        cleaned = []

        for addr_item in addresses:
            addr = addr_item.value

            # Skip if too short
            if len(addr) < 10:
                continue

            # Skip duplicates
            if addr in self.seen_addresses:
                continue

            self.seen_addresses.add(addr)
            cleaned.append(addr_item)

        return cleaned

    def _clean_opening_hours(self, hours: list[EvidenceItem]) -> list[EvidenceItem]:
        """Keep only valid opening hours patterns."""
        cleaned = []

        for hour_item in hours:
            text = hour_item.value

            # Must match at least one opening hours pattern
            if not any(re.search(pattern, text) for pattern in OPENING_HOURS_PATTERNS):
                continue

            # Skip boilerplate
            if any(keyword in text.lower() for keyword in BOILERPLATE_KEYWORDS):
                continue

            # Skip if looks like service name or degree
            if any(x in text for x in ["Dr ", "PhD", "DDS", "MD", "BSc"]):
                continue

            cleaned.append(hour_item)

        return cleaned

    def _clean_social_links(self, links: list[EvidenceItem]) -> list[EvidenceItem]:
        """Remove duplicates."""
        cleaned = []

        for link_item in links:
            url = link_item.value.lower()

            # Skip duplicates
            if url in self.seen_social_links:
                continue

            self.seen_social_links.add(url)
            cleaned.append(link_item)

        return cleaned

    def _clean_evidence_items(self, items: list[EvidenceItem]) -> list[EvidenceItem]:
        """Generic cleaning for evidence items."""
        cleaned = []
        seen = set()

        for item in items:
            if not item.value:
                continue
            if item.value in seen:
                continue

            seen.add(item.value)
            cleaned.append(item)

        return cleaned

    def _clean_schema(self, schemas: list[SchemaEvidence]) -> list[SchemaEvidence]:
        """Remove empty schemas, keep useful types only."""
        useful_types = {
            "organization",
            "localbusiness",
            "person",
            "medicalorganization",
            "dentist",
            "restaurant",
            "hotel",
            "store",
            "professionalservice",
        }

        cleaned = []
        for schema in schemas:
            if schema.schema_type.lower() in useful_types:
                if schema.data and len(schema.data) > 1:
                    cleaned.append(schema)

        return cleaned

    # ────────────────────────────────────────────────────────────────────
    # Global Extraction
    # ────────────────────────────────────────────────────────────────────

    def _extract_global_footer(self, response: WebsiteEvidence) -> Optional[dict]:
        """Extract footer once from contact or homepage."""
        footer = None

        # Prefer contact page footer
        if response.contact and response.contact.footer_text:
            footer = {
                "text": response.contact.footer_text,
                "source": response.contact.url,
            }
        elif response.homepage and response.homepage.footer_text:
            footer = {
                "text": response.homepage.footer_text,
                "source": response.homepage.url,
            }

        return footer

    def _extract_global_technology(self, response: WebsiteEvidence) -> dict:
        """Extract technology once globally from all pages."""
        tech = {}

        # Collect from all pages
        for page in [response.homepage, response.about, response.contact, response.services, response.team]:
            if page and page.scripts:
                for script in page.scripts:
                    key = f"{script.category}:{script.name}".lower()
                    if key not in tech:
                        tech[key] = script

        return tech

    # ────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ────────────────────────────────────────────────────────────────────

    def _is_fake_email(self, email: str) -> bool:
        """Check if email is system/fake."""
        email_lower = email.lower()

        # Check domain blocklist
        for fake_domain in FAKE_EMAIL_DOMAINS:
            if fake_domain in email_lower:
                return True

        # Check for hash-like emails
        if re.match(r"^[a-f0-9]{32,}@", email_lower):
            return True

        # Check for tracking
        if any(x in email_lower for x in ["bounce", "mailer-daemon", "postmaster", "tracking"]):
            return True

        return False

    def _clean_text(self, text: Optional[str], max_len: int = 200) -> Optional[str]:
        """Clean and validate text."""
        if not text:
            return None

        text = text.strip()
        if not text or len(text) < 2:
            return None

        if len(text) > max_len:
            text = text[:max_len].rstrip()

        return text

    def _has_meaningful_content(self, page: PageEvidence) -> bool:
        """Check if page has meaningful content."""
        if not page:
            return False

        content_items = (
            len(page.headings or [])
            + len(page.paragraphs or [])
            + len(page.cards or [])
            + len(page.emails or [])
            + len(page.phones or [])
        )

        return content_items > 0

    def _remove_empty_pages(self, response: WebsiteEvidence) -> WebsiteEvidence:
        """Remove pages with no meaningful content."""
        if response.homepage and not self._has_meaningful_content(response.homepage):
            response.homepage = None

        if response.about and not self._has_meaningful_content(response.about):
            response.about = None

        if response.contact and not self._has_meaningful_content(response.contact):
            response.contact = None

        if response.services and not self._has_meaningful_content(response.services):
            response.services = None

        if response.team and not self._has_meaningful_content(response.team):
            response.team = None

        if response.pricing and not self._has_meaningful_content(response.pricing):
            response.pricing = None

        if response.locations and not self._has_meaningful_content(response.locations):
            response.locations = None

        if response.faq and not self._has_meaningful_content(response.faq):
            response.faq = None

        if response.booking and not self._has_meaningful_content(response.booking):
            response.booking = None

        return response

    # Initialize seen sets for deduplication
    def __init__(self):
        self.seen_paragraphs = set()
        self.seen_headings = set()
        self.seen_emails = set()
        self.seen_phones = set()
        self.seen_addresses = set()
        self.seen_social_links = set()
        self.seen_cards = set()
        self.global_footer = None
        self.global_technology = {}
