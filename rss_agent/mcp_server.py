#!/usr/bin/env python3
"""
Low-Level Model Context Protocol (MCP) Server for RSS Processing Pipeline.

Exposes MCP tools via Stdio transport:
- ingest_rss_feed
- list_rss_articles
- get_article_details
- search_tech_articles
- get_pipeline_stats
"""

import sys
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any

# MCP low-level stdio server imports
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# ADK FunctionTool wrapper & conversion utils
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

from .pipeline import RSSPipeline, ArticleStore
from .models import FilterCriteria, RSSArticle
from .config import settings
from .prompt_manager import default_manager as prompt_manager

# Configure logging to stderr to prevent stdio protocol pollution
logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("mcp_server")

# Shared global store instance
store = ArticleStore()
pipeline = RSSPipeline(store=store)

# Fail-fast validate tool prompts on startup
prompt_manager.validate_prompts(
    required_agents=[],
    required_tools=[
        "ingest_rss_feed",
        "list_rss_articles",
        "get_article_details",
        "search_tech_articles",
        "get_pipeline_stats"
    ]
)


# ── ADK Tool Functions ───────────────────────────────────────────────────────

async def ingest_rss_feed(feed_source: Optional[str] = None) -> Dict[str, Any]:
    target = feed_source or settings.default_rss_feed
    logger.info(f"Tool ingest_rss_feed called for target: {target}")
    report = await pipeline.ingest_source(target)
    return report.to_dict()
# Inject description from prompt manager
ingest_rss_feed.__doc__ = prompt_manager.get_tool_prompt("ingest_rss_feed")


async def list_rss_articles(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: Optional[int] = 10,
) -> Dict[str, Any]:
    criteria = FilterCriteria(
        category=category,
        keyword=keyword,
        limit=limit if limit is not None else 10,
    )
    articles = store.list_articles(criteria)
    return {
        "status": "ok",
        "count": len(articles),
        "articles": [a.to_dict() for a in articles],
    }
# Inject description from prompt manager
list_rss_articles.__doc__ = prompt_manager.get_tool_prompt("list_rss_articles")


async def get_article_details(article_id: str) -> Dict[str, Any]:
    art = store.get_article(article_id)
    if not art:
        return {"status": "error", "message": f"Article ID '{article_id}' not found."}
    return {"status": "ok", "article": art.to_dict()}
# Inject description from prompt manager
get_article_details.__doc__ = prompt_manager.get_tool_prompt("get_article_details")


async def search_tech_articles(query: str, limit: Optional[int] = 5) -> Dict[str, Any]:
    results = store.search(query=query, limit=limit if limit is not None else 5)
    return {
        "status": "ok",
        "query": query,
        "count": len(results),
        "results": [a.to_dict() for a in results],
    }
# Inject description from prompt manager
search_tech_articles.__doc__ = prompt_manager.get_tool_prompt("search_tech_articles")


async def get_pipeline_stats() -> Dict[str, Any]:
    stats = store.get_stats()
    stats["status"] = "ok"
    return stats
# Inject description from prompt manager
get_pipeline_stats.__doc__ = prompt_manager.get_tool_prompt("get_pipeline_stats")


# ── Wrap tools with ADK FunctionTool ─────────────────────────────────────────

tool_ingest = FunctionTool(ingest_rss_feed)
tool_list = FunctionTool(list_rss_articles)
tool_details = FunctionTool(get_article_details)
tool_search = FunctionTool(search_tech_articles)
tool_stats = FunctionTool(get_pipeline_stats)

ALL_TOOLS = [tool_ingest, tool_list, tool_details, tool_search, tool_stats]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


# ── Low-Level MCP Server Setup ───────────────────────────────────────────────

app = Server("adk-rss-mcp-server")


@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    """Expose available MCP tools."""
    return [adk_to_mcp_tool_type(tool) for tool in ALL_TOOLS]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[mcp_types.Content]:
    """Execute an MCP tool call and return JSON TextContent."""
    if name not in TOOL_MAP:
        err = {"error": f"Unknown tool '{name}'"}
        return [mcp_types.TextContent(type="text", text=json.dumps(err))]

    target_tool = TOOL_MAP[name]
    try:
        result = await target_tool.run_async(args=arguments, tool_context=None)
        return [mcp_types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
        err = {"error": f"Tool execution failed: {str(e)}"}
        return [mcp_types.TextContent(type="text", text=json.dumps(err))]


async def run_mcp_stdio():
    """Run low-level stdio server."""
    logger.info("Starting RSS MCP Server on stdio transport...")
    async with mcp.server.stdio.stdio_server() as (r, w):
        await app.run(
            r,
            w,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(run_mcp_stdio())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user.")
