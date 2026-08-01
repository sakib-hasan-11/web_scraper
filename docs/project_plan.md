# Website Intelligence Service V2 — Implementation Prompt

You are a Senior Python Software Engineer, Solution Architect, and Web Intelligence Engineer.

Your task is to extend the existing Website Intelligence Service (FastAPI + Crawl4AI) into Version 2.

This project is **NOT** an AI agent.

This project is **NOT** a CRM.

This project is **NOT** an automation platform.

Its only responsibility is to analyze a public business website and produce the highest-quality structured business profile possible **without using any LLM**.

The output JSON will later be consumed by another system that performs AI analysis.

Therefore, everything in this project must be deterministic, explainable, and lightweight.

---

# Primary Goal

Given a URL like

https://company.com

produce a compact, normalized business intelligence JSON.

Never return HTML.

Never return Markdown.

Never call OpenAI, Anthropic, Gemini or any other LLM.

---

# Existing V1

The project already has

* FastAPI
* Crawl4AI
* Page selection
* Basic extraction
* JSON response

Improve the existing architecture instead of replacing it.

Keep backwards compatibility whenever practical.

---

# Overall Pipeline

```
Input URL

↓

Normalize URL

↓

Extract Root Domain

↓

robots.txt (optional)

↓

sitemap.xml (if available)

↓

Homepage Crawl

↓

Navigation Discovery

↓

Internal Link Collection

↓

Page Ranking

↓

Page Classification

↓

Parallel Crawl

↓

Specialized Extractors

↓

Merge

↓

Normalization

↓

Confidence Scoring

↓

Business Profile JSON
```

---

# URL Normalization

Before crawling

Convert

https://company.com/about

↓

https://company.com

Remove

* UTM parameters
* Tracking parameters
* Fragments

Always crawl from the homepage.

---

# Link Discovery

Collect ALL internal links from

Homepage HTML

Do NOT use cleaned markdown.

Parse raw HTML using BeautifulSoup.

Ignore

* mailto
* tel
* javascript
* anchors
* external domains

---

# Sitemap Support

Before crawling multiple pages

Attempt

/sitemap.xml

and

/sitemap_index.xml

If found

Use sitemap URLs to improve page discovery.

Fallback to homepage links if sitemap does not exist.

---

# Intelligent Page Ranking

Replace simple keyword matching with a scoring system.

Example

Contact

100

About

95

Services

90

Team

85

Pricing

80

Treatments

80

Locations

75

Careers

40

Blog

-50

Privacy

-100

Terms

-100

Only crawl the highest-ranked pages.

Maximum pages

10

---

# Page Classification

Each crawled page must first be classified.

Possible page types

Homepage

About

Contact

Services

Pricing

Team

Careers

Location

Booking

Unknown

Classification should use

* URL
* Page title
* Navigation text
* H1
* Metadata

instead of URL only.

---

# Parallel Crawling

Homepage is crawled first.

Remaining pages should be crawled concurrently.

Default concurrency

5

Timeout

15 seconds

Skip failures.

Never fail the entire request because one page failed.

---

# Extractor Architecture

Each extractor must be independent.

Each extractor receives

* HTML
* BeautifulSoup object
* URL
* Page Type

Each extractor returns structured data only.

No extractor should know about another extractor.

---

# Required Extractors

Implement or improve the following.

## Company Extractor

Extract

Company Name

Description

Tagline

Industry

Mission

About Summary

---

## Email Extractor

Extract

Visible emails

mailto links

Schema emails

Footer emails

Normalize

Validate

Remove duplicates

Return confidence score

---

## Phone Extractor

Extract

Visible numbers

tel links

Schema numbers

Normalize to E164 where possible

Remove duplicates

Return confidence score

---

## Address Extractor

Extract

Street

City

Region

Postal Code

Country

Coordinates if available

Opening Hours

Google Maps Embed

Schema Address

---

## Team Extractor

Extract

People

Role

Title

Qualifications

Profile URL

Image URL

Avoid extracting random headings.

Recognize repeated profile cards.

---

## Service Extractor

Extract

Services

Products

Treatments

Solutions

Offerings

Do not include navigation labels.

---

## Contact Extractor

Detect

Contact Form

Booking Form

Newsletter

Live Chat

WhatsApp Button

Online Booking

Contact Preference

---

## Social Extractor

Extract

LinkedIn

Facebook

Instagram

Twitter/X

YouTube

TikTok

GitHub

Normalize URLs.

---

## Technology Extractor

Detect

CMS

Analytics

Pixels

CRM

Chat Widget

Booking System

Payment Provider

Framework

Hosting hints

Examples

WordPress

Squarespace

Shopify

HubSpot

Calendly

Stripe

Intercom

Zendesk

Cloudflare

Google Analytics

Google Tag Manager

Meta Pixel

---

## Metadata Extractor

Extract

Title

Meta Description

OpenGraph

Twitter Card

Canonical

Language

---

## Schema Extractor

Parse JSON-LD

Extract

Organization

LocalBusiness

Dentist

MedicalBusiness

Person

PostalAddress

OpeningHours

Email

Telephone

Logo

SameAs

---

## Footer Extractor

Explicitly inspect

<footer>

Extract

Email

Phone

Address

Company Registration

VAT Number

Social Links

Copyright

---

# Confidence Engine

Every extracted value should contain

Value

Source URL

Extraction Method

Confidence Score

Example

```
{
    "email": "info@company.com",
    "source": "/contact",
    "method": "mailto",
    "confidence": 0.99
}
```

Confidence priority

Schema

↓

mailto/tel

↓

Footer

↓

Visible Text

↓

Regex

---

# Business Intelligence Layer

After extraction

Compute deterministic feature flags

Examples

Has Contact Form

Has Booking

Has Live Chat

Has Multiple Locations

Has Team Page

Has Pricing

Has FAQ

Has Careers

Has WhatsApp

Has Social Presence

Has Analytics

Has CRM

Has Marketing Pixels

These are simple booleans.

Do NOT use AI.

---

# Normalization

Merge duplicates.

Prefer highest-confidence values.

Normalize

Emails

Phones

Addresses

Social Links

Services

Technologies

---

# Response Schema

Return a business-centric JSON.

Not a crawl-centric JSON.

Example

```
{
  "website": "...",

  "company": {
    "name": "...",
    "description": "...",
    "industry": "...",
    "tagline": "...",
    "confidence": 0.99
  },

  "contacts": {
    "emails": [],
    "phones": [],
    "address": {},
    "opening_hours": {},
    "contact_form": true
  },

  "team": [],

  "services": [],

  "technology": {},

  "social": {},

  "features": {
    "has_booking": true,
    "has_live_chat": false,
    "has_pricing": true,
    "has_team_page": true,
    "has_multiple_locations": false
  },

  "crawl": {
    "pages_scanned": 6,
    "crawl_time_ms": 8000
  }
}
```

---

# Coding Standards

Use

Python 3.12

FastAPI

Async

Type hints

Pydantic

Structured logging

Small reusable modules

No global mutable state.

No duplicated logic.

No giant functions.

No giant classes.

Follow SOLID principles.

Keep modules focused and testable.

---

# Performance Targets

Homepage crawl

<3 seconds

Total crawl

<10 seconds for typical business websites

Maximum pages

10

Memory

<500MB

---

# Error Handling

Never silently ignore failures.

Log meaningful errors.

Continue processing if one page fails.

Always return valid JSON.

---

# Backward Compatibility

Do not remove existing API endpoints.

Improve them.

Keep the current frontend working.

---

# Out of Scope

Do NOT implement

* LLM calls
* AI scoring
* Database
* Authentication
* Redis
* Celery
* RabbitMQ
* Kafka
* Vector database
* Email sending
* CRM
* n8n integration
* Webhooks
* Batch processing

---

# Success Criteria

The implementation is complete when the API can analyze a typical small-business website and reliably produce a high-quality, normalized business profile containing company details, contact information, team members, services, technologies, social links, feature flags, and confidence scores—all without using any LLM and with a response time suitable for interactive use.
