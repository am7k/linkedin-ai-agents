"""
Configuration Management Module.

Loads configuration from environment variables and provides sensible production defaults.
Validates live RSS feed URL requirement and Gemini Flash-Lite model settings.
Completely stateless with zero disk storage configuration.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()


@dataclass
class Settings:
    """Production configuration settings for the Live RSS AI Agent pipeline."""

    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL", "gemini-2.5-flash-lite"))
    default_rss_feed: str = field(
        default_factory=lambda: os.getenv("DEFAULT_RSS_FEED", "https://techcrunch.com/feed/")
    )
    http_timeout: float = field(default_factory=lambda: float(os.getenv("HTTP_TIMEOUT", "10.0")))
    http_retries: int = field(default_factory=lambda: int(os.getenv("HTTP_RETRIES", "3")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def validate(self) -> bool:
        """Validate critical configuration settings."""
        # Validate that default RSS feed is a valid HTTP/HTTPS URL
        if not self.default_rss_feed.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid DEFAULT_RSS_FEED '{self.default_rss_feed}'. "
                "Production RSS pipeline exclusively accepts live HTTP/HTTPS URLs."
            )
        return True


settings = Settings()
settings.validate()
