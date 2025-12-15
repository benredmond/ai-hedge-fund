"""
MCP server configuration and lifecycle management.

This module configures MCP servers for:
- FRED (Federal Reserve Economic Data) - Node.js stdio server
- yfinance (Yahoo Finance) - Python stdio server with dedicated venv
- Composer Trade - HTTP server for symphony backtesting and portfolio monitoring

Tool prefixing strategy:
- fred_* for FRED tools
- stock_* for yfinance tools
- composer_* for Composer tools
"""

import os
import base64
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP
from pydantic_ai.tools import RunContext


# MCP Server Paths - configurable via environment variables
FRED_MCP_PATH = os.getenv(
    "FRED_MCP_PATH", str(Path.home() / "dev/fred-mcp-server/build/index.js")
)
YFINANCE_MCP_PATH = os.getenv(
    "YFINANCE_MCP_PATH", str(Path.home() / "dev/mcp/yahoo-finance-mcp/server.py")
)
YFINANCE_VENV_PYTHON = os.getenv(
    "YFINANCE_VENV_PYTHON",
    str(Path.home() / "dev/mcp/yahoo-finance-mcp/.venv/bin/python"),
)
COMPOSER_MCP_URL = os.getenv("COMPOSER_MCP_URL", "https://mcp.composer.trade/mcp/")


# Tool result compression configuration
COMPRESS_MCP_RESULTS = os.getenv("COMPRESS_MCP_RESULTS", "true").lower() == "true"
SUMMARIZATION_MODEL = os.getenv("SUMMARIZATION_MODEL", "openai:gpt-5-mini")


async def compress_tool_result(
    ctx: RunContext[Any], call_tool_func, name: str, args: dict[str, Any]
) -> Any:
    """
    Compress large tool results before they're added to conversation history.

    This callback intercepts MCP tool calls (FRED, yfinance) and compresses
    results that would otherwise consume hundreds of tokens each. Uses an LLM
    to extract only essential information (latest values, trends, key metrics).

    Args:
        ctx: Runtime context (not used currently)
        call_tool_func: Original tool function to call
        name: Tool name (e.g., "fred_get_series", "stock_get_historical_stock_prices")
        args: Tool arguments

    Returns:
        Compressed result (dict) or original result if compression not needed

    Example:
        Before: {"observations": [{...}, {...}, ...]} (2000+ tokens)
        After: {"latest_value": 5.33, "trend": "increasing", "date": "2025-10"} (30 tokens)
    """
    if not COMPRESS_MCP_RESULTS:
        # Compression disabled
        result = await call_tool_func(name, args, metadata=None)
        return result

    # Call original tool
    result = await call_tool_func(name, args, metadata=None)

    # Only compress data-heavy tools
    data_heavy_tools = [
        "fred_get_series",  # Returns long time series
        "fred_search",  # Returns many search results with descriptions
        "stock_get_historical_stock_prices",  # Returns price history
    ]

    if name not in data_heavy_tools:
        return result

    # Check result size (compress if > 200 chars - aggressive threshold)
    try:
        result_str = json.dumps(result) if not isinstance(result, str) else result
        if len(result_str) < 200:
            return result  # Too small to bother compressing
    except (TypeError, ValueError, UnicodeDecodeError) as e:
        print(
            f"Warning: Cannot serialize tool result for size check: {e.__class__.__name__}: {e}"
        )
        print(
            f"Tool result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}"
        )
        return result  # Proceed without compression

    # Import here to avoid circular dependency
    from src.agent.tool_result_summarizer import SummarizationService

    # Create summarizer (cached globally on first use)
    if not hasattr(compress_tool_result, "_summarizer"):
        compress_tool_result._summarizer = SummarizationService(
            model=SUMMARIZATION_MODEL, enabled=True
        )

    summarizer = compress_tool_result._summarizer

    try:
        # Summarize the result
        summary_data = await summarizer.summarize(name, result)

        # Return just the summary content (not the metadata dict)
        # The summary is already a dict/str from the LLM
        summary_content = summary_data["summary"]

        # Log compression stats with full content
        original_full = str(result) if result else "N/A"
        summary_full = str(summary_content) if summary_content else "N/A"
        print(
            f"[COMPRESS] {name}: {summary_data['original_tokens']} → "
            f"{summary_data['summary_tokens']} tokens "
            f"({summary_data['savings']} saved)"
        )
        print(f"[COMPRESS]   Before: {original_full}")
        print(f"[COMPRESS]   After:  {summary_full}")

        # If the LLM returned a string, parse it as JSON if possible
        if isinstance(summary_content, str):
            try:
                summary_content = json.loads(summary_content)
            except json.JSONDecodeError as e:
                print(f"Warning: Summarization LLM returned invalid JSON: {e}")
                print(f"LLM output preview: {summary_content[:200]}...")
                # Return structured error instead of raw string
                summary_content = {
                    "error": "summarization_failed",
                    "raw_output": summary_content[:500],
                    "message": "LLM returned non-JSON response",
                }

        # HARD CAP: Ensure result never exceeds 150 tokens (~600 chars)
        # This is a safety net in case LLM ignores the 30 token limit
        # WARNING: Truncation may produce invalid JSON or incomplete data
        try:
            result_str = (
                json.dumps(summary_content)
                if not isinstance(summary_content, str)
                else summary_content
            )
            if len(result_str) > 600:
                print(
                    f"Warning: Summary exceeds 600 char limit ({len(result_str)} chars), truncating"
                )
                # Truncate to 600 chars if it's too long
                if isinstance(summary_content, str):
                    summary_content = summary_content[:600]
                elif isinstance(summary_content, dict):
                    # Truncate dict values
                    for key in list(summary_content.keys()):
                        if isinstance(summary_content[key], str):
                            summary_content[key] = summary_content[key][:100]
        except Exception as e:
            print(f"Error: Hard cap truncation failed: {e.__class__.__name__}: {e}")
            # Force emergency truncation
            emergency_str = str(summary_content)[:600]
            summary_content = {"truncated": emergency_str, "error": "truncation_failed"}

        return summary_content

    except Exception as e:
        print(f"Warning: Compression failed for {name}: {e}")
        # Fall back to original result on error
        return result


def create_fred_server() -> MCPServerStdio:
    """
    Create FRED MCP server configuration.

    Returns:
        MCPServerStdio configured for FRED economic data access
    """
    fred_api_key = os.getenv("FRED_API_KEY")
    if not fred_api_key:
        raise ValueError(
            "FRED_API_KEY not set. Get a free key at: "
            "https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    return MCPServerStdio(
        command="node",
        args=[FRED_MCP_PATH],
        env={"FRED_API_KEY": fred_api_key},
        tool_prefix="fred",
        timeout=120,  # Increase from default 5s for slower environments
        process_tool_call=compress_tool_result if COMPRESS_MCP_RESULTS else None,
    )


def create_yfinance_server() -> MCPServerStdio:
    """
    Create yfinance MCP server configuration.

    CRITICAL: Uses dedicated venv at /Users/ben/dev/mcp/yahoo-finance-mcp/.venv/
    DO NOT use project's Python interpreter.

    Returns:
        MCPServerStdio configured for Yahoo Finance data access
    """
    # Verify paths exist
    if not os.path.exists(YFINANCE_VENV_PYTHON):
        raise FileNotFoundError(
            f"yfinance MCP venv not found at {YFINANCE_VENV_PYTHON}. "
            "Ensure yfinance MCP server is installed with its own venv."
        )

    if not os.path.exists(YFINANCE_MCP_PATH):
        raise FileNotFoundError(f"yfinance MCP server not found at {YFINANCE_MCP_PATH}")

    return MCPServerStdio(
        command=YFINANCE_VENV_PYTHON,
        args=[YFINANCE_MCP_PATH],
        tool_prefix="stock",
        timeout=120,  # Increase from default 5s for slower environments
        process_tool_call=compress_tool_result if COMPRESS_MCP_RESULTS else None,
    )


def create_composer_server() -> MCPServerStreamableHTTP:
    """
    Create Composer Trade MCP server configuration.

    Requires environment variables:
        COMPOSER_API_KEY: API key from Composer dashboard
        COMPOSER_API_SECRET: API secret from Composer dashboard

    Optional environment variables:
        COMPOSER_MCP_URL: HTTP endpoint (default: https://mcp.composer.trade/mcp/)

    Returns:
        MCPServerStreamableHTTP configured for Composer Trade API

    Raises:
        ValueError: If COMPOSER_API_KEY or COMPOSER_API_SECRET not set
    """
    api_key = os.getenv("COMPOSER_API_KEY")
    api_secret = os.getenv("COMPOSER_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "COMPOSER_API_KEY and COMPOSER_API_SECRET must be set. "
            "Get credentials from Composer dashboard under 'Accounts & Funding'"
        )

    # Build HTTP Basic Auth header (RFC 7617)
    credentials = f"{api_key}:{api_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    return MCPServerStreamableHTTP(
        url=COMPOSER_MCP_URL,
        headers={"Authorization": f"Basic {encoded_credentials}"},
        timeout=120,  # Connection timeout (increased from 5s)
        read_timeout=300,  # Read timeout (5 minutes)
        tool_prefix="composer",
        process_tool_call=compress_tool_result if COMPRESS_MCP_RESULTS else None,
    )


@asynccontextmanager
async def get_mcp_servers():
    """
    Get configured MCP servers as async context manager.

    Usage:
        async with get_mcp_servers() as servers:
            # servers is a dict: {'fred': MCPServerStdio, 'yfinance': MCPServerStdio}
            agent = Agent(model='...', toolsets=[servers['fred'], servers['yfinance']])

    Yields:
        Dict[str, MCPServerStdio]: Dictionary of MCP server configurations

    Raises:
        ValueError: If required environment variables are missing
        FileNotFoundError: If MCP server paths don't exist
    """
    # Create server configurations
    servers: Dict[str, Any] = {}
    errors = []

    try:
        # Add FRED server
        servers["fred"] = create_fred_server()
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"FRED MCP server failed: {e}"
        print(f"Warning: {error_msg}")
        errors.append(error_msg)

    try:
        # Add yfinance server
        servers["yfinance"] = create_yfinance_server()
    except FileNotFoundError as e:
        error_msg = f"yfinance MCP server failed: {e}"
        print(f"Warning: {error_msg}")
        errors.append(error_msg)

    try:
        # Add Composer server
        servers["composer"] = create_composer_server()
    except (ValueError, FileNotFoundError) as e:
        error_msg = f"Composer MCP server failed: {e}"
        print(f"Warning: {error_msg}")
        errors.append(error_msg)

    # Show summary of MCP server status
    if errors:
        print("\n=== MCP SERVER STARTUP ISSUES ===")
        for err in errors:
            print(f"  - {err}")
        print(f"\nContinuing with {len(servers)}/3 servers available")
        if len(servers) < 2:
            print(
                "WARNING: Running with degraded capabilities - strategy quality may be reduced"
            )

    if not servers:
        raise RuntimeError(
            "No MCP servers available. Ensure at least one MCP server is configured."
        )

    try:
        yield servers
    finally:
        # Cleanup would go here if needed
        # Pydantic AI handles MCP session lifecycle automatically
        pass


def get_available_tools() -> Dict[str, list]:
    """
    Get list of available tools from each MCP server.

    This is a utility function for debugging and validation.

    Returns:
        Dict mapping server name to list of tool names
    """
    tools = {
        "fred": ["fred_browse", "fred_search", "fred_get_series"],
        "yfinance": [
            "stock_get_stock_info",
            "stock_get_historical_stock_prices",
            "stock_get_yahoo_finance_news",
            "stock_get_financial_statement",
            "stock_get_holder_info",
            "stock_get_option_chain",
        ],
        "composer": [
            "composer_create_symphony",
            "composer_search_symphonies",
            "composer_backtest_symphony",
            "composer_backtest_symphony_by_id",
            "composer_list_accounts",
            "composer_get_account_holdings",
            "composer_get_symphony_daily_performance",
        ],
    }
    return tools
