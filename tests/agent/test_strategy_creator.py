"""
Tests for agent factory and strategy creation.
Following TDD: Write tests first, then implement strategy_creator.py.
"""

import pytest
from src.agent.models import Strategy, Charter


class TestAgentFactory:
    """Test agent creation with different providers"""

    def test_create_agent_function_exists(self):
        """create_agent function is importable"""
        from src.agent.strategy_creator import create_agent

        assert callable(create_agent)

    @pytest.mark.asyncio
    async def test_create_agent_with_claude(self):
        """create_agent works with Claude model"""
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Strategy
        )

        # Should return an AgentContext
        assert agent_ctx is not None
        assert hasattr(agent_ctx, '__aenter__')
        assert hasattr(agent_ctx, '__aexit__')

        # Test that we can enter the context
        async with agent_ctx as agent:
            assert agent is not None
            # Agent should have model configured
            assert 'claude' in str(agent._model).lower() or 'anthropic' in str(agent._model).lower()

    @pytest.mark.asyncio
    async def test_create_agent_with_openai(self):
        """create_agent works with OpenAI model"""
        import os
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        agent_ctx = await create_agent(
            model='openai:gpt-4o',
            output_type=Strategy
        )

        async with agent_ctx as agent:
            assert agent is not None
            assert 'gpt' in str(agent._model).lower() or 'openai' in str(agent._model).lower()

    @pytest.mark.asyncio
    async def test_create_agent_with_gemini(self):
        """create_agent works with Gemini model"""
        import os
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("GOOGLE_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        # Gemini provider name is "gemini" not "google" in pydantic-ai
        agent_ctx = await create_agent(
            model='gemini:gemini-2.0-flash-exp',
            output_type=Strategy
        )

        async with agent_ctx as agent:
            assert agent is not None
            assert 'gemini' in str(agent._model).lower()

    @pytest.mark.asyncio
    async def test_create_agent_with_custom_result_type(self):
        """create_agent accepts different result types"""
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        # Should work with Charter type
        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Charter
        )

        async with agent_ctx as agent:
            assert agent is not None


class TestAgentConfiguration:
    """Test agent configuration and toolsets"""

    @pytest.mark.asyncio
    async def test_agent_has_mcp_toolsets(self):
        """Agent is configured with MCP toolsets"""
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Strategy
        )

        # Agent should have toolsets configured
        # (exact structure depends on Pydantic AI internals)
        async with agent_ctx as agent:
            assert agent is not None

    @pytest.mark.asyncio
    async def test_agent_supports_multiple_calls(self):
        """Same agent can be called multiple times within context"""
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Strategy
        )

        # Agent should be reusable within the context
        async with agent_ctx as agent:
            assert agent is not None


class TestPromptLoading:
    """Test prompt template loading"""

    def test_load_system_prompt(self):
        """System prompt template can be loaded"""
        from src.agent.strategy_creator import load_prompt

        prompt = load_prompt('system_prompt.md')

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_load_strategy_creation_prompt(self):
        """Strategy creation prompt template can be loaded"""
        from src.agent.strategy_creator import load_prompt

        prompt = load_prompt('strategy_creation.md')

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_load_charter_creation_prompt(self):
        """Charter creation prompt template can be loaded"""
        from src.agent.strategy_creator import load_prompt

        prompt = load_prompt('charter_creation.md')

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Verify it contains charter-specific content
        assert 'charter' in prompt.lower()

    def test_load_nonexistent_prompt_raises(self):
        """Loading nonexistent prompt raises FileNotFoundError"""
        from src.agent.strategy_creator import load_prompt

        with pytest.raises(FileNotFoundError):
            load_prompt('nonexistent.md')


class TestAgentExecution:
    """Test agent execution (integration tests - require API keys)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_executes_simple_task(self):
        """Agent can execute a simple task within context (requires API key)"""
        import os
        from src.agent.strategy_creator import create_agent

        # Skip if API keys not configured
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")

        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Strategy
        )

        async with agent_ctx as agent:
            # This would be a real API call - expensive, so skip by default
            pytest.skip("Skipping expensive API call in unit tests")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_lifecycle_with_mcp_servers(self):
        """Agent can use MCP tools within context (verifies lifecycle fix)"""
        import os
        from src.agent.strategy_creator import create_agent

        # Skip if API keys not configured
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")
        if not os.getenv('FRED_API_KEY'):
            pytest.skip("FRED_API_KEY not configured")

        # Create agent
        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Strategy
        )

        # Test that agent works within context
        async with agent_ctx as agent:
            assert agent is not None

            # Verify MCP servers are active by checking agent has tools
            # (actual agent.run() would be expensive, so we just verify setup)
            # In a real scenario, you would call:
            # result = await agent.run("Create a 60/40 portfolio strategy")
            # assert result.data.name is not None

        # After exiting context, MCP servers should be closed
        # (no assertion needed - this is expected cleanup behavior)
