"""
Colab terminal-based runner for Website Intelligence Service.

Accepts user URL input from terminal (no frontend, no server).
Processes URLs directly and returns structured intelligence as JSON.

Pipeline:
  1. Validate + normalize URL
  2. Crawl homepage
  3. Extract + filter important internal links
  4. Crawl important pages concurrently
  5. Run all extractors over every page
  6. Merge + deduplicate results
  7. Return normalized JSON

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
from app.extractor import extract_from_pages
from app.merger import merge


async def analyze_website(url: str) -> dict:
    """
    Analyze a website and return structured intelligence.

    Pipeline:
      1. Validate + normalize URL
      2. Crawl homepage
      3. Extract + filter important internal links
      4. Crawl important pages concurrently
      5. Run all extractors over every page
      6. Merge + deduplicate results
      7. Return normalized JSON

    Args:
        url: The website URL to analyze

    Returns:
        Dictionary with extracted intelligence or error information
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

        logger.info("Starting analysis for: %s", normalized)

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
        pages_scanned = sum(1 for p in all_pages if p.success)
        logger.info("✓ Crawled %d pages total (%d successful)", len(all_pages), pages_scanned)

        # ── Step 5: Extract data ──────────────────────────────────────────
        logger.info("Extracting structured data from pages...")
        page_results = extract_from_pages(all_pages)
        logger.info("✓ Extracted data from %d page(s)", len(page_results))

        # ── Step 6: Merge results ─────────────────────────────────────────
        logger.info("Merging and deduplicating results...")
        crawl_time_ms = int((time.monotonic() - start_ms) * 1000)
        response = merge(
            website_url=normalized,
            page_results=page_results,
            pages_scanned=pages_scanned,
            crawl_time_ms=crawl_time_ms,
        )

        logger.info(
            "Analysis complete for %s — %d page(s) in %dms",
            normalized, pages_scanned, crawl_time_ms,
        )

        return {
            "success": True,
            "url": normalized,
            "pages_scanned": pages_scanned,
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
    """Main terminal loop for Colab."""
    print("\n" + "=" * 70)
    print(f"  {settings.app_name} v{settings.app_version}")
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
                print(f"✅ Analysis successful for: {result['url']}")
                print(f"📊 Pages scanned: {result['pages_scanned']}")
                print(f"⏱️  Crawl time: {result['crawl_time_ms']}ms")
                print("\n📋 Extracted Data:")
                # Convert response object to dict if needed
                data = result["data"]
                if hasattr(data, "model_dump"):
                    data = data.model_dump()
                print(json.dumps(data, indent=2, default=str))
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
    print("\n🚀 Starting Website Intelligence Service...")
    print(f"✓ {settings.app_name} v{settings.app_version}\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", str(exc), exc_info=True)
        print(f"\n❌ Fatal error: {str(exc)}\n")
        sys.exit(1)
