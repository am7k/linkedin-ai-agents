"""
Live Stateless RSS Ingestion Pipeline and In-Memory Article Store.

Provides thread-safe in-memory article storage, live asynchronous HTTP/HTTPS RSS feed fetching with retries,
fingerprint-based deduplication, and search/query functionality.
Operates 100% in-memory with zero disk persistence.
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone
import httpx

from .config import settings
from .models import RSSArticle, FeedMetadata, IngestionReport, FilterCriteria
from .parser import parse_rss_content

logger = logging.getLogger(__name__)


class ArticleStore:
    """Thread-safe, ephemeral in-memory store for normalized RSS articles and feed metadata."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._articles: Dict[str, RSSArticle] = {}
        self._feeds: Dict[str, Dict[str, Any]] = {}

    async def add_articles(
        self, feed_source: str, meta: FeedMetadata, new_articles: List[RSSArticle]
    ) -> Tuple[int, int]:
        """
        Add new articles to in-memory store, performing deduplication by article fingerprint ID.
        Returns tuple of (added_count, skipped_count).
        """
        async with self._lock:
            self._feeds[feed_source] = {
                "metadata": meta.to_dict(),
                "last_ingested": datetime.now(timezone.utc).isoformat(),
            }
            
            added = 0
            skipped = 0
            for art in new_articles:
                if art.id in self._articles:
                    skipped += 1
                else:
                    self._articles[art.id] = art
                    added += 1

            return added, skipped

    def get_article(self, article_id: str) -> Optional[RSSArticle]:
        """Retrieve article by fingerprint ID from memory."""
        return self._articles.get(article_id)

    def list_articles(self, criteria: Optional[FilterCriteria] = None) -> List[RSSArticle]:
        """Retrieve and filter in-memory stored articles sorted by publication date descending."""
        results = list(self._articles.values())

        if not criteria:
            return sorted(results, key=lambda a: a.published_at or "", reverse=True)

        if criteria.category:
            cat_lower = criteria.category.lower()
            results = [
                a for a in results
                if any(cat_lower in c.lower() for c in a.categories)
            ]

        if criteria.keyword:
            kw = criteria.keyword.lower()
            results = [
                a for a in results
                if kw in a.title.lower()
                or kw in a.summary.lower()
                or any(kw in c.lower() for c in a.categories)
            ]

        results = sorted(results, key=lambda a: a.published_at or "", reverse=True)
        return results[: criteria.limit]

    def search(self, query: str, limit: int = 10) -> List[RSSArticle]:
        """Search articles matching text query in title, summary, content, or categories."""
        return self.list_articles(FilterCriteria(keyword=query, limit=limit))

    def clear(self) -> None:
        """Clear all in-memory articles and feed metadata."""
        self._articles.clear()
        self._feeds.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Return store summary metrics."""
        return {
            "total_articles": len(self._articles),
            "total_feeds": len(self._feeds),
            "storage_type": "in_memory_ephemeral",
            "feeds": list(self._feeds.keys()),
        }


class RSSFetcher:
    """Asynchronous live HTTP/HTTPS RSS fetcher with retries and error resilience."""

    def __init__(
        self, timeout: float = settings.http_timeout, retries: int = settings.http_retries
    ):
        self.timeout = timeout
        self.retries = retries

    async def fetch_rss(self, source: str) -> str:
        """
        Fetch RSS feed content exclusively from a live HTTP/HTTPS URL.
        Rejects local file paths and file:// scheme URLs.
        """
        source_clean = source.strip()

        if not source_clean.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid RSS feed URL '{source}'. Production system exclusively consumes "
                "live RSS feeds from HTTP/HTTPS URLs. Local files or file:// schemes are not permitted."
            )

        headers = {
            "User-Agent": "ADK-RSS-Agent/1.0 (Google ADK Production RSS Aggregator)"
        }
        
        last_exception = None
        for attempt in range(1, self.retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout, follow_redirects=True
                ) as client:
                    response = await client.get(source_clean, headers=headers)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"HTTP fetch attempt {attempt}/{self.retries} failed for {source_clean}: {e}"
                )
                if attempt < self.retries:
                    await asyncio.sleep(1.0 * attempt)

        raise RuntimeError(
            f"Failed to fetch live RSS feed from {source_clean} after {self.retries} attempts: {last_exception}"
        )


class RSSPipeline:
    """High-level orchestration pipeline for ingesting live RSS sources into memory."""

    def __init__(self, store: Optional[ArticleStore] = None):
        self.store = store or ArticleStore()
        self.fetcher = RSSFetcher()

    async def ingest_source(self, source: str) -> IngestionReport:
        """Fetch, parse, deduplicate, and ingest articles from a single live RSS feed URL in memory."""
        logger.info(f"Beginning live in-memory ingestion for source: {source}")
        try:
            raw_xml = await self.fetcher.fetch_rss(source)
            meta, articles = parse_rss_content(raw_xml, feed_source=source)
            
            added, skipped = await self.store.add_articles(source, meta, articles)
            
            report = IngestionReport(
                feed_source=source,
                status="success",
                total_found=len(articles),
                new_added=added,
                duplicates_skipped=skipped,
            )
            logger.info(
                f"In-memory ingestion complete for {source}: {added} new articles added, {skipped} duplicates skipped."
            )
            return report

        except Exception as e:
            logger.error(f"Ingestion failed for {source}: {e}", exc_info=True)
            return IngestionReport(
                feed_source=source,
                status="error",
                error_message=str(e),
            )
