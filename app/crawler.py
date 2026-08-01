"""
Crawler module — wraps Crawl4AI to fetch page HTML, markdown, and metadata.

Responsibilities:
- Crawl a single page (homepage).
- Crawl multiple pages concurrently with a configurable limit.

Does NOT perform any data extraction.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

logger = logging.getLogger(__name__)


@dataclass
class CrawledPage:
    """Holds the raw output of a single crawled page."""

    url: str
    html: str = ""
    markdown: str = ""
    success: bool = False
    error: str = ""


async def crawl_page(url: str, timeout: int = 15) -> CrawledPage:
    """
    Crawl a single URL and return its raw HTML and markdown.

    Args:
        url: The URL to crawl.
        timeout: Page load timeout in seconds.

    Returns:
        CrawledPage with html, markdown, and success flag.
    """
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(page_timeout=timeout * 1000)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)

        if result.success:
            return CrawledPage(
                url=url,
                html=result.html or "",
                markdown=result.markdown or "",
                success=True,
            )
        else:
            logger.warning("Crawl failed for %s: %s", url, result.error_message)
            return CrawledPage(url=url, success=False, error=result.error_message or "Unknown error")

    except Exception as exc:
        logger.exception("Unexpected error crawling %s", url)
        return CrawledPage(url=url, success=False, error=str(exc))


async def crawl_pages(
    urls: list[str],
    concurrency: int = 5,
    timeout: int = 15,
) -> list[CrawledPage]:
    """
    Crawl multiple URLs concurrently.

    Failures are skipped — they do not raise exceptions.

    Args:
        urls: List of URLs to crawl.
        concurrency: Maximum number of simultaneous crawls.
        timeout: Per-page timeout in seconds.

    Returns:
        List of CrawledPage objects (including failed ones).
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _crawl_with_limit(url: str) -> CrawledPage:
        async with semaphore:
            return await crawl_page(url, timeout=timeout)

    tasks = [_crawl_with_limit(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)
