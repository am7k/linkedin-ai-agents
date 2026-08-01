"""
Command Line Interface (CLI) for Live RSS AI Agent & MCP Server.

Usage:
  python -m rss_agent.cli ingest [--source URL]
  python -m rss_agent.cli list [--category CAT] [--limit N]
  python -m rss_agent.cli search --query QUERY
  python -m rss_agent.cli stats
  python -m rss_agent.cli mcp
"""

import sys
import argparse
import asyncio
import json
from pathlib import Path

from .config import settings
from .pipeline import RSSPipeline, ArticleStore
from .models import FilterCriteria
from .mcp_server import run_mcp_stdio


def main():
    parser = argparse.ArgumentParser(
        description="Production Live RSS Processing Pipeline & Google ADK Agent CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Ingest live RSS feed from URL")
    ingest_parser.add_argument(
        "--source",
        type=str,
        default=settings.default_rss_feed,
        help="Live RSS feed HTTP/HTTPS URL (default: https://techcrunch.com/feed/)",
    )

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List stored articles")
    list_parser.add_argument("--category", type=str, help="Filter by category")
    list_parser.add_argument("--limit", type=int, default=10, help="Max results")

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search articles by keyword")
    search_parser.add_argument("--query", type=str, required=True, help="Search query string")
    search_parser.add_argument("--limit", type=int, default=5, help="Max results")

    # Stats subcommand
    subparsers.add_parser("stats", help="Display pipeline database stats")

    # MCP server subcommand
    subparsers.add_parser("mcp", help="Run MCP stdio server")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "ingest":
        asyncio.run(_run_ingest(args.source))
    elif args.command == "list":
        _run_list(args.category, args.limit)
    elif args.command == "search":
        _run_search(args.query, args.limit)
    elif args.command == "stats":
        _run_stats()
    elif args.command == "mcp":
        asyncio.run(run_mcp_stdio())


async def _run_ingest(source: str):
    print(f"[*] Ingesting live RSS feed source: {source}...")
    pipeline = RSSPipeline()
    report = await pipeline.ingest_source(source)
    print(f"[+] Ingestion Result:")
    print(json.dumps(report.to_dict(), indent=2))


def _run_list(category: str, limit: int):
    store = ArticleStore()
    articles = store.list_articles(FilterCriteria(category=category, limit=limit))
    print(f"[+] Found {len(articles)} articles:")
    for a in articles:
        print(f" - [{a.id}] {a.title} ({a.published_at})")
        print(f"   Categories: {', '.join(a.categories)}")
        print(f"   Link: {a.link}\n")


def _run_search(query: str, limit: int):
    store = ArticleStore()
    results = store.search(query=query, limit=limit)
    print(f"[+] Search results for '{query}' ({len(results)} found):")
    for a in results:
        print(f" - [{a.id}] {a.title}")
        print(f"   Summary: {a.summary[:150]}...\n")


def _run_stats():
    store = ArticleStore()
    stats = store.get_stats()
    print("[+] Database Statistics:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
