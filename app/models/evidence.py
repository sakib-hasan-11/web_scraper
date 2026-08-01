"""
Evidence-based response models for Website Intelligence Service V3.

Designed for LLM consumption - pure structured evidence collection.

Philosophy:
  - No business interpretation
  - No inference or classification
  - Every item includes: value, source, method, confidence
  - Organized by page type
  - Compact and deterministic
"""

from pydantic import BaseModel, Field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────
# Primitives: Evidence Items
# ──────────────────────────────────────────────────────────────────────────


class EvidenceItem(BaseModel):
    """Base evidence item with source tracking."""
    value: str
    source: str = Field(description="Page URL where evidence was found")
    method: str = Field(description="Extraction method (e.g., 'mailto', 'tel', 'visible', 'schema', 'regex')")
    confidence: float = Field(description="0.0-1.0 confidence score")
    importance: int = Field(default=5, description="Importance score 1-10 (1=low, 10=critical)")



class HeadingEvidence(BaseModel):
    """Extracted heading with level."""
    level: int = Field(description="H1-H6")
    text: str
    source: str = Field(default="", description="Page URL")


class ParagraphEvidence(BaseModel):
    """Extracted paragraph (50-800 chars, filtered)."""
    text: str
    source: str = Field(default="", description="Page URL")


class ListEvidence(BaseModel):
    """Extracted list (UL, OL, DL)."""
    type: str = Field(description="ul|ol|dl")
    items: list[str]
    source: str = Field(default="", description="Page URL")


class TableEvidence(BaseModel):
    """Extracted table."""
    headers: list[str]
    rows: list[list[str]]
    source: str = Field(default="", description="Page URL")


class CardEvidence(BaseModel):
    """Extracted card (repeating block)."""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    source: str = Field(default="", description="Page URL")


class FormEvidence(BaseModel):
    """Extracted form."""
    action: str = Field(description="Form action URL")
    method: str = Field(description="GET or POST")
    input_names: list[str] = Field(description="Form field names")
    button_text: str = Field(default="")
    source: str = Field(default="", description="Page URL")


class SchemaEvidence(BaseModel):
    """Raw JSON-LD schema grouped by type."""
    schema_type: str = Field(description="Schema.org type (Organization, Person, LocalBusiness, etc.)")
    data: dict = Field(description="Raw JSON-LD data")
    source: str = Field(default="", description="Page URL")


class ScriptEvidence(BaseModel):
    """Detected script/library."""
    name: str = Field(description="Script name (e.g., 'Google Analytics', 'Intercom')")
    category: str = Field(description="cms|framework|analytics|marketing|chat|booking|crm|payment|other")
    confidence: float = Field(default=0.9)
    importance: int = Field(default=7, description="Importance score 1-10")
    source: str = Field(default="", description="Page URL")


# ──────────────────────────────────────────────────────────────────────────
# Page Evidence: Unified structure for all pages
# ──────────────────────────────────────────────────────────────────────────


class PageEvidence(BaseModel):
    """Evidence extracted from a single page."""

    url: str = Field(description="Page URL")
    page_type: str = Field(default="unknown", description="detected|homepage|about|contact|services|team|pricing|locations|faq|booking")
    
    # Basic metadata
    title: str = Field(default="", description="Page title or H1")
    meta_title: Optional[str] = Field(default="", description="<title> tag")
    meta_description: Optional[str] = Field(default="", description="<meta description>")
    meta_og_title: Optional[str] = Field(default="", description="<meta og:title>")
    meta_og_description: Optional[str] = Field(default="", description="<meta og:description>")
    meta_og_image: Optional[str] = Field(default="", description="<meta og:image>")
    canonical_url: Optional[str] = Field(default="", description="<link rel=canonical>")

    # Navigation & Discovery
    logo_url: Optional[str] = Field(default="", description="Logo image URL")
    navigation_links: list[str] = Field(default_factory=list, description="Nav menu URLs")

    # Structured content
    headings: list[HeadingEvidence] = Field(default_factory=list, description="H1-H6 headings")
    paragraphs: list[ParagraphEvidence] = Field(default_factory=list, description="50-800 char paragraphs")
    lists: list[ListEvidence] = Field(default_factory=list, description="UL, OL, DL lists")
    tables: list[TableEvidence] = Field(default_factory=list, description="HTML tables")
    cards: list[CardEvidence] = Field(default_factory=list, description="Repeating card blocks")

    # Contact evidence
    emails: list[EvidenceItem] = Field(default_factory=list, description="Email addresses with source")
    phones: list[EvidenceItem] = Field(default_factory=list, description="Phone numbers with source")
    addresses: list[EvidenceItem] = Field(default_factory=list, description="Physical addresses with source")
    opening_hours: list[EvidenceItem] = Field(default_factory=list, description="Business hours with source")
    maps_links: list[EvidenceItem] = Field(default_factory=list, description="Google Maps URLs")

    # Forms & Interactions
    contact_forms: list[FormEvidence] = Field(default_factory=list)
    booking_forms: list[FormEvidence] = Field(default_factory=list)
    newsletter_forms: list[FormEvidence] = Field(default_factory=list)

    # Social & External
    social_links: list[EvidenceItem] = Field(default_factory=list, description="Social profile URLs")
    whatsapp_links: list[EvidenceItem] = Field(default_factory=list)
    calendar_links: list[EvidenceItem] = Field(default_factory=list, description="Calendly, Acuity, etc.")

    # Structured data
    schema_data: list[SchemaEvidence] = Field(default_factory=list, description="Raw JSON-LD schemas")

    # Technical
    scripts: list[ScriptEvidence] = Field(default_factory=list, description="Detected technology/scripts")

    # Footer evidence
    footer_emails: list[EvidenceItem] = Field(default_factory=list)
    footer_phones: list[EvidenceItem] = Field(default_factory=list)
    footer_addresses: list[EvidenceItem] = Field(default_factory=list)
    footer_social_links: list[EvidenceItem] = Field(default_factory=list)
    footer_text: Optional[str] = Field(default="", description="Footer text content")
    copyright: Optional[str] = Field(default="", description="Copyright notice")
    registration_numbers: list[str] = Field(default_factory=list, description="VAT, Company Registration, etc.")


# ──────────────────────────────────────────────────────────────────────────
# Response: Grouped by page type
# ──────────────────────────────────────────────────────────────────────────


class CrawlMetadata(BaseModel):
    """Crawl execution metadata."""
    pages_scanned: int = Field(description="Total pages crawled")
    pages_extracted: int = Field(description="Pages with successful extraction")
    crawl_time_ms: int = Field(description="Total crawl time in milliseconds")
    discovery_method: str = Field(default="", description="how pages were discovered")
    
    # Debug mode fields
    crawled_urls: list[str] = Field(default_factory=list, description="URLs that were crawled (debug mode only)")
    extraction_time_ms: int = Field(default=0, description="Time spent on extraction (debug mode)")
    aggregation_time_ms: int = Field(default=0, description="Time spent on aggregation (debug mode)")



class WebsiteEvidence(BaseModel):
    """Website evidence response - organized by page type."""

    website_url: str = Field(description="The website analyzed")

    # Evidence organized by page type
    homepage: Optional[PageEvidence] = None
    about: Optional[PageEvidence] = None
    contact: Optional[PageEvidence] = None
    services: Optional[PageEvidence] = None
    team: Optional[PageEvidence] = None
    team_profiles: list[PageEvidence] = Field(default_factory=list, description="Individual team member/doctor profiles")
    pricing: Optional[PageEvidence] = None
    locations: Optional[PageEvidence] = None
    faq: Optional[PageEvidence] = None
    booking: Optional[PageEvidence] = None

    # Additional pages (less common)
    other_pages: list[PageEvidence] = Field(default_factory=list, description="Other important pages discovered")

    # Technology stack (deterministic detection only)
    technology: list[ScriptEvidence] = Field(default_factory=list, description="Consolidated technology stack")

    # Crawl metadata
    crawl: CrawlMetadata = Field(description="Crawl statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "website_url": "https://example.com",
                "homepage": {
                    "url": "https://example.com/",
                    "page_type": "homepage",
                    "title": "Welcome",
                    "meta_title": "Example Company - Services",
                    "emails": [
                        {"value": "info@example.com", "method": "mailto", "source": "https://example.com/", "confidence": 0.99}
                    ],
                },
                "contact": {
                    "url": "https://example.com/contact",
                    "page_type": "contact",
                    "contact_forms": [
                        {"action": "/submit-contact", "method": "POST", "input_names": ["name", "email", "message"], "source": "https://example.com/contact"}
                    ],
                },
                "crawl": {
                    "pages_scanned": 5,
                    "pages_extracted": 5,
                    "crawl_time_ms": 8200,
                }
            }
        }
