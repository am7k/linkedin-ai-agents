"""
Unit tests for Google ADK Agent configuration and multi-agent setup.
"""

import pytest
from rss_agent.agent import (
    root_agent,
    rss_scout_agent,
    tech_analyst_agent,
    linkedin_writer_agent,
    DraftValidationChecker,
    robust_linkedin_writer,
)


def test_agent_initialization():
    assert root_agent.name == "RSSAgentOrchestrator"
    assert len(root_agent.tools) == 4

    assert rss_scout_agent.name == "RSSScoutAgent"
    assert tech_analyst_agent.name == "TechAnalystAgent"
    assert linkedin_writer_agent.name == "LinkedInWriterAgent"


def test_loop_agent_configuration():
    assert robust_linkedin_writer.name == "RobustLinkedInWriter"
    assert len(robust_linkedin_writer.sub_agents) == 2
    assert robust_linkedin_writer.max_iterations == 3
