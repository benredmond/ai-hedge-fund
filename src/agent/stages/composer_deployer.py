"""Deploy winning strategy to Composer.trade as a symphony."""

import asyncio
import os
import traceback
from datetime import datetime, timezone

from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    get_model_settings,
)
from src.agent.models import Strategy, Charter


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
            The description is the AI-generated strategy summary from the symphony_score root node.
        """
        # Check credentials first - early exit if not configured
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
            # Enhanced error logging with classification
            error_type, error_msg = _classify_error(e)
            print(f"\n{'='*80}")
            print(f"[ERROR:ComposerDeployer] Deployment failed")
            print(f"[ERROR:ComposerDeployer] Type: {error_type}")
            print(f"[ERROR:ComposerDeployer] Message: {error_msg}")
            print(f"[ERROR:ComposerDeployer] Strategy: {strategy.name}")
            print(f"[ERROR:ComposerDeployer] Assets: {strategy.assets}")
            # Log traceback for debugging (first 10 lines)
            tb_lines = traceback.format_exc().split('\n')[:10]
            print(f"[ERROR:ComposerDeployer] Traceback (first 10 lines):")
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

                # Enhanced error logging for MCP failures
                error_type, error_msg = _classify_error(e)
                print(f"\n{'='*80}")
                print(f"[ERROR:ComposerDeployer] Attempt {attempt}/{max_attempts} failed")
                print(f"[ERROR:ComposerDeployer] Exception type: {type(e).__name__}")
                print(f"[ERROR:ComposerDeployer] Exception message: {e}")
                print(f"[ERROR:ComposerDeployer] Classified as: {error_type}")

                # Log any extra attributes from pydantic-ai exceptions
                for attr in ['code', 'data', 'message', 'response', 'body', '__cause__']:
                    if hasattr(e, attr):
                        attr_val = getattr(e, attr, None)
                        if attr_val is not None:
                            print(f"[ERROR:ComposerDeployer] Exception.{attr}: {attr_val}")

                # Log traceback
                tb_lines = traceback.format_exc().split('\n')
                print(f"[ERROR:ComposerDeployer] Full traceback:")
                for line in tb_lines:
                    if line.strip():
                        print(f"  {line}")
                print(f"{'='*80}\n")

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
                    print(f"⚠️  Retrying in {base_delay}s...")
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
    ) -> tuple[str | None, str | None, str | None]:
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

            # Check for MCP tool errors BEFORE extracting symphony_id
            mcp_error = self._check_mcp_error(result)
            if mcp_error:
                print(f"\n{'='*80}")
                print(f"[ERROR:ComposerDeployer] MCP tool returned error")
                print(f"[ERROR:ComposerDeployer] {mcp_error}")
                print(f"{'='*80}\n")
                return None, None, None

            # Parse symphony_id and description from tool call responses
            symphony_id, description = self._extract_symphony_data(result)

            if symphony_id:
                print(f"[DEBUG:ComposerDeployer] Successfully extracted symphony_id: {symphony_id}")
                if description:
                    print(f"[DEBUG:ComposerDeployer] Extracted description: {description[:100]}...")
                deployed_at = datetime.now(timezone.utc).isoformat()
                return symphony_id, deployed_at, description

            # No symphony_id found - log full response for debugging
            print(f"\n{'='*80}")
            print(f"[ERROR:ComposerDeployer] No symphony_id found in response")
            print(f"[DEBUG:ComposerDeployer] Logging full MCP response for debugging:")
            self._log_full_response(result)
            print(f"{'='*80}\n")
            return None, None, None

    def _check_mcp_error(self, result) -> str | None:
        """
        Check for MCP tool-level errors in the agent result.

        MCP has two error channels:
        - JSON-RPC errors (protocol level) - discarded by LLM, caught as exceptions
        - Tool errors (isError=true) - visible to LLM, need explicit check

        Returns:
            Error message if tool returned an error, None otherwise
        """
        if not hasattr(result, "all_messages"):
            return None

        for msg in result.all_messages():
            if not hasattr(msg, "parts"):
                continue
            for part in msg.parts:
                # Check ToolReturnPart for save_symphony or create_symphony
                tool_name = getattr(part, "tool_name", "")
                if "symphony" not in tool_name:
                    continue

                content = getattr(part, "content", None)

                # Check for isError flag (MCP tool-level error)
                if isinstance(content, dict):
                    if content.get("isError"):
                        error_content = content.get("content", [{}])
                        if isinstance(error_content, list) and error_content:
                            error_text = error_content[0].get("text", str(content))
                        else:
                            error_text = str(content)
                        return f"Tool '{tool_name}' error: {error_text}"

                # Check for error patterns in string content
                if isinstance(content, str):
                    content_lower = content.lower()
                    if any(err in content_lower for err in ["error", "failed", "invalid", "unauthorized"]):
                        return f"Tool '{tool_name}' returned: {content[:500]}"

        return None

    def _log_full_response(self, result) -> None:
        """Log full agent result for debugging when symphony_id extraction fails."""
        print(f"[DEBUG:ComposerDeployer] result.output = {result.output}")

        if hasattr(result, "all_messages"):
            messages = result.all_messages()
            print(f"[DEBUG:ComposerDeployer] Total messages: {len(messages)}")

            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                print(f"[DEBUG:ComposerDeployer] Message {i}: {msg_type}")

                if hasattr(msg, "parts"):
                    for j, part in enumerate(msg.parts):
                        part_type = type(part).__name__
                        tool_name = getattr(part, "tool_name", None)
                        content = getattr(part, "content", None)

                        if tool_name:
                            print(f"[DEBUG:ComposerDeployer]   Part {j}: {part_type} tool={tool_name}")
                            # Log content (truncate if very long)
                            content_str = str(content)
                            if len(content_str) > 1000:
                                print(f"[DEBUG:ComposerDeployer]     Content (truncated): {content_str[:1000]}...")
                            else:
                                print(f"[DEBUG:ComposerDeployer]     Content: {content_str}")

    def _build_system_prompt(self) -> str:
        """Minimal system prompt for symphony deployment."""
        return """You deploy trading strategies to Composer.trade.

CRITICAL RULES:
- weight: null on EVERY node (literal null, not numbers)
- NO id fields anywhere
- NO children on asset nodes
- allocation field required for wt-cash-specified children

Call composer_save_symphony with the symphony_score JSON."""

    def _build_deployment_prompt(
        self, strategy: Strategy, charter: Charter, market_context: dict
    ) -> str:
        """Build minimal deployment prompt with only execution fields."""
        import json

        # Load minimal prompt
        recipe = load_prompt("composer_deployment_minimal.md")

        # MINIMAL: Only execution fields needed for symphony_score construction
        strategy_input = {
            "name": strategy.name,
            "assets": strategy.assets,
            "weights": dict(strategy.weights),
            "rebalance_frequency": strategy.rebalance_frequency.value,
        }
        # Only include logic_tree if non-empty (conditional strategy)
        if strategy.logic_tree:
            strategy_input["logic_tree"] = strategy.logic_tree

        return f"""{recipe}

## STRATEGY TO DEPLOY

{json.dumps(strategy_input, indent=2)}"""

    def _extract_symphony_data(self, result) -> tuple[str | None, str | None]:
        """
        Extract symphony_id and description from agent result.

        Returns:
            Tuple of (symphony_id, description). Description is extracted from
            the symphony_score passed to save_symphony (the root node's description field).
        """
        import json
        import re

        symphony_id: str | None = None
        description: str | None = None

        # Patterns to find symphony_id (in priority order)
        symphony_patterns = [
            r'"symphony_id"\s*:\s*"([^"]+)"',
            r"'symphony_id'\s*:\s*'([^']+)'",
            r"symphony_id[=:]\s*([a-zA-Z0-9_-]+)",
        ]
        # Fallback: generic id pattern (10+ chars to avoid false positives)
        generic_pattern = r"id[=:]\s*([a-zA-Z0-9_-]{10,})"

        def search_id_in_text(text: str, include_generic: bool = False) -> str | None:
            for pattern in symphony_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
            if include_generic:
                match = re.search(generic_pattern, text)
                if match:
                    return match.group(1)
            return None

        def extract_description_from_args(args: dict) -> str | None:
            """Extract description from symphony_score in tool call args."""
            symphony_score = args.get("symphony_score", {})
            if isinstance(symphony_score, dict):
                return symphony_score.get("description")
            return None

        # First pass: extract from tool call/return parts in messages
        if hasattr(result, "all_messages"):
            for msg in result.all_messages():
                if not hasattr(msg, "parts"):
                    continue
                for part in msg.parts:
                    tool_name = getattr(part, "tool_name", "")

                    # Check ToolCallPart for description (in the request args)
                    if "save_symphony" in tool_name and hasattr(part, "args"):
                        args = getattr(part, "args", {})
                        if isinstance(args, dict):
                            desc = extract_description_from_args(args)
                            if desc and not description:
                                description = desc
                        elif isinstance(args, str):
                            try:
                                parsed_args = json.loads(args)
                                desc = extract_description_from_args(parsed_args)
                                if desc and not description:
                                    description = desc
                            except json.JSONDecodeError:
                                pass

                    # Check ToolReturnPart for symphony_id (in the response)
                    if "save_symphony" in tool_name and hasattr(part, "content"):
                        content = getattr(part, "content", None)
                        if isinstance(content, dict) and "symphony_id" in content:
                            symphony_id = content["symphony_id"]
                        elif isinstance(content, str):
                            found = search_id_in_text(content)
                            if found:
                                symphony_id = found

        # If we found symphony_id, return early
        if symphony_id:
            return symphony_id, description

        # Fallback: search in result.output
        if hasattr(result, "output") and result.output:
            found = search_id_in_text(str(result.output), include_generic=True)
            if found:
                return found, description

        # Fallback: search in result.data
        if hasattr(result, "data") and result.data:
            found = search_id_in_text(str(result.data), include_generic=True)
            if found:
                return found, description

        # Fallback: stringify all messages
        if hasattr(result, "all_messages"):
            all_text = str(result.all_messages())
            found = search_id_in_text(all_text, include_generic=True)
            if found:
                return found, description

        # Final fallback: stringify entire result
        found = search_id_in_text(str(result), include_generic=True)
        if found:
            return found, description

        return None, None
