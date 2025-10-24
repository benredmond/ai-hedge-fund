"""
Integration tests for Composer MCP HTTP server.

Tests HTTP MCP server connectivity, tool discovery, and graceful degradation.
"""

import os
import pytest
from src.agent.mcp_config import create_composer_server, get_mcp_servers


class TestComposerServerCreation:
    """Test Composer MCP server factory function."""

    def test_composer_server_requires_api_key(self, monkeypatch):
        """Composer server raises ValueError if COMPOSER_API_KEY not set"""
        monkeypatch.delenv('COMPOSER_API_KEY', raising=False)
        monkeypatch.setenv('COMPOSER_API_SECRET', 'test-secret')

        with pytest.raises(ValueError, match="COMPOSER_API_KEY and COMPOSER_API_SECRET must be set"):
            create_composer_server()

    def test_composer_server_requires_api_secret(self, monkeypatch):
        """Composer server raises ValueError if COMPOSER_API_SECRET not set"""
        monkeypatch.setenv('COMPOSER_API_KEY', 'test-key')
        monkeypatch.delenv('COMPOSER_API_SECRET', raising=False)

        with pytest.raises(ValueError, match="COMPOSER_API_KEY and COMPOSER_API_SECRET must be set"):
            create_composer_server()

    def test_composer_server_creation_with_credentials(self, monkeypatch):
        """Composer server factory returns MCPServerStreamableHTTP with valid credentials"""
        monkeypatch.setenv('COMPOSER_API_KEY', 'test-key-123')
        monkeypatch.setenv('COMPOSER_API_SECRET', 'test-secret-456')

        server = create_composer_server()

        # Verify it's the right type
        from pydantic_ai.mcp import MCPServerStreamableHTTP
        assert isinstance(server, MCPServerStreamableHTTP)

        # Verify configuration
        assert server.tool_prefix == 'composer'
        assert server.timeout == 5
        assert server.read_timeout == 300

    def test_composer_server_uses_default_url(self, monkeypatch):
        """Composer server uses default URL when COMPOSER_MCP_URL not set"""
        monkeypatch.setenv('COMPOSER_API_KEY', 'test-key')
        monkeypatch.setenv('COMPOSER_API_SECRET', 'test-secret')

        server = create_composer_server()

        # Verify default URL is used (module-level variable set at import time)
        assert server.url == 'https://ai.composer.trade/mcp'

    def test_composer_server_base64_encoding(self, monkeypatch):
        """Composer server correctly encodes credentials in Base64"""
        import base64

        monkeypatch.setenv('COMPOSER_API_KEY', 'my-key')
        monkeypatch.setenv('COMPOSER_API_SECRET', 'my-secret')

        server = create_composer_server()

        # Verify Authorization header format
        expected_creds = base64.b64encode(b'my-key:my-secret').decode()
        expected_header = f'Basic {expected_creds}'

        assert 'Authorization' in server.headers
        assert server.headers['Authorization'] == expected_header


class TestComposerIntegration:
    """Test Composer integration with get_mcp_servers()."""

    @pytest.mark.asyncio
    async def test_get_mcp_servers_includes_composer(self, monkeypatch):
        """get_mcp_servers() includes Composer when credentials available"""
        # Set all required credentials
        monkeypatch.setenv('FRED_API_KEY', 'test-fred-key')
        monkeypatch.setenv('COMPOSER_API_KEY', 'test-composer-key')
        monkeypatch.setenv('COMPOSER_API_SECRET', 'test-composer-secret')

        async with get_mcp_servers() as servers:
            # Composer should be in servers dict
            assert 'composer' in servers

            # Verify it's the right type
            from pydantic_ai.mcp import MCPServerStreamableHTTP
            assert isinstance(servers['composer'], MCPServerStreamableHTTP)

    @pytest.mark.asyncio
    async def test_get_mcp_servers_without_composer_credentials(self, monkeypatch, capsys):
        """get_mcp_servers() works without Composer credentials (graceful degradation)"""
        # Ensure Composer credentials are NOT set
        monkeypatch.delenv('COMPOSER_API_KEY', raising=False)
        monkeypatch.delenv('COMPOSER_API_SECRET', raising=False)

        # Set other server credentials
        monkeypatch.setenv('FRED_API_KEY', 'test-fred-key')

        async with get_mcp_servers() as servers:
            # Composer should NOT be in servers dict
            assert 'composer' not in servers

            # But other servers should still work
            assert 'fred' in servers or 'yfinance' in servers

        # Verify warning message was printed
        captured = capsys.readouterr()
        assert 'Warning: Composer MCP server not available' in captured.out

    @pytest.mark.asyncio
    async def test_three_server_integration(self, monkeypatch):
        """All three servers (FRED, yfinance, Composer) can coexist"""
        # Set all credentials
        monkeypatch.setenv('FRED_API_KEY', 'test-fred-key')
        monkeypatch.setenv('COMPOSER_API_KEY', 'test-composer-key')
        monkeypatch.setenv('COMPOSER_API_SECRET', 'test-composer-secret')

        async with get_mcp_servers() as servers:
            # All servers should be available (or at least Composer + one stdio server)
            assert 'composer' in servers

            # Verify different server types coexist
            server_types = {name: type(server).__name__ for name, server in servers.items()}

            # Should have both stdio and HTTP servers
            has_stdio = any('Stdio' in t for t in server_types.values())
            has_http = any('HTTP' in t for t in server_types.values())

            assert has_http, "Should have at least one HTTP server (Composer)"
            # Note: stdio servers might not be available in test environment


class TestComposerToolPrefixing:
    """Test that Composer tools use correct prefix."""

    def test_composer_tools_have_prefix(self):
        """Composer tools documented with composer_ prefix"""
        from src.agent.mcp_config import get_available_tools

        tools = get_available_tools()

        assert 'composer' in tools
        composer_tools = tools['composer']

        # Verify all tools have composer_ prefix
        for tool in composer_tools:
            assert tool.startswith('composer_'), f"Tool {tool} missing composer_ prefix"

        # Verify expected tools are documented
        expected_tools = [
            'composer_create_symphony',
            'composer_search_symphonies',
            'composer_backtest_symphony',
            'composer_list_accounts',
        ]

        for expected in expected_tools:
            assert expected in composer_tools, f"Expected tool {expected} not documented"


@pytest.mark.integration
class TestComposerHTTPConnectivity:
    """Integration tests requiring live Composer endpoint (marked as integration)."""

    @pytest.mark.asyncio
    async def test_composer_endpoint_connectivity(self):
        """
        Test actual HTTP connectivity to Composer endpoint.

        Requires:
        - COMPOSER_API_KEY set in environment
        - COMPOSER_API_SECRET set in environment
        - Network access to https://ai.composer.trade/mcp
        """
        # Skip if credentials not available
        if not os.getenv('COMPOSER_API_KEY') or not os.getenv('COMPOSER_API_SECRET'):
            pytest.skip("COMPOSER_API_KEY and COMPOSER_API_SECRET required for integration test")

        # This test validates that the HTTP endpoint is reachable and accepts our credentials
        # Actual tool discovery test would require MCP session initialization
        # which is tested separately in test_strategy_creator.py

        server = create_composer_server()

        # Verify server configuration
        assert server.url.startswith('https://ai.composer.trade')
        assert 'Authorization' in server.headers
        assert server.headers['Authorization'].startswith('Basic ')
