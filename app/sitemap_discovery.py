"""
Sitemap discovery and parsing.

Responsibilities:
  - Detect and fetch sitemap.xml and sitemap_index.xml
  - Parse XML sitemaps
  - Extract URLs from sitemaps
  - Handle sitemap errors gracefully
"""

import logging
import asyncio
from typing import Optional, Set
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)


async def discover_sitemaps(root_domain: str, timeout: int = 10) -> list[str]:
    """
    Discover sitemap URLs from a domain.

    Attempts:
    - /sitemap.xml
    - /sitemap_index.xml

    Args:
        root_domain: Root domain URL (e.g., https://example.com)
        timeout: Request timeout in seconds

    Returns:
        List of discovered sitemap URLs (empty if not found)
    """
    sitemap_urls = []
    root_domain = root_domain.rstrip("/")

    sitemap_candidates = [
        f"{root_domain}/sitemap.xml",
        f"{root_domain}/sitemap_index.xml",
    ]

    async with httpx.AsyncClient(timeout=timeout) as client:
        for sitemap_url in sitemap_candidates:
            try:
                logger.info("Checking for sitemap: %s", sitemap_url)
                response = await client.get(sitemap_url, follow_redirects=True)

                if response.status_code == 200:
                    logger.info("✓ Found sitemap: %s", sitemap_url)
                    sitemap_urls.append(sitemap_url)
                else:
                    logger.debug("Sitemap not found at %s (status %d)", sitemap_url, response.status_code)

            except Exception as exc:
                logger.debug("Error checking sitemap %s: %s", sitemap_url, exc)
                continue

    return sitemap_urls


async def fetch_sitemap_content(sitemap_url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch sitemap XML content.

    Args:
        sitemap_url: URL to sitemap
        timeout: Request timeout in seconds

    Returns:
        XML content as string, or None if failed
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(sitemap_url, follow_redirects=True)
            if response.status_code == 200:
                return response.text
    except Exception as exc:
        logger.warning("Failed to fetch sitemap %s: %s", sitemap_url, exc)

    return None


def parse_sitemap_urls(xml_content: str) -> Set[str]:
    """
    Parse URLs from sitemap XML.

    Handles:
    - Standard sitemap.xml (list of URLs)
    - Sitemap index (list of other sitemaps)

    Args:
        xml_content: XML content as string

    Returns:
        Set of URLs found in sitemap
    """
    urls: Set[str] = set()

    try:
        root = ET.fromstring(xml_content)

        # Define namespace
        namespace = {
            "ns": "http://www.sitemaps.org/schemas/sitemap/0.9"
        }

        # Try to find URL entries (standard sitemap)
        for url_elem in root.findall(".//ns:url/ns:loc", namespace):
            if url_elem.text:
                urls.add(url_elem.text.strip())

        # Try to find sitemap entries (sitemap index)
        for sitemap_elem in root.findall(".//ns:sitemap/ns:loc", namespace):
            if sitemap_elem.text:
                urls.add(sitemap_elem.text.strip())

        # Fallback: try without namespace
        if not urls:
            for url_elem in root.findall(".//url/loc"):
                if url_elem.text:
                    urls.add(url_elem.text.strip())

            for sitemap_elem in root.findall(".//sitemap/loc"):
                if sitemap_elem.text:
                    urls.add(sitemap_elem.text.strip())

        logger.info("Parsed %d URLs from sitemap", len(urls))

    except ET.ParseError as exc:
        logger.warning("Failed to parse sitemap XML: %s", exc)
    except Exception as exc:
        logger.warning("Error parsing sitemap: %s", exc)

    return urls


async def get_sitemap_urls(root_domain: str, timeout: int = 10) -> Set[str]:
    """
    Discover and parse all sitemap URLs from a domain.

    Handles sitemap index by recursively fetching child sitemaps.

    Args:
        root_domain: Root domain URL
        timeout: Request timeout in seconds

    Returns:
        Set of all URLs found in sitemaps
    """
    all_urls: Set[str] = set()
    processed: Set[str] = set()
    to_process: list[str] = []

    # Discover initial sitemaps
    sitemaps = await discover_sitemaps(root_domain, timeout)
    to_process.extend(sitemaps)

    # Process sitemaps (handle redirects and index files)
    while to_process:
        sitemap_url = to_process.pop(0)

        if sitemap_url in processed:
            continue

        processed.add(sitemap_url)

        logger.info("Processing sitemap: %s", sitemap_url)
        xml_content = await fetch_sitemap_content(sitemap_url, timeout)

        if xml_content:
            urls = parse_sitemap_urls(xml_content)

            # Check if these are regular URLs or other sitemaps
            for url in urls:
                if url.endswith(".xml"):
                    # This is likely another sitemap (from sitemap index)
                    if url not in processed:
                        to_process.append(url)
                else:
                    # This is a regular URL
                    all_urls.add(url)

    logger.info("Discovered %d URLs from sitemaps", len(all_urls))
    return all_urls
