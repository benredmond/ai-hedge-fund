import pytest
import httpx


@pytest.mark.asyncio
async def test_composer_endpoint_reachable():
    """Composer HTTP endpoint is reachable (health check)."""
    url = "https://mcp.composer.trade/mcp/"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(url, follow_redirects=True)
            # 401 or 403 is OK (means endpoint exists, auth required)
            # 200-299 is OK (endpoint accessible)
            assert response.status_code < 500, f"Composer returned 5xx: {response.status_code}"
            print(f"✅ Composer endpoint reachable (HTTP {response.status_code})")
    except httpx.ConnectError as e:
        pytest.skip(f"Composer endpoint unreachable (network issue): {e}")
    except httpx.TimeoutException:
        pytest.skip("Composer endpoint timeout (>5s)")
