import pytest
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_yfinance_mcp_connectivity():
    """yfinance MCP server starts and lists tools."""
    yfinance_mcp_path = "/Users/ben/dev/yahoo-finance-mcp/server.py"

    if not os.path.exists(yfinance_mcp_path):
        pytest.skip(f"yfinance MCP not found at {yfinance_mcp_path}")

    # yfinance MCP is Python-based, use its venv
    yfinance_venv_python = "/Users/ben/dev/yahoo-finance-mcp/.venv/bin/python"
    server_params = StdioServerParameters(
        command=yfinance_venv_python,
        args=[yfinance_mcp_path]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List tools
                tools = await session.list_tools()

                # Validate yfinance tools
                assert len(tools.tools) >= 5, f"Expected >=5 tools, got {len(tools.tools)}"
                tool_names = [t.name for t in tools.tools]
                # Look for stock/yahoo-related tools
                assert any("stock" in name.lower() or "yahoo" in name.lower() or "price" in name.lower()
                          for name in tool_names), f"Expected stock/yahoo tools, got: {tool_names}"

                print(f"✅ yfinance MCP operational with {len(tools.tools)} tools: {tool_names}")
    except Exception as e:
        pytest.fail(f"yfinance MCP connection failed: {type(e).__name__}: {e}")
