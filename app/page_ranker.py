"""
Intelligent page ranking and scoring system.

Assigns confidence scores to pages based on URL patterns and content signals.
Higher scores = more likely to contain important business information.

Responsibilities:
  - Score pages based on URL slugs
  - Rank pages by business value
  - Classify page type
  - Filter and prioritize pages
"""

import logging
from urllib.parse import urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PageScore:
    """Page ranking information."""
    url: str
    score: float
    page_type: str
    reason: str


# Page type scoring (higher = more important)
# Negative scores = pages to skip entirely (MVP: crawl only meaningful pages)
PAGE_TYPE_SCORES = {
    # Crawl these (MVP)
    "contact": 100,
    "about": 95,
    "services": 90,
    "team": 85,
    "pricing": 80,
    "treatments": 80,
    "locations": 75,
    "faq": 70,
    "booking": 65,
    
    # Skip these (negative scores)
    "blog": -500,        # Never crawl
    "news": -500,        # Never crawl
    "posts": -500,       # Never crawl
    "author": -500,      # Never crawl author pages
    "category": -500,    # Never crawl category pages
    "archives": -500,    # Never crawl archives
    "tag": -500,         # Never crawl tag pages
    "search": -500,      # Never crawl search
    "feed": -500,        # Never crawl feeds
    "rss": -500,         # Never crawl RSS
    "privacy": -500,     # Never crawl legal
    "terms": -500,       # Never crawl legal
    "legal": -500,       # Never crawl legal
    "cookie": -500,      # Never crawl legal
    "sitemap": -500,     # Never crawl
    "robots": -500,      # Never crawl
}

# Keywords for each page type
PAGE_TYPE_KEYWORDS = {
    "contact": ["contact", "contact-us", "get-in-touch", "reach-out", "support"],
    "about": ["about", "about-us", "who-we-are", "our-story", "company"],
    "services": ["services", "solutions", "offerings", "what-we-do"],
    "team": ["team", "our-team", "people", "staff", "leadership"],
    "pricing": ["pricing", "plans", "costs", "rates", "packages"],
    "treatments": ["treatments", "procedures", "services"],
    "locations": ["locations", "offices", "branches", "our-locations"],
    "faq": ["faq", "frequently-asked", "q&a"],
    "booking": ["book", "appointment", "schedule", "booking"],
    
    # Never crawl
    "blog": ["blog", "news", "article", "post", "posts", "insight"],
    "author": ["author", "author-page"],
    "category": ["category", "categories"],
    "archives": ["archive", "archives"],
    "tag": ["tag", "tags"],
    "search": ["search", "results"],
    "feed": ["feed", "rss"],
    "privacy": ["privacy", "privacy-policy"],
    "terms": ["terms", "terms-of-service", "legal"],
    "cookie": ["cookie", "cookies"],
    "sitemap": ["sitemap"],
    "robots": ["robots.txt"],
}

# Words to ignore in URL parsing
IGNORE_WORDS = {
    "the", "a", "an", "and", "or", "is", "are", "was", "were",
    "www", "index", "default", "home", "main"
}


def extract_url_slug(url: str) -> list[str]:
    """
    Extract meaningful path segments from URL.

    Examples:
        https://example.com/about-us -> ['about', 'us']
        https://example.com/our-services/consulting -> ['our', 'services', 'consulting']
        https://example.com/contact-form -> ['contact', 'form']

    Args:
        url: URL to extract slug from

    Returns:
        List of path segments (lowercased, hyphen-split)
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower().strip("/")

        if not path:
            return []

        segments = []
        for part in path.split("/"):
            # Split hyphenated words
            words = part.split("-")
            segments.extend(words)

        # Filter empty and short strings
        return [s for s in segments if s and len(s) > 1 and s not in IGNORE_WORDS]
    except Exception as exc:
        logger.warning("Error extracting slug from %s: %s", url, exc)
        return []


def detect_page_type(url: str) -> tuple[str, float]:
    """
    Detect page type from URL.

    Returns:
        (page_type, confidence) where confidence is 0.0-1.0
    """
    slug = extract_url_slug(url)

    if not slug:
        return "homepage", 0.8

    # Check each page type
    best_type = "unknown"
    best_score = 0.0

    for page_type, keywords in PAGE_TYPE_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in slug)

        if matches > 0:
            # Confidence increases with more matches
            confidence = min(0.99, 0.5 + (matches * 0.25))

            if confidence > best_score:
                best_score = confidence
                best_type = page_type

    return best_type, best_score


def score_page(url: str) -> PageScore:
    """
    Score a single page based on URL patterns.

    Args:
        url: URL to score

    Returns:
        PageScore with score (0-100), page type, and reason
    """
    # Detect page type
    page_type, type_confidence = detect_page_type(url)

    # Get base score for page type
    base_score = PAGE_TYPE_SCORES.get(page_type, 0)

    # Apply confidence modifier (reduce score if low confidence)
    if type_confidence < 0.6:
        base_score *= 0.5

    # For negative scores (pages to skip), keep them negative
    if base_score < 0:
        final_score = base_score
    else:
        # Normalize positive scores to 0-100 range
        final_score = max(0, min(100, base_score))

    reason = f"Page type: {page_type} (confidence: {type_confidence:.0%})"

    return PageScore(
        url=url,
        score=final_score,
        page_type=page_type,
        reason=reason,
    )


def rank_pages(urls: list[str], max_pages: int = 10) -> list[str]:
    """
    Rank and filter pages by business importance.

    Args:
        urls: List of URLs to rank
        max_pages: Maximum number of pages to return

    Returns:
        Top-ranked URLs (sorted by score descending)
    """
    # Score all pages
    scored_pages = [score_page(url) for url in urls]

    # Filter negative scores (skip unimportant pages)
    filtered = [sp for sp in scored_pages if sp.score > 0]

    # Sort by score (descending)
    ranked = sorted(filtered, key=lambda x: x.score, reverse=True)

    # Log results
    logger.info("Ranked %d pages (top %d):", len(ranked), max_pages)
    for i, sp in enumerate(ranked[:max_pages], 1):
        logger.info(
            "  %d. %s (score: %.0f, type: %s)",
            i, sp.url, sp.score, sp.page_type
        )

    # Return top URLs only
    return [sp.url for sp in ranked[:max_pages]]


def get_page_type(url: str) -> str:
    """Get page type without scoring."""
    page_type, _ = detect_page_type(url)
    return page_type
