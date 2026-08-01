"""
Colab terminal-based runner for Website Intelligence Service.

Accepts user URL input from terminal (no frontend, no server).
Processes URLs directly and returns structured intelligence as JSON.

Usage:
    python colab_runner.py
"""

import asyncio
import sys
import json
import logging
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
from app.schemas import AnalyzeRequest
from app.utils import normalize_url, validate_url
from app.crawler import crawl_page, crawl_pages
from app.page_selector import extract_internal_links, filter_important_pages
from app.extractor import extract_from_pages
from app.merger import merge


async def analyze_website(url: str) -> dict:
    """
    Analyze a website and return structured intelligence.

    Args:
        url: The website URL to analyze

    Returns:
        Dictionary with extracted intelligence or error information
    """
    try:
        # Validate and normalize URL
        url = normalize_url(url)
        if not validate_url(url):
            return {
                "success": False,
                "error": f"Invalid URL: {url}",
                "url": url,
            }

        logger.info("Starting analysis for: %s", url)

        # Step 1: Crawl homepage
        logger.info("Crawling homepage...")
        homepage = await crawl_page(url)

        if not homepage.success:
            return {
                "success": False,
                "error": f"Failed to crawl homepage: {homepage.error}",
                "url": url,
            }

        logger.info("✓ Homepage crawled successfully")

        # Step 2: Extract internal links
        logger.info("Extracting internal links...")
        internal_links = extract_internal_links(homepage.html, url)
        logger.info("Found %d internal links", len(internal_links))

        # Step 3: Filter to important pages
        logger.info("Filtering to important pages...")
        important_pages = filter_important_pages(internal_links, limit=settings.page_limit)
        logger.info("Selected %d important pages", len(important_pages))

        # Step 4: Crawl important pages
        if important_pages:
            logger.info("Crawling %d important pages...", len(important_pages))
            crawled_pages = await crawl_pages(important_pages)
            all_pages = [homepage] + crawled_pages
            logger.info("✓ Crawled %d pages total", len(all_pages))
        else:
            logger.info("No additional pages to crawl")
            all_pages = [homepage]

        # Step 5: Extract data from all pages
        logger.info("Extracting structured data from pages...")
        extractions = extract_from_pages(all_pages, url)
        logger.info("✓ Extracted data from %d pages", len(extractions))

        # Step 6: Merge and deduplicate
        logger.info("Merging and deduplicating results...")
        result = merge(extractions, url)
        logger.info("✓ Analysis complete")

        return {
            "success": True,
            "url": url,
            "pages_analyzed": len(all_pages),
            "data": result,
        }

    except Exception as exc:
        logger.error("Analysis failed: %s", str(exc), exc_info=True)
        return {
            "success": False,
            "error": f"Analysis failed: {str(exc)}",
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
                print(f"📊 Pages analyzed: {result['pages_analyzed']}")
                print("\n📋 Extracted Data:")
                print(json.dumps(result["data"], indent=2))
            else:
                print(f"❌ Analysis failed: {result['error']}")
            print("-" * 70 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Analysis interrupted. Goodbye!\n")
            sys.exit(0)
        except Exception as exc:
            print(f"\n❌ Error: {str(exc)}\n")
            logger.exception("Unexpected error")


if __name__ == "__main__":
    print("\n🚀 Starting Website Intelligence Service...")
    print(f"✓ FastAPI {settings.app_name} v{settings.app_version}\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", str(exc), exc_info=True)
        sys.exit(1)
