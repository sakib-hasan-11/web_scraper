"""
Application configuration.

All settings are read from environment variables or fall back to defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised configuration for the Website Intelligence Service."""

    # Crawling
    max_pages: int = 6  # MVP: Only crawl 6 pages max (homepage + 5 important pages)
    concurrency: int = 5
    timeout_seconds: int = 12  # Reduced from 15 to 12 for faster crawling
    
    # Debug mode
    debug_mode: bool = False  # Set to True to include timing/diagnostics

    # App metadata
    app_name: str = "Website Intelligence Service"
    app_version: str = "1.0.0"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
