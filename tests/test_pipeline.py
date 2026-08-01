"""
Integration tests for Live Stateless RSS Pipeline, Fingerprint Deduplication, and In-Memory Store.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock
import httpx

from rss_agent.pipeline import ArticleStore, RSSPipeline
from rss_agent.models import FilterCriteria
from tests.conftest import SAMPLE_LIVE_RSS_XML, LIVE_FEED_URL


@pytest.mark.asyncio
async def test_pipeline_in_memory_ingest_and_deduplication():
    store = ArticleStore()
    pipeline = RSSPipeline(store=store)

    req = httpx.Request("GET", LIVE_FEED_URL)
    mock_resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)):
        # First ingestion
        report1 = await pipeline.ingest_source(LIVE_FEED_URL)
        assert report1.status == "success"
        assert report1.total_found > 0
        assert report1.new_added == report1.total_found
        assert report1.duplicates_skipped == 0

        # Second ingestion (in-memory idempotency test)
        report2 = await pipeline.ingest_source(LIVE_FEED_URL)
        assert report2.status == "success"
        assert report2.new_added == 0
        assert report2.duplicates_skipped == report1.total_found


@pytest.mark.asyncio
async def test_store_query_and_search_in_memory():
    store = ArticleStore()
    pipeline = RSSPipeline(store=store)

    req = httpx.Request("GET", LIVE_FEED_URL)
    mock_resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)):
        await pipeline.ingest_source(LIVE_FEED_URL)

    # Test listing in-memory articles
    all_articles = store.list_articles(FilterCriteria(limit=100))
    assert len(all_articles) > 0

    # Test category filtering
    ai_articles = store.list_articles(FilterCriteria(category="AI"))
    assert len(ai_articles) > 0
    for art in ai_articles:
        assert any("ai" in cat.lower() for cat in art.categories)

    # Test search by keyword
    search_results = store.search("OpenAI", limit=5)
    assert len(search_results) > 0
    assert "OpenAI" in search_results[0].title or "OpenAI" in search_results[0].summary


@pytest.mark.asyncio
async def test_pipeline_zero_file_persistence(tmp_path):
    # Capture initial directory state
    initial_files = set(os.listdir(tmp_path))

    store = ArticleStore()
    pipeline = RSSPipeline(store=store)

    req = httpx.Request("GET", LIVE_FEED_URL)
    mock_resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)):
        await pipeline.ingest_source(LIVE_FEED_URL)
        store.search("OpenAI")
        store.get_stats()

    # Verify no new files were created in tmp_path or disk
    final_files = set(os.listdir(tmp_path))
    assert final_files == initial_files
    assert not os.path.exists("data/articles.json")


@pytest.mark.asyncio
async def test_pipeline_rejects_local_file_sources():
    store = ArticleStore()
    pipeline = RSSPipeline(store=store)

    with pytest.raises(ValueError) as exc_info:
        await pipeline.fetcher.fetch_rss("techcrunch-rss-feed.txt")
    assert "exclusively consumes live RSS feeds" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        await pipeline.fetcher.fetch_rss("file:///path/to/feed.xml")
    assert "exclusively consumes live RSS feeds" in str(exc_info.value)
