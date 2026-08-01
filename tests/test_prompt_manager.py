import pytest
from pathlib import Path
from rss_agent.prompt_manager import PromptManager

def test_prompt_manager_initialization(tmp_path):
    manager = PromptManager(tmp_path)
    assert manager.agents_dir.exists()
    assert manager.tools_dir.exists()

def test_prompt_manager_validates_and_caches_successfully(tmp_path):
    manager = PromptManager(tmp_path)
    
    # Create fake prompts
    agent_file = manager.agents_dir / "test_agent.md"
    agent_file.write_text("# DESCRIPTION\nTest desc\n# INSTRUCTION\nTest inst", encoding="utf-8")
    
    tool_file = manager.tools_dir / "test_tool.md"
    tool_file.write_text("Test tool desc", encoding="utf-8")
    
    manager.validate_prompts(required_agents=["test_agent"], required_tools=["test_tool"])
    
    # Check cache
    assert "test_agent" in manager._agent_cache
    assert "test_tool" in manager._tool_cache
    
    desc, inst = manager.get_agent_prompt("test_agent")
    assert desc == "Test desc"
    assert inst == "Test inst"
    
    tool_desc = manager.get_tool_prompt("test_tool")
    assert tool_desc == "Test tool desc"

def test_prompt_manager_validates_missing_files(tmp_path):
    manager = PromptManager(tmp_path)
    
    with pytest.raises(FileNotFoundError) as exc:
        manager.validate_prompts(required_agents=["missing_agent"], required_tools=["missing_tool"])
        
    assert "missing_agent" in str(exc.value)
    assert "missing_tool" in str(exc.value)

def test_prompt_manager_agent_no_headers(tmp_path):
    manager = PromptManager(tmp_path)
    agent_file = manager.agents_dir / "test_agent_plain.md"
    agent_file.write_text("Just instruction text here", encoding="utf-8")
    
    desc, inst = manager.get_agent_prompt("test_agent_plain")
    assert desc == ""
    assert inst == "Just instruction text here"
