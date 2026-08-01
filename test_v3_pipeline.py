#!/usr/bin/env python
"""
Quick test script for colab_runner V3.

Tests basic functionality without interactive input.
"""

import asyncio
import sys
import json

from app.config import settings
from app.utils import normalize_url, validate_url
from app.url_handler import extract_root_domain
from app.sitemap_discovery import get_sitemap_urls
from app.crawler import crawl_page, crawl_pages
from app.page_selector import extract_internal_links, filter_important_pages
from app.evidence_extractor import PageEvidenceExtractor
from app.evidence_aggregator import EvidenceAggregator


async def test_evidence_pipeline(url: str = "https://example.com"):
    """Test the V3 evidence pipeline with a URL."""
    
    print(f"\n🧪 Testing V3 Evidence Pipeline")
    print(f"📍 URL: {url}\n")
    
    try:
        # Validate
        normalized = normalize_url(url)
        is_valid, error = validate_url(normalized)
        print(f"✓ URL validated: {normalized}")
        
        # Crawl homepage
        print(f"⏳ Crawling homepage...")
        homepage = await crawl_page(normalized, timeout=settings.timeout_seconds)
        
        if not homepage.success:
            print(f"❌ Failed to crawl: {homepage.error}")
            return
        
        print(f"✓ Homepage crawled ({len(homepage.html) if homepage.html else 0} bytes)")
        
        # Test evidence extraction
        print(f"⏳ Extracting evidence...")
        extractor = PageEvidenceExtractor(homepage)
        evidence = extractor.extract()
        
        if evidence:
            print(f"✓ Evidence extracted:")
            print(f"  - Title: {evidence.title}")
            print(f"  - Page type: {evidence.page_type}")
            print(f"  - Headings: {len(evidence.headings)}")
            print(f"  - Paragraphs: {len(evidence.paragraphs)}")
            print(f"  - Emails: {len(evidence.emails)}")
            print(f"  - Phones: {len(evidence.phones)}")
            print(f"  - Social links: {len(evidence.social_links)}")
            print(f"  - Forms: {len(evidence.contact_forms)} contact, {len(evidence.booking_forms)} booking")
            print(f"  - Scripts/Tech: {len(evidence.scripts)}")
            
            # Test aggregation
            print(f"⏳ Aggregating evidence...")
            aggregator = EvidenceAggregator(normalized)
            aggregator.add_page_evidence(evidence)
            response = aggregator.build_response(100)
            
            print(f"✓ Evidence aggregated:")
            print(f"  - Pages scanned: {response.crawl.pages_scanned}")
            print(f"  - Pages extracted: {response.crawl.pages_extracted}")
            
            # Show sample output
            print(f"\n✅ V3 Pipeline Test Successful!")
            print(f"\n📄 Sample Response Structure:")
            if response.homepage:
                print(f"  homepage: {{url, title, headings[], emails[], ...}}")
            if response.contact:
                print(f"  contact: {{url, emails[], phones[], forms[], ...}}")
            print(f"  technology: [{{name, category, confidence}}]")
            print(f"  crawl: {{pages_scanned, pages_extracted, crawl_time_ms}}")
            
        else:
            print(f"❌ No evidence extracted")
            
    except Exception as exc:
        print(f"❌ Error: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  Website Intelligence Service V3 — Evidence Pipeline Test")
    print("="*70)
    
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    
    try:
        asyncio.run(test_evidence_pipeline(url))
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted")
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ Test failed: {exc}")
        sys.exit(1)
