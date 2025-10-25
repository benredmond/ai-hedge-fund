"""Generate 5 candidate strategies using AI."""

from typing import List
import json
from src.agent.strategy_creator import create_agent, load_prompt, DEFAULT_MODEL
from src.agent.models import Strategy


class CandidateGenerator:
    """
    Stage 1: Generate 5 candidate trading strategies.

    Analyzes market context and generates diverse candidates
    with different edges, archetypes, and regime assumptions.
    """

    async def generate(
        self,
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> List[Strategy]:
        """
        Generate 5 distinct candidate strategies.

        Args:
            market_context: Market context pack (date-anchored)
            model: LLM model identifier

        Returns:
            List of exactly 5 Strategy objects

        Raises:
            ValueError: If != 5 candidates or duplicates detected
        """
        # Load candidate generation prompt
        system_prompt = load_prompt("candidate_generation.md")

        # Create agent context
        agent_ctx = await create_agent(
            model=model,
            output_type=List[Strategy],
            system_prompt=system_prompt
        )

        # Generate candidates
        async with agent_ctx as agent:
            market_context_json = json.dumps(market_context, indent=2)

            prompt = f"""Generate 5 candidate trading strategies based on this market context:

{market_context_json}

Follow the workflow: analyze → generate 5 distinct candidates → return list.

Remember: EXACTLY 5 strategies, all different from each other.
"""

            result = await agent.run(prompt)
            candidates = result.output

        # Validate count
        if len(candidates) != 5:
            raise ValueError(f"Expected 5 candidates, got {len(candidates)}")

        # Check for duplicates (simple ticker comparison)
        ticker_sets = [set(c.assets) for c in candidates]
        unique_ticker_sets = set(tuple(sorted(ts)) for ts in ticker_sets)
        if len(ticker_sets) != len(unique_ticker_sets):
            raise ValueError("Duplicate candidates detected (same ticker sets)")

        return candidates
