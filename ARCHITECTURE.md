# Architectural Overview: Production Live Stateless RSS AI Agent & MCP Server

## 1. Executive Summary

This architecture implements a production-grade, asynchronous, **100% stateless** Live RSS Processing Pipeline, Model Context Protocol (MCP) Server, and Google Agent Development Kit (ADK) Multi-Agent System inside `linkedin-ai-agents`.

The system continuously ingests, normalizes, deduplicates, and analyzes technology news articles exclusively from **live HTTP/HTTPS RSS feeds** (such as TechCrunch), processing articles entirely **in-memory** for the lifetime of execution. No article content is ever persisted to disk, saved in a database, or cached between runs. The multi-agent workflow is powered by **Gemini Flash-Lite (`gemini-2.5-flash-lite`)**.

---

## 2. System Layer Diagram

```
                                  ┌───────────────────────────┐
                                  │      User / Caller        │
                                  └─────────────┬─────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
             ┌─────────────────────────┐                 ┌─────────────────────────┐
             │ Google ADK Agent System │                 │  Low-Level MCP Server   │
             │ (Gemini Flash-Lite)     │                 │    (Stdio Transport)    │
             └────────────┬────────────┘                 └────────────┬────────────┘
                          │                                           │
                          └─────────────────────┬─────────────────────┘
                                                ▼
                                 ┌─────────────────────────────┐
                                 │   MCP Toolset Abstraction   │
                                 └──────────────┬──────────────┘
                                                ▼
                                 ┌─────────────────────────────┐
                                 │ Live RSS Ingestion Pipeline │
                                 │ (HTTP/HTTPS Fetcher, Parser,│
                                 │  SHA-256 Deduplication)     │
                                 └──────────────┬──────────────┘
                                                ▼
                                 ┌─────────────────────────────┐
                                 │ Ephemeral In-Memory Store   │
                                 │ (Zero File Persistence)     │
                                 └─────────────────────────────┘
```

---

## 3. Core Component Design

### 3.1 Data Layer (`models.py`)
- **`RSSArticle`**: Normalized in-memory data model representing articles with SHA-256 fingerprint IDs (`id`), title, link, summary, raw HTML content, author, publication date (ISO-8601), categories, and live feed URL source.
- **`FeedMetadata`**: Channel metadata (title, link, description, last build date, language).
- **`IngestionReport`**: Diagnostic report containing status, total found, new added, duplicates skipped, timestamp, and error messages.

### 3.2 Parsing & Normalization Engine (`parser.py`)
- **Dual Parser Support**: Primary parsing using `feedparser` with standard library `xml.etree.ElementTree` fallback.
- **HTML Sanitization**: Strips HTML tags and unescapes entities while normalizing punctuation whitespace.
- **Date Normalization**: Standardizes RFC-822 / RFC-2822 / ISO-8601 strings into normalized UTC ISO timestamps.

### 3.3 Live Async Pipeline & Ephemeral Deduplication (`pipeline.py`)
- **Live Asynchronous Fetcher (`httpx`)**: Handles HTTP/HTTPS URLs with custom User-Agent headers, configurable timeouts, and exponential backoff retries.
- **Local File Rejection**: Strictly rejects local file paths or `file://` scheme URLs to prevent offline feed dependency.
- **Deduplication Engine**: Calculates SHA-256 fingerprints over article GUIDs and `(title + link)` pairs, preventing duplicate processing.
- **Thread-Safe Ephemeral In-Memory Store (`ArticleStore`)**: Manages in-memory article lookup, category filtering, keyword searching, and statistics without writing to disk.

### 3.4 Low-Level MCP Server (`mcp_server.py`)
Exposes tools via Stdio protocol:
1. `ingest_rss_feed`: Ingests RSS feeds from live HTTP/HTTPS URLs into memory.
2. `list_rss_articles`: Filters in-memory articles by category, keyword, and result limits.
3. `get_article_details`: Retrieves full metadata for an in-memory article by fingerprint ID.
4. `search_tech_articles`: Performs full-text search across in-memory articles.
5. `get_pipeline_stats`: Returns in-memory database metrics and tracked feeds.

### 3.5 Google ADK Multi-Agent Architecture (`agent.py`)
- **`RSSScoutAgent`**: Selects top technical news stories.
- **`TechAnalystAgent`**: Conducts technical trade-off and architectural impact analysis.
- **`RobustLinkedInWriter`**: Google ADK `LoopAgent` pairing `LinkedInWriterAgent` with `DraftValidationChecker` to enforce mobile formatting constraints.
- **`RSSAgentOrchestrator`**: Root Google ADK agent binding `MCPToolset` tools and sub-agent tools, configured to use `gemini-2.5-flash-lite`.

---

## 4. Error Handling & Failure Recovery

| Failure Scenario | Mitigation Strategy |
|---|---|
| Network connection drops | Retries with exponential backoff via `httpx` |
| Malformed RSS XML | Falls back to `xml.etree.ElementTree` parser |
| Attempted local file reference | Rejects invalid source schemes with explicit `ValueError` |
| Storage persistence request | Rejected; system operates 100% statelessly in memory |
| Missing API Keys | Graceful fallback to local pipeline execution without LLM calls |

---

## 5. Security Review

- **Zero Disk Persistence**: Sensitive article data is never written to disk or stored persistently.
- **Input Sanitization**: All incoming HTML content is sanitized and stripped before display or model consumption.
- **Protocol Safety**: Logging is directed strictly to `stderr` to prevent stdio MCP channel corruption.
- **Environment Isolation**: No hardcoded API keys or secrets; environment variables are managed via `.env`.
