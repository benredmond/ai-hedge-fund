"""
Multi-provider agent factory for trading strategy creation.

This module provides:
- Agent creation with Claude, GPT-4, or Gemini
- MCP tool integration (FRED, yfinance)
- Prompt template loading
- Type-safe strategy output
"""

import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings, PromptedOutput
from pydantic_ai import messages as _messages
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.tools import RunContext
from typing_extensions import assert_never

from src.agent.mcp_config import get_mcp_servers

T = TypeVar("T", bound=BaseModel)

# Default model from environment variable
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai:gpt-4o")

# Provider-specific base URLs for cheaper alternatives
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
KIMI_BASE_URL = "https://api.moonshot.ai/v1"
ANTHROPIC_THINKING_BUDGET_TOKENS = 32000
_ANTHROPIC_THINKING_MODEL_MARKERS = ("claude-opus-4-5",)
_ANTHROPIC_THINKING_OUTPUT_TOKENS = {
    "candidate_generation": 8192,
    "edge_scoring": 2048,
    "winner_selection": 2048,
    "charter_generation": 8192,
    "composer_deployment": 4096,
}
_DEEPSEEK_THINKING_CONFIG = {"thinking": {"type": "enabled"}}


def _split_model(model: str) -> tuple[str, str]:
    """Return provider and model name from a '<provider>:<model>' string."""
    if ":" in model:
        return model.split(":", 1)
    return "", model


def _is_deepseek_model(provider: str, model_name: str) -> bool:
    """Return True for DeepSeek models using either openai: or deepseek: providers."""
    if provider.lower() not in {"openai", "deepseek"}:
        return False
    return model_name.lower().startswith("deepseek")


def _is_anthropic_model(model: str) -> bool:
    """Return True for Anthropic Claude models, with or without provider prefix."""
    provider, model_name = _split_model(model)
    if provider:
        return provider.lower() == "anthropic"
    return model_name.lower().startswith("claude")


def _get_deepseek_base_url() -> str:
    """Return DeepSeek base URL, allowing override via DEEPSEEK_BASE_URL."""
    return os.getenv("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)


def _deepseek_thinking_enabled() -> bool:
    """Return True when DeepSeek thinking is enabled (default on)."""
    value = os.getenv("DEEPSEEK_THINKING", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


class _DeepSeekChatModel(OpenAIChatModel):
    """OpenAI-compatible DeepSeek model with reasoning_content support for tool calls."""

    def _should_include_reasoning(self) -> bool:
        model_name = self.model_name.lower()
        if model_name.startswith("deepseek-reasoner"):
            return True
        if model_name.startswith("deepseek-chat"):
            return _deepseek_thinking_enabled()
        return False

    async def _map_messages(self, messages: list) -> list:
        from openai.types import chat

        openai_messages: list[chat.ChatCompletionMessageParam] = []
        for message in messages:
            if isinstance(message, _messages.ModelRequest):
                async for item in self._map_user_message(message):
                    openai_messages.append(item)
            elif isinstance(message, _messages.ModelResponse):
                texts: list[str] = []
                tool_calls: list[chat.ChatCompletionMessageFunctionToolCallParam] = []
                reasoning_chunks: list[str] = []
                for item in message.parts:
                    if isinstance(item, _messages.TextPart):
                        texts.append(item.content)
                    elif isinstance(item, _messages.ThinkingPart):
                        reasoning_chunks.append(item.content)
                    elif isinstance(item, _messages.ToolCallPart):
                        tool_calls.append(self._map_tool_call(item))
                    elif isinstance(item, (_messages.BuiltinToolCallPart, _messages.BuiltinToolReturnPart)):
                        pass
                    elif isinstance(item, _messages.FilePart):
                        pass
                    else:
                        assert_never(item)

                message_param = chat.ChatCompletionAssistantMessageParam(role="assistant")
                message_param["content"] = "\n\n".join(texts) if texts else None
                if tool_calls:
                    message_param["tool_calls"] = tool_calls

                if self._should_include_reasoning() or reasoning_chunks:
                    if reasoning_chunks:
                        message_param["reasoning_content"] = "\n\n".join(reasoning_chunks)
                    elif tool_calls:
                        # DeepSeek requires reasoning_content when tool calls are present.
                        message_param["reasoning_content"] = ""

                openai_messages.append(message_param)
            else:
                assert_never(message)

        if instructions := self._get_instructions(messages):
            openai_messages.insert(
                0, chat.ChatCompletionSystemMessageParam(content=instructions, role="system")
            )
        return openai_messages



def is_reasoning_model(model: str) -> bool:
    """
    Check if model is reasoning-focused (extended thinking).

    Reasoning models like kimi-k2-thinking, o1, o3 generate separate
    reasoning traces before final answers, requiring specific configuration.

    Args:
        model: Model identifier (e.g., "openai:gpt-4o", "openai:kimi-k2-thinking")

    Returns:
        True if model is a reasoning model, False otherwise
    """
    model_name = model.split(":", 1)[-1].lower()
    if model_name.startswith("deepseek-chat"):
        return _deepseek_thinking_enabled()
    if "thinking" in model_name or "reasoning" in model_name or "reasoner" in model_name:
        return True

    # Reasoning-by-default: explicit allowlist for known non-reasoning families.
    non_reasoning_prefixes = (
        "gpt-4o",
        "gpt-4.1",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5",
        "claude-3",
        "claude-2",
        "moonshot",
        "kimi-",
    )
    return not model_name.startswith(non_reasoning_prefixes)


def _openai_reasoning_effort(model: str) -> str | None:
    """Return OpenAI reasoning effort for models that should force thinking."""
    provider, model_name = _split_model(model)
    if provider != "openai":
        return None
    model_name = model_name.lower()
    if model_name.startswith("gpt-5.2"):
        return "high"
    return None


def _deepseek_thinking_config(model: str) -> dict | None:
    """Return DeepSeek request overrides to enable thinking mode by default."""
    provider, model_name = _split_model(model)
    if not _is_deepseek_model(provider, model_name):
        return None
    if not _deepseek_thinking_enabled():
        return None
    model_lower = model_name.lower()
    if any(marker in model_lower for marker in ("reasoner", "reasoning", "thinking")):
        return None
    # DeepSeek accepts extra request fields via OpenAI-compatible extra_body.
    return dict(_DEEPSEEK_THINKING_CONFIG)


def is_anthropic_thinking_model(model: str) -> bool:
    """Return True for Anthropic models that should run with thinking enabled."""
    provider, model_name = _split_model(model)
    if provider != "anthropic":
        return False
    model_name = model_name.lower()
    return any(marker in model_name for marker in _ANTHROPIC_THINKING_MODEL_MARKERS)


def _anthropic_thinking_config(model: str) -> dict | None:
    """Build Anthropic thinking config for supported models."""
    if not is_anthropic_thinking_model(model):
        return None
    return {"type": "enabled", "budget_tokens": ANTHROPIC_THINKING_BUDGET_TOKENS}


def _apply_anthropic_thinking(
    model: str, stage: str, settings: dict
) -> dict:
    """Inject Anthropic thinking settings and ensure max_tokens is sufficient."""
    thinking = _anthropic_thinking_config(model)
    if not thinking:
        return settings
    settings["anthropic_thinking"] = thinking
    output_buffer = _ANTHROPIC_THINKING_OUTPUT_TOKENS.get(stage, 4096)
    min_tokens = ANTHROPIC_THINKING_BUDGET_TOKENS + output_buffer
    current_max = settings.get("max_tokens")
    if current_max is None or current_max < min_tokens:
        settings["max_tokens"] = min_tokens
    return settings


def _apply_deepseek_thinking(model: str, stage: str, settings: dict) -> dict:
    """Inject DeepSeek thinking overrides when enabled."""
    config = _deepseek_thinking_config(model)
    if not config:
        return settings

    extra_body = settings.get("extra_body")
    if isinstance(extra_body, dict):
        merged = dict(extra_body)
        for key, value in config.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                nested = dict(merged[key])
                nested.update(value)
                merged[key] = nested
            else:
                merged[key] = value
        settings["extra_body"] = merged
    else:
        settings["extra_body"] = config

    # Thinking mode benefits from a larger output budget across stages.
    stage_min_tokens = {
        "candidate_generation": 32768,
        "edge_scoring": 16384,
        "winner_selection": 16384,
        "charter_generation": 32768,
        "composer_deployment": 32768,
    }
    min_tokens = stage_min_tokens.get(stage, 0)
    if min_tokens:
        current_max = settings.get("max_tokens")
        if current_max is None or current_max < min_tokens:
            settings["max_tokens"] = min_tokens

    return settings


def _maybe_prompted_output(model: str, output_type: Type[T]):
    """Force text-mode structured output when Anthropic thinking is enabled."""
    if not is_anthropic_thinking_model(model):
        return output_type
    if output_type is str:
        return output_type
    if isinstance(output_type, PromptedOutput):
        return output_type
    return PromptedOutput(output_type)


def get_model_settings(
    model: str, stage: str, custom_settings: Optional[ModelSettings] = None
) -> Optional[ModelSettings]:
    """
    Get stage-specific ModelSettings for given model.

    Configuration rationale:
    - temperature=1.0: Balanced creativity/consistency for reasoning models (Kimi/Moonshot)
    - OpenAI GPT-5.2: set openai_reasoning_effort="high" and avoid temperature/top_p
    - Anthropic Claude Opus 4.5: enable thinking with a fixed 32k budget
    - max_tokens=16384: Minimum for reasoning trace + final answer
    - parallel_tool_calls=False: Workaround for Pydantic AI bug #1429 + reasoning models don't support parallel

    Args:
        model: Model identifier (e.g., "openai:kimi-k2-thinking")
        stage: Workflow stage ("candidate_generation", "edge_scoring", "winner_selection", "charter_generation")
        custom_settings: Optional custom settings to override defaults

    Returns:
        ModelSettings configured for the model and stage, or None if no special settings needed

    Raises:
        ValueError: If stage is not recognized
    """
    VALID_STAGES = {
        "candidate_generation",
        "edge_scoring",
        "winner_selection",
        "charter_generation",
        "composer_deployment",
    }
    if stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: '{stage}'. Must be one of {VALID_STAGES}")

    if custom_settings:
        return custom_settings

    is_reasoning = is_reasoning_model(model)
    openai_reasoning_effort = _openai_reasoning_effort(model)
    allow_sampling_params = openai_reasoning_effort is None

    # Default timeout for all API calls (15 minutes for slow providers like Kimi reasoning models)
    DEFAULT_TIMEOUT = 900.0

    # Stage-specific settings
    if stage == "candidate_generation":
        settings: dict = {
            "parallel_tool_calls": False,  # Fix for Pydantic AI bug #1429
            "timeout": DEFAULT_TIMEOUT,
        }
        if is_reasoning:
            settings["max_tokens"] = 32768  # Increased from 16384 to prevent thesis truncation
            if allow_sampling_params:
                settings["temperature"] = 1.0  # Balanced creativity/consistency for reasoning models
        if openai_reasoning_effort:
            settings["openai_reasoning_effort"] = openai_reasoning_effort
        settings = _apply_anthropic_thinking(model, stage, settings)
        settings = _apply_deepseek_thinking(model, stage, settings)
        return ModelSettings(**settings)

    elif stage in ["edge_scoring", "winner_selection"]:
        settings: dict = {"timeout": DEFAULT_TIMEOUT}
        if is_reasoning:
            settings["max_tokens"] = 16384
            if allow_sampling_params:
                settings["temperature"] = 1.0
        if openai_reasoning_effort:
            settings["openai_reasoning_effort"] = openai_reasoning_effort
        settings = _apply_anthropic_thinking(model, stage, settings)
        settings = _apply_deepseek_thinking(model, stage, settings)
        return ModelSettings(**settings)

    elif stage == "charter_generation":
        settings: dict = {
            "max_tokens": 32768,  # Increased from 20000 to handle large charter output
            "timeout": DEFAULT_TIMEOUT,
        }
        if is_reasoning and allow_sampling_params:
            settings["temperature"] = 1.0
        if openai_reasoning_effort:
            settings["openai_reasoning_effort"] = openai_reasoning_effort
        settings = _apply_anthropic_thinking(model, stage, settings)
        settings = _apply_deepseek_thinking(model, stage, settings)
        return ModelSettings(**settings)

    elif stage == "composer_deployment":
        # Deployment needs tools, similar to candidate generation
        settings: dict = {
            "parallel_tool_calls": False,
            "timeout": DEFAULT_TIMEOUT,
        }
        if is_reasoning:
            settings["max_tokens"] = 32768  # Increased for reasoning trace + JSON output
            if allow_sampling_params:
                settings["temperature"] = 1.0
                if not _is_anthropic_model(model):
                    settings["top_p"] = 1.0
        if openai_reasoning_effort:
            settings["openai_reasoning_effort"] = openai_reasoning_effort
        settings = _apply_anthropic_thinking(model, stage, settings)
        settings = _apply_deepseek_thinking(model, stage, settings)
        return ModelSettings(**settings)

    settings = {"timeout": DEFAULT_TIMEOUT}
    settings = _apply_anthropic_thinking(model, stage, settings)
    settings = _apply_deepseek_thinking(model, stage, settings)
    return ModelSettings(**settings)


class AgentContext:
    """
    Async context manager that wraps an agent and its MCP server lifecycle.

    This ensures MCP servers remain active for the agent's lifetime.

    Usage:
        async with create_agent(...) as agent:
            result = await agent.run("Create strategy")

    The MCP servers will be automatically closed when exiting the context.
    """

    def __init__(
        self,
        agent: Agent,
        stack: AsyncExitStack,
        restore_env: Optional[dict[str, Optional[str]]] = None,
    ):
        self._agent = agent
        self._stack = stack
        self._restore_env = restore_env

    async def __aenter__(self):
        """Enter the async context, returning the agent"""
        return self._agent

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context, closing MCP servers"""
        await self._stack.aclose()
        if self._restore_env:
            for key, value in self._restore_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def __getattr__(self, name):
        """Delegate attribute access to the underlying agent"""
        return getattr(self._agent, name)


# Prompt directory
PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str, include_tools: bool = True) -> str:
    """
    Load prompt template from prompts directory with optional tool injection.

    Args:
        filename: Prompt template filename (e.g., 'system_prompt.md')
        include_tools: Whether to inject tool documentation (default: True)

    Returns:
        Prompt content as string (with tool docs appended if requested)

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = PROMPT_DIR / filename

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt template not found: {prompt_path}\n"
            f"Available prompts: {list(PROMPT_DIR.glob('*.md'))}"
        )

    content = prompt_path.read_text()

    # Auto-inject tool documentation for system prompts only
    # System prompts define agent role/constraints and are passed to create_agent(system_prompt=...)
    # Recipe prompts provide workflow instructions and are passed in user messages
    is_system_prompt = filename.startswith("system/")

    if include_tools and is_system_prompt:
        tool_docs = _load_tool_documentation()
        if tool_docs:  # Only append if we found tool docs
            content += "\n\n---\n\n## AVAILABLE TOOLS\n\n" + tool_docs

    return content


def _load_tool_documentation() -> str:
    """
    Load and concatenate all tool documentation files.

    Returns:
        Combined tool documentation, or empty string if no tools found
    """
    tools_dir = PROMPT_DIR / "tools"

    if not tools_dir.exists():
        return ""

    tool_sections = []

    # Load in specific order: FRED (most important), yfinance, Composer
    for tool_file in ["fred.md", "yfinance.md", "composer.md"]:
        tool_path = tools_dir / tool_file
        if tool_path.exists():
            tool_sections.append(tool_path.read_text())

    return "\n\n---\n\n".join(tool_sections)


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
    include_fred: bool = True,
    include_yfinance: bool = True,
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
        include_fred: Whether to include FRED MCP tools (default: True)
        include_yfinance: Whether to include yfinance/stock MCP tools (default: True)
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
    provider = provider.lower()
    model_name = model_name.strip()
    model = f"{provider}:{model_name}"

    # Alias "gemini:" to the official Google provider prefix for pydantic-ai
    if provider == "gemini":
        provider = "google-gla"
        model = f"{provider}:{model_name}"

    model_name_lower = model_name.lower()
    if provider == "deepseek":
        model_name = model_name_lower
        model = f"{provider}:{model_name}"

    restore_env: Optional[dict[str, Optional[str]]] = None
    if provider == "openai":
        original_openai_key = os.getenv("OPENAI_API_KEY")
        original_base_url = os.getenv("OPENAI_BASE_URL")
        # DeepSeek uses OpenAI-compatible API
        if model_name_lower.startswith("deepseek"):
            model_name = model_name_lower
            model = f"{provider}:{model_name}"
            deepseek_key = os.getenv("DEEPSEEK_API_KEY")
            if not deepseek_key:
                raise ValueError(
                    "DEEPSEEK_API_KEY environment variable required for DeepSeek models"
                )
            os.environ["OPENAI_API_KEY"] = deepseek_key
            os.environ["OPENAI_BASE_URL"] = _get_deepseek_base_url()
            restore_env = {
                "OPENAI_API_KEY": original_openai_key,
                "OPENAI_BASE_URL": original_base_url,
            }
        # Kimi/Moonshot uses OpenAI-compatible API
        elif model_name.startswith("moonshot") or model_name.startswith("kimi"):
            kimi_key = os.getenv("KIMI_API_KEY")
            if not kimi_key:
                raise ValueError(
                    "KIMI_API_KEY environment variable required for Kimi/Moonshot models"
                )
            os.environ["OPENAI_API_KEY"] = kimi_key
            os.environ["OPENAI_BASE_URL"] = KIMI_BASE_URL
            restore_env = {
                "OPENAI_API_KEY": original_openai_key,
                "OPENAI_BASE_URL": original_base_url,
            }
        else:
            # Reset base URL if it was set for OpenAI-compatible providers.
            base_url = os.getenv("OPENAI_BASE_URL")
            if base_url in {DEEPSEEK_BASE_URL, KIMI_BASE_URL}:
                os.environ.pop("OPENAI_BASE_URL", None)

    stack: Optional[AsyncExitStack] = None
    try:
        # Load system prompt if not provided
        if system_prompt is None:
            system_prompt = load_prompt("system_prompt.md")

        # Create AsyncExitStack to manage MCP server lifecycle (and any provider clients)
        stack = AsyncExitStack()

        # Enter MCP servers context and keep it alive
        servers = await stack.enter_async_context(get_mcp_servers())

        # Create toolsets list from available servers
        toolsets = []

        if "fred" in servers and include_fred:
            toolsets.append(servers["fred"])

        if "yfinance" in servers and include_yfinance:
            toolsets.append(servers["yfinance"])

        if "composer" in servers and include_composer:
            toolsets.append(servers["composer"])

        # Allow agents with no tools (e.g., deployment stage that outputs JSON directly)
        if not toolsets:
            toolsets = None

        # Determine if we need to patch tools (specifically for Composer)
        prepare_tools = None
        if include_composer:
            from src.agent.schema_fixes import fix_composer_schema
            prepare_tools = fix_composer_schema

        # Use a dedicated http client for Google to avoid shared client closure across agents.
        model_for_agent = model
        if provider in {"google-gla", "google-vertex"}:
            import httpx
            from pydantic_ai.providers.google import GoogleProvider
            from pydantic_ai.models.google import GoogleModel

            http_client = await stack.enter_async_context(httpx.AsyncClient())
            google_provider = GoogleProvider(
                vertexai=provider == "google-vertex",
                http_client=http_client,
            )
            model_for_agent = GoogleModel(model_name=model_name, provider=google_provider)
        elif _is_deepseek_model(provider, model_name):
            # DeepSeek doesn't support tool_choice="required"; disable it via profile override.
            from pydantic_ai.profiles.openai import OpenAIModelProfile
            from pydantic_ai.providers import infer_provider

            deepseek_provider = infer_provider("openai" if provider == "openai" else "deepseek")

            def _deepseek_profile(name: str):
                base_profile = deepseek_provider.model_profile(name)
                return OpenAIModelProfile(openai_supports_tool_choice_required=False).update(base_profile)

            model_for_agent = _DeepSeekChatModel(
                model_name=model_name,
                provider=deepseek_provider,
                profile=_deepseek_profile,
            )

        # Force text-mode structured output when Anthropic thinking is enabled.
        output_spec = _maybe_prompted_output(model, output_type)

        # Create agent with Pydantic AI using configurable history processor
        agent = Agent(
            model=model_for_agent,
            output_type=output_spec,
            system_prompt=system_prompt,
            toolsets=toolsets,
            history_processors=[create_history_processor(max_messages=history_limit)],
            model_settings=model_settings,
            prepare_tools=prepare_tools,
        )

        # Return wrapped agent with lifecycle management
        return AgentContext(agent, stack, restore_env=restore_env)
    except Exception:
        if stack is not None:
            await stack.aclose()
        if restore_env:
            for key, value in restore_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        raise
