"""
Email Quality Engine.

Filters out system emails and classifies business emails.

Prevents false positives from common system providers (Sentry, Cloudflare, etc).
"""

import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class EmailCategory(Enum):
    """Email classification categories."""
    BUSINESS = "business"      # Legitimate business email
    SUPPORT = "support"        # Support desk email
    SALES = "sales"            # Sales team email
    MARKETING = "marketing"    # Marketing/newsletter email
    PERSONAL = "personal"      # Personal email
    SYSTEM = "system"          # System-generated email
    UNKNOWN = "unknown"        # Could not classify


# Block list: System providers and non-business domains
SYSTEM_DOMAINS = {
    # Wix/Website builders
    "sentry.wixpress.com",
    "sentry-next.wixpress.com",
    "mail.wixpress.com",
    
    # CDNs and infrastructure
    "cloudflare.com",
    "fastmail.com",
    
    # Google
    "googleusercontent.com",
    "noreply@google.com",
    
    # Common system emails
    "noreply",
    "donotreply",
    "no-reply",
    "notification",
    "system",
    "admin",
    "webmaster",
    
    # Localhost and test
    "localhost",
    "example.com",
    "test.com",
    
    # Email tracking
    "bounce",
    "mailer-daemon",
    "postmaster",
}

# Allow list: Known business email patterns
BUSINESS_PATTERNS = {
    r"^(info|contact|hello|support|sales)@",  # Common business emails
    r"^[a-z\.]+(info|contact|hello|support|sales)@",  # Name-prefixed business
}

# Support-specific patterns
SUPPORT_PATTERNS = {
    r"^(support|help|assistance|service)@",
}

# Sales-specific patterns
SALES_PATTERNS = {
    r"^(sales|quote|pricing|business)@",
}

# Marketing-specific patterns
MARKETING_PATTERNS = {
    r"^(marketing|newsletter|promo|campaign)@",
}


def is_system_email(email: str) -> bool:
    """
    Check if email is from a system provider (block list).

    Args:
        email: Email address

    Returns:
        True if email should be blocked (system/non-business)
    """
    if not email:
        return True

    email_lower = email.lower()

    # Check for system keywords
    for system_keyword in SYSTEM_DOMAINS:
        if system_keyword in email_lower:
            return True

    # Check for noreply/no-reply
    if any(x in email_lower for x in ["noreply", "no-reply", "donotreply"]):
        return True

    # Check for localhost
    if email_lower.endswith("@localhost"):
        return True

    return False


def classify_email(email: str) -> EmailCategory:
    """
    Classify email into category.

    Args:
        email: Email address

    Returns:
        EmailCategory
    """
    if not email:
        return EmailCategory.UNKNOWN

    email_lower = email.lower()

    # Check if system email
    if is_system_email(email):
        return EmailCategory.SYSTEM

    # Check support patterns
    for pattern in SUPPORT_PATTERNS:
        if re.match(pattern, email_lower):
            return EmailCategory.SUPPORT

    # Check sales patterns
    for pattern in SALES_PATTERNS:
        if re.match(pattern, email_lower):
            return EmailCategory.SALES

    # Check marketing patterns
    for pattern in MARKETING_PATTERNS:
        if re.match(pattern, email_lower):
            return EmailCategory.MARKETING

    # Check business patterns
    for pattern in BUSINESS_PATTERNS:
        if re.match(pattern, email_lower):
            return EmailCategory.BUSINESS

    # Personal email check (gmail.com, yahoo.com, etc)
    if re.search(r"@(gmail|yahoo|hotmail|outlook|aol|protonmail)\.com$", email_lower):
        return EmailCategory.PERSONAL

    # Default to unknown if domain-specific
    if "@" in email:
        return EmailCategory.UNKNOWN

    return EmailCategory.UNKNOWN


def filter_and_classify_emails(emails: list[str]) -> dict[str, list[dict]]:
    """
    Filter and classify emails.

    Returns organized dict of categorized emails.

    Args:
        emails: List of email addresses

    Returns:
        {
            "business": [{"email": "", "confidence": 0.95}],
            "support": [...],
            "sales": [...],
            "system_blocked": [...],
            "unknown": [...]
        }
    """
    result = {
        "business": [],
        "support": [],
        "sales": [],
        "marketing": [],
        "personal": [],
        "system_blocked": [],
        "unknown": [],
    }

    seen = set()

    for email in emails:
        if not email or email in seen:
            continue

        seen.add(email)
        email_lower = email.lower()

        # Classify
        category = classify_email(email)

        # Determine confidence
        if category == EmailCategory.BUSINESS:
            confidence = 0.95
        elif category == EmailCategory.SUPPORT:
            confidence = 0.90
        elif category == EmailCategory.SALES:
            confidence = 0.90
        elif category == EmailCategory.MARKETING:
            confidence = 0.85
        elif category == EmailCategory.PERSONAL:
            confidence = 0.70
        elif category == EmailCategory.SYSTEM:
            confidence = 0.0  # Should be blocked
        else:
            confidence = 0.50

        entry = {
            "email": email,
            "confidence": confidence,
            "category": category.value,
        }

        # Add to appropriate list
        if category == EmailCategory.BUSINESS:
            result["business"].append(entry)
        elif category == EmailCategory.SUPPORT:
            result["support"].append(entry)
        elif category == EmailCategory.SALES:
            result["sales"].append(entry)
        elif category == EmailCategory.MARKETING:
            result["marketing"].append(entry)
        elif category == EmailCategory.PERSONAL:
            result["personal"].append(entry)
        elif category == EmailCategory.SYSTEM:
            result["system_blocked"].append(entry)
        else:
            result["unknown"].append(entry)

    return result


def get_verified_business_emails(emails: list[str]) -> list[str]:
    """
    Get only verified business emails (filters out system/spam).

    Args:
        emails: List of email addresses

    Returns:
        List of business-relevant emails, sorted by priority
    """
    classified = filter_and_classify_emails(emails)

    # Priority order: business > support > sales > marketing
    verified = []
    verified.extend([e["email"] for e in classified["business"]])
    verified.extend([e["email"] for e in classified["support"]])
    verified.extend([e["email"] for e in classified["sales"]])
    verified.extend([e["email"] for e in classified["marketing"]])

    return verified
