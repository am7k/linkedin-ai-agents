"""
Integration tests for low-level MCP server and tool bindings with live RSS HTTP mocks.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
import httpx

from rss_agent.mcp_server import (
    app,
    list_tools,
    call_tool,
    ingest_rss_feed,
    list_rss_articles,
    search_tech_articles,
    get_pipeline_stats,
)
from tests.conftest import SAMPLE_LIVE_RSS_XML, LIVE_FEED_URL


@pytest.mark.asyncio
async def test_mcp_list_tools():
    tools = await list_tools()
    tool_names = [t.name for t in tools]
    assert "ingest_rss_feed" in tool_names
    assert "list_rss_articles" in tool_names
    assert "get_article_details" in tool_names
    assert "search_tech_articles" in tool_names
    assert "get_pipeline_stats" in tool_names


@pytest.mark.asyncio
async def test_mcp_call_tool_ingest_and_search():
    req = httpx.Request("GET", LIVE_FEED_URL)
    mock_resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)):
        # Ingest feed via MCP tool execution
        ingest_result = await call_tool(
            name="ingest_rss_feed",
            arguments={"feed_source": LIVE_FEED_URL},
        )
        assert len(ingest_result) == 1
        ingest_data = json.loads(ingest_result[0].text)
        assert ingest_data.get("status") == "success"

        # Search articles via MCP tool execution
        search_result = await call_tool(
            name="search_tech_articles",
            arguments={"query": "OpenAI", "limit": 3},
        )
        assert len(search_result) == 1
        search_data = json.loads(search_result[0].text)
        assert search_data.get("status") == "ok"
        assert search_data.get("count") > 0

        # Get stats via MCP tool execution
        stats_result = await call_tool(
            name="get_pipeline_stats",
            arguments={},
        )
        stats_data = json.loads(stats_result[0].text)
        assert stats_data.get("status") == "ok"
        assert stats_data.get("total_articles") > 0
