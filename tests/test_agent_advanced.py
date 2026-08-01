"""
Advanced Google ADK Agent and Multi-Agent Workflow Test Suite.
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


def test_root_agent_structure_and_tools():
    assert root_agent.name == "RSSAgentOrchestrator"
    assert "Google ADK" in root_agent.instruction
    tool_names = [getattr(t, "name", type(t).__name__) for t in root_agent.tools]
    assert "RobustLinkedInWriter" in tool_names
    assert "RSSScoutAgent" in tool_names
    assert "TechAnalystAgent" in tool_names



def test_draft_validation_checker_agent():
    checker = DraftValidationChecker()
    assert checker.name == "DraftValidationChecker"
    assert checker.output_key == "validation_result"
    assert "check the text in state `linkedin_draft`" in checker.instruction.lower()


def test_sub_agent_output_keys():
    assert rss_scout_agent.output_key == "scouted_articles"
    assert tech_analyst_agent.output_key == "technical_analysis"
    assert linkedin_writer_agent.output_key == "linkedin_draft"
