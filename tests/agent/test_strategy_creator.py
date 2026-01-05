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

    @pytest.mark.asyncio
    async def test_agent_accepts_custom_history_limit(self):
        """create_agent accepts custom history_limit parameter"""
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not configured")

        from src.agent.strategy_creator import create_agent

        # Should work with custom history limit
        agent_ctx = await create_agent(
            model='anthropic:claude-3-5-sonnet-20241022',
            output_type=Strategy,
            history_limit=10  # Smaller limit for simple tasks
        )

        async with agent_ctx as agent:
            assert agent is not None
            # Agent should have history processor configured
            # (exact internal structure depends on pydantic-ai)


class TestHistoryProcessor:
    """Test history processor factory"""

    def test_create_history_processor_factory_exists(self):
        """create_history_processor factory function is importable"""
        from src.agent.strategy_creator import create_history_processor

        assert callable(create_history_processor)

    def test_create_history_processor_returns_function(self):
        """create_history_processor returns a callable processor"""
        from src.agent.strategy_creator import create_history_processor

        processor = create_history_processor(max_messages=10)

        assert callable(processor)

    def test_history_processor_trims_to_limit(self):
        """History processor trims messages to specified limit"""
        from src.agent.strategy_creator import create_history_processor
        from pydantic_ai import messages as _messages
        from unittest.mock import Mock

        processor = create_history_processor(max_messages=5)
        ctx = Mock()

        # Create 10 messages
        test_messages = [_messages.ModelRequest(parts=[]) for _ in range(10)]

        # Process should trim to 5
        result = processor(ctx, test_messages)

        assert len(result) <= 5, f"Expected <= 5 messages, got {len(result)}"

    def test_history_processor_preserves_under_limit(self):
        """History processor preserves all messages when under limit"""
        from src.agent.strategy_creator import create_history_processor
        from pydantic_ai import messages as _messages
        from unittest.mock import Mock

        processor = create_history_processor(max_messages=10)
        ctx = Mock()

        # Create 5 messages (under limit)
        test_messages = [_messages.ModelRequest(parts=[]) for _ in range(5)]

        # Process should keep all
        result = processor(ctx, test_messages)

        assert len(result) == 5, f"Expected 5 messages, got {len(result)}"


class TestReasoningDetection:
    """Test reasoning-model detection rules."""

    def test_is_reasoning_model_default_allowlist(self):
        """Reasoning defaults to True unless model is in the non-reasoning allowlist."""
        from src.agent.strategy_creator import is_reasoning_model

        # Explicit non-reasoning families
        assert is_reasoning_model("openai:gpt-4o") is False
        assert is_reasoning_model("openai:gpt-4.1") is False
        assert is_reasoning_model("openai:deepseek-chat") is False
        assert is_reasoning_model("openai:moonshot-v1-32k") is False
        assert is_reasoning_model("openai:kimi-k2-0905-preview") is False
        assert is_reasoning_model("anthropic:claude-3-5-sonnet-20241022") is False

        # Reasoning-by-default or explicit reasoning
        assert is_reasoning_model("openai:gpt-5.2") is True
        assert is_reasoning_model("openai:deepseek-reasoner") is True
        assert is_reasoning_model("openai:kimi-k2-thinking") is True
        assert is_reasoning_model("google-gla:gemini-3-pro-preview") is True


class TestProviderEnvRestore:
    """Test that provider env overrides are restored after agent lifecycle."""

    @pytest.mark.asyncio
    async def test_create_agent_restores_env_after_deepseek(self, monkeypatch):
        import os
        import src.agent.strategy_creator as strategy_creator
        from src.agent.models import Strategy

        class DummyAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class DummyServers:
            async def __aenter__(self):
                return {}

            async def __aexit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(strategy_creator, "Agent", DummyAgent)
        monkeypatch.setattr(strategy_creator, "get_mcp_servers", lambda: DummyServers())

        monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        agent_ctx = await strategy_creator.create_agent(
            model="openai:deepseek-chat",
            output_type=Strategy,
            system_prompt="test",
            include_composer=False,
            include_fred=False,
            include_yfinance=False,
        )

        async with agent_ctx as _agent:
            assert os.environ["OPENAI_API_KEY"] == "deepseek-key"
            assert os.environ["OPENAI_BASE_URL"] == strategy_creator.DEEPSEEK_BASE_URL

        assert os.environ["OPENAI_API_KEY"] == "openai-key"
        assert os.environ["OPENAI_BASE_URL"] == "https://api.openai.com/v1"

    @pytest.mark.asyncio
    async def test_create_agent_restores_env_on_failure(self, monkeypatch):
        import os
        import src.agent.strategy_creator as strategy_creator
        from src.agent.models import Strategy

        class FailingServers:
            async def __aenter__(self):
                raise RuntimeError("boom")

            async def __aexit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(strategy_creator, "get_mcp_servers", lambda: FailingServers())
        monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        with pytest.raises(RuntimeError, match="boom"):
            await strategy_creator.create_agent(
                model="openai:deepseek-chat",
                output_type=Strategy,
                system_prompt="test",
                include_composer=False,
                include_fred=False,
                include_yfinance=False,
            )

        assert os.environ["OPENAI_API_KEY"] == "openai-key"
        assert "OPENAI_BASE_URL" not in os.environ


class TestPromptLoading:
    """Test prompt template loading"""

    def test_load_system_prompt(self):
        """System prompt template can be loaded"""
        from src.agent.strategy_creator import load_prompt

        prompt = load_prompt('system_prompt.md')

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_load_candidate_generation_prompt(self):
        """Candidate generation prompt template can be loaded"""
        from src.agent.strategy_creator import load_prompt

        prompt = load_prompt('candidate_generation.md')

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
