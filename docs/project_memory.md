# Project Memory — Website Intelligence Service

---

## Project Overview

A standalone FastAPI microservice that accepts a website URL, crawls important public pages, extracts structured business information (no LLM), and returns a compact JSON response.

**Version:** 1.0.0 (MVP)
**Purpose:** Feed structured company data into downstream LLM/CRM systems.
**Scope:** URL → JSON only. No auth, no DB, no queues, no AI.

---

## Current Architecture

```
POST /analyze
    │
    ▼
normalize_url + validate_url          [app/utils.py]
    │
    ▼
crawl_page (homepage)                 [app/crawler.py — Crawl4AI]
    │
    ▼
extract_internal_links                [app/page_selector.py]
filter_important_pages                [app/page_selector.py]
    │
    ▼
crawl_pages (concurrent, max 10)      [app/crawler.py]
    │
    ▼
extract_from_pages                    [app/extractor.py — orchestrator]
  ├── email.py
  ├── phone.py
  ├── social.py
  ├── metadata.py
  ├── company.py
  ├── services.py
  ├── forms.py
  ├── technology.py
  └── schema.py
    │
    ▼
merge()                               [app/merger.py]
    │
    ▼
WebsiteIntelligenceResponse           [app/models/response.py]
```

---

## Completed Features

- [x] FastAPI app with `/analyze`, `/health`, `/version` endpoints
- [x] URL normalization (HTTPS enforcement, trailing slash removal)
- [x] URL validation (reject localhost, IPs, invalid domains)
- [x] Homepage crawl via Crawl4AI (async, Playwright-based)
- [x] Internal link extraction (ignores mailto, tel, JS, anchors, external)
- [x] Important page detection (keyword slug matching)
- [x] Parallel page crawl (concurrency=5, timeout=15s, max=10 pages)
- [x] Email extractor (mailto links + regex, validated via email-validator)
- [x] Phone extractor (tel: links + PhoneNumberMatcher, E.164 normalisation)
- [x] Social extractor (LinkedIn, Facebook, Instagram, Twitter/X, YouTube, TikTok, GitHub)
- [x] Metadata extractor (title, description, language, H1/H2, OG, Twitter Card, canonical)
- [x] Company extractor (name from og:site_name/title, tagline, about paragraph)
- [x] Services extractor (section-scoped heading/list extraction)
- [x] Forms extractor (contact form, booking form, newsletter form, chat widget detection)
- [x] Technology extractor (CMS, analytics, widgets, booking tools via HTML signatures)
- [x] JSON-LD schema extractor (Organization, LocalBusiness, PostalAddress, etc.)
- [x] Merger (confidence priority: Schema > Visible > Metadata > Regex, deduplication)
- [x] Pydantic v2 response models matching spec
- [x] Frontend UI (URL input, loading state, structured display, raw JSON viewer)
- [x] CORS enabled (all origins, suitable for local dev)
- [x] Dockerfile for local Docker usage

---

## Pending Features

- [ ] Unit tests for core logic (page_selector, merger, individual extractors)
- [ ] `.env` file for local config overrides
- [ ] Industry detection (currently always empty — needs LLM or keyword DB)

---

## API Endpoints

| Method | Path       | Description                          |
|--------|-----------|--------------------------------------|
| POST   | /analyze  | Analyze a website, return JSON       |
| GET    | /health   | Returns `{"status": "ok"}`           |
| GET    | /version  | Returns `{"version": "1.0.0"}`       |
| GET    | /         | Serves frontend UI (index.html)      |

---

## Folder Structure

```
web_scraper/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + routes
│   ├── config.py            # Settings (pydantic-settings)
│   ├── schemas.py           # Request/response schemas
│   ├── utils.py             # URL normalization & validation
│   ├── crawler.py           # Crawl4AI wrapper
│   ├── page_selector.py     # Link extraction & filtering
│   ├── extractor.py         # Extraction orchestrator
│   ├── merger.py            # Result merge & deduplication
│   ├── constants/
│   │   ├── __init__.py
│   │   └── keywords.py      # All keyword constants
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── phone.py
│   │   ├── social.py
│   │   ├── metadata.py
│   │   ├── company.py
│   │   ├── services.py
│   │   ├── forms.py
│   │   ├── technology.py
│   │   └── schema.py
│   └── models/
│       ├── __init__.py
│       └── response.py      # Pydantic response models
├── frontend/
│   └── index.html           # Single-page frontend UI
├── docs/
│   ├── AGENT.md
│   ├── project_plan.md
│   └── project_memory.md    # This file
├── Dockerfile
├── README.md
└── requirements.txt
```

---

## Important Design Decisions

1. **No wappalyzer dependency** — Tech detection done manually via HTML signature patterns in `constants/keywords.py`. Avoids Node.js dependency.
2. **Crawl4AI for crawling** — Playwright-based headless browser handles JS-heavy sites better than httpx alone.
3. **Each extractor is independent** — All receive `(html, soup, url)` and return structured dicts. No extractor depends on another.
4. **Extraction orchestrator (`extractor.py`) is separate from merger** — Separation of concerns: extraction collects raw data, merging produces final output.
5. **Merger confidence order** — JSON-LD schema > visible content extractor > metadata tags > regex. This ensures authoritative structured data wins.
6. **IMPORTANT_SLUGS / IGNORE_SLUGS in constants** — All keyword decisions are in one place to avoid scattered magic strings.
7. **Frontend served via FastAPI StaticFiles** — Opens at `http://localhost:8000/` when server runs. Also works as standalone HTML file.
8. **Industry field is empty** — Cannot be reliably determined without LLM. Left as empty string per V1 scope.

---

## Known Issues

- None at initial implementation. To be updated as testing reveals issues.

---

## Future Ideas

- Unit tests for extractors, page_selector, merger
- `/analyze` async job system if long crawl times become an issue
- Industry classification via keyword DB
- Confidence scores per field in response
- Support for multiple URLs in one request

---

## Git History Summary

| Commit | Description |
|--------|-------------|
| feat: implement V1 MVP — full website intelligence pipeline | Initial working implementation |
