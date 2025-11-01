"""
Integration test for Kimi K2 model.

This test actually calls the Kimi API to verify the integration works end-to-end.
"""
import pytest
import os
from pydantic import BaseModel
from src.agent.strategy_creator import create_agent


class SimpleResponse(BaseModel):
    """Simple response model for testing"""
    message: str


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KIMI_API_KEY"),
    reason="KIMI_API_KEY not set - cannot run integration test"
)
@pytest.mark.asyncio
async def test_kimi_k2_real_api_call():
    """
    Integration test: Verify Kimi K2 model can actually make API calls.

    This test hits the real Moonshot API to ensure:
    1. Model name is recognized by the API
    2. Authentication works
    3. Response is properly parsed
    """
    agent_ctx = await create_agent(
        model="openai:kimi-k2-0905-preview",
        output_type=SimpleResponse,
        system_prompt="You are a helpful assistant. Respond concisely.",
        include_composer=False,
        history_limit=5
    )

    async with agent_ctx as agent:
        # Make a real API call
        result = await agent.run("Say hello in exactly 3 words.")

        # Verify we got a response
        assert result.output is not None
        assert isinstance(result.output, SimpleResponse)
        assert len(result.output.message) > 0

        print(f"\n✅ Kimi K2 integration test passed!")
        print(f"   Model response: {result.output.message}")
