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

1. **thesis_document (GENERATE FIRST - MOST IMPORTANT):**
   - Write 200-2000 character investment thesis explaining:
     - Market opportunity: What regime/trend are you exploiting?
     - Edge explanation: Why does this inefficiency exist? Why persistent?
     - Regime fit: Why NOW? Cite context pack data (VIX, breadth, sector leadership)
     - Risk factors: Specific failure modes with triggers and impact
   - Plain text paragraphs (NO markdown headers)
   - Specific to THIS strategy (not generic "buy winners" boilerplate)
   - Cite context pack numbers (e.g., "VIX 18.6 indicates low vol regime")

2. **Edge Articulation Requirements**:
   - Specific inefficiency being exploited
   - Why the edge exists (causal mechanism)
   - Why now (cite context pack regime data)
   - Realistic failure modes with specific triggers

3. **Diversity Requirements**:
   - ≥3 different edge types (behavioral/structural/informational/risk premium)
   - ≥3 different archetypes (momentum/mean reversion/carry/directional/volatility)
   - Mix of concentration (focused vs diversified)
   - Mix of regime positioning (pro-cyclical vs counter-cyclical)
   - ≥3 different rebalancing frequencies

4. **Platform Compliance**:
   - All weights sum to 1.0
   - No single asset >50%
   - Valid tickers (ETFs or stocks)
   - Rebalance frequency specified

**CRITICAL FIELD ORDERING:**
Generate thesis_document FIRST for each strategy (before name, assets, weights).
This enables chain-of-thought reasoning before committing to execution details.

**CRITICAL logic_tree STRUCTURE (for conditional strategies):**
If your strategy uses conditional logic, you MUST use this EXACT structure:
```python
logic_tree={{
  "condition": "VIX > 22",  # String comparison expression
  "if_true": {{              # Dictionary with assets and weights
    "assets": ["TLT", "GLD"],
    "weights": {{"TLT": 0.5, "GLD": 0.5}}
  }},
  "if_false": {{             # Dictionary with assets and weights
    "assets": ["SPY", "QQQ"],
    "weights": {{"SPY": 0.6, "QQQ": 0.4}}
  }}
}}
```
DO NOT use string descriptions like "true_action": "allocate 70%..." - use actual asset/weight dicts.
For static strategies, use logic_tree={{}}.

**IMPORTANT:**
- Primary data source: Context pack above
- Tool usage: Optional, only for gaps in context pack
- Citation: Reference context pack data (e.g., "VIX 18.6 per context pack")
- Diversity: Essential - explore possibility space, don't optimize for single approach

Output List[Strategy] with exactly 5 candidates in ONE response (not one at a time).
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

            # Debug logging: Print full LLM response
            print(f"\n[DEBUG:CandidateGenerator] Full LLM response:")
            print(f"{result.output}")

            # Post-generation validation (Fix #1: Post-validation retry)
            candidates = result.output
            validation_errors = self._validate_semantics(candidates, market_context)

            if validation_errors:
                print(f"\n[WARNING] Post-generation validation found {len(validation_errors)} issues:")
                for idx, error in enumerate(validation_errors, 1):
                    print(f"  {idx}. {error}")

                print("\n[RETRY] Attempting targeted fixes...")
                fixed_candidates = await self._retry_failed_strategies(
                    candidates, validation_errors, agent, market_context_json, tracker
                )
                return fixed_candidates

            return candidates

    def _validate_semantics(self, candidates: List[Strategy], market_context: dict) -> List[str]:
        """
        Validate semantic coherence of generated candidates.

        Checks:
        1. Thesis-logic_tree coherence (conditional keywords → logic_tree populated)
        2. Rebalancing alignment (edge type → frequency match)
        3. Weight derivation (no arbitrary round numbers without justification)

        Args:
            candidates: List of generated Strategy objects
            market_context: Market context pack for validation

        Returns:
            List of validation error messages (empty if all pass)
        """
        errors = []

        for idx, strategy in enumerate(candidates, 1):
            # Check 1: Conditional keywords in thesis require logic_tree
            import re
            conditional_patterns = [
                r'\bif\b', r'\bwhen\b', r'\btrigger\b', r'\bthreshold\b',
                r'\bbreach\b', r'\bcross\b', r'\bexceed\b', r'\bspike\b',
                r'\brotation\b', r'\bdefensive mode\b', r'\btactical\b',
                r'\bswitch\b', r'\bshift\b', r'\ballocate based on\b',
                r'vix\s*>', r'vix\s*<', r'vix exceeds', r'vix above', r'vix below'
            ]
            thesis_lower = strategy.thesis_document.lower()
            has_conditional_keywords = any(re.search(p, thesis_lower, re.IGNORECASE) for p in conditional_patterns)
            matched_keywords = [p for p in conditional_patterns if re.search(p, thesis_lower, re.IGNORECASE)]

            if has_conditional_keywords and not strategy.logic_tree:
                errors.append(
                    f"Candidate #{idx} ({strategy.name}): Thesis describes conditional logic "
                    f"(matched patterns: {matched_keywords[:3]}), "
                    f"but logic_tree is empty. Must implement conditional logic or revise thesis."
                )

            # Check 2: Archetype-frequency alignment
            archetype = strategy.archetype
            frequency = strategy.rebalance_frequency

            # Edge-frequency violations (from architecture plan RC-4B)
            # Use string conversion for robust enum comparison
            archetype_str = str(archetype).lower() if archetype else ""
            if archetype_str == "momentum" and frequency == "quarterly":
                errors.append(
                    f"Candidate #{idx} ({strategy.name}): Momentum archetype with quarterly "
                    f"rebalancing is too slow (momentum decays faster than quarterly). "
                    f"Use daily/weekly/monthly instead."
                )
            elif archetype_str == "mean_reversion" and frequency in ["daily", "weekly"]:
                errors.append(
                    f"Candidate #{idx} ({strategy.name}): Mean reversion archetype with "
                    f"{frequency} rebalancing is too fast (creates whipsaw, prevents reversion capture). "
                    f"Use monthly/quarterly instead."
                )
            elif archetype_str == "carry" and frequency in ["daily", "weekly", "monthly"]:
                errors.append(
                    f"Candidate #{idx} ({strategy.name}): Carry archetype with {frequency} "
                    f"rebalancing has excessive turnover (destroys carry edge). "
                    f"Use quarterly or none instead."
                )
            elif archetype_str in ["volatility", "tactical"] and frequency in ["monthly", "quarterly"]:
                errors.append(
                    f"Candidate #{idx} ({strategy.name}): Volatility/tactical archetype with "
                    f"{frequency} rebalancing is too slow (regime shifts happen faster). "
                    f"Use daily/weekly instead."
                )

            # Check 3: Weight derivation (detect arbitrary round numbers)
            if strategy.weights:
                weights_list = list(strategy.weights.values())
                # Check if all weights are "suspiciously round" (0.20, 0.25, 0.30, 0.33, 0.35, 0.40, 0.50)
                round_numbers = [0.20, 0.25, 0.30, 0.333, 0.334, 0.35, 0.40, 0.50]
                all_round = all(
                    any(abs(w - rn) < 0.005 for rn in round_numbers)
                    for w in weights_list
                )

                # Check if rebalancing_rationale explains weight derivation
                rationale_lower = strategy.rebalancing_rationale.lower()
                derivation_phrases = [
                    "weights derived", "weight", "allocation",
                    "momentum-weighted", "equal-weight", "equal weight",
                    "allocated using", "weighted by", "divided based on",
                    "proportional to", "inverse to volatility", "risk-parity", "risk parity",
                    "sized based on", "positions sized", "conviction"
                ]
                has_derivation = any(phrase in rationale_lower for phrase in derivation_phrases)

                if all_round and len(weights_list) >= 3 and not has_derivation:
                    errors.append(
                        f"Candidate #{idx} ({strategy.name}): All weights are round numbers "
                        f"({weights_list}), but rebalancing_rationale doesn't explain derivation method. "
                        f"Must justify weights or use thesis-driven derivation."
                    )

            # Check 4: Alpha vs Beta - Mean Reversion with sector ETFs
            archetype_str = str(archetype).lower() if archetype else ""
            if archetype_str in ["mean_reversion", "value"]:
                # Check if using sector ETFs instead of individual stocks
                sector_etfs = ["XLK", "XLF", "XLE", "XLU", "XLV", "XLI", "XLP", "XLY", "XLC", "XLRE", "XLB"]
                has_sector_etfs = any(asset in strategy.assets for asset in sector_etfs)
                thesis_lower = strategy.thesis_document.lower()
                has_stock_language = any(word in thesis_lower for word in ["oversold", "undervalued", "quality", "fundamental", "p/e", "balance sheet"])

                if has_sector_etfs and has_stock_language:
                    sector_etf_list = [a for a in strategy.assets if a in sector_etfs]
                    errors.append(
                        f"Candidate #{idx} ({strategy.name}): Mean Reversion/Value archetype with sector ETFs "
                        f"{sector_etf_list}, but thesis describes stock-level analysis "
                        f"(contains: oversold/undervalued/quality/fundamental). Must use individual stocks "
                        f"[TICKER, TICKER, TICKER] with security selection workflow per Alpha vs Beta framework."
                    )

        return errors

    def _create_fix_prompt(self, validation_errors: List[str]) -> str:
        """
        Create targeted fix prompt from validation errors.

        Args:
            validation_errors: List of validation error messages

        Returns:
            Prompt string with specific fix instructions
        """
        fix_prompt = "# SURGICAL VALIDATION FIX - PRESERVE STRUCTURE\n\n"
        fix_prompt += "## ⚠️ CRITICAL: PRESERVE THESE FIELDS (DO NOT MODIFY)\n"
        fix_prompt += "**These fields MUST remain EXACTLY as originally generated:**\n"
        fix_prompt += "- **assets**: MUST preserve EXACT list (same tickers, same order)\n"
        fix_prompt += "- **weights**: MUST preserve EXACT dict keys (same assets as keys)\n"
        fix_prompt += "- **name**: MUST preserve EXACT string\n\n"
        fix_prompt += "**❌ FORBIDDEN CHANGES:**\n"
        fix_prompt += "- DO NOT change [XLK, XLY, XLF] to [XLK, XLV, XLU]\n"
        fix_prompt += "- DO NOT add/remove assets from the original list\n"
        fix_prompt += "- DO NOT change weight keys (must match assets exactly)\n\n"
        fix_prompt += "**✅ VALIDATION ENFORCEMENT:**\n"
        fix_prompt += "After this fix, programmatic checks will verify assets/weights unchanged.\n"
        fix_prompt += "Any modification to assets/weights will cause immediate failure.\n\n"
        fix_prompt += "## ONLY REVISE THESE FIELDS:\n"
        fix_prompt += "- thesis_document: Fix language to match conditional logic requirements\n"
        fix_prompt += "- rebalancing_rationale: Add weight derivation explanation if missing\n"
        fix_prompt += "- logic_tree: Add conditional structure if thesis describes conditional logic\n\n"

        fix_prompt += f"The following {len(validation_errors)} validation errors were found:\n\n"

        for idx, error in enumerate(validation_errors, 1):
            fix_prompt += f"{idx}. {error}\n\n"

        fix_prompt += "\n## REQUIRED FIXES\n\n"
        fix_prompt += "For each error above:\n"
        fix_prompt += "1. If thesis describes conditional logic but logic_tree empty → Implement logic_tree\n"
        fix_prompt += "2. If archetype-frequency mismatch → Change frequency to match edge timescale\n"
        fix_prompt += "3. If weights lack derivation → Add weight derivation explanation to rebalancing_rationale\n"
        fix_prompt += "4. If Alpha vs Beta mismatch → Must use individual stocks with security selection workflow\n\n"
        fix_prompt += "Return the CORRECTED List[Strategy] with all validation errors fixed.\n"

        return fix_prompt

    async def _retry_failed_strategies(
        self,
        candidates: List[Strategy],
        validation_errors: List[str],
        agent,
        market_context_json: str,
        tracker: TokenTracker
    ) -> List[Strategy]:
        """
        Retry generation with targeted fix prompt.

        Args:
            candidates: Original candidates with validation errors
            validation_errors: List of validation error messages
            agent: Pydantic AI agent
            market_context_json: JSON string of market context
            tracker: Token usage tracker

        Returns:
            Fixed candidates (merge of passing + fixed failing)
        """
        fix_prompt = self._create_fix_prompt(validation_errors)

        retry_prompt = f"""You generated 5 strategies, but post-validation found issues.

**ORIGINAL MARKET CONTEXT:**
{market_context_json}

**VALIDATION ERRORS:**
{fix_prompt}

**YOUR TASK:**
Fix ONLY the strategies with validation errors. Return complete List[Strategy] with exactly 5 candidates.

**FIXES REQUIRED:**
{fix_prompt}

Output List[Strategy] with all errors corrected."""

        print(f"\n[RETRY] Sending fix prompt ({len(retry_prompt)} chars)...")
        tracker.estimate_prompt(
            label="Retry Fix",
            system_prompt="(same as generation)",
            user_prompt=retry_prompt,
            notes="Single retry with targeted error fixes"
        )

        try:
            result = await agent.run(retry_prompt)
            print(f"✓ Retry succeeded - received {len(result.output)} candidates")

            # CRITICAL: Validate that retry preserved asset structure (data integrity check)
            fixed_candidates = result.output
            if len(fixed_candidates) != len(candidates):
                raise ValueError(
                    f"Retry changed candidate count: {len(candidates)} → {len(fixed_candidates)}. "
                    f"Must preserve exactly 5 candidates."
                )

            for i, (original, fixed) in enumerate(zip(candidates, fixed_candidates)):
                # Check assets preserved
                if fixed.assets != original.assets:
                    raise ValueError(
                        f"Retry modified assets for candidate {i} ({original.name}): "
                        f"{original.assets} → {fixed.assets}. "
                        f"Assets must be preserved exactly - only thesis/logic_tree/rationale can change."
                    )

                # Check weights structure preserved (keys match, even if values differ slightly)
                if set(fixed.weights.keys()) != set(original.weights.keys()):
                    raise ValueError(
                        f"Retry modified weights structure for candidate {i} ({original.name}): "
                        f"keys {list(original.weights.keys())} → {list(fixed.weights.keys())}. "
                        f"Weight keys must match assets exactly."
                    )

            print("✓ Data integrity validated - assets and weights preserved")
            return fixed_candidates
        except Exception as e:
            print(f"✗ Retry failed: {e}")
            print("  Returning original candidates (with validation warnings)")
            return candidates
