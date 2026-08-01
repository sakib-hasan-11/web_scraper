"""
Pydantic schemas for API request and response validation.
"""

from pydantic import BaseModel, HttpUrl, field_validator


class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze."""

    url: str
    debug: bool = False  # Optional: include timing/diagnostics in response

    @field_validator("url")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty")
        return v.strip()


class ErrorResponse(BaseModel):
    """Standard error response shape."""

    success: bool = False
    error: str
    details: str = ""
