# Website Intelligence Service V2.1 — Data Quality & Performance Improvements

You are continuing development on an existing Website Intelligence Service.

The project already has:

* FastAPI
* Crawl4AI
* Parallel crawling
* Page selection
* Multiple extractors
* JSON response
* Confidence scoring

Do NOT rewrite the project.

Improve the existing implementation.

The primary objective of this iteration is **data quality**, **crawl performance**, and **lead intelligence**.

The goal is NOT to crawl more pages.

The goal is to return **higher quality business information**.

---

# Highest Priority

Improve the quality of extracted business information.

False positives are worse than missing information.

Never return system-generated values as business information.

Always prefer fewer high-confidence results over many low-quality results.

---

# Task 1 — Email Quality Engine

Current problem:

The crawler extracts emails like

```text
xxxxx@sentry.wixpress.com
xxxxx@sentry-next.wixpress.com
```

These are not business emails.

Build an Email Quality Engine.

Every email must be classified.

Possible categories

Business

Support

Sales

Marketing

Personal

System

Unknown

Reject emails from common system providers.

Examples

sentry.io

sentry.wixpress.com

sentry-next.wixpress.com

cloudflare.com

googleusercontent.com

example.com

localhost

noreply addresses

hashed addresses

tracking addresses

Build both

Allow List

Block List

Every email should include

Value

Category

Source URL

Confidence

Extraction Method

Ignore Flag

Only business-relevant emails should appear in the final response.

---

# Task 2 — Phone Quality Engine

Improve phone extraction.

Priority order

1. tel links

2. JSON-LD

3. Footer

4. Contact Page

5. Visible Text

Normalize every phone number.

Remove duplicates.

Return confidence score.

---

# Task 3 — Smart Page Ranking

Current implementation still crawls blog posts.

Blogs are low priority.

Page ranking must become smarter.

Score pages.

Example

Contact

100

About

95

Services

90

Treatments

90

Pricing

85

Team

80

Locations

75

FAQ

70

Booking

70

Blog

-100

News

-100

Posts

-100

Privacy

-200

Terms

-200

Never crawl blogs unless explicitly requested.

---

# Task 4 — Page Classification

Do not classify pages using URL only.

Use

URL

Title

H1

Navigation Text

Meta Description

Breadcrumb

Examples

"Treatments"

should become

Services Page

"Meet Our Team"

should become

Team Page

"Get in Touch"

should become

Contact Page

Every page must have one page type before extraction begins.

---

# Task 5 — Page-Specific Extraction

Do NOT run every extractor on every page.

Create an Extraction Router.

Homepage

Company

Technology

Navigation

Metadata

Contact

Emails

Phones

Address

Opening Hours

Forms

About

Company Summary

History

Mission

Team

People

Roles

Qualifications

Profile Links

Services

Treatments

Products

Pricing

Booking

Footer

Registration

VAT

Social Links

Contact Info

Only execute extractors that make sense for that page type.

---

# Task 6 — Team Extraction

Current implementation returns empty team arrays.

Improve extraction.

Detect repeating profile cards.

Extract

Name

Role

Qualifications

Profile URL

Image URL

Bio (if available)

Ignore navigation items.

Ignore headings that are not people.

---

# Task 7 — Service Extraction

Current implementation extracts marketing headlines.

Instead extract actual services.

Examples

Dental Implants

Root Canal

Invisalign

Teeth Whitening

Emergency Dentist

Do not extract hero text.

Do not extract advertisements.

Prefer

Service Cards

Navigation

Treatment Lists

Pricing Tables

---

# Task 8 — Contact Information

Improve contact discovery.

Search

Footer

Header

Contact Page

JSON-LD

mailto

tel

Google Maps Embed

Business Schema

Return

Emails

Phones

Address

Opening Hours

Google Maps URL

Contact Form

Booking Form

---

# Task 9 — Technology Detection

Expand technology detection.

Current detection

CMS

Analytics

Widgets

Add

CRM

HubSpot

Salesforce

Zoho

Booking

Calendly

TidyCal

Wix Booking

SimplyBook

Payments

Stripe

PayPal

Square

Chat

Intercom

Zendesk

Drift

Crisp

Tawk.to

Marketing

Google Ads

Meta Pixel

Hotjar

Microsoft Clarity

Cookiebot

Cloudflare

Framework

Next.js

React

Vue

Laravel

WordPress

Squarespace

Wix

Shopify

---

# Task 10 — Confidence Engine

Replace one overall confidence score.

Score each section independently.

Example

Company

Contacts

Services

Technology

Team

Social

Address

Every field should contain

Value

Confidence

Source URL

Extraction Method

---

# Task 11 — Crawl Performance

Current crawl time

60–70 seconds

Target

10–15 seconds

Investigate

Sequential crawling

JavaScript wait time

Images

Fonts

Videos

Unused assets

Optimize browser settings.

Use concurrent crawling.

Skip unnecessary resources.

---

# Task 12 — Business Intelligence Output

The response should describe the BUSINESS.

Not the crawl.

Current response contains debugging information.

Create two response modes.

Default

Business Profile

Debug

Business Profile

*

Crawl Details

*

URLs

*

Timing

Production mode should hide implementation details.

---

# Desired Business Profile

The final response should resemble

{
"company": {},

"contacts": {},

"address": {},

"team": [],

"services": [],

"technology": {},

"social": {},

"features": {},

"confidence": {}
}

Every section should contain structured information.

Never return raw HTML.

Never return Markdown.

Never return random headings.

Never return duplicate values.

---

# Coding Requirements

Improve the existing architecture.

Do not rewrite working components.

Keep FastAPI routes unchanged.

Keep API compatibility.

Use SOLID principles.

Keep modules small.

Every extractor must remain independent.

Every improvement should be unit-testable.

Avoid duplicated logic.

---

# Acceptance Criteria

The implementation is successful when

* False system emails are eliminated.
* Business emails have high confidence.
* Blog pages are no longer crawled by default.
* Team members are extracted correctly.
* Services contain real offerings instead of marketing slogans.
* Contact information is significantly more accurate.
* Page classification is content-aware instead of URL-only.
* Crawl time is reduced substantially through optimized crawling.
* Production JSON represents a clean business profile suitable for downstream AI analysis.
* Existing API endpoints and frontend continue to work without breaking changes.
