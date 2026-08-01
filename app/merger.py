"""
Phase 4 Merger - Business-centric response aggregation.

Merges per-page extraction results into business-centric response structure.
"""

import logging
from datetime import datetime
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
    SummaryMetrics,
    VerifiedContact,
    VerifiedAddress,
    PresenceInfo,
    CapabilityStack,
    DiscoveryMetadata,
)
from app.constants.keywords import IMPORTANT_SLUGS

logger = logging.getLogger(__name__)


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
        industry="",
    )


def _merge_verified_contacts(page_results: list[dict]) -> list[VerifiedContact]:
    """
    Phase 4: Create verified contact list with confidence scores.
    """
    contacts = []
    seen = set()

    # Process emails
    for page in page_results:
        for email in page.get("emails", []):
            if email not in seen:
                seen.add(email)
                # Try to find confidence score from page_classification
                confidence = 0.85  # Default confidence
                source = "visible"

                # Check if from schema
                for schema in page.get("schema", []):
                    if schema.get("email") == email:
                        confidence = 0.99
                        source = "schema"
                        break

                contacts.append(
                    VerifiedContact(
                        value=email,
                        confidence=confidence,
                        source=source,
                        type="email",
                    )
                )

    # Process phones
    for page in page_results:
        for phone in page.get("phones", []):
            if phone not in seen:
                seen.add(phone)
                confidence = 0.85
                source = "visible"

                # Check if from schema
                for schema in page.get("schema", []):
                    if schema.get("telephone") == phone:
                        confidence = 0.93
                        source = "schema"
                        break

                contacts.append(
                    VerifiedContact(
                        value=phone,
                        confidence=confidence,
                        source=source,
                        type="phone",
                    )
                )

    return contacts


def _merge_addresses(page_results: list[dict]) -> list[VerifiedAddress]:
    """
    Phase 4: Extract and merge addresses with confidence.
    """
    addresses = []
    seen = set()

    for page in page_results:
        # Try to find addresses from extractors
        for schema in page.get("schema", []):
            if schema.get("@type") == "PostalAddress":
                addr = schema.get("address", "")
                if addr and addr not in seen:
                    seen.add(addr)
                    addresses.append(
                        VerifiedAddress(
                            value=addr,
                            confidence=0.99,
                            source="schema",
                            is_primary=len(addresses) == 0,  # First is primary
                        )
                    )

    return addresses


def _merge_social(page_results: list[dict]) -> dict[str, str]:
    """Phase 4: Merge social links across pages."""
    merged: dict[str, str] = {}

    for page in page_results:
        social = page.get("social", {})
        for platform, url in social.items():
            if platform not in merged and url:
                merged[platform] = url

    return merged


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
    """Merge technology detections across pages."""
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


def _merge_features(page_results: list[dict]) -> FeatureFlags:
    """Phase 4: Merge feature flags (OR logic across pages)."""
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


def _calculate_data_quality_score(page_results: list[dict]) -> float:
    """
    Phase 4: Calculate overall data quality score (0.0-1.0).
    
    Based on:
    - Number of extraction sources
    - Average confidence across data
    - Number of pages with data
    """
    if not page_results:
        return 0.0

    # Count pages with various data types
    pages_with_emails = sum(1 for p in page_results if p.get("emails"))
    pages_with_phones = sum(1 for p in page_results if p.get("phones"))
    pages_with_company = sum(1 for p in page_results if p.get("company", {}).get("name"))
    pages_with_tech = sum(1 for p in page_results if p.get("technology", {}).get("cms"))

    data_points_found = bool(pages_with_emails) + bool(pages_with_phones) + bool(pages_with_company) + bool(pages_with_tech)

    # Calculate average confidence
    confidences = []
    for page in page_results:
        page_class = page.get("page_classification", {})
        if page_class.get("confidence"):
            confidences.append(page_class["confidence"])

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

    # Combine: 50% from data variety, 50% from confidence
    quality_score = (data_points_found / 4.0) * 0.5 + avg_confidence * 0.5
    return round(min(0.99, quality_score), 2)


def _extract_key_features(page_results: list[dict], services: list[str]) -> list[str]:
    """
    Phase 4: Extract top 3-5 key features for summary.
    
    Based on features detected + services mentioned.
    """
    features = []
    feature_flags = _merge_features(page_results)

    # Add features in priority order
    priority_features = [
        ("Live Chat Support", feature_flags.has_live_chat),
        ("Booking System", feature_flags.has_booking),
        ("Contact Form", feature_flags.has_contact_form),
        ("Pricing Information", feature_flags.has_pricing),
        ("Team/Staff Directory", feature_flags.has_team_page),
        ("FAQ Section", feature_flags.has_faq),
        ("Multiple Locations", feature_flags.has_multiple_locations),
    ]

    for feature_name, is_present in priority_features:
        if is_present:
            features.append(feature_name)
            if len(features) >= 5:  # Limit to 5 features
                break

    # Add top service if available
    if services and len(features) < 5:
        features.append(services[0])

    return features


def _build_summary(
    website_url: str,
    company: CompanyInfo,
    contacts: list[VerifiedContact],
    services: list[str],
    addresses: list[VerifiedAddress],
    page_results: list[dict],
) -> SummaryMetrics:
    """Phase 4: Build high-level business summary."""
    # Extract key features
    key_features = _extract_key_features(page_results, services)

    # Count unique contact methods
    contact_methods = len(set(c.value for c in contacts))

    # Extract locations
    locations = len(addresses) or 1

    # Extract team size (from page_classification results)
    team_size = 0
    for page in page_results:
        # This would be populated by team extraction in Phase 3
        pass

    # Calculate quality score
    quality_score = _calculate_data_quality_score(page_results)

    return SummaryMetrics(
        business_name=company.name or urlparse(website_url).netloc,
        tagline=company.tagline,
        primary_industry=company.industry,
        contact_methods_found=contact_methods,
        locations_count=locations,
        key_features=key_features,
        data_quality_score=quality_score,
        team_size_estimated=team_size,
    )


def _build_presence(
    website_url: str,
    contacts: list[VerifiedContact],
    addresses: list[VerifiedAddress],
    social: dict[str, str],
) -> PresenceInfo:
    """Phase 4: Build online presence section."""
    return PresenceInfo(
        website_url=website_url,
        verified_contacts=contacts,
        addresses=addresses,
        social_profiles=social,
    )


def _build_capabilities(
    services: list[str],
    page_results: list[dict],
    tech_stack: TechnologyStack,
) -> CapabilityStack:
    """Phase 4: Build capabilities section."""
    feature_flags = _merge_features(page_results)

    return CapabilityStack(
        services=services,
        features=feature_flags,
        technology=tech_stack,
        team_members=[],  # Would be populated by team extraction
    )


def _build_discovery(
    website_url: str,
    page_results: list[dict],
    pages_scanned: int,
    crawl_time_ms: int,
) -> DiscoveryMetadata:
    """Phase 4: Build discovery metadata."""
    pages_crawled = [p.get("url", "") for p in page_results]

    # Build confidence summary by data type
    confidence_summary = {
        "overall": _calculate_data_quality_score(page_results),
        "pages": sum(p.get("page_classification", {}).get("confidence", 0) for p in page_results) / max(1, len(page_results)),
    }

    # Build data sources (which pages had which data)
    data_sources = {}
    for page in page_results:
        url = page.get("url", "")
        if page.get("emails"):
            if "emails" not in data_sources:
                data_sources["emails"] = []
            data_sources["emails"].append(url)
        if page.get("phones"):
            if "phones" not in data_sources:
                data_sources["phones"] = []
            data_sources["phones"].append(url)

    return DiscoveryMetadata(
        pages_crawled=pages_crawled,
        crawl_time_ms=crawl_time_ms,
        last_updated=datetime.now(),
        confidence_summary=confidence_summary,
        data_sources=data_sources,
    )


def merge(
    website_url: str,
    page_results: list[dict],
    pages_scanned: int,
    crawl_time_ms: int,
) -> WebsiteIntelligenceResponse:
    """
    Phase 4: Merge all per-page extraction results into business-centric response.

    Args:
        website_url: The original analyzed URL.
        page_results: List of per-page extraction result dicts.
        pages_scanned: Total number of pages that were crawled.
        crawl_time_ms: Total crawl duration in milliseconds.

    Returns:
        WebsiteIntelligenceResponse with business-centric structure.
    """
    logger.info("Phase 4: Merging results into business-centric response for %s", website_url)

    # Phase 4: Aggregate data
    company = _merge_company(page_results)
    contacts = _merge_verified_contacts(page_results)
    addresses = _merge_addresses(page_results)
    social = _merge_social(page_results)
    services = _merge_services(page_results)
    tech_stack = _merge_technology(page_results)

    # Phase 4: Build business-centric sections
    summary = _build_summary(website_url, company, contacts, services, addresses, page_results)
    presence = _build_presence(website_url, contacts, addresses, social)
    capabilities = _build_capabilities(services, page_results, tech_stack)
    discovery = _build_discovery(website_url, page_results, pages_scanned, crawl_time_ms)

    return WebsiteIntelligenceResponse(
        summary=summary,
        presence=presence,
        capabilities=capabilities,
        discovery=discovery,
    )
