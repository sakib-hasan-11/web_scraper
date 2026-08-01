# Website Intelligence Service

A standalone microservice that accepts a website URL, crawls its important public pages, extracts structured business information (no LLM), and returns a compact JSON response.

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- Crawl4AI (Playwright-based crawler)
- BeautifulSoup4, lxml, Trafilatura
- Pydantic v2

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright browsers (required by Crawl4AI)

```bash
playwright install chromium
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### 4. Open the frontend

Open `frontend/index.html` in your browser, or visit `http://localhost:8000/` when the server is running.

---

## API Endpoints

### `POST /analyze`

Analyze a website and return structured business intelligence.

**Request:**
```json
{ "url": "https://company.com" }
```

**Response:**
```json
{
  "website": "https://company.com",
  "company": { "name": "", "description": "", "industry": "", "tagline": "" },
  "contact": { "emails": [], "phones": [], "contact_form": false, "booking": false },
  "social": { "linkedin": "", "facebook": "", "instagram": "", "twitter": "", "youtube": "" },
  "services": [],
  "technology": { "cms": "", "analytics": [], "widgets": [], "booking": [] },
  "seo": { "title": "", "description": "", "language": "" },
  "pages": { "homepage": true, "about": false, "services": false, "pricing": false, "contact": false },
  "crawl": { "pages_scanned": 1, "crawl_time_ms": 0 }
}
```

### `GET /health`

Returns `{"status": "ok"}`.

### `GET /version`

Returns `{"version": "1.0.0"}`.

---

## Docker

```bash
docker build -t website-intelligence .
docker run -p 8000:8000 website-intelligence
```

---

## Performance Targets

| Metric | Target |
|---|---|
| Homepage crawl | < 3 seconds |
| Full crawl | < 20 seconds |
| Max pages crawled | 10 |
| Concurrency | 5 |
| Timeout per page | 15 seconds |
