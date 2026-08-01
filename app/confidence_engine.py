"""
Confidence scoring engine.

Provides standardized confidence scoring for all extracted values.

Confidence factors:
- Source (schema=99%, mailto=95%, footer=85%, visible=75%, regex=50%)
- Validation (valid format=+20%, invalid=-50%)
- Redundancy (found on multiple pages=+10%)
- Recency (found on important pages first=+5%)
"""

import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ExtractionSource(Enum):
    """Source of extracted value."""
    SCHEMA = "schema"               # JSON-LD or microdata
    MAILTO = "mailto"               # mailto: link
    TEL = "tel"                     # tel: link
    FOOTER = "footer"               # In <footer> element
    VISIBLE = "visible"             # Visible text on page
    REGEX = "regex"                 # Pattern matched
    FORM = "form"                   # From form action/method
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """Confidence level categories."""
    VERY_HIGH = 0.95       # 95-99%
    HIGH = 0.85            # 85-94%
    MEDIUM = 0.70          # 70-84%
    LOW = 0.50             # 50-69%
    VERY_LOW = 0.30        # 30-49%


@dataclass
class ConfidenceScore:
    """Score for a single extracted value."""
    value: str
    confidence: float       # 0.0-1.0
    source: ExtractionSource
    validation: str = ""    # "valid", "invalid", "unvalidated"
    reason: str = ""        # Explanation of score


BASE_CONFIDENCE = {
    ExtractionSource.SCHEMA: 0.99,
    ExtractionSource.MAILTO: 0.95,
    ExtractionSource.TEL: 0.93,
    ExtractionSource.FOOTER: 0.85,
    ExtractionSource.FORM: 0.80,
    ExtractionSource.VISIBLE: 0.75,
    ExtractionSource.REGEX: 0.50,
    ExtractionSource.UNKNOWN: 0.30,
}


def calculate_confidence(
    value: str,
    source: ExtractionSource = ExtractionSource.VISIBLE,
    is_valid: bool = True,
    is_redundant: bool = False,
) -> float:
    """
    Calculate confidence score for extracted value.

    Args:
        value: The extracted value
        source: Source of extraction
        is_valid: Whether value passed validation
        is_redundant: Whether found on multiple pages/sources

    Returns:
        Confidence score 0.0-1.0
    """
    # Start with base confidence
    confidence = BASE_CONFIDENCE.get(source, 0.3)

    # Adjust for validation
    if is_valid:
        confidence = min(0.99, confidence + 0.05)
    else:
        confidence = max(0.0, confidence - 0.30)

    # Adjust for redundancy
    if is_redundant:
        confidence = min(0.99, confidence + 0.08)

    return round(confidence, 2)


def score_email(email: str, source: ExtractionSource) -> ConfidenceScore:
    """
    Score an email address.

    Args:
        email: Email to score
        source: Where it came from

    Returns:
        ConfidenceScore
    """
    # Basic email validation
    is_valid = "@" in email and "." in email.split("@")[-1]

    confidence = calculate_confidence(email, source, is_valid)

    return ConfidenceScore(
        value=email,
        confidence=confidence,
        source=source,
        validation="valid" if is_valid else "invalid",
        reason=f"Source: {source.value}, Valid: {is_valid}",
    )


def score_phone(phone: str, source: ExtractionSource, is_normalized: bool = False) -> ConfidenceScore:
    """
    Score a phone number.

    Args:
        phone: Phone number to score
        source: Where it came from
        is_normalized: Whether in E.164 format

    Returns:
        ConfidenceScore
    """
    # Check if looks like a phone number
    digits = "".join(c for c in phone if c.isdigit())
    is_valid = len(digits) >= 10

    confidence = calculate_confidence(phone, source, is_valid)

    # Bonus for normalized format
    if is_normalized and is_valid:
        confidence = min(0.99, confidence + 0.05)

    return ConfidenceScore(
        value=phone,
        confidence=confidence,
        source=source,
        validation="valid" if is_valid else "invalid",
        reason=f"Source: {source.value}, Digits: {len(digits)}, Normalized: {is_normalized}",
    )


def score_url(url: str, source: ExtractionSource) -> ConfidenceScore:
    """
    Score a URL (social link, website, etc).

    Args:
        url: URL to score
        source: Where it came from

    Returns:
        ConfidenceScore
    """
    is_valid = url.startswith(("http://", "https://", "www."))

    confidence = calculate_confidence(url, source, is_valid)

    return ConfidenceScore(
        value=url,
        confidence=confidence,
        source=source,
        validation="valid" if is_valid else "invalid",
        reason=f"Source: {source.value}, Valid URL: {is_valid}",
    )


def score_text(text: str, source: ExtractionSource, min_length: int = 3) -> ConfidenceScore:
    """
    Score general text content.

    Args:
        text: Text to score
        source: Where it came from
        min_length: Minimum length to consider valid

    Returns:
        ConfidenceScore
    """
    is_valid = len(text) >= min_length and text.strip() != ""

    confidence = calculate_confidence(text, source, is_valid)

    return ConfidenceScore(
        value=text,
        confidence=confidence,
        source=source,
        validation="valid" if is_valid else "invalid",
        reason=f"Source: {source.value}, Length: {len(text)}",
    )


def merge_scores(scores: list[ConfidenceScore]) -> ConfidenceScore:
    """
    Merge multiple scores for same value.

    Prefers highest confidence, but may average similar scores.

    Args:
        scores: List of ConfidenceScores for same value

    Returns:
        Merged ConfidenceScore
    """
    if not scores:
        return ConfidenceScore(
            value="",
            confidence=0.0,
            source=ExtractionSource.UNKNOWN,
            reason="No scores to merge",
        )

    if len(scores) == 1:
        return scores[0]

    # Use highest confidence as primary
    best_score = max(scores, key=lambda s: s.confidence)

    # Calculate average confidence
    avg_confidence = sum(s.confidence for s in scores) / len(scores)

    # Boost confidence if multiple sources agree
    redundancy_boost = min(0.1, (len(scores) - 1) * 0.03)
    final_confidence = min(0.99, avg_confidence + redundancy_boost)

    return ConfidenceScore(
        value=best_score.value,
        confidence=round(final_confidence, 2),
        source=best_score.source,
        validation=best_score.validation,
        reason=f"Merged from {len(scores)} sources, avg: {avg_confidence:.0%}",
    )
