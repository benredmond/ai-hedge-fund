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
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP


# MCP Server Paths - configurable via environment variables
FRED_MCP_PATH = os.getenv(
    'FRED_MCP_PATH',
    str(Path.home() / 'dev/fred-mcp-server/build/index.js')
)
YFINANCE_MCP_PATH = os.getenv(
    'YFINANCE_MCP_PATH',
    str(Path.home() / 'dev/yahoo-finance-mcp/server.py')
)
YFINANCE_VENV_PYTHON = os.getenv(
    'YFINANCE_VENV_PYTHON',
    str(Path.home() / 'dev/yahoo-finance-mcp/.venv/bin/python')
)
COMPOSER_MCP_URL = os.getenv(
    'COMPOSER_MCP_URL',
    'https://ai.composer.trade/mcp'
)


def create_fred_server() -> MCPServerStdio:
    """
    Create FRED MCP server configuration.

    Returns:
        MCPServerStdio configured for FRED economic data access
    """
    fred_api_key = os.getenv('FRED_API_KEY')
    if not fred_api_key:
        raise ValueError(
            "FRED_API_KEY not set. Get a free key at: "
            "https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    return MCPServerStdio(
        command='node',
        args=[FRED_MCP_PATH],
        env={'FRED_API_KEY': fred_api_key},
        tool_prefix='fred'
    )


def create_yfinance_server() -> MCPServerStdio:
    """
    Create yfinance MCP server configuration.

    CRITICAL: Uses dedicated venv at /Users/ben/dev/yahoo-finance-mcp/.venv/
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
        raise FileNotFoundError(
            f"yfinance MCP server not found at {YFINANCE_MCP_PATH}"
        )

    return MCPServerStdio(
        command=YFINANCE_VENV_PYTHON,
        args=[YFINANCE_MCP_PATH],
        tool_prefix='stock'
    )


def create_composer_server() -> MCPServerStreamableHTTP:
    """
    Create Composer Trade MCP server configuration.

    Requires environment variables:
        COMPOSER_API_KEY: API key from Composer dashboard
        COMPOSER_API_SECRET: API secret from Composer dashboard

    Optional environment variables:
        COMPOSER_MCP_URL: HTTP endpoint (default: https://ai.composer.trade/mcp)

    Returns:
        MCPServerStreamableHTTP configured for Composer Trade API

    Raises:
        ValueError: If COMPOSER_API_KEY or COMPOSER_API_SECRET not set
    """
    api_key = os.getenv('COMPOSER_API_KEY')
    api_secret = os.getenv('COMPOSER_API_SECRET')

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
        headers={'Authorization': f'Basic {encoded_credentials}'},
        timeout=5,           # Connection timeout
        read_timeout=300,    # Read timeout (5 minutes)
        tool_prefix='composer'
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

    try:
        # Add FRED server
        servers['fred'] = create_fred_server()
    except (ValueError, FileNotFoundError) as e:
        print(f"Warning: FRED MCP server not available: {e}")

    try:
        # Add yfinance server
        servers['yfinance'] = create_yfinance_server()
    except FileNotFoundError as e:
        print(f"Warning: yfinance MCP server not available: {e}")

    try:
        # Add Composer server
        servers['composer'] = create_composer_server()
    except (ValueError, FileNotFoundError) as e:
        print(f"Warning: Composer MCP server not available: {e}")

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
        'fred': [
            'fred_browse',
            'fred_search',
            'fred_get_series'
        ],
        'yfinance': [
            'stock_get_stock_info',
            'stock_get_historical_stock_prices',
            'stock_get_yahoo_finance_news',
            'stock_get_financial_statement',
            'stock_get_holder_info',
            'stock_get_option_chain'
        ],
        'composer': [
            'composer_create_symphony',
            'composer_search_symphonies',
            'composer_backtest_symphony',
            'composer_backtest_symphony_by_id',
            'composer_list_accounts',
            'composer_get_account_holdings',
            'composer_get_symphony_daily_performance'
        ]
    }
    return tools
