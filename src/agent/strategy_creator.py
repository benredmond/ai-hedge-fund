"""
Multi-provider agent factory for trading strategy creation.

This module provides:
- Agent creation with Claude, GPT-4, or Gemini
- MCP tool integration (FRED, yfinance)
- Prompt template loading
- Type-safe strategy output
"""

from contextlib import AsyncExitStack
from pathlib import Path
from typing import Type, TypeVar
import os
from pydantic import BaseModel
from pydantic_ai import Agent
from src.agent.mcp_config import get_mcp_servers


T = TypeVar("T", bound=BaseModel)

# Default model from environment variable
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai:gpt-4o")


class AgentContext:
    """
    Async context manager that wraps an agent and its MCP server lifecycle.

    This ensures MCP servers remain active for the agent's lifetime.

    Usage:
        async with create_agent(...) as agent:
            result = await agent.run("Create strategy")

    The MCP servers will be automatically closed when exiting the context.
    """

    def __init__(self, agent: Agent, stack: AsyncExitStack):
        self._agent = agent
        self._stack = stack

    async def __aenter__(self):
        """Enter the async context, returning the agent"""
        return self._agent

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context, closing MCP servers"""
        await self._stack.aclose()

    def __getattr__(self, name):
        """Delegate attribute access to the underlying agent"""
        return getattr(self._agent, name)


# Prompt directory
PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """
    Load prompt template from prompts directory.

    Args:
        filename: Prompt template filename (e.g., 'system_prompt.md')

    Returns:
        Prompt content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = PROMPT_DIR / filename

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt template not found: {prompt_path}\n"
            f"Available prompts: {list(PROMPT_DIR.glob('*.md'))}"
        )

    return prompt_path.read_text()


async def create_agent(
    model: str, output_type: Type[T], system_prompt: str | None = None
) -> AgentContext:
    """
    Create AI agent with multi-provider support and MCP tools.

    IMPORTANT: Returns an async context manager. Use with 'async with':

        async with create_agent(...) as agent:
            result = await agent.run("Create strategy")

    This ensures MCP servers remain active for the agent's lifetime.

    Supports:
    - Claude: 'anthropic:claude-3-5-sonnet-20241022'
    - GPT-4: 'openai:gpt-4o'
    - Gemini: 'gemini:gemini-2.0-flash-exp'

    Args:
        model: Model identifier (format: 'provider:model-name')
        output_type: Pydantic model for structured output (Strategy, Charter, etc.)
        system_prompt: Optional system prompt (defaults to system_prompt.md)

    Returns:
        AgentContext that manages agent and MCP server lifecycle

    Raises:
        ValueError: If model format is invalid
        RuntimeError: If MCP servers are unavailable

    Example:
        >>> # Create agent context
        >>> agent_ctx = await create_agent(
        ...     model='anthropic:claude-3-5-sonnet-20241022',
        ...     output_type=Strategy
        ... )
        >>> # Use agent within context
        >>> async with agent_ctx as agent:
        ...     result = await agent.run("Create a 60/40 portfolio strategy")
        ...     print(result.output.name)
        '60/40 Portfolio'
    """
    # Validate model format
    if ":" not in model:
        raise ValueError(
            f"Invalid model format: '{model}'. "
            f"Expected 'provider:model-name' (e.g., 'anthropic:claude-3-5-sonnet-20241022')"
        )

    # Load system prompt if not provided
    if system_prompt is None:
        system_prompt = load_prompt("system_prompt.md")

    # Create AsyncExitStack to manage MCP server lifecycle
    stack = AsyncExitStack()

    # Enter MCP servers context and keep it alive
    servers = await stack.enter_async_context(get_mcp_servers())

    # Create toolsets list from available servers
    toolsets = []

    if "fred" in servers:
        toolsets.append(servers["fred"])

    if "yfinance" in servers:
        toolsets.append(servers["yfinance"])

    if "composer" in servers:
        toolsets.append(servers["composer"])

    if not toolsets:
        await stack.aclose()  # Clean up before raising
        raise RuntimeError(
            "No MCP servers available. Ensure FRED, yfinance, and/or Composer are configured."
        )

    # Create agent with Pydantic AI
    agent = Agent(
        model=model,
        output_type=output_type,
        system_prompt=system_prompt,
        toolsets=toolsets,
    )

    # Return wrapped agent with lifecycle management
    return AgentContext(agent, stack)


async def create_strategy_agent(
    model: str = DEFAULT_MODEL,
) -> AgentContext:
    """
    Create agent configured for strategy creation workflow.

    This is a convenience function that:
    - Loads strategy creation prompt
    - Configures Strategy as result type
    - Sets up all MCP tools

    IMPORTANT: Returns an async context manager. Use with 'async with':

        async with create_strategy_agent() as agent:
            result = await agent.run(market_context_json)

    Args:
        model: LLM provider and model (default: Claude 3.5 Sonnet)

    Returns:
        AgentContext for strategy creation

    Example:
        >>> agent_ctx = await create_strategy_agent()
        >>> async with agent_ctx as agent:
        ...     result = await agent.run(market_context_json)
        ...     strategy = result.output  # Type: Strategy
    """
    from src.agent.models import Strategy

    # Load combined prompt (system + workflow)
    system_prompt = load_prompt("system_prompt.md")
    workflow_prompt = load_prompt("strategy_creation.md")

    combined_prompt = f"{system_prompt}\n\n{workflow_prompt}"

    return await create_agent(
        model=model, output_type=Strategy, system_prompt=combined_prompt
    )


async def create_charter_agent(
    model: str = DEFAULT_MODEL,
) -> AgentContext:
    """
    Create agent configured for charter generation.

    This is a convenience function that:
    - Loads charter creation workflow prompt
    - Configures Charter as result type
    - Sets up all MCP tools for market analysis

    IMPORTANT: Returns an async context manager. Use with 'async with':

        async with create_charter_agent() as agent:
            result = await agent.run(f"Create charter for: {strategy}")

    Args:
        model: LLM provider and model (default: Claude 3.5 Sonnet)

    Returns:
        AgentContext for charter creation

    Example:
        >>> agent_ctx = await create_charter_agent()
        >>> async with agent_ctx as agent:
        ...     result = await agent.run(f"Create charter for: {strategy}")
        ...     charter = result.output  # Type: Charter
    """
    from src.agent.models import Charter

    # Load combined prompt (system + charter workflow)
    system_prompt = load_prompt("system_prompt.md")
    charter_prompt = load_prompt("charter_creation.md")

    combined_prompt = f"{system_prompt}\n\n{charter_prompt}"

    return await create_agent(
        model=model, output_type=Charter, system_prompt=combined_prompt
    )
