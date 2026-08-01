"""
Team member extraction module.

Extracts team members, staff, and company leadership from pages.
Detects team cards, bio sections, directory listings.
Tracks confidence scores.
"""

import logging
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass

from app.confidence_engine import (
    ExtractionSource,
    ConfidenceScore,
    score_text,
)

logger = logging.getLogger(__name__)


@dataclass
class TeamMember:
    """Extracted team member."""
    name: str
    title: str = ""
    department: str = ""
    email: str = ""
    phone: str = ""
    social_links: dict = None
    confidence: float = 0.0


EXECUTIVE_TITLES = {
    "ceo", "cto", "cfo", "coo", "president", "founder", "co-founder",
    "managing director", "managing partner", "principal", "partner",
    "executive director", "general manager", "vice president", "vp",
}

TITLE_INDICATORS = {
    "founder", "ceo", "cto", "cfo", "developer", "designer", "manager",
    "engineer", "director", "lead", "coach", "trainer", "consultant",
    "analyst", "specialist", "coordinator", "associate", "officer",
}


def extract_team_members(soup: BeautifulSoup, html: str) -> list[ConfidenceScore]:
    """
    Extract team members from page.

    Args:
        soup: BeautifulSoup object
        html: Full HTML content

    Returns:
        List of ConfidenceScore objects (team member data)
    """
    scores = []

    # 1. Look for team/about sections
    team_sections = _find_team_sections(soup)
    for section in team_sections:
        members = _extract_members_from_section(section)
        for member in members:
            member_text = f"{member.name} - {member.title}".strip(" -")
            score = score_text(member_text, ExtractionSource.VISIBLE, min_length=5)
            score.value = member_text  # Store structured data
            scores.append(score)

    # 2. Look for structured data (schema.org)
    schema_members = _extract_schema_members(soup)
    for member in schema_members:
        member_text = f"{member.get('name', '')} - {member.get('title', '')}".strip(" -")
        if member_text:
            score = score_text(member_text, ExtractionSource.SCHEMA, min_length=5)
            scores.append(score)

    # 3. Look for common patterns (LinkedIn, company page links)
    linkedin_links = soup.find_all("a", href=re.compile(r"linkedin\.com/in/", re.I))
    for link in linkedin_links:
        name = link.get_text(strip=True)
        if name:
            score = score_text(name, ExtractionSource.VISIBLE, min_length=2)
            scores.append(score)

    # Deduplicate by name
    seen = set()
    unique_scores = []
    for score in scores:
        # Extract name (first part before " - ")
        name = score.value.split(" - ")[0].strip()
        if name not in seen and len(name) > 2:
            seen.add(name)
            unique_scores.append(score)

    return unique_scores[:20]  # Limit to 20 team members


def _find_team_sections(soup: BeautifulSoup) -> list[BeautifulSoup]:
    """Find sections that likely contain team information."""
    sections = []

    # Look for common team section patterns
    patterns = [
        {"class": re.compile(r"team|staff|about|leadership", re.I)},
        {"id": re.compile(r"team|staff|about|leadership", re.I)},
    ]

    for pattern in patterns:
        sections.extend(soup.find_all(re.compile(r"section|div|article"), pattern))

    return sections


def _extract_members_from_section(section: BeautifulSoup) -> list[TeamMember]:
    """Extract team member data from a section."""
    members = []

    # Look for team cards (common pattern)
    cards = section.find_all(class_=re.compile(r"card|member|person|bio|team-", re.I))

    for card in cards:
        member = _parse_team_card(card)
        if member.name:
            members.append(member)

    # If no cards found, try parsing raw structure
    if not members:
        # Look for name + title pairs
        headings = section.find_all(re.compile(r"h[2-6]"))
        for heading in headings:
            name = heading.get_text(strip=True)
            # Look for title after heading
            title_elem = heading.find_next(re.compile(r"p|span|div"))
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Check if looks like a title
            if any(indicator in title.lower() for indicator in TITLE_INDICATORS):
                members.append(TeamMember(name=name, title=title))

    return members


def _parse_team_card(card: BeautifulSoup) -> TeamMember:
    """Parse team member data from a card element."""
    member = TeamMember(name="")

    # Find name (usually largest text or has specific class)
    name_elem = card.find(class_=re.compile(r"name|title|heading", re.I))
    if not name_elem:
        name_elem = card.find(re.compile(r"h[3-6]"))
    if not name_elem:
        # Try first significant text
        name_elem = card.find(re.compile(r"p|span|div"))

    if name_elem:
        member.name = name_elem.get_text(strip=True)

    # Find title
    title_elem = card.find(class_=re.compile(r"title|position|role|job", re.I))
    if title_elem:
        member.title = title_elem.get_text(strip=True)
    else:
        # Look for text that looks like a title
        for elem in card.find_all(re.compile(r"p|span")):
            text = elem.get_text(strip=True)
            if any(indicator in text.lower() for indicator in TITLE_INDICATORS):
                member.title = text
                break

    # Find email (if visible)
    email_elem = card.find("a", href=re.compile(r"^mailto:"))
    if email_elem:
        member.email = email_elem.get("href", "").replace("mailto:", "")

    # Find social links
    social = {}
    for link in card.find_all("a", href=True):
        href = link.get("href", "")
        if "linkedin" in href:
            social["linkedin"] = href
        elif "twitter" in href or "x.com" in href:
            social["twitter"] = href
        elif "github" in href:
            social["github"] = href

    if social:
        member.social_links = social

    return member


def _extract_schema_members(soup: BeautifulSoup) -> list[dict]:
    """Extract team members from schema.org data."""
    members = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)

            # Look for Organization with team members
            if isinstance(data, dict) and data.get("@type") == "Organization":
                if "team" in data:
                    team = data["team"]
                    if isinstance(team, list):
                        members.extend(team)
                    else:
                        members.append(team)

                # Also check founder/founder
                if "founder" in data:
                    founder = data["founder"]
                    if isinstance(founder, list):
                        members.extend(founder)
                    else:
                        members.append(founder)

        except:
            pass

    return members


def has_team_page(html: str) -> bool:
    """
    Check if page is likely a team/about page.

    Args:
        html: HTML content

    Returns:
        True if page contains team information
    """
    # Heuristics
    team_indicators = [
        r"our\s+team",
        r"meet\s+(?:the\s+)?team",
        r"team\s+members?",
        r"staff\s+directory",
        r"leadership",
        r"about\s+us",
    ]

    html_lower = html.lower()
    team_count = sum(1 for pattern in team_indicators if re.search(pattern, html_lower))

    return team_count >= 1
