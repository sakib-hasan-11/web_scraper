"""
Pydantic response models for the Website Intelligence API.

These models define the exact shape of the JSON returned by POST /analyze.
"""

from pydantic import BaseModel, Field


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


class CrawlMeta(BaseModel):
    pages_scanned: int = 0
    crawl_time_ms: int = 0


class WebsiteIntelligenceResponse(BaseModel):
    """Full response returned by POST /analyze."""

    website: str
    company: CompanyInfo = Field(default_factory=CompanyInfo)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    social: SocialLinks = Field(default_factory=SocialLinks)
    services: list[str] = Field(default_factory=list)
    technology: TechnologyStack = Field(default_factory=TechnologyStack)
    seo: SEOInfo = Field(default_factory=SEOInfo)
    pages: PagesFound = Field(default_factory=PagesFound)
    crawl: CrawlMeta = Field(default_factory=CrawlMeta)
