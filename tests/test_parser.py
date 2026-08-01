"""
Unit tests for RSS parsing and normalization module (parser.py).
"""

import pytest
from rss_agent.parser import (
    parse_rss_content,
    strip_html_tags,
    normalize_pub_date,
    parse_rss_content_elementtree,
)
from rss_agent.models import RSSArticle, FeedMetadata
from tests.conftest import SAMPLE_LIVE_RSS_XML, LIVE_FEED_URL


def test_strip_html_tags():
    raw_html = "<p>OpenAI has reportedly found evidence of <b>additional agent misbehavior</b>. <a href='#'>Read more</a></p>"
    clean = strip_html_tags(raw_html)
    assert "OpenAI has reportedly found evidence of additional agent misbehavior. Read more" in clean
    assert "<p>" not in clean
    assert "<b>" not in clean


def test_normalize_pub_date():
    rfc_date = "Fri, 31 Jul 2026 22:47:26 +0000"
    iso_date = normalize_pub_date(rfc_date)
    assert "2026-07-31" in iso_date
    assert "+00:00" in iso_date or "Z" in iso_date or "00:00" in iso_date


def test_parse_techcrunch_rss_feed(sample_rss_xml):
    meta, articles = parse_rss_content(sample_rss_xml, feed_source=LIVE_FEED_URL)

    assert isinstance(meta, FeedMetadata)
    assert meta.title == "TechCrunch"
    assert "Startup and Technology News" in meta.description

    assert len(articles) > 0
    first = articles[0]
    assert isinstance(first, RSSArticle)
    assert "OpenAI" in first.title
    assert first.author == "Lucas Ropek"
    assert "AI" in first.categories or "OpenAI" in first.categories
    assert first.id is not None and len(first.id) == 16


def test_elementtree_fallback_parser(sample_rss_xml):
    meta, articles = parse_rss_content_elementtree(sample_rss_xml, feed_source=LIVE_FEED_URL)

    assert meta.title == "TechCrunch"
    assert len(articles) > 0
    assert "OpenAI" in articles[0].title
