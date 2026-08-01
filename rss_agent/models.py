"""
Domain Data Models.

Defines type-safe data structures for normalized RSS articles, feed metadata,
ingestion diagnostics, and search/filter parameters.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import hashlib
import json

@dataclass
class RSSArticle:
    """Normalized technology news article representation."""
    id: str                                  # Unique SHA-256 fingerprint ID
    guid: str                                # Original RSS GUID or ID
    title: str                               # Article title
    link: str                                # Canonical URL link
    summary: str                             # Plaintext executive summary / excerpt
    content_raw: Optional[str] = None        # Raw HTML or CDATA content
    author: str = "Unknown"                  # Author / creator name
    published_at: str = ""                   # ISO-8601 formatted publication timestamp
    categories: List[str] = field(default_factory=list) # List of category tags
    feed_url: str = ""                       # Source feed URL or file identifier
    ingested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def generate_id(cls, guid: str, title: str, link: str) -> str:
        """Generate deterministic SHA-256 fingerprint for deduplication."""
        unique_seed = f"{guid or ''}|{title or ''}|{link or ''}"
        return hashlib.sha256(unique_seed.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RSSArticle":
        """Reconstruct model from dictionary."""
        return cls(**data)


@dataclass
class FeedMetadata:
    """Channel/Feed level metadata."""
    title: str
    link: str
    description: str
    last_build_date: Optional[str] = None
    language: Optional[str] = None
    generator: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IngestionReport:
    """Diagnostic report generated after an ingestion run."""
    feed_source: str
    status: str                              # "success" or "error"
    total_found: int = 0
    new_added: int = 0
    duplicates_skipped: int = 0
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FilterCriteria:
    """Filter and query criteria for stored articles."""
    category: Optional[str] = None
    keyword: Optional[str] = None
    limit: int = 10
    min_date: Optional[str] = None
