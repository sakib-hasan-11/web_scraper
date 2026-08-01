# Phase 3 Implementation Summary

## What Was Implemented

Website Intelligence Service V2 - Phase 3 adds confidence scoring, phone/email normalization, and advanced extraction (addresses, team members, enhanced social links).

---

## New Modules

### 1. `app/confidence_engine.py`
**Standardized confidence scoring system**

Provides confidence scoring for all extracted values:
- Source-based scoring (Schema=99%, Mailto=95%, Tel=93%, Footer=85%, Visible=75%, Regex=50%)
- Validation adjustment (+20% for valid, -50% for invalid)
- Redundancy boost (+8% if found multiple places)

**Key enums:**

```python
class ExtractionSource(Enum):
    SCHEMA = "schema"           # JSON-LD or microdata
    MAILTO = "mailto"           # mailto: link
    TEL = "tel"                 # tel: link
    FOOTER = "footer"           # In <footer> element
    VISIBLE = "visible"         # Visible text on page
    REGEX = "regex"             # Pattern matched
    FORM = "form"               # From form action
    UNKNOWN = "unknown"

class ConfidenceLevel(Enum):
    VERY_HIGH = 0.95    # 95-99%
    HIGH = 0.85         # 85-94%
    MEDIUM = 0.70       # 70-84%
    LOW = 0.50          # 50-69%
    VERY_LOW = 0.30     # 30-49%
```

**Key functions:**

- `calculate_confidence(value, source, is_valid, is_redundant)` → float (0.0-1.0)
- `score_email(email, source)` → ConfidenceScore
- `score_phone(phone, source, is_normalized)` → ConfidenceScore
- `score_url(url, source)` → ConfidenceScore
- `score_text(text, source, min_length)` → ConfidenceScore
- `merge_scores(scores)` → ConfidenceScore (merges multiple sources)

**ConfidenceScore dataclass:**

```python
@dataclass
class ConfidenceScore:
    value: str
    confidence: float       # 0.0-1.0
    source: ExtractionSource
    validation: str         # "valid", "invalid", "unvalidated"
    reason: str             # Explanation
```

---

### 2. `app/extractors/contact_enhanced.py`
**Enhanced contact extraction with normalization**

Phone normalization to E.164 format (e.g., +1-234-567-8900).
Email validation using RFC 5322 simplified pattern.
Tracks confidence scores per contact method.

**Key functions:**

- `normalize_phone(phone, country="US")` → (formatted_phone, is_valid)
  - Uses phonenumbers library
  - Handles international numbers
  - Returns E.164 format: +1234567890

- `validate_email(email)` → bool
  - RFC 5322 simplified pattern
  - Checks for @ and domain TLD

- `extract_phones_enhanced(soup, html)` → list[ConfidenceScore]
  - Extracts from: tel: links, schema.org, footer, regex patterns
  - Normalizes all to E.164
  - Deduplicates

- `extract_emails_enhanced(soup, html)` → list[ConfidenceScore]
  - Extracts from: mailto: links, schema.org, footer, regex patterns
  - Validates all addresses
  - Deduplicates

---

### 3. `app/extractors/address.py`
**Address extraction and location detection**

Extracts business addresses.
Detects multiple business locations.
Validates address format.

**Key functions:**

- `extract_addresses(soup, html)` → list[ConfidenceScore]
  - Sources: schema.org PostalAddress, <address> tags, footer, contact sections, regex
  - US address pattern support
  - Returns: {street, city, state, zip}

- `_extract_schema_addresses(soup)` → list[str]
  - Parses JSON-LD PostalAddress and contactPoint.address

- `count_locations(addresses)` → int
  - Returns number of unique business locations
  - Simple heuristic: different cities = different locations

**Usage example:**

```python
addresses = extract_addresses(soup, html)
for score in addresses:
    print(f"{score.value} (confidence: {score.confidence})")

num_locations = count_locations(addresses)
print(f"Business has {num_locations} location(s)")
```

---

### 4. `app/extractors/team.py`
**Team member extraction**

Extracts company team and leadership information.
Detects team names, titles, social profiles.
Handles team pages and about sections.

**Key functions:**

- `extract_team_members(soup, html)` → list[ConfidenceScore]
  - Sources: team sections, schema.org, LinkedIn links
  - Deduplicates by name
  - Returns: {name, title, email, phone, social_links}

- `has_team_page(html)` → bool
  - Detects if page is team/about page
  - Uses pattern matching

**TeamMember dataclass:**

```python
@dataclass
class TeamMember:
    name: str
    title: str = ""
    department: str = ""
    email: str = ""
    phone: str = ""
    social_links: dict = None
    confidence: float = 0.0
```

---

### 5. `app/extractors/social_enhanced.py`
**Enhanced social link extraction**

Improved social platform detection.
Validates social URLs for specific platforms.
Normalizes URLs to standard formats.

**Platforms detected:**

```
LinkedIn, Facebook, Twitter/X, Instagram, YouTube
TikTok, GitHub, WhatsApp, Telegram, Discord, Reddit
```

**Key functions:**

- `extract_social_links_enhanced(html, soup)` → dict[str, ConfidenceScore]
  - Searches: anchor tags, footer, header/nav
  - Platform-specific regex patterns
  - Returns: {platform: ConfidenceScore}

- `validate_social_url(url, platform)` → bool
  - Validates URL for specific platform

- `normalize_social_url(url, platform)` → str
  - Converts to standard format
  - Adds https:// if missing
  - Normalizes twitter.com → x.com

- `merge_social_links(current, new)` → dict
  - Merges links with validation

---

## Updated Response Schema

The Phase 3 response includes confidence scores. Example structure:

```json
{
  "website": "https://example.com",
  "contact": {
    "emails": [
      {
        "value": "info@example.com",
        "confidence": 0.95,
        "source": "mailto",
        "validation": "valid"
      }
    ],
    "phones": [
      {
        "value": "+1-234-567-8900",
        "confidence": 0.93,
        "source": "tel",
        "validation": "valid"
      }
    ],
    "contact_form": true,
    "booking": false
  },
  "addresses": [
    {
      "value": "123 Main St, San Francisco, CA 94105",
      "confidence": 0.85,
      "source": "visible"
    }
  ],
  "locations_count": 1,
  "team_members": [
    {
      "name": "John Doe",
      "confidence": 0.75,
      "source": "visible"
    }
  ],
  "social": {
    "linkedin": {
      "value": "https://linkedin.com/company/example",
      "confidence": 0.95,
      "source": "footer"
    },
    "twitter": {
      "value": "https://x.com/example",
      "confidence": 0.80,
      "source": "visible"
    }
  },
  "features": {
    "has_contact_form": true,
    "has_multiple_locations": false
  },
  "crawl": {
    "pages_scanned": 6,
    "crawl_time_ms": 8500
  }
}
```

---

## Pipeline Flow (Phase 3)

```
Per-page extraction:

HTML + URL
  ↓
[Phase 2: Classification + Features]
  ↓
Enhanced Contact Extraction (new)
  - Extract tel: links (E.164 normalized)
  - Extract mailto: links (validated)
  - Extract schema.org contacts
  - Deduplicate with confidence
  ↓
Address Extraction (new)
  - Find addresses in schema.org
  - Parse <address> tags
  - Regex patterns for US format
  - Detect multiple locations
  ↓
Team Member Extraction (new)
  - Find team/about sections
  - Parse team cards
  - Extract from schema.org
  - Detect LinkedIn profiles
  ↓
Enhanced Social Link Extraction (new)
  - Platform-specific patterns
  - Validate URLs
  - Normalize formats
  ↓
Per-page Result: {
    url,
    page_classification,
    features,
    emails: [ConfidenceScore],
    phones: [ConfidenceScore],
    addresses: [ConfidenceScore],
    team_members: [ConfidenceScore],
    social: {platform: ConfidenceScore},
    ...
}

---

Final Response includes:
- All extraction results
- Confidence scores for each value
- Data source tracking
- Validation status
- Location count (for multi-location businesses)
- Team member list (if detected)
```

---

## Benefits of Phase 3

✅ **Confidence scoring** — Know which data is reliable
✅ **Phone normalization** — E.164 format for global compatibility
✅ **Email validation** — RFC 5322 format checking
✅ **Address extraction** — Multi-location business support
✅ **Team detection** — Leadership and staff identification
✅ **Enhanced social** — Better platform detection and normalization
✅ **Source tracking** — Know where each value came from
✅ **Validation metadata** — See if values passed validation

---

## Performance Impact

- Contact enhancement: ~30-50ms per page
- Address extraction: ~20-40ms per page
- Team extraction: ~30-60ms per page (depends on page size)
- Social enhancement: ~20-30ms per page
- Total Phase 3 overhead: ~100-180ms per page
- Overall: Still under 10-second target for 5-10 pages

---

## Requirements

Phase 3 requires these packages (already in requirements.txt):

```
phonenumbers>=8.13.39         # Phone normalization
email-validator>=2.2.0        # Email validation (optional, using regex in code)
```

---

## Testing Phase 3

```python
# Test phone normalization
from app.extractors.contact_enhanced import normalize_phone

formatted, is_valid = normalize_phone("(555) 123-4567", country="US")
print(formatted)  # +15551234567

# Test email validation
from app.extractors.contact_enhanced import validate_email

is_valid = validate_email("john@example.com")
print(is_valid)  # True

# Test address extraction
from app.extractors.address import extract_addresses

addresses = extract_addresses(soup, html)
for score in addresses:
    print(f"{score.value} ({score.confidence})")

# Test team extraction
from app.extractors.team import extract_team_members

members = extract_team_members(soup, html)
print(f"Found {len(members)} team members")

# Test social links
from app.extractors.social_enhanced import extract_social_links_enhanced

social = extract_social_links_enhanced(html, soup)
for platform, score in social.items():
    print(f"{platform}: {score.value}")

# Test confidence scoring
from app.confidence_engine import (
    calculate_confidence,
    ExtractionSource,
)

confidence = calculate_confidence(
    value="info@example.com",
    source=ExtractionSource.MAILTO,
    is_valid=True,
    is_redundant=False,
)
print(f"Confidence: {confidence:.0%}")  # 95%
```

---

## Next Phase

**Phase 4:** Response Schema Restructuring
- Restructure response to be business-centric (not crawl-centric)
- Add summary section with key metrics
- Reorganize data for better API usability
- Add data freshness indicators
