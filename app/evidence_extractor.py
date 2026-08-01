"""
Evidence Extractor V3.

Orchestrates extraction of all evidence from a crawled page.

Returns PageEvidence with:
  - Structured content (headings, paragraphs, lists, tables, cards)
  - Contact evidence (emails, phones, addresses, forms)
  - Social evidence (social links, WhatsApp, Calendar)
  - Technical evidence (scripts, schema)
  - All items include source, method, confidence

No business logic. No inference. Just collection.
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.crawler import CrawledPage
from app.models.evidence import (
    PageEvidence,
    HeadingEvidence,
    ParagraphEvidence,
    ListEvidence,
    TableEvidence,
    CardEvidence,
    FormEvidence,
    EvidenceItem,
    SchemaEvidence,
    ScriptEvidence,
)

# Import existing extractors (they return raw data)
from app.extractors.email import extract_emails
from app.extractors.phone import extract_phones
from app.extractors.social import extract_social_links
from app.extractors.metadata import extract_metadata
from app.extractors.forms import extract_forms
from app.extractors.technology import extract_technology
from app.extractors.schema import extract_schema

logger = logging.getLogger(__name__)


class PageEvidenceExtractor:
    """Extracts all evidence from a page into structured PageEvidence."""

    def __init__(self, page: CrawledPage):
        self.page = page
        self.url = page.url
        self.html = page.html
        self.soup = BeautifulSoup(page.html, "lxml") if page.html else None

    def extract(self) -> Optional[PageEvidence]:
        """
        Extract all evidence from page.

        Returns:
            PageEvidence or None if extraction fails
        """
        if not self.page.success or not self.html or not self.soup:
            logger.warning("Skipping extraction for failed page: %s", self.url)
            return None

        logger.info("Extracting evidence from: %s", self.url)

        evidence = PageEvidence(url=self.url)

        # ── Basic Metadata ─────────────────────────────────────────────
        evidence.title = self._extract_title()
        evidence.meta_title = self._extract_meta_tag("title")
        evidence.meta_description = self._extract_meta_tag("description")
        evidence.meta_og_title = self._extract_meta_tag("og:title")
        evidence.meta_og_description = self._extract_meta_tag("og:description")
        evidence.meta_og_image = self._extract_meta_tag("og:image")
        evidence.canonical_url = self._extract_canonical()

        # ── Logo & Navigation ──────────────────────────────────────────
        evidence.logo_url = self._extract_logo()
        evidence.navigation_links = self._extract_navigation()

        # ── Structured Content ─────────────────────────────────────────
        evidence.headings = self._extract_headings()
        evidence.paragraphs = self._extract_paragraphs()
        evidence.lists = self._extract_lists()
        evidence.tables = self._extract_tables()
        evidence.cards = self._extract_cards()

        # ── Contact Evidence ───────────────────────────────────────────
        evidence.emails = self._extract_contact_emails()
        evidence.phones = self._extract_contact_phones()
        evidence.addresses = self._extract_addresses()
        evidence.opening_hours = self._extract_opening_hours()
        evidence.maps_links = self._extract_maps_links()

        # ── Forms ──────────────────────────────────────────────────────
        evidence.contact_forms = self._extract_contact_forms()
        evidence.booking_forms = self._extract_booking_forms()
        evidence.newsletter_forms = self._extract_newsletter_forms()

        # ── Social & External ──────────────────────────────────────────
        evidence.social_links = self._extract_social_links()
        evidence.whatsapp_links = self._extract_whatsapp_links()
        evidence.calendar_links = self._extract_calendar_links()

        # ── Schema Data ────────────────────────────────────────────────
        evidence.schema_data = self._extract_schema()

        # ── Technology ─────────────────────────────────────────────────
        evidence.scripts = self._extract_scripts()

        # ── Footer Evidence ────────────────────────────────────────────
        evidence.footer_text = self._extract_footer_text()
        evidence.footer_emails = self._extract_footer_emails()
        evidence.footer_phones = self._extract_footer_phones()
        evidence.footer_social_links = self._extract_footer_social()
        evidence.copyright = self._extract_copyright()

        # ── Detect Page Type ───────────────────────────────────────────
        evidence.page_type = self._detect_page_type()

        logger.info(
            "Extracted evidence: %d headings, %d paragraphs, %d emails, %d phones",
            len(evidence.headings),
            len(evidence.paragraphs),
            len(evidence.emails),
            len(evidence.phones),
        )

        return evidence

    # ────────────────────────────────────────────────────────────────────
    # Metadata Extraction
    # ────────────────────────────────────────────────────────────────────

    def _extract_title(self) -> str:
        """Extract page title from H1 or title tag."""
        h1 = self.soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        title_tag = self.soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return ""

    def _extract_meta_tag(self, name: str) -> str:
        """Extract meta tag content."""
        meta = self.soup.find("meta", {"name": name}) or self.soup.find("meta", {"property": name})
        if meta and meta.get("content"):
            return meta["content"]
        return ""

    def _extract_canonical(self) -> str:
        """Extract canonical URL."""
        link = self.soup.find("link", {"rel": "canonical"})
        if link and link.get("href"):
            return link["href"]
        return ""

    def _extract_logo(self) -> str:
        """Extract logo URL from common locations."""
        # Try header logo
        header = self.soup.find("header")
        if header:
            img = header.find("img")
            if img and img.get("src"):
                return urljoin(self.url, img["src"])

        # Try first img with alt="logo"
        img = self.soup.find("img", {"alt": lambda x: x and "logo" in x.lower()})
        if img and img.get("src"):
            return urljoin(self.url, img["src"])

        return ""

    def _extract_navigation(self) -> list[str]:
        """Extract navigation links."""
        nav_links = []
        nav = self.soup.find("nav")
        if nav:
            for link in nav.find_all("a", href=True):
                href = link["href"]
                if href and not href.startswith("#"):
                    nav_links.append(urljoin(self.url, href))

        return list(set(nav_links))[:20]  # Limit to 20

    # ────────────────────────────────────────────────────────────────────
    # Content Extraction
    # ────────────────────────────────────────────────────────────────────

    def _extract_headings(self) -> list[HeadingEvidence]:
        """Extract all headings (H1-H6)."""
        headings = []
        for level in range(1, 7):
            for heading in self.soup.find_all(f"h{level}"):
                text = heading.get_text(strip=True)
                if text and len(text) > 2:
                    # Filter out navigation/menu headings
                    if not any(x in text.lower() for x in ["menu", "cookie", "subscribe"]):
                        headings.append(
                            HeadingEvidence(
                                level=level,
                                text=text,
                                source=self.url,
                            )
                        )

        return headings

    def _extract_paragraphs(self) -> list[ParagraphEvidence]:
        """Extract meaningful paragraphs (50-800 chars, filtered)."""
        paragraphs = []
        seen = set()

        for p in self.soup.find_all("p"):
            text = p.get_text(strip=True)

            # Filter criteria
            if not text or text in seen:
                continue
            if len(text) < 50 or len(text) > 800:
                continue
            if any(x in text.lower() for x in ["cookie", "privacy policy", "terms of service", "newsletter", "subscribe"]):
                continue

            seen.add(text)
            paragraphs.append(
                ParagraphEvidence(
                    text=text,
                    source=self.url,
                )
            )

        return paragraphs

    def _extract_lists(self) -> list[ListEvidence]:
        """Extract lists (UL, OL, DL)."""
        lists = []

        # Unordered lists
        for ul in self.soup.find_all("ul"):
            # Skip navigation lists
            if ul.find_parent("nav"):
                continue
            items = [li.get_text(strip=True) for li in ul.find_all("li", recursive=False)]
            if items and len(items) > 0:
                lists.append(
                    ListEvidence(
                        type="ul",
                        items=items,
                        source=self.url,
                    )
                )

        # Ordered lists
        for ol in self.soup.find_all("ol"):
            items = [li.get_text(strip=True) for li in ol.find_all("li", recursive=False)]
            if items:
                lists.append(
                    ListEvidence(
                        type="ol",
                        items=items,
                        source=self.url,
                    )
                )

        return lists[:10]  # Limit to 10

    def _extract_tables(self) -> list[TableEvidence]:
        """Extract tables."""
        tables = []

        for table in self.soup.find_all("table"):
            headers = []
            rows = []

            # Extract headers
            for th in table.find_all("th"):
                headers.append(th.get_text(strip=True))

            # Extract rows
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)

            if headers or rows:
                tables.append(
                    TableEvidence(
                        headers=headers,
                        rows=rows,
                        source=self.url,
                    )
                )

        return tables[:5]  # Limit to 5

    def _extract_cards(self) -> list[CardEvidence]:
        """Extract repeating cards (simplified)."""
        cards = []

        # Look for common card patterns
        for card_div in self.soup.find_all("div", {"class": lambda x: x and any(k in x.lower() for k in ["card", "feature", "service", "team", "box"])}):
            title_elem = card_div.find(["h2", "h3", "h4"])
            subtitle_elem = card_div.find("h5") or card_div.find(["p", "span"], {"class": lambda x: x and "subtitle" in x.lower()})
            desc_elem = card_div.find("p")
            img_elem = card_div.find("img")
            link_elem = card_div.find("a")

            cards.append(
                CardEvidence(
                    title=title_elem.get_text(strip=True) if title_elem else None,
                    subtitle=subtitle_elem.get_text(strip=True) if subtitle_elem else None,
                    description=desc_elem.get_text(strip=True) if desc_elem else None,
                    image_url=urljoin(self.url, img_elem["src"]) if img_elem and img_elem.get("src") else None,
                    link_url=urljoin(self.url, link_elem["href"]) if link_elem and link_elem.get("href") else None,
                    source=self.url,
                )
            )

        return cards[:20]  # Limit to 20

    # ────────────────────────────────────────────────────────────────────
    # Contact Evidence
    # ────────────────────────────────────────────────────────────────────

    def _extract_contact_emails(self) -> list[EvidenceItem]:
        """Extract emails with source/method/confidence."""
        emails = []
        raw_emails = extract_emails(self.html, self.soup, self.url)

        for email in raw_emails:
            # Determine extraction method
            if "mailto:" in self.html.lower():
                method = "mailto"
                confidence = 0.99
            elif any(x in self.html for x in ["schema", "json-ld"]):
                method = "schema"
                confidence = 0.95
            else:
                method = "regex"
                confidence = 0.70

            emails.append(
                EvidenceItem(
                    value=email,
                    method=method,
                    source=self.url,
                    confidence=confidence,
                )
            )

        return emails

    def _extract_contact_phones(self) -> list[EvidenceItem]:
        """Extract phones with source/method/confidence."""
        phones = []
        raw_phones = extract_phones(self.html, self.soup, self.url)

        for phone in raw_phones:
            # Determine method
            if "tel:" in self.html.lower():
                method = "tel"
                confidence = 0.99
            elif "schema" in self.html.lower():
                method = "schema"
                confidence = 0.95
            else:
                method = "regex"
                confidence = 0.75

            phones.append(
                EvidenceItem(
                    value=phone,
                    method=method,
                    source=self.url,
                    confidence=confidence,
                )
            )

        return phones

    def _extract_addresses(self) -> list[EvidenceItem]:
        """Extract addresses."""
        addresses = []

        # From schema
        address_tags = self.soup.find_all("address")
        for addr in address_tags:
            text = addr.get_text(strip=True)
            if text:
                addresses.append(
                    EvidenceItem(
                        value=text,
                        method="address_tag",
                        source=self.url,
                        confidence=0.90,
                    )
                )

        return addresses

    def _extract_opening_hours(self) -> list[EvidenceItem]:
        """Extract opening hours."""
        hours = []

        # Look for common patterns
        for text in self.soup.stripped_strings:
            if any(x in text.lower() for x in ["hours", "open", "close", "monday", "am", "pm"]):
                if len(text) < 200:
                    hours.append(
                        EvidenceItem(
                            value=text,
                            method="visible",
                            source=self.url,
                            confidence=0.70,
                        )
                    )

        return hours[:5]

    def _extract_maps_links(self) -> list[EvidenceItem]:
        """Extract Google Maps links."""
        maps = []

        for link in self.soup.find_all("a", href=True):
            href = link["href"]
            if "maps.google.com" in href or "google.com/maps" in href:
                maps.append(
                    EvidenceItem(
                        value=href,
                        method="link",
                        source=self.url,
                        confidence=0.99,
                    )
                )

        return maps

    # ────────────────────────────────────────────────────────────────────
    # Forms
    # ────────────────────────────────────────────────────────────────────

    def _extract_contact_forms(self) -> list[FormEvidence]:
        """Extract contact forms."""
        forms = []
        for form in self.soup.find_all("form"):
            if any(x in str(form).lower() for x in ["contact", "message", "inquiry"]):
                forms.append(self._build_form_evidence(form))
        return forms

    def _extract_booking_forms(self) -> list[FormEvidence]:
        """Extract booking forms."""
        forms = []
        for form in self.soup.find_all("form"):
            if any(x in str(form).lower() for x in ["book", "appointment", "schedule", "reservation"]):
                forms.append(self._build_form_evidence(form))
        return forms

    def _extract_newsletter_forms(self) -> list[FormEvidence]:
        """Extract newsletter forms."""
        forms = []
        for form in self.soup.find_all("form"):
            if any(x in str(form).lower() for x in ["subscribe", "newsletter", "email"]):
                forms.append(self._build_form_evidence(form))
        return forms

    def _build_form_evidence(self, form) -> FormEvidence:
        """Build FormEvidence from form element."""
        action = form.get("action", "")
        method = form.get("method", "POST").upper()
        inputs = [inp.get("name", "") for inp in form.find_all(["input", "textarea", "select"]) if inp.get("name")]
        button = ""
        for btn in form.find_all(["button", "input[type=submit]"]):
            if btn.get("value"):
                button = btn["value"]
            elif btn.get_text():
                button = btn.get_text(strip=True)

        return FormEvidence(
            action=urljoin(self.url, action) if action else self.url,
            method=method,
            input_names=inputs,
            button_text=button,
            source=self.url,
        )

    # ────────────────────────────────────────────────────────────────────
    # Social & External
    # ────────────────────────────────────────────────────────────────────

    def _extract_social_links(self) -> list[EvidenceItem]:
        """Extract social profile links."""
        socials = extract_social_links(self.html, self.soup, self.url)
        items = []
        for platform, url in socials.items():
            if url:
                items.append(
                    EvidenceItem(
                        value=url,
                        method="link",
                        source=self.url,
                        confidence=0.95,
                    )
                )
        return items

    def _extract_whatsapp_links(self) -> list[EvidenceItem]:
        """Extract WhatsApp links."""
        whatsapp = []
        for link in self.soup.find_all("a", href=True):
            href = link["href"]
            if "whatsapp.com" in href or "wa.me" in href:
                whatsapp.append(
                    EvidenceItem(
                        value=href,
                        method="link",
                        source=self.url,
                        confidence=0.99,
                    )
                )
        return whatsapp

    def _extract_calendar_links(self) -> list[EvidenceItem]:
        """Extract calendar/booking links (Calendly, Acuity, etc)."""
        calendars = []
        for link in self.soup.find_all("a", href=True):
            href = link["href"]
            if any(x in href for x in ["calendly.com", "acuityscheduling.com", "setmore.com"]):
                calendars.append(
                    EvidenceItem(
                        value=href,
                        method="link",
                        source=self.url,
                        confidence=0.99,
                    )
                )
        return calendars

    # ────────────────────────────────────────────────────────────────────
    # Technical
    # ────────────────────────────────────────────────────────────────────

    def _extract_schema(self) -> list[SchemaEvidence]:
        """Extract raw JSON-LD schemas."""
        schemas = extract_schema(self.html, self.soup, self.url)
        evidence = []

        # extract_schema() returns a list of schema dicts
        for schema_dict in schemas:
            if schema_dict:
                # Get schema type from @type field
                schema_type = schema_dict.get("@type", "unknown")
                if isinstance(schema_type, list):
                    schema_type = schema_type[0]  # Use first type if list
                schema_type = str(schema_type).lower()

                evidence.append(
                    SchemaEvidence(
                        schema_type=schema_type,
                        data=schema_dict,
                        source=self.url,
                    )
                )

        return evidence

    def _extract_scripts(self) -> list[ScriptEvidence]:
        """Extract detected technology/scripts."""
        scripts = extract_technology(self.html, self.soup, self.url)
        evidence = []

        for category, techs in scripts.items():
            for tech in techs:
                evidence.append(
                    ScriptEvidence(
                        name=tech,
                        category=category,
                        confidence=0.85,
                        source=self.url,
                    )
                )

        return evidence

    # ────────────────────────────────────────────────────────────────────
    # Footer Evidence
    # ────────────────────────────────────────────────────────────────────

    def _extract_footer_text(self) -> str:
        """Extract footer text."""
        footer = self.soup.find("footer")
        if footer:
            return footer.get_text(strip=True)[:500]
        return ""

    def _extract_footer_emails(self) -> list[EvidenceItem]:
        """Extract emails from footer."""
        footer = self.soup.find("footer")
        emails = []
        if footer:
            for link in footer.find_all("a", href=True):
                if "mailto:" in link["href"]:
                    email = link["href"].replace("mailto:", "")
                    emails.append(
                        EvidenceItem(
                            value=email,
                            method="footer_mailto",
                            source=self.url,
                            confidence=0.99,
                        )
                    )
        return emails

    def _extract_footer_phones(self) -> list[EvidenceItem]:
        """Extract phones from footer."""
        footer = self.soup.find("footer")
        phones = []
        if footer:
            for link in footer.find_all("a", href=True):
                if "tel:" in link["href"]:
                    phone = link["href"].replace("tel:", "")
                    phones.append(
                        EvidenceItem(
                            value=phone,
                            method="footer_tel",
                            source=self.url,
                            confidence=0.99,
                        )
                    )
        return phones

    def _extract_footer_social(self) -> list[EvidenceItem]:
        """Extract social links from footer."""
        footer = self.soup.find("footer")
        socials = []
        if footer:
            for link in footer.find_all("a", href=True):
                href = link["href"]
                if any(x in href for x in ["facebook", "twitter", "instagram", "linkedin", "youtube"]):
                    socials.append(
                        EvidenceItem(
                            value=href,
                            method="footer_link",
                            source=self.url,
                            confidence=0.95,
                        )
                    )
        return socials

    def _extract_copyright(self) -> str:
        """Extract copyright notice."""
        footer = self.soup.find("footer")
        if footer:
            for text in footer.stripped_strings:
                if "©" in text or "copyright" in text.lower():
                    return text
        return ""

    # ────────────────────────────────────────────────────────────────────
    # Page Type Detection (Deterministic, No Classification)
    # ────────────────────────────────────────────────────────────────────

    def _detect_page_type(self) -> str:
        """
        Detect page type from URL and content (deterministic only).

        Returns:
            Page type string (homepage|about|contact|services|team|pricing|locations|faq|booking|unknown)
        """
        from urllib.parse import urlparse
        
        url_lower = self.url.lower()
        
        # Homepage detection - Check if URL is just domain (with or without trailing slash)
        parsed = urlparse(url_lower)
        path = parsed.path.rstrip("/")
        
        if not path or path == "":
            # No path = homepage (root domain)
            return "homepage"
        
        if url_lower.endswith("index.html"):
            return "homepage"

        # URL-based detection
        type_keywords = {
            "about": ["about", "who-we-are", "our-story", "company"],
            "contact": ["contact", "contact-us", "get-in-touch"],
            "services": ["services", "solutions", "offerings"],
            "team": ["team", "our-team", "people", "staff"],
            "pricing": ["pricing", "plans", "rates"],
            "locations": ["locations", "offices", "branches"],
            "faq": ["faq", "frequently-asked"],
            "booking": ["book", "appointment", "schedule"],
        }

        for page_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in url_lower:
                    return page_type

        # Content-based detection (last resort)
        page_text = self.soup.get_text().lower()

        if "faq" in page_text and page_text.count("q:") + page_text.count("question") > 5:
            return "faq"

        return "unknown"
