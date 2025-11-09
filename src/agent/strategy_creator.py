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
from typing import Optional, Type, TypeVar
import os
from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings
from pydantic_ai import messages as _messages
from pydantic_ai.tools import RunContext
from src.agent.mcp_config import get_mcp_servers


T = TypeVar("T", bound=BaseModel)

# Default model from environment variable
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai:gpt-4o")

# Provider-specific configuration for cheaper alternatives
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_BASE_URL = "https://api.moonshot.ai/v1"


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


def create_history_processor(max_messages: int = 20):
    """
    Factory for creating adaptive history processors with configurable limits.

    Different workflow stages have different iteration needs:
    - Candidate Generation (20): Iterative with optional tool usage
    - Edge Scoring (10): Single evaluation, no tools
    - Winner Selection (10): Single-pass reasoning
    - Charter Generation (20): Complex synthesis with tools

    Args:
        max_messages: Maximum messages to keep in history (default: 20)

    Returns:
        History processor function for Agent initialization

    Example:
        >>> agent = Agent(
        ...     model=model,
        ...     history_processors=[create_history_processor(max_messages=10)]
        ... )
    """

    def processor(ctx: RunContext, messages: list) -> list:
        """Keep most recent N messages, ensuring valid message list."""
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

    return processor


def adaptive_history_processor(ctx: RunContext, messages: list) -> list:
    """
    Default adaptive history processor (20 messages).

    DEPRECATED: Use create_history_processor(max_messages=N) instead for
    explicit control over history limits per stage.

    This function maintained for backward compatibility.
    """
    return create_history_processor(max_messages=20)(ctx, messages)


async def create_agent(
    model: str,
    output_type: Type[T],
    system_prompt: str | None = None,
    include_composer: bool = True,
    history_limit: int = 20,
    model_settings: Optional[ModelSettings] = None,
) -> AgentContext:
    """
    Create AI agent with multi-provider support and MCP tools.

    IMPORTANT: Returns an async context manager. Use with 'async with':

        async with create_agent(...) as agent:
            result = await agent.run("Create strategy")

    This ensures MCP servers remain active for the agent's lifetime.

    Supports:
    - Claude
    - GPT
    - Gemini
    - DeepSeek
    - Kimi

    Args:
        model: Model identifier (format: 'provider:model-name')
        output_type: Pydantic model for structured output (Strategy, Charter, etc.)
        system_prompt: Optional system prompt (defaults to system_prompt.md)
        include_composer: Whether to include Composer MCP tools (default: True)
        history_limit: Max messages to keep in conversation history (default: 20)
            Recommended limits per stage:
            - Candidate Generation: 20 (iterative with tools)
            - Edge Scoring: 10 (single evaluation)
            - Winner Selection: 10 (single-pass reasoning)
            - Charter Generation: 20 (complex synthesis)

    Returns:
        AgentContext that manages agent and MCP server lifecycle

    Raises:
        ValueError: If model format is invalid
        RuntimeError: If MCP servers are unavailable

    Example:
        >>> # Create agent context with custom history limit
        >>> agent_ctx = await create_agent(
        ...     model='anthropic:claude-3-5-sonnet-20241022',
        ...     output_type=EdgeScorecard,
        ...     history_limit=10  # Smaller limit for simple evaluation
        ... )
        >>> # Use agent within context
        >>> async with agent_ctx as agent:
        ...     result = await agent.run(prompt)
        ...     print(result.output.total_score)
        4.2
    """
    # Validate model format
    if ":" not in model:
        raise ValueError(
            f"Invalid model format: '{model}'. "
            f"Expected 'provider:model-name' (e.g., 'anthropic:claude-3-5-sonnet-20241022')"
        )

    # Configure provider-specific settings for cheaper alternatives
    provider, model_name = model.split(":", 1)

    if provider == "openai":
        # DeepSeek uses OpenAI-compatible API
        if model_name.startswith("deepseek"):
            if not DEEPSEEK_API_KEY:
                raise ValueError(
                    "DEEPSEEK_API_KEY environment variable required for DeepSeek models"
                )
            os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
            os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL
        # Kimi/Moonshot uses OpenAI-compatible API
        elif model_name.startswith("moonshot") or model_name.startswith("kimi"):
            if not KIMI_API_KEY:
                raise ValueError(
                    "KIMI_API_KEY environment variable required for Kimi/Moonshot models"
                )
            os.environ["OPENAI_API_KEY"] = KIMI_API_KEY
            os.environ["OPENAI_BASE_URL"] = KIMI_BASE_URL

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

    # Create agent with Pydantic AI using configurable history processor
    agent = Agent(
        model=model,
        output_type=output_type,
        system_prompt=system_prompt,
        toolsets=toolsets,
        history_processors=[create_history_processor(max_messages=history_limit)],
        model_settings=model_settings,
    )

    # Return wrapped agent with lifecycle management
    return AgentContext(agent, stack)
