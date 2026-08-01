"""
Merger module.

Takes raw per-page extraction results and merges them into a single
WebsiteIntelligenceResponse.

Merge priorities (highest to lowest):
  Schema.org structured data > Visible page content > Metadata > Regex

Deduplicates emails, phones, social links, services, and technology detections.
"""

import logging
from urllib.parse import urlparse

from app.models.response import (
    WebsiteIntelligenceResponse,
    CompanyInfo,
    ContactInfo,
    SocialLinks,
    TechnologyStack,
    SEOInfo,
    PagesFound,
    FeatureFlags,
    CrawlMeta,
)
from app.constants.keywords import IMPORTANT_SLUGS

logger = logging.getLogger(__name__)


def _detect_page_type(url: str) -> str | None:
    """Return the page category slug if the URL matches a known important slug."""
    path = urlparse(url).path.lower()
    if not path or path == "/":
        return "homepage"
    for slug in ("about", "service", "solution", "pricing", "plan", "contact"):
        if slug in path:
            return slug
    return None


def _merge_company(page_results: list[dict]) -> CompanyInfo:
    """
    Merge company info across pages.
    Priority: JSON-LD schema → visible company extractor → metadata.
    """
    name = ""
    description = ""
    tagline = ""

    # 1. JSON-LD Schema (highest confidence)
    for page in page_results:
        for schema in page.get("schema", []):
            if not name and schema.get("name"):
                name = schema["name"]
            if not description and schema.get("description"):
                description = schema["description"]

    # 2. Visible company extractor
    for page in page_results:
        company = page.get("company", {})
        if not name and company.get("name"):
            name = company["name"]
        if not tagline and company.get("tagline"):
            tagline = company["tagline"]
        if not description and company.get("description"):
            description = company["description"]

    # 3. Metadata fallback
    for page in page_results:
        meta = page.get("metadata", {})
        if not name and meta.get("og_title"):
            name = meta["og_title"]
        if not tagline and meta.get("description"):
            tagline = meta["description"]

    return CompanyInfo(
        name=name,
        description=description,
        tagline=tagline,
        industry="",  # Not detectable without LLM in V1
    )


def _merge_contact(page_results: list[dict]) -> ContactInfo:
    """Merge and deduplicate all contact information across pages."""
    all_emails: set[str] = set()
    all_phones: set[str] = set()
    contact_form = False
    booking = False

    for page in page_results:
        all_emails.update(page.get("emails", []))
        all_phones.update(page.get("phones", []))

        # Also collect from JSON-LD schema
        for schema in page.get("schema", []):
            if schema.get("email"):
                all_emails.add(schema["email"].lower())
            if schema.get("telephone"):
                all_phones.add(schema["telephone"])

        forms = page.get("forms", {})
        if forms.get("contact_form"):
            contact_form = True
        if forms.get("booking_form"):
            booking = True

    return ContactInfo(
        emails=sorted(all_emails),
        phones=sorted(all_phones),
        contact_form=contact_form,
        booking=booking,
    )


def _merge_social(page_results: list[dict]) -> SocialLinks:
    """Merge social links across pages — first occurrence per platform wins."""
    merged: dict[str, str] = {}

    for page in page_results:
        social = page.get("social", {})
        for platform, url in social.items():
            if platform not in merged and url:
                merged[platform] = url

    return SocialLinks(
        linkedin=merged.get("linkedin", ""),
        facebook=merged.get("facebook", ""),
        instagram=merged.get("instagram", ""),
        twitter=merged.get("twitter", ""),
        youtube=merged.get("youtube", ""),
        tiktok=merged.get("tiktok", ""),
        github=merged.get("github", ""),
    )


def _merge_services(page_results: list[dict]) -> list[str]:
    """Merge and deduplicate service names across pages."""
    seen: set[str] = set()
    services: list[str] = []

    for page in page_results:
        for svc in page.get("services", []):
            if svc not in seen:
                seen.add(svc)
                services.append(svc)

    return services


def _merge_technology(page_results: list[dict]) -> TechnologyStack:
    """Merge technology detections across pages — deduplicated."""
    cms = ""
    analytics: set[str] = set()
    widgets: set[str] = set()
    booking: set[str] = set()

    for page in page_results:
        tech = page.get("technology", {})
        if not cms and tech.get("cms"):
            cms = tech["cms"]
        analytics.update(tech.get("analytics", []))
        widgets.update(tech.get("widgets", []))
        booking.update(tech.get("booking", []))

    return TechnologyStack(
        cms=cms,
        analytics=sorted(analytics),
        widgets=sorted(widgets),
        booking=sorted(booking),
    )


def _merge_seo(page_results: list[dict]) -> SEOInfo:
    """Extract SEO info from the homepage (first result)."""
    if not page_results:
        return SEOInfo()

    # Prefer homepage metadata (first page is always homepage)
    meta = page_results[0].get("metadata", {})
    return SEOInfo(
        title=meta.get("title", ""),
        description=meta.get("description", "") or meta.get("og_description", ""),
        language=meta.get("language", ""),
    )


def _merge_pages_found(page_results: list[dict], homepage_url: str) -> PagesFound:
    """Detect which key page types were crawled."""
    crawled_urls = [p.get("url", "") for p in page_results]

    def _found(slug: str) -> bool:
        return any(slug in url.lower() for url in crawled_urls)

    return PagesFound(
        homepage=True,
        about=_found("about") or _found("company"),
        services=_found("service") or _found("solution"),
        pricing=_found("pricing") or _found("plan"),
        contact=_found("contact"),
    )


def _merge_features(page_results: list[dict]) -> FeatureFlags:
    """
    Phase 2: Merge and aggregate feature flags across pages.

    Returns True if feature is found on ANY page.
    """
    merged_features = {
        "has_contact_form": False,
        "has_booking": False,
        "has_live_chat": False,
        "has_pricing": False,
        "has_team_page": False,
        "has_faq": False,
        "has_careers": False,
        "has_whatsapp": False,
        "has_analytics": False,
        "has_crm": False,
        "has_marketing_pixels": False,
        "has_social_links": False,
        "has_multiple_locations": False,
    }

    for page in page_results:
        features = page.get("features", {})
        for key in merged_features:
            if features.get(key, False):
                merged_features[key] = True

    return FeatureFlags(**merged_features)


def merge(
    website_url: str,
    page_results: list[dict],
    pages_scanned: int,
    crawl_time_ms: int,
) -> WebsiteIntelligenceResponse:
    """
    Merge all per-page extraction results into the final API response.

    Phase 2: Now includes page classification and feature flags.

    Args:
        website_url: The original analyzed URL.
        page_results: List of per-page extraction result dicts.
        pages_scanned: Total number of pages that were crawled.
        crawl_time_ms: Total crawl duration in milliseconds.

    Returns:
        Fully populated WebsiteIntelligenceResponse.
    """
    logger.info("Merging results from %d page(s) for %s", len(page_results), website_url)

    return WebsiteIntelligenceResponse(
        website=website_url,
        company=_merge_company(page_results),
        contact=_merge_contact(page_results),
        social=_merge_social(page_results),
        services=_merge_services(page_results),
        technology=_merge_technology(page_results),
        seo=_merge_seo(page_results),
        pages=_merge_pages_found(page_results, website_url),
        features=_merge_features(page_results),
        crawl=CrawlMeta(
            pages_scanned=pages_scanned,
            crawl_time_ms=crawl_time_ms,
        ),
    )
