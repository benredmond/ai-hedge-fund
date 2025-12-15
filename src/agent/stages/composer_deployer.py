"""Deploy winning strategy to Composer.trade as a symphony."""

import asyncio
import os
from datetime import datetime, timezone

from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    get_model_settings,
)
from src.agent.models import Strategy, Charter


class ComposerDeployer:
    """
    Stage 5: Deploy strategy to Composer.trade.

    Creates a symphony on Composer using the save_symphony MCP tool.
    Uses LLM to interpret Strategy/Charter and construct valid symphony JSON.

    Design decisions:
    - Graceful degradation: Returns (None, None) if Composer unavailable
    - Credentials check first: Early exit if COMPOSER_API_KEY/SECRET not set
    - LLM interprets schema: save_symphony schema undocumented, let LLM figure it out
    - Retry with backoff: Handle rate limits (5s, 10s, 20s delays)
    """

    async def deploy(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str = DEFAULT_MODEL,
    ) -> tuple[str | None, str | None]:
        """
        Deploy strategy to Composer.trade.

        Args:
            strategy: Winning strategy to deploy
            charter: Generated charter document
            market_context: Market context pack (for regime info)
            model: LLM model identifier

        Returns:
            Tuple of (symphony_id, deployed_at) or (None, None) if deployment skipped/failed
        """
        # Check credentials first - early exit if not configured
        api_key = os.getenv("COMPOSER_API_KEY")
        api_secret = os.getenv("COMPOSER_API_SECRET")

        if not api_key or not api_secret:
            print("⚠️  Composer deployment skipped: COMPOSER_API_KEY/SECRET not set")
            return None, None

        try:
            return await self._run_with_retries(
                strategy=strategy,
                charter=charter,
                market_context=market_context,
                model=model,
            )
        except Exception as e:
            print(f"⚠️  Composer deployment failed: {e}")
            return None, None

    async def _run_with_retries(
        self,
        strategy: Strategy,
        charter: Charter,
        market_context: dict,
        model: str,
        max_attempts: int = 3,
        base_delay: float = 5.0,
    ) -> tuple[str | None, str | None]:
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

                # Check for rate limit errors
                is_rate_limit = (
                    "rate" in error_str
                    or "429" in error_str
                    or "too many" in error_str
                )

                if is_rate_limit and attempt < max_attempts:
                    wait_time = base_delay * (2 ** (attempt - 1))
                    print(
                        f"⚠️  Composer rate limit (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Non-rate-limit error or final attempt
                if attempt < max_attempts:
                    print(
                        f"⚠️  Composer deployment error (attempt {attempt}/{max_attempts}): {e}"
                    )
                    await asyncio.sleep(base_delay)
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
    ) -> tuple[str | None, str | None]:
        """Single deployment attempt."""
        prompt = self._build_deployment_prompt(strategy, charter, market_context)
        system_prompt = self._build_system_prompt()

        model_settings = get_model_settings(model, stage="composer_deployment")

        # Create agent without structured output - we'll parse tool responses
        agent_ctx = await create_agent(
            model=model,
            output_type=None,  # No structured output - parse tool call responses
            system_prompt=system_prompt,
            include_composer=True,
            history_limit=10,
            model_settings=model_settings,
        )

        async with agent_ctx as agent:
            result = await agent.run(prompt)

            # Parse symphony_id from tool call responses
            symphony_id = self._extract_symphony_id(result)

            if symphony_id:
                deployed_at = datetime.now(timezone.utc).isoformat()
                return symphony_id, deployed_at

            # No symphony_id found - deployment may have failed silently
            print("⚠️  Composer deployment completed but no symphony_id found in response")
            return None, None

    def _build_system_prompt(self) -> str:
        """Build system prompt with auto-injected Composer tool docs."""
        return load_prompt("system/composer_deployment_system.md")

    def _build_deployment_prompt(
        self, strategy: Strategy, charter: Charter, market_context: dict
    ) -> str:
        """Build deployment prompt with full strategy context."""
        import json

        # Load recipe prompt
        recipe = load_prompt("composer_deployment.md")

        # Include FULL thesis document and strategy context
        strategy_json = {
            "name": strategy.name,
            "thesis_document": strategy.thesis_document,  # Full thesis, not truncated
            "rebalancing_rationale": strategy.rebalancing_rationale,
            "assets": strategy.assets,
            "weights": dict(strategy.weights),
            "rebalance_frequency": strategy.rebalance_frequency.value,
            "logic_tree": strategy.logic_tree,
            "edge_type": getattr(strategy.edge_type, "value", str(strategy.edge_type)),
            "archetype": getattr(strategy.archetype, "value", str(strategy.archetype)),
        }

        # Include charter context for additional guidance
        charter_context = {
            "market_thesis": charter.market_thesis[:500],
            "expected_behavior": charter.expected_behavior[:500],
        }

        return f"""{recipe}

## STRATEGY TO DEPLOY

{json.dumps(strategy_json, indent=2)}

## CHARTER CONTEXT

{json.dumps(charter_context, indent=2)}"""

    def _extract_symphony_id(self, result) -> str | None:
        """Extract symphony_id from agent result."""
        import re

        # Patterns to find symphony_id (in priority order)
        symphony_patterns = [
            r'"symphony_id"\s*:\s*"([^"]+)"',
            r"'symphony_id'\s*:\s*'([^']+)'",
            r"symphony_id[=:]\s*([a-zA-Z0-9_-]+)",
        ]
        # Fallback: generic id pattern (10+ chars to avoid false positives)
        generic_pattern = r"id[=:]\s*([a-zA-Z0-9_-]{10,})"

        def search_in_text(text: str, include_generic: bool = False) -> str | None:
            for pattern in symphony_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
            if include_generic:
                match = re.search(generic_pattern, text)
                if match:
                    return match.group(1)
            return None

        # First check: tool return content in messages (most reliable)
        if hasattr(result, "all_messages"):
            for msg in result.all_messages():
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        # Check ToolReturnPart from composer_save_symphony
                        if hasattr(part, "tool_name") and "save_symphony" in part.tool_name:
                            content = getattr(part, "content", None)
                            if isinstance(content, dict) and "symphony_id" in content:
                                return content["symphony_id"]
                            if isinstance(content, str):
                                found = search_in_text(content)
                                if found:
                                    return found

        # Second check: result.output
        if hasattr(result, "output") and result.output:
            found = search_in_text(str(result.output), include_generic=True)
            if found:
                return found

        # Third check: result.data attribute
        if hasattr(result, "data") and result.data:
            found = search_in_text(str(result.data), include_generic=True)
            if found:
                return found

        # Fourth check: stringify all messages
        if hasattr(result, "all_messages"):
            all_text = str(result.all_messages())
            found = search_in_text(all_text, include_generic=True)
            if found:
                return found

        # Final fallback: stringify the entire result
        found = search_in_text(str(result), include_generic=True)
        if found:
            return found

        return None
