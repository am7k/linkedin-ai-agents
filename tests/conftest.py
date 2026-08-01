"""
Shared Pytest Fixtures and Mock Live Feed Payloads.
"""

import pytest

SAMPLE_LIVE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
    <title>TechCrunch</title>
    <link>https://techcrunch.com/</link>
    <description>Startup and Technology News</description>
    <lastBuildDate>Sat, 01 Aug 2026 03:33:00 +0000</lastBuildDate>
    <item>
        <title>OpenAI reportedly finds evidence that more of its agents ran amok</title>
        <link>https://techcrunch.com/2026/07/31/openai-reportedly-finds-evidence-that-more-of-its-agents-ran-amok/</link>
        <dc:creator><![CDATA[Lucas Ropek]]></dc:creator>
        <pubDate>Fri, 31 Jul 2026 22:47:26 +0000</pubDate>
        <category><![CDATA[AI]]></category>
        <category><![CDATA[OpenAI]]></category>
        <guid isPermaLink="false">https://techcrunch.com/?p=3148949</guid>
        <description><![CDATA[OpenAI has reportedly found evidence of additional agent misbehavior as it looks into the incident that occurred with Hugging Face.]]></description>
    </item>
    <item>
        <title>Rivian spinoff Also to start delivering e-bikes after months of delays</title>
        <link>https://techcrunch.com/2026/07/31/rivian-spinoff-also-to-start-delivering-e-bikes-after-months-of-delays/</link>
        <dc:creator><![CDATA[Sean O'Kane]]></dc:creator>
        <pubDate>Fri, 31 Jul 2026 22:00:08 +0000</pubDate>
        <category><![CDATA[Transportation]]></category>
        <guid isPermaLink="false">https://techcrunch.com/?p=3148946</guid>
        <description><![CDATA[Also has big plans beyond the TM-B.]]></description>
    </item>
</channel>
</rss>
"""

LIVE_FEED_URL = "https://techcrunch.com/feed/"


@pytest.fixture
def sample_rss_xml():
    return SAMPLE_LIVE_RSS_XML


@pytest.fixture
def live_feed_url():
    return LIVE_FEED_URL
