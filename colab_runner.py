"""
Terminal-based runner for Website Intelligence Service V3.

Accepts user URL input from terminal (no frontend, no server).
Processes URLs directly and returns structured evidence as JSON.

V3 Pipeline (Evidence Collection):
  1. Validate + normalize URL
  2. Crawl homepage
  3. Extract + filter important internal links
  4. Crawl important pages concurrently
  5. Extract evidence from each page (NEW: V3)
  6. Aggregate evidence by page type (NEW: V3)
  7. Return evidence JSON (no business interpretation)

Usage:
    python colab_runner.py
"""

import asyncio
import sys
import json
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Set event loop policy for Windows compatibility (harmless on Linux/Colab)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import application modules
from app.config import settings
from app.utils import normalize_url, validate_url
from app.url_handler import extract_root_domain
from app.sitemap_discovery import get_sitemap_urls
from app.crawler import crawl_page, crawl_pages
from app.page_selector import extract_internal_links, filter_important_pages
from app.evidence_extractor import PageEvidenceExtractor
from app.evidence_aggregator import EvidenceAggregator


async def analyze_website(url: str) -> dict:
    """
    Analyze a website and collect structured evidence (V3).

    V3 Pipeline:
      1. Validate + normalize URL
      2. Crawl homepage
      3. Extract + filter important internal links
      4. Crawl important pages concurrently
      5. Extract evidence from each page (NEW)
      6. Aggregate evidence by page type (NEW)
      7. Return evidence JSON

    Args:
        url: The website URL to analyze

    Returns:
        Dictionary with extracted evidence or error information
    """
    start_ms = time.monotonic()

    try:
        # ── Step 1: Validate URL ──────────────────────────────────────────
        normalized = normalize_url(url)
        is_valid, error_msg = validate_url(normalized)
        if not is_valid:
            logger.warning("Invalid URL submitted: %s — %s", url, error_msg)
            return {
                "success": False,
                "error": "Invalid URL",
                "details": error_msg,
                "url": url,
            }

        logger.info("Starting evidence collection for: %s", normalized)

        # ── Step 2: Crawl homepage ────────────────────────────────────────
        logger.info("Crawling homepage...")
        homepage = await crawl_page(normalized, timeout=settings.timeout_seconds)

        if not homepage.success:
            logger.error("Homepage crawl failed for %s: %s", normalized, homepage.error)
            return {
                "success": False,
                "error": "Unable to crawl website",
                "details": homepage.error,
                "url": normalized,
            }

        logger.info("✓ Homepage crawled successfully")

        # ── Step 3: Find important pages ──────────────────────────────────
        root_domain = extract_root_domain(normalized)
        logger.info("Discovering important pages from: %s", root_domain)

        # Try to get URLs from sitemap first
        logger.info("Attempting to discover pages from sitemap...")
        sitemap_urls = await get_sitemap_urls(root_domain, timeout=settings.timeout_seconds)

        # Also extract links from homepage
        logger.info("Extracting internal links...")
        internal_links = extract_internal_links(homepage.html, normalized)
        logger.info("Found %d internal links", len(internal_links))

        # Combine sitemap URLs with internal links (deduplicate)
        all_candidate_urls = list(set(sitemap_urls) | set(internal_links))
        logger.info("Discovered %d candidate pages (from sitemap + homepage links)", len(all_candidate_urls))

        # Rank and filter to important pages
        logger.info("Filtering to important pages...")
        important_urls = filter_important_pages(all_candidate_urls, max_pages=settings.max_pages)
        logger.info("Found %d important page(s) to crawl", len(important_urls))

        # ── Step 4: Crawl important pages ─────────────────────────────────
        additional_pages = await crawl_pages(
            important_urls,
            concurrency=settings.concurrency,
            timeout=settings.timeout_seconds,
        )

        all_pages = [homepage] + additional_pages
        logger.info("✓ Crawled %d pages total", len(all_pages))

        # ── Step 5: Extract evidence from each page (V3 NEW) ───────────────
        logger.info("Extracting evidence from pages (V3)...")
        aggregator = EvidenceAggregator(normalized)

        for page in all_pages:
            if page.success:
                extractor = PageEvidenceExtractor(page)
                evidence = extractor.extract()
                if evidence:
                    aggregator.add_page_evidence(evidence)

        # ── Step 6: Build response (V3 NEW) ───────────────────────────────
        crawl_time_ms = int((time.monotonic() - start_ms) * 1000)
        response = aggregator.build_response(crawl_time_ms)

        logger.info(
            "Evidence collection complete for %s — %d page(s) extracted in %dms",
            normalized, aggregator.pages_extracted, crawl_time_ms,
        )

        return {
            "success": True,
            "url": normalized,
            "pages_scanned": aggregator.pages_scanned,
            "pages_extracted": aggregator.pages_extracted,
            "crawl_time_ms": crawl_time_ms,
            "data": response,
        }

    except Exception as exc:
        logger.error("Analysis failed: %s", str(exc), exc_info=True)
        return {
            "success": False,
            "error": "Analysis failed",
            "details": str(exc),
            "url": url,
        }


async def main():
    """Main terminal loop."""
    print("\n" + "=" * 70)
    print(f"  {settings.app_name} v{settings.app_version} — Evidence Collection Engine (V3)")
    print("=" * 70)
    print("\n📍 Enter website URLs to analyze (one per line)")
    print("⚠️  Type 'exit' or 'quit' to stop\n")

    while True:
        try:
            # Get user input
            user_input = input("🔗 Enter URL: ").strip()

            # Check for exit commands
            if user_input.lower() in ("exit", "quit", "q", ""):
                if user_input.lower() != "":
                    print("\n👋 Goodbye!\n")
                break

            # Analyze the website
            print("\n⏳ Analyzing...\n")
            result = await analyze_website(user_input)

            # Display results
            print("\n" + "-" * 70)
            if result["success"]:
                print(f"✅ Evidence collection successful for: {result['url']}")
                print(f"📊 Pages scanned: {result['pages_scanned']}")
                print(f"📄 Pages extracted: {result['pages_extracted']}")
                print(f"⏱️  Crawl time: {result['crawl_time_ms']}ms")

                # Convert response to dict if needed
                response = result["data"]
                if hasattr(response, "model_dump"):
                    response = response.model_dump()

                # Display V3 evidence-based summary
                print("\n📋 Evidence Found:")
                
                if response.get("homepage"):
                    print("   ✓ Homepage evidence extracted")
                    homepage = response["homepage"]
                    if homepage.get("emails"):
                        print(f"     - {len(homepage['emails'])} email(s)")
                    if homepage.get("phones"):
                        print(f"     - {len(homepage['phones'])} phone(s)")
                    if homepage.get("social_links"):
                        print(f"     - {len(homepage['social_links'])} social link(s)")

                if response.get("contact"):
                    print("   ✓ Contact page evidence extracted")
                    contact = response["contact"]
                    if contact.get("contact_forms"):
                        print(f"     - {len(contact['contact_forms'])} contact form(s)")
                    if contact.get("phones"):
                        print(f"     - {len(contact['phones'])} phone(s)")
                    if contact.get("addresses"):
                        print(f"     - {len(contact['addresses'])} address(es)")

                if response.get("services"):
                    print("   ✓ Services page evidence extracted")
                    services = response["services"]
                    if services.get("headings"):
                        print(f"     - {len(services['headings'])} heading(s)")
                    if services.get("cards"):
                        print(f"     - {len(services['cards'])} card(s)")

                if response.get("team"):
                    print("   ✓ Team page evidence extracted")
                    team = response["team"]
                    if team.get("cards"):
                        print(f"     - {len(team['cards'])} team card(s)")

                if response.get("technology"):
                    print(f"   ✓ Technology detected: {len(response['technology'])} tech(s)")
                    for tech in response["technology"][:5]:
                        print(f"     - {tech['name']} ({tech['category']})")

                # Display evidence samples
                print("\n📌 Evidence Samples:")
                
                if response.get("homepage") and response["homepage"].get("emails"):
                    emails = response["homepage"]["emails"][:2]
                    print("   Emails (with source tracking):")
                    for email in emails:
                        print(f"     • {email['value']} (method: {email['method']}, confidence: {email['confidence']:.0%})")
                
                if response.get("contact") and response["contact"].get("phones"):
                    phones = response["contact"]["phones"][:2]
                    print("   Phones (with source tracking):")
                    for phone in phones:
                        print(f"     • {phone['value']} (method: {phone['method']}, confidence: {phone['confidence']:.0%})")

                if response.get("contact") and response["contact"].get("contact_forms"):
                    forms = response["contact"]["contact_forms"][:1]
                    print("   Contact Forms:")
                    for form in forms:
                        print(f"     • Action: {form['action']}, Method: {form['method']}")
                        print(f"       Fields: {', '.join(form['input_names'][:3])}")

                # Full JSON output
                print("\n📄 Full Response (V3 Evidence JSON):")
                print(json.dumps(response, indent=2, default=str))
            else:
                print(f"❌ Analysis failed")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                if "details" in result:
                    print(f"   Details: {result['details']}")
            print("-" * 70 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Analysis interrupted. Goodbye!\n")
            sys.exit(0)
        except Exception as exc:
            print(f"\n❌ Error: {str(exc)}\n")
            logger.exception("Unexpected error in main loop")


if __name__ == "__main__":
    print("\n🚀 Starting Website Intelligence Service V3...")
    print(f"✓ {settings.app_name} v{settings.app_version} — Evidence Collection Engine\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", str(exc), exc_info=True)
        print(f"\n❌ Fatal error: {str(exc)}\n")
        sys.exit(1)
