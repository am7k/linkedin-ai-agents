"""
Google ADK Multi-Agent Architecture for RSS Feed Processing and LinkedIn Content Generation.

Combines Google ADK Agent, LoopAgent, AgentTool, and MCPToolset to ingest RSS news,
analyze technical implications, and draft high-impact LinkedIn technical posts.
"""

import os
import sys
from pathlib import Path
import datetime
from dotenv import load_dotenv

from google.adk.agents import Agent, LoopAgent
from google.adk.tools import agent_tool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters

from .config import settings
from .prompt_manager import default_manager as prompt_manager

load_dotenv()

MODEL = settings.model_name

# Fail-fast validate agent prompts on startup
prompt_manager.validate_prompts(
    required_agents=[
        "rss_scout",
        "tech_analyst",
        "linkedin_writer",
        "draft_checker",
        "orchestrator"
    ],
    required_tools=[]
)


# ── MCP Toolset Integration ──────────────────────────────────────────────────
# Connects ADK agent to local RSS MCP Server running over stdio
mcp_server_script = str(Path(__file__).parent / "mcp_server.py")

rss_mcp_server_params = StdioServerParameters(
    command=sys.executable,
    args=["-m", "rss_agent.mcp_server"],
    env=dict(os.environ),
)

rss_mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=rss_mcp_server_params
    )
)


# ── Sub-Agent 1: RSS Feed Scout & Ingester ───────────────────────────────────
scout_desc, scout_inst = prompt_manager.get_agent_prompt("rss_scout")
rss_scout_agent = Agent(
    name="RSSScoutAgent",
    model=MODEL,
    description=scout_desc,
    instruction=scout_inst,
    tools=[rss_mcp_toolset],
    output_key="scouted_articles",
)


# ── Sub-Agent 2: Technical Content Analyst ───────────────────────────────────
analyst_desc, analyst_inst = prompt_manager.get_agent_prompt("tech_analyst")
tech_analyst_agent = Agent(
    name="TechAnalystAgent",
    model=MODEL,
    description=analyst_desc,
    instruction=analyst_inst,
    tools=[rss_mcp_toolset],
    output_key="technical_analysis",
)


# ── Sub-Agent 3: LinkedIn Post Writer ─────────────────────────────────────────
writer_desc, writer_inst = prompt_manager.get_agent_prompt("linkedin_writer")
linkedin_writer_agent = Agent(
    name="LinkedInWriterAgent",
    model=MODEL,
    description=writer_desc,
    instruction=writer_inst,
    output_key="linkedin_draft",
)


# ── Sub-Agent 4: Draft Validation Checker ─────────────────────────────────────
checker_desc, checker_inst = prompt_manager.get_agent_prompt("draft_checker")
class DraftValidationChecker(Agent):
    """Google ADK Agent validating LinkedIn draft formatting rules."""

    def __init__(self):
        super().__init__(
            name="DraftValidationChecker",
            model=MODEL,
            description=checker_desc,
            instruction=checker_inst,
            output_key="validation_result",
        )


# ── ADK LoopAgent for Iterative Refinement ────────────────────────────────────
robust_linkedin_writer = LoopAgent(
    name="RobustLinkedInWriter",
    description="Iteratively drafts and validates LinkedIn posts to guarantee formatting compliance.",
    sub_agents=[linkedin_writer_agent, DraftValidationChecker()],
    max_iterations=3,
)


# Expose sub-agents as explicit AgentTools for the root orchestrator
scout_tool = agent_tool.AgentTool(agent=rss_scout_agent)
analyst_tool = agent_tool.AgentTool(agent=tech_analyst_agent)
writer_tool = agent_tool.AgentTool(agent=robust_linkedin_writer)


# ── Root Orchestrator Agent ──────────────────────────────────────────────────
orch_desc, orch_inst = prompt_manager.get_agent_prompt("orchestrator")
# Inject today's date dynamically into the loaded instruction string
orch_inst = orch_inst + f"\n\nDate: {datetime.datetime.now().strftime('%Y-%m-%d')}"

root_agent = Agent(
    name="RSSAgentOrchestrator",
    model=MODEL,
    description=orch_desc,
    instruction=orch_inst,
    tools=[
        rss_mcp_toolset,
        scout_tool,
        analyst_tool,
        writer_tool,
    ],
)
