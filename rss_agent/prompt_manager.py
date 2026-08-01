"""
Prompt management module for loading, validating, and caching external prompt assets.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger("prompt_manager")

class PromptManager:
    """Loads and caches agent and tool instructions from external markdown files."""

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.agents_dir = self.prompts_dir / "agents"
        self.tools_dir = self.prompts_dir / "tools"
        self._agent_cache: Dict[str, Tuple[str, str]] = {}
        self._tool_cache: Dict[str, str] = {}
        
        # Ensure directories exist
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)

    def validate_prompts(self, required_agents: list[str], required_tools: list[str]):
        """
        Fail-fast validation to ensure all required prompts are present.
        Raises FileNotFoundError if any are missing.
        """
        missing = []
        for agent in required_agents:
            if not (self.agents_dir / f"{agent}.md").exists():
                missing.append(f"agents/{agent}.md")
        for tool in required_tools:
            if not (self.tools_dir / f"{tool}.md").exists():
                missing.append(f"tools/{tool}.md")
                
        if missing:
            raise FileNotFoundError(f"Missing required prompt files: {', '.join(missing)}")
            
        # Pre-cache them
        for agent in required_agents:
            self.get_agent_prompt(agent)
        for tool in required_tools:
            self.get_tool_prompt(tool)
            
        logger.info(f"Successfully loaded and validated {len(required_agents)} agent prompts and {len(required_tools)} tool prompts.")

    def get_agent_prompt(self, agent_name: str) -> Tuple[str, str]:
        """
        Loads the agent prompt and splits it into (description, instruction).
        Expects `# DESCRIPTION` and `# INSTRUCTION` headers in the markdown file.
        Returns from cache if already loaded.
        """
        if agent_name in self._agent_cache:
            return self._agent_cache[agent_name]
            
        file_path = self.agents_dir / f"{agent_name}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Agent prompt not found: {file_path}")
            
        content = file_path.read_text(encoding="utf-8")
        
        # Simple splitting logic
        description = ""
        instruction = ""
        
        if "# DESCRIPTION" in content and "# INSTRUCTION" in content:
            parts = content.split("# INSTRUCTION")
            desc_part = parts[0].replace("# DESCRIPTION", "").strip()
            inst_part = parts[1].strip()
            description = desc_part
            instruction = inst_part
        else:
            instruction = content.strip()
            
        self._agent_cache[agent_name] = (description, instruction)
        return description, instruction

    def get_tool_prompt(self, tool_name: str) -> str:
        """
        Loads the tool prompt/docstring.
        Returns from cache if already loaded.
        """
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]
            
        file_path = self.tools_dir / f"{tool_name}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Tool prompt not found: {file_path}")
            
        content = file_path.read_text(encoding="utf-8").strip()
        self._tool_cache[tool_name] = content
        return content

# Global singleton instance
# Default to linkedin-ai-agents/prompts/
PROJECT_ROOT = Path(__file__).parent.parent
default_manager = PromptManager(PROJECT_ROOT / "prompts")
