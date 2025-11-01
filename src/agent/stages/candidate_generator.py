"""Generate 5 candidate strategies using AI."""

from typing import List
import json
import os
from src.agent.strategy_creator import create_agent, load_prompt, DEFAULT_MODEL
from src.agent.models import Strategy
from src.agent.token_tracker import TokenTracker


class CandidateGenerator:
    """
    Stage 1: Generate 5 candidate trading strategies.

    Uses comprehensive market context pack (macro/market regime, sector leadership,
    manual Composer examples) with optional tool usage during generation.

    Tools available but not required:
    - composer_search_symphonies: Additional pattern inspiration
    - stock_get_historical_stock_prices: Specific asset data
    - fred_get_series: Macro data verification
    """

    async def generate(
        self,
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> List[Strategy]:
        """
        Generate 5 distinct candidate strategies.

        Args:
            market_context: Comprehensive market context pack with:
                - Macro indicators (FRED data)
                - Market regime (trend, volatility, breadth, leadership)
                - Sector performance and factor premiums
                - Manual Composer pattern examples (curated)
                - Recent market events
            model: LLM model identifier

        Returns:
            List of exactly 5 Strategy objects

        Raises:
            ValueError: If != 5 candidates or duplicates detected
        """
        # Initialize token tracker
        enable_tracking = os.getenv("TRACK_TOKENS", "true").lower() == "true"
        tracker = TokenTracker(model=model, enabled=enable_tracking)

        # Load prompts
        system_prompt = load_prompt("system/candidate_generation_system.md")
        recipe_prompt = load_prompt("candidate_generation.md")

        # Generate candidates (single phase)
        print("Generating candidate strategies...")
        candidates = await self._generate_candidates(
            market_context, system_prompt, recipe_prompt, model, tracker
        )
        print(f"✓ Generated {len(candidates)} candidates")

        # Print token usage report
        if enable_tracking:
            tracker.print_report()

        # Validate count
        if len(candidates) != 5:
            raise ValueError(f"Expected 5 candidates, got {len(candidates)}")

        # Check for duplicates (simple ticker comparison)
        ticker_sets = [set(c.assets) for c in candidates]
        unique_ticker_sets = set(tuple(sorted(ts)) for ts in ticker_sets)
        if len(ticker_sets) != len(unique_ticker_sets):
            raise ValueError("Duplicate candidates detected (same ticker sets)")

        return candidates

    async def _generate_candidates(
        self,
        market_context: dict,
        system_prompt: str,
        recipe_prompt: str,
        model: str,
        tracker: TokenTracker
    ) -> List[Strategy]:
        """
        Generate 5 diverse candidates using market context pack.

        Tools are available but optional - use only for data gaps:
        - composer_search_symphonies: Additional pattern inspiration
        - stock_get_historical_stock_prices: Specific asset data
        - fred_get_series: Macro data verification

        Args:
            market_context: Comprehensive market context pack (date-anchored)
            system_prompt: System-level prompt with schemas and constraints
            recipe_prompt: Recipe with frameworks and examples
            model: LLM model identifier
            tracker: Token usage tracker

        Returns:
            List of exactly 5 Strategy objects
        """
        # Create agent with all tools available (but usage optional)
        agent_ctx = await create_agent(
            model=model,
            output_type=List[Strategy],
            system_prompt=system_prompt,
            include_composer=True  # Keep tools available
        )

        async with agent_ctx as agent:
            market_context_json = json.dumps(market_context, indent=2)

            generate_prompt = f"""Generate 5 diverse trading strategy candidates.

**COMPREHENSIVE MARKET CONTEXT PACK:**

The following market analysis is already provided. Use it as your primary data source:

{market_context_json}

This context pack includes:
- Macro regime: Interest rates, inflation, employment, yield curve
- Market regime: Trend (bull/bear), volatility (VIX), breadth (% sectors >50d MA)
- Sector leadership: Top 3 leaders and bottom 3 laggards vs SPY (30d)
- Factor premiums: Value vs growth, momentum, quality, size (30d)
- Benchmark performance: SPY/QQQ/AGG/60-40/risk parity (30d returns, Sharpe, vol)
- Recent events: Curated market-moving events (30d lookback)
- Manual Composer examples: Proven successful strategy patterns (if provided)

**OPTIONAL TOOL USAGE:**

Tools are available if you need data NOT in the context pack:
- composer_search_symphonies: Search for additional patterns beyond manual examples
- stock_get_historical_stock_prices: Get specific asset data for individual stocks
- fred_get_series: Verify specific macro indicators if context seems surprising

**RECIPE GUIDANCE:**

{recipe_prompt}

**YOUR TASK:**

Generate exactly 5 Strategy objects with:

1. **Edge Articulation** for each:
   - Specific inefficiency being exploited
   - Why the edge exists (mechanism)
   - Why now (cite context pack regime data)
   - Realistic failure modes

2. **Diversity Requirements**:
   - ≥3 different edge types (behavioral/structural/informational/risk premium)
   - ≥3 different archetypes (momentum/mean reversion/carry/directional/volatility)
   - Mix of concentration (focused vs diversified)
   - Mix of regime positioning (pro-cyclical vs counter-cyclical)
   - ≥3 different rebalancing frequencies

3. **Platform Compliance**:
   - All weights sum to 1.0
   - No single asset >50%
   - Valid tickers (ETFs or stocks)
   - Rebalance frequency specified

**IMPORTANT:**
- Primary data source: Context pack above
- Tool usage: Optional, only for gaps in context pack
- Citation: Reference context pack data (e.g., "VIX 18.6 per context pack")
- Diversity: Essential - explore possibility space, don't optimize for single approach

Output List[Strategy] with exactly 5 candidates.
"""

            # Track token usage before API call
            tracker.estimate_prompt(
                label="Candidate Generation",
                system_prompt=system_prompt,
                user_prompt=generate_prompt,
                tool_definitions_est=8000,  # Estimate for all MCP tools (optional usage)
                notes="Single-phase generation with optional tool usage"
            )

            result = await agent.run(generate_prompt)
            return result.output
