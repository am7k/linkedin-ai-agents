"""
Advanced MCP Tool Functionality, Parameter Validation, and Boundary Test Suite.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
import httpx

from rss_agent.mcp_server import (
    call_tool,
    ingest_rss_feed,
    list_rss_articles,
    get_article_details,
    search_tech_articles,
    get_pipeline_stats,
    store,
)
from tests.conftest import SAMPLE_LIVE_RSS_XML, LIVE_FEED_URL


@pytest.fixture(autouse=True)
def mock_httpx_rss():
    req = httpx.Request("GET", LIVE_FEED_URL)
    resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=resp)):
        yield


@pytest.mark.asyncio
async def test_mcp_ingest_rss_feed_default():
    result = await ingest_rss_feed(feed_source=LIVE_FEED_URL)
    assert result.get("status") == "success"
    assert result.get("total_found") > 0


@pytest.mark.asyncio
async def test_mcp_list_rss_articles_boundaries():
    await ingest_rss_feed(feed_source=LIVE_FEED_URL)

    # Test with zero limit
    res_zero = await list_rss_articles(limit=0)
    assert res_zero.get("status") == "ok"
    assert len(res_zero.get("articles")) == 0

    # Test with non-matching category
    res_cat = await list_rss_articles(category="NonExistentCategoryXYZ")
    assert res_cat.get("status") == "ok"
    assert len(res_cat.get("articles")) == 0

    # Test with keyword search
    res_kw = await list_rss_articles(keyword="Rivian")
    assert res_kw.get("status") == "ok"
    assert len(res_kw.get("articles")) > 0


@pytest.mark.asyncio
async def test_mcp_get_article_details_valid_and_invalid():
    await ingest_rss_feed(feed_source=LIVE_FEED_URL)
    all_arts = store.list_articles()
    assert len(all_arts) > 0

    valid_id = all_arts[0].id
    res_valid = await get_article_details(article_id=valid_id)
    assert res_valid.get("status") == "ok"
    assert res_valid.get("article").get("id") == valid_id

    res_invalid = await get_article_details(article_id="non_existent_id_9999")
    assert res_invalid.get("status") == "error"
    assert "not found" in res_invalid.get("message")


@pytest.mark.asyncio
async def test_mcp_unknown_tool_call():
    result = await call_tool(name="unknown_fake_tool", arguments={})
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "Unknown tool" in data["error"]


@pytest.mark.asyncio
async def test_mcp_tool_execution_exception():
    result = await call_tool(name="get_article_details", arguments={})
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
