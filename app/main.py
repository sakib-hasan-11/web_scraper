"""
Website Intelligence Service — FastAPI application entry point.

Endpoints:
  POST /analyze   — analyze a website and return structured JSON
  GET  /health    — health check
  GET  /version   — application version
  GET  /          — serve the frontend UI
"""

# Windows fix: Playwright requires ProactorEventLoop to launch browser subprocesses.
# SelectorEventLoop (Windows default) raises NotImplementedError on subprocess_exec.
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.schemas import AnalyzeRequest, ErrorResponse
from app.utils import normalize_url, validate_url
from app.url_handler import extract_root_domain
from app.sitemap_discovery import get_sitemap_urls
from app.crawler import crawl_page, crawl_pages
from app.page_selector import extract_internal_links, filter_important_pages
from app.evidence_extractor import PageEvidenceExtractor
from app.evidence_aggregator import EvidenceAggregator

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Accepts a website URL and returns structured business intelligence as JSON.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Meta"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/version", tags=["Meta"])
async def version() -> dict:
    """Return the application version."""
    return {"version": settings.app_version}


@app.get("/", response_class=HTMLResponse, tags=["Meta"], include_in_schema=False)
async def index():
    """Serve the frontend UI."""
    index_path = _frontend_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>Website Intelligence Service</h1><p>Frontend not found.</p>"
    )


@app.post("/analyze", tags=["Intelligence"])
async def analyze(request: AnalyzeRequest):
    """
    Analyze a website and collect structured evidence.

    Pipeline:
      1. Validate + normalize URL
      2. Crawl homepage
      3. Extract + filter important internal links
      4. Crawl important pages concurrently
      5. Extract evidence from each page
      6. Aggregate evidence by page type
      7. Return JSON for LLM processing
    """
    start_ms = time.monotonic()

    # ── Step 1: Validate URL ──────────────────────────────────────────────
    normalized = normalize_url(request.url)
    is_valid, error_msg = validate_url(normalized)
    if not is_valid:
        logger.warning("Invalid URL submitted: %s — %s", request.url, error_msg)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(error="Invalid URL", details=error_msg).model_dump(),
        )

    logger.info("Starting evidence collection for: %s", normalized)

    # ── Step 2: Crawl homepage ─────────────────────────────────────────────
    homepage = await crawl_page(normalized, timeout=settings.timeout_seconds)
    if not homepage.success:
        logger.error("Homepage crawl failed for %s: %s", normalized, homepage.error)
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error="Unable to crawl website",
                details=homepage.error,
            ).model_dump(),
        )

    # ── Step 3: Find important pages ──────────────────────────────────────
    root_domain = extract_root_domain(normalized)
    logger.info("Discovering important pages from: %s", root_domain)

    # Try to get URLs from sitemap first
    logger.info("Attempting to discover pages from sitemap...")
    sitemap_urls = await get_sitemap_urls(root_domain, timeout=settings.timeout_seconds)

    # Also extract links from homepage
    internal_links = extract_internal_links(homepage.html, normalized)

    # Combine sitemap URLs with internal links (deduplicate)
    all_candidate_urls = list(set(sitemap_urls) | set(internal_links))
    logger.info("Discovered %d candidate pages (from sitemap + homepage links)", len(all_candidate_urls))

    # Rank and filter to important pages
    important_urls = filter_important_pages(all_candidate_urls, max_pages=settings.max_pages)
    logger.info("Selected %d important page(s) to crawl", len(important_urls))

    # ── Step 4: Crawl important pages ─────────────────────────────────────
    additional_pages = await crawl_pages(
        important_urls,
        concurrency=settings.concurrency,
        timeout=settings.timeout_seconds,
    )

    all_pages = [homepage] + additional_pages

    # ── Step 5: Extract evidence from each page ───────────────────────────
    logger.info("Extracting evidence from %d crawled page(s)...", len(all_pages))
    aggregator = EvidenceAggregator(normalized, debug_mode=request.debug)
    extraction_start = time.monotonic()

    for page in all_pages:
        extractor = PageEvidenceExtractor(page)
        evidence = extractor.extract()
        if evidence:
            aggregator.add_page_evidence(evidence)

    # ── Step 6: Build response ────────────────────────────────────────────
    crawl_time_ms = int((time.monotonic() - start_ms) * 1000)
    extraction_time_ms = int((time.monotonic() - extraction_start) * 1000)
    response = aggregator.build_response(crawl_time_ms)
    
    # Add extraction time to debug if enabled
    if request.debug:
        response.crawl.extraction_time_ms = extraction_time_ms

    logger.info(
        "Evidence collection complete for %s — %d page(s) extracted in %dms",
        normalized, aggregator.pages_extracted, crawl_time_ms,
    )

    return response
