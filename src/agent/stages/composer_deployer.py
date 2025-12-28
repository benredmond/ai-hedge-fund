"""Deploy winning strategy to Composer.trade as a symphony."""

import asyncio
import json
import logging
import os
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from src.agent.mcp_config import create_composer_server

# Enable debug logging for pydantic_ai when DEBUG_PROMPTS is set (skip noisy HTTP logs)
if os.getenv("DEBUG_PROMPTS", "0") == "1":
    logging.getLogger("pydantic_ai").setLevel(logging.DEBUG)
    # Suppress noisy HTTP logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    get_model_settings,
)
from src.agent.models import Strategy, Charter


class SymphonyConfirmation(BaseModel):
    """Simple confirmation model - model just confirms deployment."""

    ready_to_deploy: bool = Field(
        description="True if the strategy is ready to deploy"
    )
    symphony_name: str = Field(
        description="Name for the symphony (short, descriptive)"
    )
    symphony_description: str = Field(
        description="Brief description of the strategy (1-2 sentences)"
    )


def _classify_error(e: Exception) -> tuple[str, str]:
    """
    Classify an exception into an error type and actionable message.

    Returns:
        Tuple of (error_type, user_message)
    """
    error_str = str(e).lower()

    # Authentication errors
    if "401" in error_str or "unauthorized" in error_str:
        return "AUTH", (
            "Composer credentials invalid or expired. "
            "Check COMPOSER_API_KEY and COMPOSER_API_SECRET in .env"
        )
    if "403" in error_str or "forbidden" in error_str:
        return "AUTH", (
            "Composer access forbidden. Your API key may lack required permissions."
        )

    # Rate limiting
    if "429" in error_str or "rate" in error_str or "too many" in error_str:
        return "RATE_LIMIT", "Composer rate limit exceeded. Will retry with backoff."

    # Schema/validation errors
    if "schema" in error_str or "invalid" in error_str or "required" in error_str:
        return "SCHEMA", f"Symphony schema validation failed: {e}"

    # Network errors
    if "timeout" in error_str or "connection" in error_str or "network" in error_str:
        return "NETWORK", f"Network error connecting to Composer: {e}"

    # Unknown - include full details
    return "UNKNOWN", f"Unexpected error: {type(e).__name__}: {e}"


def _get_exchange(ticker: str) -> str:
    """Map ticker to exchange code."""
    etfs = {
        "SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "VTI", "VOO", "BND",
        "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY", "XLC",
        "BIL", "SHY", "IEF", "AGG", "LQD", "HYG", "EMB", "VNQ", "ARKK", "SMH",
    }
    if ticker in etfs:
        return "ARCX"
    nasdaq = {
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "NFLX",
        "ADBE", "CRM", "PYPL", "INTC", "AMD", "QCOM", "CSCO", "AVGO", "TXN", "COST", "PEP",
    }
    if ticker in nasdaq:
        return "XNAS"
    return "XNYS"


def _build_symphony_json(
    name: str,
    description: str,
    tickers: list[str],
    rebalance: str = "monthly",
) -> dict:
    """
    Build valid Composer symphony JSON structure for save_symphony.

    This is done in Python to avoid LLM hallucination issues with nested JSON.

    Returns dict with:
        - symphony_score: The symphony structure
        - color: Required hex color for the symphony
        - hashtag: Required hashtag identifier
        - asset_class: EQUITIES or CRYPTO
    """
    # Build asset nodes
    asset_nodes = []
    for ticker in tickers:
        asset_nodes.append({
            "id": str(uuid.uuid4()),
            "step": "asset",
            "ticker": ticker,
            "exchange": _get_exchange(ticker),
            "name": ticker,
            "weight": None,
        })

    # Build complete symphony
    symphony_score = {
        "id": str(uuid.uuid4()),
        "name": name,
        "step": "root",
        "weight": None,
        "rebalance": rebalance,
        "description": description,
        "rebalance-corridor-width": None,
        "children": [{
            "id": str(uuid.uuid4()),
            "step": "wt-cash-equal",
            "weight": None,
            "children": asset_nodes,
        }],
    }

    # Generate hashtag from name (remove spaces, add #)
    hashtag = "#" + "".join(name.split()[:2])

    return {
        "symphony_score": symphony_score,
        "color": "#17BAFF",  # Blue (from Composer's allowed palette)
        "hashtag": hashtag,
        "asset_class": "EQUITIES",
    }


async def _call_composer_api(symphony_json: dict) -> dict:
    """
    Call Composer MCP API to create symphony using pydantic_ai's session management.

    Uses MCPServerStreamableHTTP.direct_call_tool() which handles:
    - Session initialization (gets Mcp-Session-Id)
    - Proper MCP protocol handshake
    - Tool invocation with session context

    Returns:
        API response dict with symphony_id
    """
    debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

    if debug:
        print(f"\n[DEBUG:_call_composer_api] Symphony JSON:")
        print(json.dumps(symphony_json, indent=2, default=str))

    # Create Composer MCP server (handles auth via mcp_config)
    server = create_composer_server()

    async with server:
        if debug:
            # List available tools for debugging
            tools = await server.list_tools()
            tool_names = [t.name for t in tools]
            print(f"[DEBUG:_call_composer_api] Available tools: {tool_names}")

        # Call save_symphony tool directly (bypasses LLM, no hallucination)
        # Note: save_symphony actually saves and returns symphony_id
        # create_symphony only validates/previews without saving
        result = await server.direct_call_tool("save_symphony", symphony_json)

        if debug:
            print(f"[DEBUG:_call_composer_api] Result: {result}")

        # direct_call_tool returns the parsed tool result directly
        # For save_symphony, this is a dict with symphony_id and version_id
        if isinstance(result, dict):
            return result

        # Fallback: try to parse as JSON if it's a string
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw_response": result}

        return {"result": str(result)}


class ComposerDeployer:
    """
    Stage 5: Deploy strategy to Composer.trade.

    Design:
    - LLM confirms deployment and provides name/description
    - Python builds the symphony JSON (no LLM hallucination)
    - Direct API call to Composer (no MCP tool schema issues)
    """

    async def deploy(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str = DEFAULT_MODEL,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Deploy strategy to Composer.trade.

        Args:
            strategy: Winning strategy to deploy
            charter: Generated charter document
            market_context: Market context pack (for regime info)
            model: LLM model identifier

        Returns:
            Tuple of (symphony_id, deployed_at, description) or (None, None, None) if deployment skipped/failed.
        """
        # Check credentials first
        api_key = os.getenv("COMPOSER_API_KEY")
        api_secret = os.getenv("COMPOSER_API_SECRET")

        if not api_key or not api_secret:
            print("⚠️  Composer deployment skipped: COMPOSER_API_KEY/SECRET not set")
            return None, None, None

        try:
            return await self._run_with_retries(
                strategy=strategy,
                charter=charter,
                market_context=market_context,
                model=model,
            )
        except Exception as e:
            error_type, error_msg = _classify_error(e)
            print(f"\n{'='*80}")
            print(f"[ERROR:ComposerDeployer] Deployment failed")
            print(f"[ERROR:ComposerDeployer] Type: {error_type}")
            print(f"[ERROR:ComposerDeployer] Message: {error_msg}")
            print(f"[ERROR:ComposerDeployer] Strategy: {strategy.name}")
            print(f"[ERROR:ComposerDeployer] Assets: {strategy.assets}")
            tb_lines = traceback.format_exc().split('\n')[:10]
            print(f"[ERROR:ComposerDeployer] Traceback:")
            for line in tb_lines:
                if line.strip():
                    print(f"  {line}")
            print(f"{'='*80}\n")
            return None, None, None

    async def _run_with_retries(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str,
        max_attempts: int = 3,
        base_delay: float = 5.0,
    ) -> tuple[str | None, str | None, str | None]:
        """Run deployment with exponential backoff retry."""
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                return await self._deploy_once(
                    strategy=strategy,
                    charter=charter,
                    market_context=market_context,
                    model=model,
                )
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                error_type, error_msg = _classify_error(e)
                print(f"\n{'='*80}")
                print(f"[ERROR:ComposerDeployer] Attempt {attempt}/{max_attempts} failed")
                print(f"[ERROR:ComposerDeployer] Exception: {type(e).__name__}: {e}")
                print(f"[ERROR:ComposerDeployer] Classified as: {error_type}")
                print(f"{'='*80}\n")

                is_rate_limit = "rate" in error_str or "429" in error_str

                if attempt < max_attempts:
                    wait_time = base_delay * (2 ** (attempt - 1)) if is_rate_limit else base_delay
                    print(f"⚠️  Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    continue

                raise

        if last_error:
            raise last_error

        raise RuntimeError("Deployment failed without raising an error")

    async def _deploy_once(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str,
    ) -> tuple[str | None, str | None, str | None]:
        """Single deployment attempt."""
        debug = os.getenv("DEBUG_PROMPTS", "0") == "1"

        # Step 1: Get LLM confirmation and description (no tool calling)
        confirmation = await self._get_llm_confirmation(
            strategy=strategy,
            charter=charter,
            model=model,
        )

        if not confirmation.ready_to_deploy:
            print("⚠️  LLM declined to deploy strategy")
            return None, None, None

        # Step 2: Build symphony JSON in Python (no LLM hallucination)
        symphony_json = _build_symphony_json(
            name=confirmation.symphony_name,
            description=confirmation.symphony_description,
            tickers=strategy.assets,
            rebalance=strategy.rebalance_frequency.value,
        )

        if debug:
            print(f"\n[DEBUG:ComposerDeployer] Built symphony JSON:")
            print(json.dumps(symphony_json, indent=2, default=str))

        # Step 3: Call Composer API directly
        print(f"📤 Deploying symphony: {confirmation.symphony_name}")
        response = await _call_composer_api(symphony_json)

        # Step 4: Extract symphony_id from response
        symphony_id = self._extract_symphony_id(response)

        if symphony_id:
            deployed_at = datetime.now(timezone.utc).isoformat()
            print(f"✅ Symphony deployed: {symphony_id}")
            return symphony_id, deployed_at, confirmation.symphony_description
        else:
            print(f"❌ Failed to extract symphony_id from response")
            if debug:
                print(f"[DEBUG] Response: {response}")
            return None, None, None

    async def _get_llm_confirmation(
        self,
        strategy: Strategy,
        charter: Charter,
        model: str,
    ) -> SymphonyConfirmation:
        """Get LLM confirmation for deployment (no tool calling)."""
        system_prompt = """You are confirming a trading strategy deployment to Composer.trade.

Review the strategy and provide:
1. Confirmation that it's ready to deploy
2. A short name for the symphony (e.g., "Defensive Sectors Q1 2025")
3. A brief description (1-2 sentences summarizing the strategy)"""

        user_prompt = f"""Strategy to deploy:

Name: {strategy.name}
Assets: {', '.join(strategy.assets)}
Rebalance: {strategy.rebalance_frequency.value}

Market Thesis: {charter.market_thesis[:500] if charter.market_thesis else 'N/A'}

Confirm deployment and provide symphony name and description."""

        model_settings = get_model_settings(model, stage="composer_deployment")

        # Create agent WITHOUT Composer tools - just structured output
        agent_ctx = await create_agent(
            model=model,
            output_type=SymphonyConfirmation,
            system_prompt=system_prompt,
            include_fred=False,
            include_yfinance=False,
            include_composer=False,  # No tools!
            history_limit=5,
            model_settings=model_settings,
        )

        async with agent_ctx as agent:
            result = await agent.run(user_prompt)
            return result.output

    def _extract_symphony_id(self, response: dict) -> Optional[str]:
        """Extract symphony_id from MCP response."""
        # MCP response format: {"jsonrpc": "2.0", "id": "...", "result": {...}}
        result = response.get("result", {})

        # Handle different response structures
        if isinstance(result, dict):
            # Direct symphony_id in result
            if "symphony_id" in result:
                return result["symphony_id"]

            # Nested in content array (MCP tool response format)
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        if isinstance(text, str) and "symphony_id" in text:
                            # Try to parse as JSON
                            try:
                                parsed = json.loads(text)
                                if "symphony_id" in parsed:
                                    return parsed["symphony_id"]
                            except json.JSONDecodeError:
                                pass

        # Fallback: search for symphony_id pattern in full response
        import re
        response_str = json.dumps(response)
        match = re.search(r'"symphony_id"\s*:\s*"([^"]+)"', response_str)
        if match:
            return match.group(1)

        return None
