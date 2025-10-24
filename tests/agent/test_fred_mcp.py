import pytest
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_fred_mcp_connectivity():
    """FRED MCP server starts and lists tools."""
    fred_mcp_path = "/Users/ben/dev/fred-mcp-server/build/index.js"

    if not os.path.exists(fred_mcp_path):
        pytest.skip(f"FRED MCP not found at {fred_mcp_path}")

    server_params = StdioServerParameters(
        command="node",
        args=[fred_mcp_path],
        env={"FRED_API_KEY": os.getenv("FRED_API_KEY")}
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List tools
                tools = await session.list_tools()

                # Validate
                assert len(tools.tools) >= 3, f"Expected >=3 tools, got {len(tools.tools)}"
                tool_names = [t.name for t in tools.tools]
                assert any("fred" in name.lower() or "macro" in name.lower() for name in tool_names), \
                    f"Expected FRED/macro tools, got: {tool_names}"

                print(f"✅ FRED MCP operational with {len(tools.tools)} tools: {tool_names}")
    except Exception as e:
        pytest.fail(f"FRED MCP connection failed: {type(e).__name__}: {e}")
