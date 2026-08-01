"""
Application configuration.

All settings are read from environment variables or fall back to defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised configuration for the Website Intelligence Service."""

    # Crawling
    max_pages: int = 10
    concurrency: int = 5
    timeout_seconds: int = 15

    # App metadata
    app_name: str = "Website Intelligence Service"
    app_version: str = "1.0.0"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
