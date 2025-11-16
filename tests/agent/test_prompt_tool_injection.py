"""Unit tests for tool prompt injection in load_prompt()."""

import pytest
from pathlib import Path
from src.agent.strategy_creator import load_prompt, _load_tool_documentation


class TestToolPromptInjection:
    """Test that tool documentation is properly injected into system prompts."""

    def test_system_prompts_include_tools(self):
        """System prompts in system/ subdirectory should include tool docs."""
        system_prompt = load_prompt("system/candidate_generation_system.md")

        # Should contain tool documentation
        assert "## AVAILABLE TOOLS" in system_prompt
        assert "FRED MCP Tools" in system_prompt
        assert "yfinance" in system_prompt.lower()

        # Should be substantially longer than without tools
        prompt_without_tools = load_prompt("system/candidate_generation_system.md", include_tools=False)
        assert len(system_prompt) > len(prompt_without_tools)

    def test_recipe_prompts_exclude_tools(self):
        """Recipe prompts should NOT include tool docs (they're workflow guides)."""
        recipe_prompt = load_prompt("candidate_generation.md")

        # Should NOT contain injected tool documentation
        assert "## AVAILABLE TOOLS" not in recipe_prompt

    def test_tool_injection_can_be_disabled(self):
        """System prompts should allow disabling tool injection."""
        system_with_tools = load_prompt("system/candidate_generation_system.md", include_tools=True)
        system_without_tools = load_prompt("system/candidate_generation_system.md", include_tools=False)

        # With tools should be longer
        assert len(system_with_tools) > len(system_without_tools)

        # Without tools should not have AVAILABLE TOOLS section
        assert "## AVAILABLE TOOLS" not in system_without_tools
        assert "## AVAILABLE TOOLS" in system_with_tools

    def test_load_tool_documentation_returns_all_tools(self):
        """_load_tool_documentation() should load all tool files."""
        tool_docs = _load_tool_documentation()

        # Should contain all three tool documentation sections
        assert "FRED MCP Tools" in tool_docs
        assert "yfinance" in tool_docs.lower()
        assert "composer" in tool_docs.lower()

        # Should be non-empty
        assert len(tool_docs) > 100

    def test_load_tool_documentation_order(self):
        """Tool documentation should be loaded in priority order: FRED, yfinance, Composer."""
        tool_docs = _load_tool_documentation()

        # Find positions of each tool section
        fred_pos = tool_docs.find("FRED MCP Tools")
        yfinance_pos = tool_docs.lower().find("yfinance")
        composer_pos = tool_docs.lower().find("composer")

        # FRED should come first (most important for token management)
        assert fred_pos >= 0
        assert fred_pos < yfinance_pos
        assert yfinance_pos < composer_pos

    def test_tool_docs_contain_critical_info(self):
        """Tool documentation should contain critical usage information."""
        tool_docs = _load_tool_documentation()

        # FRED critical info: limit parameter requirement
        assert "limit" in tool_docs.lower()
        assert "token" in tool_docs.lower()

        # Should include example usage
        assert "fred_get_series" in tool_docs or "fred_search" in tool_docs

    def test_nonexistent_prompt_raises_error(self):
        """Loading a nonexistent prompt should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt.md")

    def test_all_system_prompts_get_tools(self):
        """All system prompts in system/ subdirectory should get tool injection."""
        # List all system prompts
        prompts_dir = Path(__file__).parent.parent.parent / "src" / "agent" / "prompts" / "system"
        system_prompts = list(prompts_dir.glob("*.md"))

        assert len(system_prompts) > 0, "Should have at least one system prompt"

        for prompt_file in system_prompts:
            relative_path = f"system/{prompt_file.name}"
            prompt_content = load_prompt(relative_path)

            # Each system prompt should have tools injected
            assert "## AVAILABLE TOOLS" in prompt_content, \
                f"{relative_path} should have AVAILABLE TOOLS section"

    def test_tool_injection_preserves_original_content(self):
        """Tool injection should append to original content, not replace it."""
        # Load original without tools
        original = load_prompt("system/candidate_generation_system.md", include_tools=False)

        # Load with tools
        with_tools = load_prompt("system/candidate_generation_system.md", include_tools=True)

        # Original content should be present
        assert original in with_tools

        # Tools should be appended after original
        assert with_tools.startswith(original.split("\n")[0])
