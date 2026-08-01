# Production-Grade Live Stateless RSS Processing Pipeline & Google ADK AI Agent

A production-ready AI Agent and Model Context Protocol (MCP) server built with **Google ADK (Agent Development Kit)** and Python. It continuously ingests, normalizes, deduplicates, and analyzes live technology news RSS feeds (such as TechCrunch), offering rich interaction capabilities via MCP tools and a multi-agent Google ADK workflow powered by **Gemini Flash-Lite (`gemini-2.5-flash-lite`)**.

The system is **100% stateless** with respect to RSS articles — feeds are fetched live over HTTP/HTTPS, processed in memory, passed to the AI agent / MCP tools, and discarded. Zero article content is saved to disk.

---

## Key Features

- **100% Stateless Architecture**: No persistent database, no SQLite, no JSON storage files, no disk caching. All RSS article processing happens in-memory for the lifetime of the execution session.
- **Live RSS Ingestion**: Exclusively consumes live RSS feeds from HTTP/HTTPS URLs (e.g. `https://techcrunch.com/feed/`). Rejects local offline files and `file://` scheme URLs.
- **Gemini Flash-Lite Model**: Powered by the latest Gemini Flash-Lite (`gemini-2.5-flash-lite`) model across all Google ADK agent roles.
- **Google ADK Multi-Agent Architecture**: Built using Google ADK `Agent`, `LoopAgent`, `AgentTool`, and `MCPToolset`.
- **Low-Level MCP Server**: Exposes standard MCP tools over `stdio` transport (`ingest_rss_feed`, `list_rss_articles`, `get_article_details`, `search_tech_articles`, `get_pipeline_stats`).
- **In-Memory Fingerprint Deduplication**: Uses SHA-256 fingerprinting on article GUIDs and content tuples to guarantee idempotent processing during live feed ingestion.
- **LinkedIn Post Generation**: Includes specialized ADK loop agents that automatically draft mobile-optimized technical LinkedIn posts adhering to strict formatting rules.

---

## Directory Structure

```
linkedin-ai-agents/
├── trending-linkedin-agent.md      # LinkedIn content strategy reference
├── requirements.txt                # Package dependencies
├── .env.example                    # Environment settings template
├── README.md                       # Complete documentation
├── ARCHITECTURE.md                 # System architecture overview
├── rss_agent/                      # Core Python Package
│   ├── __init__.py
│   ├── config.py                   # Environment & settings validation (Gemini Flash-Lite & Live URL checks)
│   ├── models.py                   # Dataclass & Pydantic domain models
│   ├── parser.py                   # RSS/Atom normalization & HTML sanitization
│   ├── pipeline.py                 # Live async HTTP/HTTPS fetching, deduplication & in-memory store
│   ├── mcp_server.py               # Low-level MCP stdio server
│   ├── agent.py                    # Google ADK agent configurations & tools
│   └── cli.py                      # CLI runner interface
└── tests/                          # Test Suite
    ├── conftest.py                 # Shared live feed fixtures and mocks
    ├── test_parser.py              # Parser unit tests
    ├── test_pipeline.py            # In-memory ingestion & zero file persistence tests
    ├── test_edge_cases.py          # Network resiliency & local file rejection tests
    ├── test_mcp_server.py          # MCP tool integration tests
    ├── test_mcp_advanced.py        # Boundary & error payload tests
    ├── test_agent.py               # Google ADK Agent structure tests
    ├── test_agent_advanced.py      # Agent prompt & tool tests
    └── test_cli.py                 # CLI interface tests
```

---

## Quick Start & Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.14 compatible)
- Google AI Studio API Key

### 2. Environment Setup

```bash
# Navigate to project directory
cd linkedin-ai-agents

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Linux/macOS: source venv/bin/activate)

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and set your configuration variables:

```bash
GEMINI_API_KEY=your_google_ai_studio_api_key
MODEL=gemini-2.5-flash-lite
DEFAULT_RSS_FEED=https://techcrunch.com/feed/
```

---

## CLI Usage

The package includes a CLI runner for easy interaction:

### Ingest Live RSS Feed (In Memory)
```bash
# Ingest live TechCrunch HTTP feed
python -m rss_agent.cli ingest --source https://techcrunch.com/feed/
```

### List Articles (In Memory)
```bash
# List top 10 in-memory articles
python -m rss_agent.cli list

# List articles filtered by category
python -m rss_agent.cli list --category AI --limit 5
```

### Search Tech Articles
```bash
python -m rss_agent.cli search --query "OpenAI" --limit 3
```

### Check In-Memory Pipeline Statistics
```bash
python -m rss_agent.cli stats
```

### Launch MCP Stdio Server
```bash
python -m rss_agent.cli mcp
```

---

## MCP Server & Available Tools

The MCP server connects to AI desktop applications over standard input/output (`stdio`).

| MCP Tool Name | Description | Parameters |
|---|---|---|
| `ingest_rss_feed` | Ingests tech articles into memory from a live HTTP/HTTPS feed URL | `feed_source` (optional string) |
| `list_rss_articles` | Retrieves in-memory articles with filtering options | `category` (str), `keyword` (str), `limit` (int) |
| `get_article_details` | Gets complete article metadata by SHA-256 ID | `article_id` (str) |
| `search_tech_articles` | Performs full-text search across in-memory articles | `query` (str), `limit` (int) |
| `get_pipeline_stats` | Returns in-memory store & pipeline metrics | None |

---

## Testing

Run the automated pytest suite:

```bash
pytest -v
```

All tests verify that the application is completely stateless, processes articles exclusively in memory, creates zero files on disk, and rejects local file schemes.
