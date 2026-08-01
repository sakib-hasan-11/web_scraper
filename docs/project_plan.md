# Website Intelligence Service (FastAPI + Crawl4AI)

## Objective

Build a production-ready REST API that accepts a website domain, intelligently crawls only the important public pages, extracts structured business information without using an LLM, and returns a compact JSON object that is ready to be passed into an LLM for lead qualification.

The service **must not know anything about n8n, workflows, CRM systems, email automation, or databases.**

It is a standalone microservice.

---

# High-Level Architecture

```
POST /analyze

        │
        ▼

Validate URL

        │
        ▼

Homepage Crawl

        │
        ▼

Extract Internal Links

        │
        ▼

Filter Important Pages

        │
        ▼

Crawl Important Pages

        │
        ▼

HTML Processing

        │
        ▼

Extract Structured Data

        │
        ▼

Merge Results

        │
        ▼

Return JSON
```

---

# Tech Stack

Python 3.12

FastAPI

Uvicorn

Crawl4AI

BeautifulSoup4

Trafilatura

lxml

httpx

tldextract

pydantic

extruct

wappalyzer (or equivalent)

phonenumbers

email-validator

orjson

---

# Project Structure

```
website-intelligence/

│

├── app/

│   ├── main.py

│   ├── config.py

│   ├── schemas.py

│   ├── crawler.py

│   ├── page_selector.py

│   ├── extractor.py

│   ├── merger.py

│   ├── utils.py

│   │
│   ├── extractors/

│   │      email.py

│   │      phone.py

│   │      social.py

│   │      metadata.py

│   │      services.py

│   │      forms.py

│   │      technology.py

│   │      company.py

│   │      schema.py

│   │
│   ├── models/

│   │      response.py

│   │
│   └── constants/

│          keywords.py

│

├── tests/

├── requirements.txt

├── Dockerfile

└── README.md
```

---

# API

## POST

```
/analyze
```

Request

```json
{
    "url":"https://company.com"
}
```

---

Response

```json
{
    ...
}
```

Always return JSON.

Never return HTML.

Never return Markdown.

---

# Processing Pipeline

## Step 1

Validate URL

Requirements

* normalize URL
* enforce HTTPS if possible
* reject localhost
* reject IP addresses
* reject invalid domains

---

## Step 2

Homepage Crawl

Use Crawl4AI

Retrieve

* HTML
* Markdown
* metadata

Do not recursively crawl.

---

## Step 3

Extract Internal Links

Collect every internal link.

Ignore

* external domains
* mailto
* tel
* javascript
* anchors

---

## Step 4

Important Page Detection

Keep only URLs containing

```
about
about-us
company
services
solutions
pricing
contact
team
staff
leadership
careers
book
appointment
demo
```

Ignore

```
blog

tag

category

privacy

cookies

terms

author

search

login

register

cart

checkout

dashboard

admin

feed
```

Maximum pages

10

---

## Step 5

Parallel Crawl

Crawl selected pages concurrently.

Concurrency

5

Timeout

15 seconds

Skip failures.

Continue crawling.

---

# Extraction Layer

Each extractor must be completely independent.

Each extractor receives

```
HTML

BeautifulSoup

URL
```

and returns structured data.

No extractor may depend on another extractor.

---

## Email Extractor

Extract

* visible emails
* mailto links

Remove duplicates.

Validate emails.

---

## Phone Extractor

Extract phone numbers.

Normalize to E164.

Remove duplicates.

---

## Social Extractor

Detect

LinkedIn

Facebook

Instagram

Twitter/X

YouTube

TikTok

GitHub

---

## Metadata Extractor

Extract

Title

Meta Description

H1

H2

OpenGraph

Twitter Card

Canonical

Language

---

## Company Extractor

Find

Company Name

Tagline

Mission

About paragraph

---

## Services Extractor

Extract

Service names

Products

Solutions

Offerings

Avoid navigation labels.

---

## Contact Extractor

Detect

Contact Form

Booking Form

Newsletter Form

Chat Widget

Live Chat

---

## Technology Extractor

Detect

WordPress

Shopify

Webflow

HubSpot

Calendly

Stripe

Intercom

Zendesk

Google Analytics

Google Tag Manager

Meta Pixel

Cloudflare

---

## Schema Extractor

Parse JSON-LD

Extract

Organization

LocalBusiness

Person

Postal Address

Opening Hours

Telephone

Email

---

# Merge Layer

Merge outputs.

Remove duplicates.

Rank confidence.

Prefer

Schema

↓

Visible Content

↓

Metadata

↓

Regex

---

# Final Response Format

```json
{
  "website":"https://company.com",

  "company":{

      "name":"",

      "description":"",

      "industry":"",

      "tagline":""

  },

  "contact":{

      "emails":[],

      "phones":[],

      "contact_form":true,

      "booking":false

  },

  "social":{

      "linkedin":"",

      "facebook":"",

      "instagram":"",

      "twitter":"",

      "youtube":""

  },

  "services":[],

  "technology":{

      "cms":"",

      "analytics":[],

      "widgets":[],

      "booking":[]

  },

  "seo":{

      "title":"",

      "description":"",

      "language":""

  },

  "pages":{

      "homepage":true,

      "about":true,

      "services":true,

      "pricing":false,

      "contact":true

  },

  "crawl":{

      "pages_scanned":5,

      "crawl_time_ms":0

  }
}
```

This JSON is the only output consumed by downstream systems.

---

# Non-Functional Requirements

* Async FastAPI
* Fully typed code
* Pydantic models
* Structured logging
* Retry failed HTTP requests
* Configurable timeout
* Configurable concurrency
* Docker compatible
* Linux compatible
* Python 3.12
* No global state
* Stateless service
* No database
* No authentication (initial version)
* No LLM calls
* No vector database
* No automation platform integration

---

# FastAPI Endpoints

```
POST /analyze
```

Analyze a website.

---

```
GET /health
```

Health check.

---

```
GET /version
```

Application version.

---

# Error Handling

Return consistent JSON errors.

Example

```json
{
  "success":false,
  "error":"Unable to crawl website",
  "details":"Timeout after 15 seconds"
}
```

---

# Performance Targets

Homepage crawl

< 3 seconds

Full crawl

< 20 seconds

Memory

< 500 MB

Average pages

5–10

---

# Coding Principles

* SOLID architecture
* Single Responsibility Principle
* One extractor = one responsibility
* Dependency injection where appropriate
* No business logic inside FastAPI routes
* Keep crawler, extraction, and response formatting independent
* Every module should be unit-testable
* Avoid duplicated parsing logic
* Prefer deterministic extraction over AI
* Produce compact, normalized JSON suitable for downstream LLM consumption

---

