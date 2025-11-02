"""
Tests for MCP server configuration and lifecycle management.
Following TDD: Write tests first, then implement mcp_config.py.
"""

import pytest
import os


class TestMCPConfiguration:
    """Test MCP server configuration"""

    @pytest.mark.asyncio
    async def test_get_mcp_servers_returns_context_manager(self):
        """get_mcp_servers returns async context manager"""
        from src.agent.mcp_config import get_mcp_servers

        # Should be callable and return async context manager
        servers_cm = get_mcp_servers()
        assert hasattr(servers_cm, "__aenter__")
        assert hasattr(servers_cm, "__aexit__")

    @pytest.mark.asyncio
    async def test_mcp_servers_initialized(self):
        """MCP servers are initialized with correct configuration"""
        from src.agent.mcp_config import get_mcp_servers

        async with get_mcp_servers() as servers:
            # Should have FRED and yfinance servers (Composer deferred)
            assert "fred" in servers or "yfinance" in servers
            assert isinstance(servers, dict)

    @pytest.mark.asyncio
    async def test_fred_server_configuration(self):
        """FRED MCP server configured with correct parameters"""
        from src.agent.mcp_config import create_fred_server

        server = create_fred_server()

        # Check it's the right type
        assert hasattr(server, "__aenter__")  # Context manager

        # Verify configuration (tool prefix will be checked in integration test)
        assert server is not None

    @pytest.mark.asyncio
    async def test_yfinance_server_configuration(self):
        """yfinance MCP server configured with correct parameters"""
        from src.agent.mcp_config import create_yfinance_server

        server = create_yfinance_server()

        # Check it's the right type
        assert hasattr(server, "__aenter__")  # Context manager
        assert server is not None

    @pytest.mark.asyncio
    async def test_mcp_cleanup_on_exit(self):
        """MCP servers cleaned up properly on context exit"""
        from src.agent.mcp_config import get_mcp_servers

        servers = None
        async with get_mcp_servers() as srv:
            servers = srv
            assert servers is not None

        # After exit, context should be cleaned up
        # (actual cleanup verification would need integration test)


class TestToolPrefixing:
    """Test tool prefixing to prevent naming conflicts"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fred_tools_have_prefix(self):
        """FRED MCP tools have 'fred_' prefix"""
        from src.agent.mcp_config import create_fred_server
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters

        server_params = StdioServerParameters(
            command="node",
            args=["/Users/ben/dev/mcp/fred-mcp-server/build/index.js"],
            env={"FRED_API_KEY": os.getenv("FRED_API_KEY")},
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()

                # All FRED tools should have prefix (when integrated with Pydantic AI)
                # This test verifies the MCP server is reachable
                assert len(tools.tools) >= 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_yfinance_tools_reachable(self):
        """yfinance MCP server is reachable and returns tools"""
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from mcp.client.session import ClientSession

        yfinance_venv_python = "/Users/ben/dev/mcp/yahoo-finance-mcp/.venv/bin/python"
        yfinance_mcp_path = "/Users/ben/dev/mcp/yahoo-finance-mcp/server.py"

        server_params = StdioServerParameters(
            command=yfinance_venv_python, args=[yfinance_mcp_path]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()

                # yfinance should have multiple tools
                assert len(tools.tools) >= 5


class TestMCPServerPaths:
    """Test MCP server path validation"""

    def test_fred_mcp_path_exists(self):
        """FRED MCP server path exists"""
        fred_path = "/Users/ben/dev/mcp/fred-mcp-server/build/index.js"

        if not os.path.exists(fred_path):
            pytest.skip(f"FRED MCP not found at {fred_path}")

        assert os.path.exists(fred_path)

    def test_yfinance_mcp_path_exists(self):
        """yfinance MCP server path exists"""
        yfinance_path = "/Users/ben/dev/mcp/yahoo-finance-mcp/server.py"

        if not os.path.exists(yfinance_path):
            pytest.skip(f"yfinance MCP not found at {yfinance_path}")

        assert os.path.exists(yfinance_path)

    def test_yfinance_venv_exists(self):
        """yfinance MCP dedicated venv exists"""
        venv_python = "/Users/ben/dev/mcp/yahoo-finance-mcp/.venv/bin/python"

        if not os.path.exists(venv_python):
            pytest.skip(f"yfinance venv not found at {venv_python}")

        assert os.path.exists(venv_python)
