"""
Test DeepSeek and Kimi provider support.

These tests verify that the agent creation works correctly for cheaper
alternative LLM providers that use OpenAI-compatible APIs.
"""
import pytest
import os
from src.agent.strategy_creator import create_agent
from src.agent.models import Strategy


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set"
)
@pytest.mark.asyncio
async def test_deepseek_creates_agent():
    """Test that DeepSeek can create an agent successfully"""
    agent_ctx = await create_agent(
        model="openai:deepseek-chat",
        output_type=Strategy,
        system_prompt="You are a trading strategy assistant.",
        include_composer=False,
        history_limit=5
    )

    async with agent_ctx as agent:
        assert agent is not None
        assert agent.output_type == Strategy


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set"
)
@pytest.mark.asyncio
async def test_deepseek_reasoner_creates_agent():
    """Test that DeepSeek reasoner model can create an agent"""
    agent_ctx = await create_agent(
        model="openai:deepseek-reasoner",
        output_type=Strategy,
        system_prompt="You are a trading strategy assistant.",
        include_composer=False,
        history_limit=5
    )

    async with agent_ctx as agent:
        assert agent is not None
        assert agent.output_type == Strategy


@pytest.mark.skipif(
    not os.getenv("KIMI_API_KEY"),
    reason="KIMI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_kimi_creates_agent():
    """Test that Kimi/Moonshot can create an agent successfully"""
    agent_ctx = await create_agent(
        model="openai:moonshot-v1-128k",
        output_type=Strategy,
        system_prompt="You are a trading strategy assistant.",
        include_composer=False,
        history_limit=5
    )

    async with agent_ctx as agent:
        assert agent is not None
        assert agent.output_type == Strategy


@pytest.mark.skipif(
    not os.getenv("KIMI_API_KEY"),
    reason="KIMI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_kimi_32k_creates_agent():
    """Test that Kimi 32k context model can create an agent"""
    agent_ctx = await create_agent(
        model="openai:moonshot-v1-32k",
        output_type=Strategy,
        system_prompt="You are a trading strategy assistant.",
        include_composer=False,
        history_limit=5
    )

    async with agent_ctx as agent:
        assert agent is not None
        assert agent.output_type == Strategy


@pytest.mark.asyncio
async def test_deepseek_without_key_raises_error():
    """Test that DeepSeek without API key raises appropriate error"""
    # Temporarily clear the environment variable
    original_key = os.environ.get("DEEPSEEK_API_KEY")
    if "DEEPSEEK_API_KEY" in os.environ:
        del os.environ["DEEPSEEK_API_KEY"]

    try:
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY environment variable required"):
            await create_agent(
                model="openai:deepseek-chat",
                output_type=Strategy,
                system_prompt="Test prompt",
                include_composer=False,
                history_limit=5
            )
    finally:
        # Restore original key if it existed
        if original_key:
            os.environ["DEEPSEEK_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_kimi_without_key_raises_error():
    """Test that Kimi without API key raises appropriate error"""
    # Temporarily clear the environment variable
    original_key = os.environ.get("KIMI_API_KEY")
    if "KIMI_API_KEY" in os.environ:
        del os.environ["KIMI_API_KEY"]

    try:
        with pytest.raises(ValueError, match="KIMI_API_KEY environment variable required"):
            await create_agent(
                model="openai:moonshot-v1-128k",
                output_type=Strategy,
                system_prompt="Test prompt",
                include_composer=False,
                history_limit=5
            )
    finally:
        # Restore original key if it existed
        if original_key:
            os.environ["KIMI_API_KEY"] = original_key
