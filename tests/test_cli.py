"""
Tests for Command Line Interface (cli.py) with live HTTP mocks.
"""

import pytest
from unittest.mock import patch, AsyncMock
import httpx

from rss_agent.cli import main, _run_list, _run_search, _run_stats
from tests.conftest import SAMPLE_LIVE_RSS_XML, LIVE_FEED_URL


@pytest.fixture(autouse=True)
def mock_cli_http():
    req = httpx.Request("GET", LIVE_FEED_URL)
    resp = httpx.Response(200, text=SAMPLE_LIVE_RSS_XML, request=req)
    with patch("httpx.AsyncClient.get", AsyncMock(return_value=resp)):
        yield


def test_cli_stats_command(capsys):
    _run_stats()
    captured = capsys.readouterr()
    assert "[+] Database Statistics:" in captured.out
    assert "total_articles" in captured.out


def test_cli_list_command(capsys):
    _run_list(category=None, limit=2)
    captured = capsys.readouterr()
    assert "[+] Found" in captured.out


def test_cli_search_command(capsys):
    _run_search(query="OpenAI", limit=2)
    captured = capsys.readouterr()
    assert "Search results for 'OpenAI'" in captured.out


def test_cli_main_help_and_subcommands(capsys):
    with patch("sys.argv", ["cli.py", "stats"]):
        main()
        captured = capsys.readouterr()
        assert "Database Statistics:" in captured.out
