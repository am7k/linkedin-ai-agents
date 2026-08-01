"""
Comprehensive Edge-Case and Resiliency Test Suite.

Tests feed parsing edge cases, HTTP error scenarios, malformed XML, missing fields,
live concurrent in-memory ingestion, rejection of local file sources,
and configuration validation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import httpx

from rss_agent.parser import (
    parse_rss_content,
    parse_rss_content_elementtree,
    strip_html_tags,
    normalize_pub_date,
)
from rss_agent.models import RSSArticle, FilterCriteria
from rss_agent.pipeline import ArticleStore, RSSPipeline, RSSFetcher
from rss_agent.config import settings, Settings
from tests.conftest import SAMPLE_LIVE_RSS_XML, LIVE_FEED_URL


# ── Edge Case 1: Malformed & Corrupted XML ───────────────────────────────────

def test_parse_malformed_xml():
    malformed_xml = "<rss><channel><title>Broken Feed</title><item><title>Unclosed Tag"
    meta, articles = parse_rss_content(malformed_xml, "https://example.com/feed")
    assert isinstance(meta.title, str)
    assert isinstance(articles, list)


def test_parse_empty_channel_xml():
    empty_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Empty Feed</title>
            <description>No items here</description>
            <link>https://example.com</link>
        </channel>
    </rss>
    """
    meta, articles = parse_rss_content(empty_xml, "https://example.com/feed")
    assert meta.title == "Empty Feed"
    assert len(articles) == 0


def test_parse_missing_fields_in_item():
    partial_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Partial Feed</title>
            <link>https://example.com</link>
            <description>Test</description>
            <item>
                <description>Only description provided</description>
            </item>
        </channel>
    </rss>
    """
    meta, articles = parse_rss_content(partial_xml, "https://example.com/feed")
    assert len(articles) == 1
    art = articles[0]
    assert art.title == ""
    assert art.summary == "Only description provided"
    assert art.author == "Unknown"
    assert art.id is not None


def test_parse_unicode_and_emojis():
    unicode_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Unicode 🚀 Feed</title>
            <link>https://example.com</link>
            <description>Testing unicode: Hello 世界 🌍</description>
            <item>
                <title>AI Revolution 🤖 &amp; Future</title>
                <link>https://example.com/ai</link>
                <description>&lt;p&gt;Content with unicode: Developer &amp; AI ⚡&lt;/p&gt;</description>
            </item>
        </channel>
    </rss>
    """
    meta, articles = parse_rss_content(unicode_xml, "https://example.com/feed")
    assert "🚀" in meta.title or "Unicode" in meta.title
    assert len(articles) == 1
    assert "AI Revolution 🤖 & Future" in articles[0].title
    assert "Developer & AI ⚡" in articles[0].summary


# ── Edge Case 2: Rejection of Local File Paths ───────────────────────────────

@pytest.mark.asyncio
async def test_fetcher_rejects_local_file_paths():
    fetcher = RSSFetcher(timeout=1.0, retries=1)
    
    with pytest.raises(ValueError) as exc1:
        await fetcher.fetch_rss("techcrunch-rss-feed.txt")
    assert "exclusively consumes live RSS feeds" in str(exc1.value)

    with pytest.raises(ValueError) as exc2:
        await fetcher.fetch_rss("file:///C:/local/feed.xml")
    assert "exclusively consumes live RSS feeds" in str(exc2.value)


# ── Edge Case 3: HTTP Networking Resiliency ──────────────────────────────────

@pytest.mark.asyncio
async def test_fetcher_http_404_error():
    fetcher = RSSFetcher(timeout=1.0, retries=1)
    
    req = httpx.Request("GET", "https://example.com/404")
    resp = httpx.Response(404, request=req)

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=resp)):
        with pytest.raises(RuntimeError) as exc_info:
            await fetcher.fetch_rss("https://example.com/404")
        assert "Failed to fetch live RSS feed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetcher_http_timeout():
    fetcher = RSSFetcher(timeout=0.1, retries=2)
    
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(RuntimeError) as exc_info:
            await fetcher.fetch_rss("https://example.com/slow")
        assert "timed out" in str(exc_info.value) or "Failed to fetch live RSS feed" in str(exc_info.value)


# ── Edge Case 4: In-Memory Resiliency & High Concurrency ─────────────────────

@pytest.mark.asyncio
async def test_high_volume_and_concurrent_in_memory_ingestion():
    store = ArticleStore()
    pipeline = RSSPipeline(store=store)

    req = httpx.Request("GET", LIVE_FEED_URL)
    resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=resp)):
        tasks = [pipeline.ingest_source(LIVE_FEED_URL) for _ in range(5)]
        reports = await asyncio.gather(*tasks)

    for r in reports:
        assert r.status == "success"

    assert store.get_stats()["total_articles"] == 2
    assert store.get_stats()["storage_type"] == "in_memory_ephemeral"


# ── Edge Case 5: Configuration Validation ────────────────────────────────────

def test_settings_validation():
    s = Settings(default_rss_feed="https://techcrunch.com/feed/")
    assert s.validate() is True


def test_settings_validation_invalid_feed_scheme():
    s = Settings(default_rss_feed="techcrunch-rss-feed.txt")
    with pytest.raises(ValueError) as exc:
        s.validate()
    assert "Production RSS pipeline exclusively accepts live HTTP/HTTPS URLs" in str(exc.value)
