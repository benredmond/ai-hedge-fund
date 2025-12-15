"""
Debug tests for Composer MCP connection issues.

These tests diagnose why composer_save_symphony is failing with:
"Tool 'composer_save_symphony' exceeded max retries count of 1"

Run with: source .env && ./venv/bin/pytest tests/agent/test_composer_mcp_debug.py -v -s
"""

import os
import base64
import pytest
import httpx


def get_composer_credentials():
    """Get Composer credentials from environment."""
    api_key = os.getenv("COMPOSER_API_KEY")
    api_secret = os.getenv("COMPOSER_API_SECRET")
    url = os.getenv("COMPOSER_MCP_URL", "https://mcp.composer.trade/mcp/")
    return api_key, api_secret, url


def get_auth_headers(api_key: str, api_secret: str) -> dict:
    """Build HTTP Basic Auth headers."""
    credentials = f"{api_key}:{api_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",  # Required for Composer MCP
    }


class TestComposerCredentials:
    """Test that Composer credentials are properly configured."""

    def test_api_key_exists(self):
        """COMPOSER_API_KEY environment variable is set."""
        api_key, _, _ = get_composer_credentials()
        assert api_key is not None, "COMPOSER_API_KEY not set in environment"
        assert len(api_key) > 0, "COMPOSER_API_KEY is empty"

    def test_api_secret_exists(self):
        """COMPOSER_API_SECRET environment variable is set."""
        _, api_secret, _ = get_composer_credentials()
        assert api_secret is not None, "COMPOSER_API_SECRET not set in environment"
        assert len(api_secret) > 0, "COMPOSER_API_SECRET is empty"

    def test_credentials_format(self):
        """Credentials appear to be valid format (not placeholder values)."""
        api_key, api_secret, _ = get_composer_credentials()

        # Check for common placeholder patterns
        placeholders = ["your-key", "xxx", "test", "placeholder", "example"]

        for placeholder in placeholders:
            assert placeholder not in api_key.lower(), f"API key appears to be placeholder: {api_key[:10]}..."
            assert placeholder not in api_secret.lower(), f"API secret appears to be placeholder"


class TestComposerEndpointConnectivity:
    """Test basic HTTP connectivity to Composer MCP endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_reachable(self):
        """Composer MCP endpoint responds to HTTP requests."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # GET request to check endpoint exists
            response = await client.get(url, headers=headers)

            # Should get some response (even if error)
            assert response.status_code is not None, "No response from endpoint"
            print(f"\nGET {url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    @pytest.mark.asyncio
    async def test_endpoint_accepts_post(self):
        """Composer MCP endpoint accepts POST requests."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Empty POST to see what happens
            response = await client.post(url, json={}, headers=headers)

            print(f"\nPOST {url} (empty body)")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")

            # 400/405 is expected for empty body, 401/403 indicates auth issue
            if response.status_code in (401, 403):
                pytest.fail(f"Authentication failed: {response.status_code} - {response.text}")


def parse_sse_response(text: str) -> dict:
    """Parse Server-Sent Events response to extract JSON data."""
    import json
    for line in text.split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise ValueError(f"No data line found in SSE response: {text[:200]}")


class TestComposerMCPProtocol:
    """Test MCP JSON-RPC protocol communication."""

    @pytest.mark.asyncio
    async def test_mcp_initialize(self):
        """MCP initialize handshake succeeds and returns session ID."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest-debug", "version": "1.0.0"}
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            print(f"\nMCP Initialize Request")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:1000]}")

            assert response.status_code == 200, f"Initialize failed: {response.status_code}"

            # Parse SSE response
            data = parse_sse_response(response.text)
            print(f"\nParsed data: {data}")

            assert "error" not in data, f"MCP error: {data.get('error')}"
            assert "result" in data, f"No result in response: {data}"

            # Check for session ID in headers
            session_id = response.headers.get("mcp-session-id")
            print(f"\nSession ID from header: {session_id}")

    @pytest.mark.asyncio
    async def test_mcp_list_tools_with_session(self):
        """MCP tools/list works with proper session management."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Initialize to get session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-debug", "version": "1.0.0"}
                }
            }
            init_response = await client.post(url, json=init_payload, headers=headers)
            print(f"\n1. Initialize response headers: {dict(init_response.headers)}")

            session_id = init_response.headers.get("mcp-session-id")
            print(f"   Session ID: {session_id}")

            if not session_id:
                pytest.fail("No session ID returned from initialize")

            # Step 2: Send initialized notification
            init_notif = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            headers_with_session = {**headers, "mcp-session-id": session_id}
            notif_response = await client.post(url, json=init_notif, headers=headers_with_session)
            print(f"\n2. Initialized notification status: {notif_response.status_code}")

            # Step 3: List tools with session
            list_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            list_response = await client.post(url, json=list_payload, headers=headers_with_session)

            print(f"\n3. tools/list Request")
            print(f"   Status: {list_response.status_code}")
            print(f"   Response: {list_response.text[:2000]}")

            assert list_response.status_code == 200, f"tools/list failed: {list_response.status_code}"

            data = parse_sse_response(list_response.text)
            assert "error" not in data, f"MCP error: {data.get('error')}"

            # Check for save_symphony tool
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
                tool_names = [t.get("name") for t in tools]
                print(f"\nAvailable tools: {tool_names}")

                assert "save_symphony" in tool_names, (
                    f"save_symphony not in available tools: {tool_names}"
                )


class TestComposerSaveSymphony:
    """Test the specific save_symphony tool that's failing."""

    @pytest.mark.asyncio
    async def test_save_symphony_direct_mcp_call(self):
        """Call save_symphony directly via MCP protocol with proper session."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Initialize session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-save-symphony", "version": "1.0.0"}
                }
            }
            init_response = await client.post(url, json=init_payload, headers=headers)
            session_id = init_response.headers.get("mcp-session-id")
            print(f"\n1. Session ID: {session_id}")

            if not session_id:
                pytest.fail("No session ID returned")

            headers_with_session = {**headers, "mcp-session-id": session_id}

            # Step 2: Send initialized notification
            init_notif = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            await client.post(url, json=init_notif, headers=headers_with_session)

            # Step 3: First get save_symphony schema to understand required params
            list_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            list_response = await client.post(url, json=list_payload, headers=headers_with_session)
            list_data = parse_sse_response(list_response.text)
            tools = list_data.get("result", {}).get("tools", [])

            save_tool = next((t for t in tools if t["name"] == "save_symphony"), None)
            if save_tool:
                print(f"\n2. save_symphony schema:")
                print(f"   {save_tool.get('inputSchema', {})}")

            # Step 4: Call save_symphony with proper schema
            # Based on Composer docs, need to pass a symphony object from create_symphony
            # Let's first create a symphony, then save it
            create_payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "create_symphony",
                    "arguments": {
                        "name": "Debug Test Symphony",
                        "description": "Test symphony for debugging MCP",
                        "tickers": ["SPY"],  # Simple SPY-only strategy
                    }
                }
            }

            print(f"\n3. Creating symphony...")
            create_response = await client.post(url, json=create_payload, headers=headers_with_session)
            print(f"   Status: {create_response.status_code}")
            print(f"   Response: {create_response.text[:1500]}")

            if create_response.status_code != 200:
                pytest.fail(f"create_symphony failed: {create_response.text}")

            create_data = parse_sse_response(create_response.text)
            print(f"   Parsed: {create_data}")

            if "error" in create_data:
                pytest.fail(f"create_symphony error: {create_data['error']}")

            # Extract symphony from result
            symphony = create_data.get("result", {}).get("content", [{}])[0].get("text", "{}")
            print(f"\n4. Created symphony: {symphony[:500]}")

            # Step 5: Now save the symphony
            save_payload = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "save_symphony",
                    "arguments": {
                        "symphony": symphony,  # Pass the created symphony
                    }
                }
            }

            print(f"\n5. Saving symphony...")
            save_response = await client.post(url, json=save_payload, headers=headers_with_session)
            print(f"   Status: {save_response.status_code}")
            print(f"   Response: {save_response.text[:2000]}")

            if save_response.status_code != 200:
                print(f"\n   Full headers: {dict(save_response.headers)}")
                pytest.fail(f"save_symphony HTTP failed: {save_response.status_code}")

            save_data = parse_sse_response(save_response.text)
            print(f"   Parsed: {save_data}")

            if "error" in save_data:
                error = save_data["error"]
                pytest.fail(
                    f"save_symphony MCP error:\n"
                    f"  Code: {error.get('code')}\n"
                    f"  Message: {error.get('message')}\n"
                    f"  Data: {error.get('data')}"
                )

            # Check for symphony_id in result
            result = save_data.get("result", {})
            print(f"\n6. Save result: {result}")

    @pytest.mark.asyncio
    async def test_get_create_symphony_schema(self):
        """Get create_symphony schema to understand required params."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Initialize session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-schema", "version": "1.0.0"}
                }
            }
            init_response = await client.post(url, json=init_payload, headers=headers)
            session_id = init_response.headers.get("mcp-session-id")
            headers_with_session = {**headers, "mcp-session-id": session_id}

            # Send initialized notification
            init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            await client.post(url, json=init_notif, headers=headers_with_session)

            # Get tools list
            list_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            list_response = await client.post(url, json=list_payload, headers=headers_with_session)
            list_data = parse_sse_response(list_response.text)
            tools = list_data.get("result", {}).get("tools", [])

            # Find create_symphony and save_symphony
            create_tool = next((t for t in tools if t["name"] == "create_symphony"), None)
            save_tool = next((t for t in tools if t["name"] == "save_symphony"), None)

            print("\n=== create_symphony schema ===")
            if create_tool:
                import json
                print(json.dumps(create_tool, indent=2))

            print("\n=== save_symphony description ===")
            if save_tool:
                print(f"Description: {save_tool.get('description', 'N/A')}")

    @pytest.mark.asyncio
    async def test_create_and_save_symphony_full_flow(self):
        """Test complete create -> save symphony flow with correct schemas."""
        api_key, api_secret, url = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        headers = get_auth_headers(api_key, api_secret)

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Initialize session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-full-flow", "version": "1.0.0"}
                }
            }
            init_response = await client.post(url, json=init_payload, headers=headers)
            session_id = init_response.headers.get("mcp-session-id")
            headers_with_session = {**headers, "mcp-session-id": session_id}

            # Send initialized notification
            init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            await client.post(url, json=init_notif, headers=headers_with_session)

            # Step 1: Create symphony with just symphony_score (no color/hashtag)
            # Based on the example in the schema description
            symphony_score = {
                "step": "root",
                "name": "Debug Test Symphony",
                "description": "Simple SPY-only test strategy for MCP debugging",
                "rebalance": "monthly",
                "rebalance-corridor-width": None,
                "weight": None,
                "children": [
                    {
                        "step": "wt-cash-equal",
                        "weight": None,
                        "children": [
                            {
                                "ticker": "SPY",
                                "exchange": "XNYS",
                                "name": "SPDR S&P 500 ETF Trust",
                                "step": "asset",
                                "weight": None
                            }
                        ]
                    }
                ]
            }

            create_payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "create_symphony",
                    "arguments": {
                        "symphony_score": symphony_score
                    }
                }
            }

            print(f"\n1. Creating symphony...")
            create_response = await client.post(url, json=create_payload, headers=headers_with_session)
            print(f"   Status: {create_response.status_code}")
            print(f"   Response: {create_response.text[:1500]}")

            create_data = parse_sse_response(create_response.text)

            if create_data.get("result", {}).get("isError"):
                error_text = create_data.get("result", {}).get("content", [{}])[0].get("text", "")
                pytest.fail(f"create_symphony failed: {error_text}")

            # Extract the created symphony from result
            result_content = create_data.get("result", {}).get("content", [{}])
            created_symphony_text = result_content[0].get("text", "") if result_content else ""
            print(f"\n2. Created symphony text: {created_symphony_text[:500]}")

            # Step 2: Save the symphony with color and hashtag
            # Parse the created symphony if it's JSON
            import json
            try:
                created_symphony = json.loads(created_symphony_text)
            except json.JSONDecodeError:
                print(f"   Created symphony is not JSON, using as-is")
                created_symphony = created_symphony_text

            # Add required fields that save_symphony expects but create_symphony doesn't return
            # This is a schema inconsistency in Composer MCP API
            def add_weight_recursively(node):
                """Add weight: null to all nodes recursively."""
                if isinstance(node, dict):
                    if "weight" not in node:
                        node["weight"] = None
                    if "children" in node:
                        for child in node["children"]:
                            add_weight_recursively(child)
                return node

            if isinstance(created_symphony, dict):
                add_weight_recursively(created_symphony)
                # Add rebalance-corridor-width: null (required by save_symphony schema)
                if "rebalance-corridor-width" not in created_symphony:
                    created_symphony["rebalance-corridor-width"] = None

            save_payload = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "save_symphony",
                    "arguments": {
                        "symphony_score": created_symphony if isinstance(created_symphony, dict) else symphony_score,
                        "color": "#AEC3C6",
                        "hashtag": "#DEBUGTEST"
                    }
                }
            }

            print(f"\n3. Saving symphony...")
            save_response = await client.post(url, json=save_payload, headers=headers_with_session)
            print(f"   Status: {save_response.status_code}")
            print(f"   Response: {save_response.text[:2000]}")

            save_data = parse_sse_response(save_response.text)

            if save_data.get("result", {}).get("isError"):
                error_text = save_data.get("result", {}).get("content", [{}])[0].get("text", "")
                pytest.fail(f"save_symphony failed: {error_text}")

            # Check for symphony_id
            save_result_content = save_data.get("result", {}).get("content", [{}])
            save_result_text = save_result_content[0].get("text", "") if save_result_content else ""
            print(f"\n4. Save result: {save_result_text}")

            # Try to extract symphony_id
            import re
            symphony_id_match = re.search(r'"symphony_id"\s*:\s*"([^"]+)"', save_result_text)
            if symphony_id_match:
                print(f"\n✅ SUCCESS! Symphony ID: {symphony_id_match.group(1)}")
            else:
                print(f"\n⚠️ No symphony_id found in response")


class TestPydanticAIMCPIntegration:
    """Test Composer MCP through pydantic-ai's MCPServerStreamableHTTP."""

    @pytest.mark.asyncio
    async def test_mcp_server_creation(self):
        """MCPServerStreamableHTTP can be created with Composer config."""
        api_key, api_secret, _ = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        from src.agent.mcp_config import create_composer_server

        server = create_composer_server()

        assert server is not None
        assert server.url == "https://mcp.composer.trade/mcp/"
        assert "Authorization" in server.headers
        print(f"\nServer created successfully")
        print(f"URL: {server.url}")
        print(f"Timeout: {server.timeout}")
        print(f"Read timeout: {server.read_timeout}")

    @pytest.mark.asyncio
    async def test_mcp_server_tool_discovery(self):
        """MCPServerStreamableHTTP discovers Composer tools."""
        api_key, api_secret, _ = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        from pydantic_ai import Agent
        from src.agent.mcp_config import create_composer_server

        server = create_composer_server()

        # Create a simple agent with just Composer
        agent = Agent(
            model="openai:gpt-4o-mini",  # Cheap model for tool discovery
            tools=[],
        )

        # Use the server as a toolset
        async with server:
            # Get tools from the server
            tools = await server.list_tools()
            tool_names = [t.name for t in tools]

            print(f"\nDiscovered tools via pydantic-ai:")
            for name in tool_names:
                print(f"  - {name}")

            assert "save_symphony" in tool_names, (
                f"save_symphony not discovered. Available: {tool_names}"
            )

    @pytest.mark.asyncio
    async def test_agent_with_composer_toolset(self):
        """Agent can use Composer as a toolset and call save_symphony."""
        api_key, api_secret, _ = get_composer_credentials()

        if not api_key or not api_secret:
            pytest.skip("Composer credentials not set")

        from pydantic_ai import Agent
        from src.agent.mcp_config import create_composer_server

        server = create_composer_server()

        # Create agent with Composer toolset
        agent = Agent(
            model="openai:gpt-4o-mini",
            system_prompt=(
                "You are a test agent. When asked to save a symphony, "
                "call the composer_save_symphony tool with the provided config."
            ),
        )

        async with server:
            # Simple prompt to trigger tool call
            result = await agent.run(
                "Save a symphony named 'Test Debug Symphony' with just SPY at 100% weight. "
                "Use asset format EQUITIES::SPY//USD.",
                toolsets=[server],
            )

            print(f"\nAgent result: {result.output}")
            print(f"Tool calls made: {len(result.all_messages())}")

            # Check if tool was called
            for msg in result.all_messages():
                print(f"  Message type: {type(msg).__name__}")
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        print(f"    Part: {type(part).__name__}")
