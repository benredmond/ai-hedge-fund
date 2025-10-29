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
from pydantic_ai import messages as _messages
from pydantic_ai.tools import RunContext
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


def adaptive_history_processor(ctx: RunContext, messages: list) -> list:
    """
    Adaptive history management for token-efficient multi-turn conversations.

    Strategy: Keep ~20 messages on average, rely on tool result compression
    to manage token count rather than aggressive message trimming.

    This prevents the agent from losing context and getting stuck in loops
    while still managing overall token usage through aggressive compression
    of tool results before they enter history.

    Increased from 10 → 20 messages because:
    - Compression reduces tool results by ~97% (1578 → 50 tokens)
    - Agent was looping due to forgetting previous search attempts
    - With compression, 20 messages ≈ same tokens as 10 uncompressed messages

    Args:
        ctx: Runtime context with run_step counter
        messages: Current conversation history

    Returns:
        Trimmed message list (must end with ModelRequest per pydantic-ai requirement)
    """
    # Keep 20 messages - focus on compressing tool results instead of trimming history
    max_messages = 20

    if len(messages) <= max_messages:
        return messages

    # Keep only most recent messages
    result = messages[-max_messages:]

    # CRITICAL: Ensure we end with a ModelRequest (required by pydantic-ai)
    # See pydantic_ai/_agent_graph.py lines 1206-1210
    if result and not isinstance(result[-1], _messages.ModelRequest):
        # Add empty request if needed
        result.append(_messages.ModelRequest(parts=[]))

    return result


async def create_agent(
    model: str,
    output_type: Type[T],
    system_prompt: str | None = None,
    include_composer: bool = True
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
        include_composer: Whether to include Composer MCP tools (default: True)

    Note:
        Uses adaptive_history_processor for automatic token management. History
        is dynamically adjusted based on execution phase to prevent token overflow
        during multi-tool research phases.

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

    if "composer" in servers and include_composer:
        toolsets.append(servers["composer"])

    if not toolsets:
        await stack.aclose()  # Clean up before raising
        raise RuntimeError(
            "No MCP servers available. Ensure FRED, yfinance, and/or Composer are configured."
        )

    # Create agent with Pydantic AI using adaptive history processor
    # This processor takes RunContext and dynamically adjusts based on execution phase
    agent = Agent(
        model=model,
        output_type=output_type,
        system_prompt=system_prompt,
        toolsets=toolsets,
        history_processors=[adaptive_history_processor],
    )

    # Return wrapped agent with lifecycle management
    return AgentContext(agent, stack)
