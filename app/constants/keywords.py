"""
Keyword constants used across the application.

Centralised here to avoid magic strings scattered throughout the codebase.
"""

# ---------------------------------------------------------------------------
# Page Selector
# ---------------------------------------------------------------------------

IMPORTANT_SLUGS: tuple[str, ...] = (
    "about",
    "about-us",
    "about_us",
    "company",
    "our-company",
    "services",
    "our-services",
    "solutions",
    "our-solutions",
    "pricing",
    "plans",
    "contact",
    "contact-us",
    "contact_us",
    "team",
    "our-team",
    "staff",
    "leadership",
    "careers",
    "jobs",
    "book",
    "booking",
    "appointment",
    "appointments",
    "demo",
    "get-demo",
    "schedule",
)

IGNORE_SLUGS: tuple[str, ...] = (
    "blog",
    "news",
    "tag",
    "tags",
    "category",
    "categories",
    "privacy",
    "privacy-policy",
    "cookie",
    "cookies",
    "terms",
    "tos",
    "author",
    "search",
    "login",
    "signin",
    "sign-in",
    "register",
    "signup",
    "sign-up",
    "cart",
    "checkout",
    "dashboard",
    "admin",
    "feed",
    "rss",
    "sitemap",
    "wp-content",
    "wp-admin",
    "wp-json",
    "cdn",
    "assets",
    "static",
)

# ---------------------------------------------------------------------------
# Social Media Detection
# ---------------------------------------------------------------------------

SOCIAL_DOMAINS: dict[str, str] = {
    "linkedin.com": "linkedin",
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "instagram.com": "instagram",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "tiktok.com": "tiktok",
    "github.com": "github",
}

# ---------------------------------------------------------------------------
# Technology Fingerprinting
# ---------------------------------------------------------------------------

# Each entry: (tech_name, category, list_of_html_signatures)
# Signatures are substring patterns searched in the raw HTML.
TECH_SIGNATURES: list[tuple[str, str, list[str]]] = [
    # CMS
    ("WordPress", "cms", ["/wp-content/", "/wp-includes/", "wp-json"]),
    ("Shopify", "cms", ["cdn.shopify.com", "shopify.com/s/", "Shopify.theme"]),
    ("Webflow", "cms", ["webflow.com", "data-wf-page", "data-wf-site"]),
    ("Squarespace", "cms", ["squarespace.com", "static1.squarespace.com"]),
    ("Wix", "cms", ["wix.com", "wixstatic.com", "X-Wix-"]),
    ("Ghost", "cms", ["ghost.io", "content.ghost.io"]),
    # Analytics
    ("Google Analytics", "analytics", ["google-analytics.com", "gtag('config", "ga('create"]),
    ("Google Tag Manager", "analytics", ["googletagmanager.com", "GTM-"]),
    ("Meta Pixel", "analytics", ["connect.facebook.net", "fbq('init", "facebook-jssdk"]),
    ("Hotjar", "analytics", ["hotjar.com", "hj('create"]),
    ("Mixpanel", "analytics", ["mixpanel.com", "mixpanel.init"]),
    ("Segment", "analytics", ["cdn.segment.com", "analytics.load"]),
    # Widgets / Chat
    ("Intercom", "widgets", ["intercomcdn.com", "intercom.io", "Intercom("]),
    ("Zendesk", "widgets", ["zendesk.com", "zdassets.com", "zE("]),
    ("Drift", "widgets", ["js.driftt.com", "drift.com"]),
    ("Crisp", "widgets", ["client.crisp.chat", "CRISP_WEBSITE_ID"]),
    ("Tawk.to", "widgets", ["tawk.to", "embed.tawk.to"]),
    # Booking
    ("Calendly", "booking", ["calendly.com", "assets.calendly.com"]),
    ("Acuity Scheduling", "booking", ["acuityscheduling.com"]),
    ("SimplyBook", "booking", ["simplybook.me"]),
    ("HubSpot", "booking", ["js.hubspot.com", "hubspot.com", "hs-scripts.com"]),
    # Infrastructure
    ("Cloudflare", "widgets", ["cloudflare.com", "__cf_bm", "cf-ray"]),
    # Payments
    ("Stripe", "widgets", ["js.stripe.com", "stripe.com/v3"]),
]
