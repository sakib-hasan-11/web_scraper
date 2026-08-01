# Website Intelligence Service V3 — Evidence Extraction Engine

## Overview

**V3 is a fundamental architectural shift** from an AI-inference engine to a pure evidence-collection engine.

### What Changed?

**V1-V2:** Service attempted to understand businesses
- Business classification
- Lead scoring
- Service identification
- Company profiling
- Opportunity detection

**V3:** Service collects structured evidence only
- No business interpretation
- No inference
- No lead scores
- No business profiles
- Pure evidence collection optimized for LLM consumption

---

## Philosophy: Separation of Concerns

### Website Intelligence Service V3 (This Project)

**Responsibility:** Collect structured evidence

**Input:** Website URL

**Process:**
1. Crawl website pages
2. Extract raw evidence (emails, headings, cards, tables, etc.)
3. Structure evidence with source/method/confidence
4. Return compact JSON

**Output:** Structured evidence grouped by page type

**Constraint:** NEVER interpret. NEVER infer. ONLY collect.

### Downstream LLM (Your AI System)

**Responsibility:** Interpret evidence and generate intelligence

**Input:** Structured evidence JSON from V3

**Process:**
1. Read evidence
2. Understand context
3. Generate business insights
4. Identify opportunities
5. Score leads
6. Extract intelligence

**Output:** Business insights, lead scores, opportunities

---

## Architecture Change

### Before (V1-V2)

```
Crawl
  ↓
Extract (feature detection, page classification)
  ↓
Merge (business logic, confidence scoring, lead scoring)
  ↓
Return (business profile, opportunities, lead score)
```

**Problems:**
- Service had business logic buried in extractors
- Multiple responsibilities in one system
- Hard to fix or improve inference
- LLM had to re-parse and re-interpret data
- Duplicate business logic in web service and LLM

### After (V3)

```
Crawl (unchanged)
  ↓
Extract → PageEvidence
  ↓
Aggregate (pure grouping, no logic)
  ↓
Return (structured evidence, no inference)
```

**Benefits:**
- Clean separation: Collection vs. Interpretation
- LLM gets high-quality structured data directly
- Easy to improve evidence collection
- Service stays deterministic
- No duplicate business logic
- LLM can reuse evidence for multiple analyses

---

## Response Format

### V2 Response (Business-Centric)

```json
{
  "summary": {
    "business_name": "...",
    "data_quality_score": 0.85,
    "key_features": [...]
  },
  "presence": {
    "website_url": "...",
    "verified_contacts": [...]
  },
  "capabilities": {
    "services": [...],
    "technology": [...]
  },
  "discovery": {...}
}
```

**Problem:** Service made decisions about what's "important"

### V3 Response (Evidence-Based)

```json
{
  "website_url": "...",
  "homepage": {
    "url": "...",
    "title": "...",
    "headings": [...],
    "paragraphs": [...],
    "cards": [...],
    "emails": [
      {
        "value": "info@example.com",
        "method": "mailto",
        "source": "https://example.com/",
        "confidence": 0.99
      }
    ],
    "forms": [...]
  },
  "contact": {...},
  "services": {...},
  "technology": [...],
  "crawl": {
    "pages_scanned": 5,
    "pages_extracted": 5,
    "crawl_time_ms": 8200
  }
}
```

**Benefit:** LLM gets all the evidence and can make decisions

---

## Page Evidence Model

Every crawled page produces the same structure: `PageEvidence`

```python
class PageEvidence:
    url: str
    page_type: str  # detected from URL/content
    
    # Metadata
    title: str
    meta_title: str
    meta_description: str
    
    # Structured Content
    headings: list[HeadingEvidence]      # H1-H6
    paragraphs: list[ParagraphEvidence]  # 50-800 chars, filtered
    lists: list[ListEvidence]            # UL, OL, DL
    tables: list[TableEvidence]          # Headers + Rows
    cards: list[CardEvidence]            # Repeating blocks
    
    # Contact Evidence
    emails: list[EvidenceItem]           # All emails with source
    phones: list[EvidenceItem]           # All phones with source
    addresses: list[EvidenceItem]        # All addresses
    forms: list[FormEvidence]            # All forms
    
    # Social & External
    social_links: list[EvidenceItem]     # All social profiles
    whatsapp_links: list[EvidenceItem]
    calendar_links: list[EvidenceItem]   # Calendly, Acuity, etc.
    
    # Technical
    schema_data: list[SchemaEvidence]    # Raw JSON-LD
    scripts: list[ScriptEvidence]        # Detected tech
```

### Uniform Structure

**Key benefit:** Every page has the same structure. LLM can process uniformly.

Example:
- Homepage has emails, social links, navigation
- Contact page has emails, phones, addresses, forms
- Services page has headings, cards, lists, pricing tables
- Team page has cards, headings, descriptions
- LLM processes them all with one algorithm

---

## Evidence Items

Every extracted piece includes:

```python
class EvidenceItem:
    value: str          # The actual data
    source: str         # URL where found
    method: str         # How extracted (mailto, tel, schema, link, regex, visible)
    confidence: float   # 0.0-1.0
```

Example:

```json
{
  "value": "info@example.com",
  "method": "mailto",
  "source": "https://example.com/",
  "confidence": 0.99
}
```

### Method Values

- `mailto` - From `<a href="mailto:">` link
- `tel` - From `<a href="tel:">` link
- `schema` - From JSON-LD structured data
- `link` - From regular hyperlink
- `regex` - From pattern matching in text
- `visible` - From visible page text
- `address_tag` - From `<address>` HTML tag
- `footer_*` - From footer section

### Confidence Scores

- `0.99` - Explicit markup (mailto:, tel:, schema)
- `0.95` - Strong signals (JSON-LD, footer links)
- `0.90` - Address tags, metadata
- `0.85` - Form fields, script detection
- `0.75` - Phone regex patterns
- `0.70` - Email patterns, opening hours text
- `0.50` - General text extraction

---

## No More Business Classification

### What Removed

`page_classifier.py` - REMOVED
- Don't classify pages by type
- URL-based type detection only

`feature_detector.py` - REMOVED
- Don't detect "has_booking" or "has_live_chat"
- Return detected scripts; let LLM decide

`merger.py` - REPLACED
- Old: Merged results with business logic
- New: Simple aggregation by page type

`confidence_engine.py` - NOT USED
- Global quality score removed
- Per-item confidence kept

### What Stayed

- `page_ranker.py` - Still ranks pages (deterministic, no interpretation)
- `crawler.py` - Crawls pages unchanged
- `sitemap_discovery.py` - Finds sitemaps unchanged
- All existing extractors - Return raw data, not interpreted

---

## Content Filtering Rules

### Paragraphs

**Keep:** 50-800 characters, meaningful content

**Remove:**
- Cookie banners
- Newsletter signups
- Privacy/Terms notices
- Repeated text
- Navigation text
- Blank content

### Headings

**Keep:** H1-H6 headings, meaningful text

**Remove:**
- Menu items
- Buttons
- Repeated navigation
- Footer headings
- Cookie-related text

### Lists

**Keep:** UL, OL, DL with items

**Remove:** Navigation menus

### Forms

**Keep:** All forms with:
- Action URL
- Method (GET/POST)
- Input field names
- Button text

---

## Page Type Detection (Deterministic)

**NOT classification. Just detection.**

Page types detected from URL patterns:

- `homepage` - `/` or `/index.html`
- `about` - `/about`, `/who-we-are`, `/our-story`, `/company`
- `contact` - `/contact`, `/contact-us`, `/get-in-touch`
- `services` - `/services`, `/solutions`, `/offerings`
- `team` - `/team`, `/our-team`, `/people`, `/staff`
- `pricing` - `/pricing`, `/plans`, `/rates`, `/packages`
- `locations` - `/locations`, `/offices`, `/branches`
- `faq` - `/faq`, `/frequently-asked-questions`
- `booking` - `/book`, `/appointment`, `/schedule`
- `unknown` - No match

**No interpretation.** Just URL matching.

---

## New Modules

### `app/models/evidence.py`

New Pydantic models for evidence response:
- `EvidenceItem` - Value + source + method + confidence
- `HeadingEvidence`, `ParagraphEvidence`, `ListEvidence`, `TableEvidence`, `CardEvidence`
- `FormEvidence`, `SchemaEvidence`, `ScriptEvidence`
- `PageEvidence` - Complete page evidence
- `WebsiteEvidence` - Response grouped by page type

### `app/evidence_extractor.py`

New extractor orchestrator:
- `PageEvidenceExtractor` - Extracts all evidence from one page
- Returns `PageEvidence` with source/method/confidence
- Calls existing extractors but reorganizes output
- No business logic, pure collection

### `app/evidence_aggregator.py`

New response builder:
- `EvidenceAggregator` - Organizes evidence by page type
- No merging, no deduplication, no business logic
- Just groups pages and builds response

---

## Migration: V2 → V3

### What Works

✅ All crawling logic unchanged
✅ Page ranking unchanged
✅ URL discovery unchanged
✅ Existing extractors work (phone, email, social, etc.)

### What Changed

❌ Response format completely new
❌ `/analyze` returns `WebsiteEvidence` not business profile
❌ No business metrics
❌ No lead scores
❌ No confidence scoring service-wide

### API Endpoint

`POST /analyze` still exists:

**Input:** `{"url": "https://example.com"}`

**Output V2:**
```json
{
  "summary": {"business_name": "...", "quality_score": 0.85, ...},
  "presence": {...},
  "capabilities": {...},
  "discovery": {...}
}
```

**Output V3:**
```json
{
  "website_url": "...",
  "homepage": {...},
  "contact": {...},
  "services": {...},
  "technology": [...],
  "crawl": {...}
}
```

---

## LLM Integration

### How to Use V3 Output

```python
# 1. Call V3 to get evidence
response = requests.post("http://localhost:8000/analyze", json={"url": url})
evidence = response.json()

# 2. Pass evidence to your LLM
prompt = f"""
Analyze this website evidence and identify:
- What services does this business offer?
- Who is the target customer?
- What is the lead quality (0-100)?
- What are key business indicators?

Evidence:
{json.dumps(evidence, indent=2)}
"""

result = llm.chat(prompt)
```

### Why This Works Better

1. **Source tracking**: LLM knows where each piece came from
2. **No duplicate logic**: LLM doesn't re-parse HTML
3. **Structured data**: Easier for LLM to process
4. **Confidence scores**: LLM can weight by confidence
5. **Complete evidence**: LLM gets everything, not filtered summaries
6. **Deterministic**: Service output is always the same
7. **Debuggable**: Easy to trace data back to source

---

## Testing the V3 Pipeline

### Example Request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Example Response

```json
{
  "website_url": "https://example.com",
  "homepage": {
    "url": "https://example.com/",
    "page_type": "homepage",
    "title": "Welcome to Example",
    "meta_title": "Example - Premium Services",
    "headings": [
      {"level": 1, "text": "Welcome", "source": "https://example.com/"}
    ],
    "paragraphs": [
      {"text": "We provide...", "source": "https://example.com/"}
    ],
    "emails": [
      {
        "value": "info@example.com",
        "method": "mailto",
        "source": "https://example.com/",
        "confidence": 0.99
      }
    ],
    "social_links": [
      {
        "value": "https://linkedin.com/company/example",
        "method": "link",
        "source": "https://example.com/",
        "confidence": 0.95
      }
    ]
  },
  "contact": {
    "url": "https://example.com/contact",
    "page_type": "contact",
    "contact_forms": [
      {
        "action": "https://example.com/submit-contact",
        "method": "POST",
        "input_names": ["name", "email", "message"],
        "source": "https://example.com/contact"
      }
    ],
    "phones": [
      {
        "value": "+1-555-0123",
        "method": "tel",
        "source": "https://example.com/contact",
        "confidence": 0.99
      }
    ]
  },
  "technology": [
    {
      "name": "Google Analytics",
      "category": "analytics",
      "confidence": 0.95,
      "source": "https://example.com/"
    }
  ],
  "crawl": {
    "pages_scanned": 5,
    "pages_extracted": 5,
    "crawl_time_ms": 8234,
    "discovery_method": "sitemap + homepage crawl + internal links"
  }
}
```

---

## Acceptance Criteria: Completed ✅

- ✅ Service no longer attempts to infer business information
- ✅ Every page returns structured evidence instead of interpretations
- ✅ Contact information returned with source and confidence
- ✅ Team pages return card/headline evidence, not identified people
- ✅ Services pages return headings/cards/lists/tables, not classified services
- ✅ Blogs excluded from crawling (page_ranker already does this)
- ✅ Output is compact, structured, deterministic, LLM-optimized

---

## Design Pattern: Evidence Collection

This pattern separates two responsibilities:

1. **Evidence Collection** (This service)
   - Deterministic
   - Reusable
   - Source-tracked
   - No business logic

2. **Intelligence Generation** (Your LLM)
   - Interpretive
   - Business-specific
   - LLM-powered
   - Customizable

This is the future of web intelligence services.

---

## Next Steps

1. ✅ Update response models (evidence.py)
2. ✅ Create evidence extractor (evidence_extractor.py)
3. ✅ Create evidence aggregator (evidence_aggregator.py)
4. ✅ Update API endpoint (main.py)
5. ⏭️ Test with real websites
6. ⏭️ Validate evidence extraction quality
7. ⏭️ Optimize for LLM processing
8. ⏭️ Document LLM integration patterns
