"""
Pydantic response models for the Website Intelligence API.

These models define the exact shape of the JSON returned by POST /analyze.

Phase 4: Business-centric schema with summary, presence, capabilities, discovery.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class CompanyInfo(BaseModel):
    name: str = ""
    description: str = ""
    industry: str = ""
    tagline: str = ""


class ContactInfo(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    contact_form: bool = False
    booking: bool = False


class SocialLinks(BaseModel):
    linkedin: str = ""
    facebook: str = ""
    instagram: str = ""
    twitter: str = ""
    youtube: str = ""
    tiktok: str = ""
    github: str = ""


class TechnologyStack(BaseModel):
    cms: str = ""
    analytics: list[str] = Field(default_factory=list)
    widgets: list[str] = Field(default_factory=list)
    booking: list[str] = Field(default_factory=list)


class SEOInfo(BaseModel):
    title: str = ""
    description: str = ""
    language: str = ""


class PagesFound(BaseModel):
    homepage: bool = True
    about: bool = False
    services: bool = False
    pricing: bool = False
    contact: bool = False


class FeatureFlags(BaseModel):
    """Phase 2: Business-critical features detected on website."""

    has_contact_form: bool = False
    has_booking: bool = False
    has_live_chat: bool = False
    has_pricing: bool = False
    has_team_page: bool = False
    has_faq: bool = False
    has_careers: bool = False
    has_whatsapp: bool = False
    has_analytics: bool = False
    has_crm: bool = False
    has_marketing_pixels: bool = False
    has_social_links: bool = False
    has_multiple_locations: bool = False


class CrawlMeta(BaseModel):
    pages_scanned: int = 0
    crawl_time_ms: int = 0


class SummaryMetrics(BaseModel):
    """Phase 4: High-level business summary."""

    business_name: str = ""
    tagline: str = ""
    primary_industry: str = ""
    contact_methods_found: int = 0  # Number of unique email/phone
    locations_count: int = 1
    key_features: list[str] = Field(default_factory=list)  # Top 3-5 capabilities
    data_quality_score: float = 0.0  # 0.0-1.0, avg confidence
    team_size_estimated: int = 0  # Count of extracted team members


class VerifiedContact(BaseModel):
    """A contact method with validation and confidence."""

    value: str
    confidence: float = 0.0  # 0.0-1.0
    source: str = ""  # "mailto", "tel", "form", etc.
    type: str = ""  # "email" or "phone"


class VerifiedAddress(BaseModel):
    """A verified business address."""

    value: str
    confidence: float = 0.0
    source: str = ""
    is_primary: bool = False


class PresenceInfo(BaseModel):
    """Phase 4: Online presence and verified contacts."""

    website_url: str = ""
    verified_contacts: list[VerifiedContact] = Field(default_factory=list)
    addresses: list[VerifiedAddress] = Field(default_factory=list)
    social_profiles: dict[str, str] = Field(default_factory=dict)  # {platform: url}


class CapabilityStack(BaseModel):
    """Phase 4: What the business can do / has."""

    services: list[str] = Field(default_factory=list)
    features: "FeatureFlags" = Field(default_factory=lambda: FeatureFlags())
    technology: TechnologyStack = Field(default_factory=TechnologyStack)
    team_members: list[str] = Field(default_factory=list)  # Names of extracted team


class DiscoveryMetadata(BaseModel):
    """Phase 4: How and when data was discovered."""

    pages_crawled: list[str] = Field(default_factory=list)  # URLs of pages crawled
    crawl_time_ms: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_summary: dict[str, float] = Field(
        default_factory=dict
    )  # {data_type: avg_confidence}
    data_sources: dict[str, list[str]] = Field(
        default_factory=dict
    )  # {data_type: [page_urls_where_found]}


class WebsiteIntelligenceResponse(BaseModel):
    """
    Full response returned by POST /analyze.
    
    Phase 4: Business-centric structure with:
    - summary: Key metrics about the business
    - presence: Online presence and contact info
    - capabilities: What the business offers
    - discovery: How data was found
    """

    # Phase 4: Business-centric sections
    summary: SummaryMetrics = Field(default_factory=SummaryMetrics)
    presence: PresenceInfo = Field(default_factory=PresenceInfo)
    capabilities: CapabilityStack = Field(default_factory=CapabilityStack)
    discovery: DiscoveryMetadata = Field(default_factory=DiscoveryMetadata)
