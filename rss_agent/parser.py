"""
RSS Feed Parsing and Content Normalization Module.

Extracts, cleans, and normalizes raw XML/RSS feeds into standardized RSSArticle models.
Supports both feedparser and standard library xml.etree.ElementTree fallbacks.
"""

import re
import html
import logging
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from typing import Tuple, List, Optional
from email.utils import parsedate_to_datetime

from .models import RSSArticle, FeedMetadata

logger = logging.getLogger(__name__)

def strip_html_tags(raw_text: Optional[str]) -> str:
    """Strip HTML tags and unescape HTML entities to produce clean plain text."""
    if not raw_text:
        return ""
    # Remove HTML tags using regex
    clean = re.sub(r"<[^>]+>", " ", raw_text)
    # Unescape HTML entities (&amp;, &lt;, &gt;, etc.)
    clean = html.unescape(clean)
    # Fix spaces before punctuation (e.g. "misbehavior ." -> "misbehavior.")
    clean = re.sub(r"\s+([.,!?;:])", r"\1", clean)
    # Normalize whitespace
    return " ".join(clean.split())



def normalize_pub_date(pub_date_str: Optional[str]) -> str:
    """Normalize RFC-822 / RFC-2822 / ISO-8601 date strings to ISO-8601 format."""
    if not pub_date_str:
        return datetime.now(timezone.utc).isoformat()
    
    try:
        dt = parsedate_to_datetime(pub_date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        # Fallback if date string format is non-standard
        return pub_date_str


def parse_rss_content(
    xml_content: str, feed_source: str = ""
) -> Tuple[FeedMetadata, List[RSSArticle]]:
    """
    Parse raw RSS 2.0 / Atom XML text into FeedMetadata and a list of normalized RSSArticles.
    Attempts feedparser first if available; falls back to xml.etree.ElementTree.
    """
    try:
        import feedparser
        parsed = feedparser.parse(xml_content)
        
        feed_meta = FeedMetadata(
            title=parsed.feed.get("title", "Untitled Feed"),
            link=parsed.feed.get("link", ""),
            description=parsed.feed.get("description", ""),
            last_build_date=parsed.feed.get("updated", parsed.feed.get("published")),
            language=parsed.feed.get("language"),
            generator=parsed.feed.get("generator"),
        )

        articles: List[RSSArticle] = []
        for entry in parsed.entries:
            guid = entry.get("id", entry.get("link", ""))
            title = strip_html_tags(entry.get("title", ""))
            link = entry.get("link", "")
            
            # Extract summary/description
            summary_raw = entry.get("summary", entry.get("description", ""))
            summary_clean = strip_html_tags(summary_raw)

            # Raw content if present
            content_raw = None
            if "content" in entry and entry.content:
                content_raw = entry.content[0].get("value")

            author = entry.get("author", entry.get("dc_creator", "Unknown"))
            pub_date = normalize_pub_date(entry.get("published", entry.get("updated")))

            # Extract category tags
            categories = []
            if "tags" in entry:
                categories = [t.get("term", "").strip() for t in entry.tags if t.get("term")]

            article_id = RSSArticle.generate_id(guid, title, link)
            article = RSSArticle(
                id=article_id,
                guid=guid,
                title=title,
                link=link,
                summary=summary_clean,
                content_raw=content_raw,
                author=author,
                published_at=pub_date,
                categories=categories,
                feed_url=feed_source,
            )
            articles.append(article)

        return feed_meta, articles

    except ImportError:
        logger.warning("feedparser module not available. Falling back to ElementTree XML parser.")
        return parse_rss_content_elementtree(xml_content, feed_source)
    except Exception as e:
        logger.error(f"feedparser failed: {e}. Trying ElementTree fallback.")
        return parse_rss_content_elementtree(xml_content, feed_source)


def parse_rss_content_elementtree(
    xml_content: str, feed_source: str = ""
) -> Tuple[FeedMetadata, List[RSSArticle]]:
    """Standard library XML ElementTree fallback parser for RSS feeds."""
    root = ET.fromstring(xml_content)
    channel = root.find("channel")
    if channel is None:
        channel = root

    feed_title = channel.findtext("title", "Untitled Feed")
    feed_link = channel.findtext("link", "")
    feed_desc = channel.findtext("description", "")
    last_build = channel.findtext("lastBuildDate", None)

    meta = FeedMetadata(
        title=feed_title,
        link=feed_link,
        description=feed_desc,
        last_build_date=last_build,
    )

    # Namespaces commonly used in RSS 2.0 (dc, content)
    namespaces = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    articles: List[RSSArticle] = []
    for item in channel.findall("item"):
        title = strip_html_tags(item.findtext("title", ""))
        link = item.findtext("link", "")
        guid = item.findtext("guid", link)
        desc = strip_html_tags(item.findtext("description", ""))
        
        # Author extraction from dc:creator or author element
        creator = item.findtext("{http://purl.org/dc/elements/1.1/}creator")
        if not creator:
            creator = item.findtext("author", "Unknown")
            
        pub_date = normalize_pub_date(item.findtext("pubDate"))
        
        categories = [cat.text.strip() for cat in item.findall("category") if cat.text]
        content_raw = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")

        art_id = RSSArticle.generate_id(guid, title, link)
        article = RSSArticle(
            id=art_id,
            guid=guid,
            title=title,
            link=link,
            summary=desc,
            content_raw=content_raw,
            author=creator,
            published_at=pub_date,
            categories=categories,
            feed_url=feed_source,
        )
        articles.append(article)

    return meta, articles
