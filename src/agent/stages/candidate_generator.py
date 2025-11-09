"""Generate 5 candidate strategies using AI."""

from typing import List, Dict
import json
import os
import re
from dataclasses import dataclass
from pydantic_ai import ModelSettings
from src.agent.strategy_creator import create_agent, load_prompt, DEFAULT_MODEL
from src.agent.models import Strategy
from src.agent.token_tracker import TokenTracker
from src.agent.config.leverage import (
    APPROVED_2X_ETFS,
    APPROVED_3X_ETFS,
    ALL_LEVERAGED_ETFS,
    detect_leverage,
    get_drawdown_bounds,
    get_decay_cost_range,
)


# Pre-compiled regex patterns for validation (performance optimization)
_DECAY_NUMBER_PATTERN = re.compile(
    r'\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?%?\s*(?:annual|yearly|per year|decay)'
)
_DRAWDOWN_PATTERN = re.compile(r'(\d+)%?\s*(?:drawdown|dd|decline|loss)')
_EXIT_SPECIFIC_PATTERN = re.compile(r'(?:exit|rotate|stop).*(?:if|when|vix >|momentum <)')


@dataclass
class QualityScore:
    """
    Aggregate quality metrics for strategy evaluation.

    Weighted scoring system to guide retry intensity:
    - overall >= 0.6 AND no dimension < 0.3 → passes quality gate
    - overall < 0.4 → aggressive retry with detailed guidance
    - 0.4 <= overall < 0.6 → standard retry with targeted fixes
    """
    quantification: float  # 0-1, has Sharpe/alpha/drawdown
    coherence: float       # 0-1, thesis matches implementation
    edge_frequency: float  # 0-1, archetype matches rebalancing
    diversification: float # 0-1, low concentration risk
    syntax: float         # 0-1, structure valid

    @property
    def overall(self) -> float:
        """Weighted overall quality score."""
        return (
            0.25 * self.quantification +
            0.30 * self.coherence +
            0.20 * self.edge_frequency +
            0.15 * self.diversification +
            0.10 * self.syntax
        )

    @property
    def passes_gate(self) -> bool:
        """Pass if overall >= 0.6 AND no dimension < 0.3"""
        if self.overall < 0.6:
            return False
        return all([
            self.quantification >= 0.3,
            self.coherence >= 0.3,
            self.edge_frequency >= 0.3,
            self.diversification >= 0.3,
            self.syntax >= 0.3,
        ])


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
        # Fix for Pydantic AI bug #1429: Disable parallel tool calls to prevent LLM
        # from calling final_result multiple times (once per strategy) instead of
        # once with the complete list. This ensures all 5 strategies are generated.
        # See: https://github.com/pydantic/pydantic-ai/issues/1429
        model_settings = ModelSettings(parallel_tool_calls=False)

        # Create agent with all tools available (but usage optional)
        agent_ctx = await create_agent(
            model=model,
            output_type=List[Strategy],
            system_prompt=system_prompt,
            include_composer=True,  # Keep tools available
            model_settings=model_settings
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

Return all 5 candidates together in a single List[Strategy] containing exactly 5 Strategy objects.
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

                # Compute quality scores for each candidate
                quality_scores = []
                for candidate in candidates:
                    candidate_errors = [e for e in validation_errors if candidate.name in e]
                    score = self.compute_quality_score(candidate, candidate_errors)
                    quality_scores.append(score)

                # Calculate average quality
                avg_quality = sum(s.overall for s in quality_scores) / len(quality_scores)

                print(f"\n[QUALITY ASSESSMENT]")
                print(f"  Average quality score: {avg_quality:.2f}/1.0")
                for i, (candidate, score) in enumerate(zip(candidates, quality_scores), 1):
                    status = "✅ PASS" if score.passes_gate else "❌ FAIL"
                    print(f"  Candidate #{i} ({candidate.name[:40]}...): {score.overall:.2f} {status}")
                    print(f"    - Quantification: {score.quantification:.2f}")
                    print(f"    - Coherence: {score.coherence:.2f}")
                    print(f"    - Edge-Frequency: {score.edge_frequency:.2f}")
                    print(f"    - Diversification: {score.diversification:.2f}")
                    print(f"    - Syntax: {score.syntax:.2f}")

                # Determine retry intensity based on quality
                if avg_quality < 0.4:
                    print("\n[RETRY INTENSITY] Low quality detected (<0.4) - providing detailed prescriptive guidance")
                elif avg_quality < 0.6:
                    print("\n[RETRY INTENSITY] Moderate quality (0.4-0.6) - providing specific dimension feedback")
                else:
                    print("\n[RETRY INTENSITY] Minor issues (>0.6) - providing targeted fixes only")

                print("\n[RETRY] Attempting targeted fixes...")
                fixed_candidates = await self._retry_failed_strategies(
                    candidates, validation_errors, agent, market_context_json, tracker
                )
                return fixed_candidates

            return candidates

    def _validate_non_approved_etfs(
        self,
        strategy: Strategy,
        leveraged_2x: List[str],
        leveraged_3x: List[str]
    ) -> List[str]:
        """Check for non-approved leveraged tickers."""
        errors = []
        for asset in strategy.assets:
            if any(indicator in asset for indicator in ["2X", "3X", "ULTRA", "TRIPLE", "DOUBLE"]):
                if asset not in ALL_LEVERAGED_ETFS:
                    errors.append(
                        f"Priority 2 (RETRY): {strategy.name} uses non-approved leveraged ETF '{asset}'. "
                        f"Approved 2x: {sorted(APPROVED_2X_ETFS)}. Approved 3x: {sorted(APPROVED_3X_ETFS)}. "
                        f"Use only whitelisted instruments for liquidity/reliability."
                    )
        return errors

    def _validate_convexity(
        self,
        strategy: Strategy,
        max_leverage: int,
        combined_text: str,
        leveraged_assets_str: str
    ) -> List[str]:
        """Validate convexity advantage explanation."""
        errors = []
        convexity_keywords = ["convexity", "amplif", "leverage enhances", "edge window", "faster capture"]
        has_convexity = any(kw in combined_text for kw in convexity_keywords)

        if not has_convexity:
            severity = "Priority 1 (HARD REJECT)" if max_leverage == 3 else "Priority 2 (RETRY)"
            errors.append(
                f"{severity}: {strategy.name} uses {max_leverage}x leverage ({leveraged_assets_str}) "
                f"but doesn't explain convexity advantage. Thesis must explain: "
                f"WHY does leverage enhance your edge vs unleveraged version? "
                f"Example: 'Edge window (2-4 weeks) shorter than decay threshold (30+ days)' or "
                f"'{max_leverage}x captures momentum spike faster before mean reversion.'"
            )
        return errors

    def _validate_decay(
        self,
        strategy: Strategy,
        max_leverage: int,
        combined_text: str
    ) -> List[str]:
        """Validate decay cost quantification."""
        errors = []
        decay_keywords = ["decay", "friction", "daily rebalancing cost", "contango"]
        has_decay = any(kw in combined_text for kw in decay_keywords)
        has_decay_number = bool(_DECAY_NUMBER_PATTERN.search(combined_text))

        if not (has_decay and has_decay_number):
            severity = "Priority 1 (HARD REJECT)" if max_leverage == 3 else "Priority 2 (RETRY)"
            decay_min, decay_max = get_decay_cost_range(max_leverage)
            errors.append(
                f"{severity}: {strategy.name} uses {max_leverage}x leverage but doesn't quantify decay cost. "
                f"Must include: '{max_leverage}x ETFs decay ~{decay_min}-{decay_max}% annually in sideways markets.' "
                f"Must explain why edge magnitude justifies this cost (should be 5-10x decay)."
            )
        return errors

    def _validate_drawdown(
        self,
        strategy: Strategy,
        max_leverage: int,
        combined_text: str
    ) -> List[str]:
        """Validate realistic drawdown expectations."""
        errors = []
        drawdown_keywords = ["drawdown", "max dd", "maximum decline", "worst case"]
        has_drawdown = any(kw in combined_text for kw in drawdown_keywords)

        drawdown_numbers = _DRAWDOWN_PATTERN.findall(combined_text)
        drawdown_values = [int(d) for d in drawdown_numbers if d.isdigit()]

        min_realistic_dd, max_realistic_dd = get_drawdown_bounds(max_leverage)

        if drawdown_values:
            max_claimed_dd = max(drawdown_values)
            if max_claimed_dd < min_realistic_dd:
                errors.append(
                    f"Priority 1 (HARD REJECT): {strategy.name} uses {max_leverage}x leverage "
                    f"but claims only {max_claimed_dd}% max drawdown. UNREALISTIC. "
                    f"{max_leverage}x leverage amplifies drawdowns non-linearly. "
                    f"Realistic range: {min_realistic_dd}% to {max_realistic_dd}%. "
                    f"Example: 2022 TQQQ -80% vs QQQ -35%. Be pessimistic."
                )
        elif not has_drawdown:
            severity = "Priority 1 (HARD REJECT)" if max_leverage == 3 else "Priority 2 (RETRY)"
            errors.append(
                f"{severity}: {strategy.name} uses {max_leverage}x leverage but doesn't specify expected drawdown. "
                f"Must include realistic worst-case: '{max_leverage}x expected max drawdown: "
                f"{min_realistic_dd}% to {max_realistic_dd}%' with historical justification."
            )
        return errors

    def _validate_benchmark(
        self,
        strategy: Strategy,
        max_leverage: int,
        combined_text: str,
        leveraged_2x: List[str],
        leveraged_3x: List[str],
        leveraged_assets_str: str
    ) -> List[str]:
        """Validate benchmark comparison."""
        errors = []
        unleveraged_map = {
            "SSO": "SPY", "UPRO": "SPY", "SPXL": "SPY",
            "QLD": "QQQ", "TQQQ": "QQQ", "SQQQ": "QQQ",
            "SOXL": "SMH", "TECL": "XLK", "FAS": "XLF",
            "TMF": "TLT", "UBT": "TLT",
        }

        benchmark_mentioned = []
        for lev_asset in (leveraged_2x + leveraged_3x):
            if lev_asset in unleveraged_map:
                benchmark = unleveraged_map[lev_asset]
                if benchmark.lower() in combined_text:
                    benchmark_mentioned.append(f"{lev_asset} vs {benchmark}")

        if not benchmark_mentioned and (leveraged_2x or leveraged_3x):
            severity = "Priority 2 (RETRY)" if max_leverage == 2 else "Priority 1 (HARD REJECT)"
            example_comparisons = []
            for lev_asset in (leveraged_2x + leveraged_3x)[:2]:
                if lev_asset in unleveraged_map:
                    example_comparisons.append(f"{lev_asset} vs {unleveraged_map[lev_asset]}")

            errors.append(
                f"{severity}: {strategy.name} uses leveraged ETFs ({leveraged_assets_str}) "
                f"but doesn't compare to unleveraged alternatives. Must explain: "
                f"Why not just use {', '.join(example_comparisons)}? "
                f"Example: 'TQQQ vs QQQ: {max_leverage}x captures 2-4 week momentum before decay dominates, "
                f"targeting +18-22% alpha vs QQQ after decay costs.'"
            )
        return errors

    def _validate_stress_test(
        self,
        strategy: Strategy,
        combined_text: str
    ) -> List[str]:
        """Validate stress test for 3x strategies."""
        errors = []
        stress_keywords = ["2022", "2020", "2008", "covid", "rate shock", "financial crisis"]
        has_stress_test = any(kw in combined_text for kw in stress_keywords)

        if not has_stress_test:
            errors.append(
                f"Priority 1 (HARD REJECT): {strategy.name} uses 3x leverage but lacks stress test. "
                f"3x strategies MUST include historical crisis analog (2022, 2020, or 2008). "
                f"Example: '2022 analog: TQQQ -80% vs QQQ -35% during rate shock. "
                f"Acceptable for aggressive conviction betting on AI momentum reversal.' or "
                f"'2020 COVID: TQQQ -75% in 30 days vs QQQ -30%. Exit at VIX >30 limits exposure.'"
            )
        return errors

    def _validate_exit_criteria(
        self,
        strategy: Strategy,
        combined_text: str
    ) -> List[str]:
        """Validate exit criteria for 3x strategies."""
        errors = []
        exit_keywords = ["exit", "stop", "de-risk", "rotate to", "if vix", "when momentum"]
        has_exit_criteria = any(kw in combined_text for kw in exit_keywords)
        has_specific_exit = bool(_EXIT_SPECIFIC_PATTERN.search(combined_text))

        if not (has_exit_criteria and has_specific_exit):
            errors.append(
                f"Priority 1 (HARD REJECT): {strategy.name} uses 3x leverage but lacks exit criteria. "
                f"3x strategies MUST specify when to de-risk. "
                f"Example: 'Exit if VIX > 30 for 5+ consecutive days OR momentum turns negative OR "
                f"AI CapEx growth < 10% YoY (thesis breakdown).'"
            )
        return errors

    def _validate_leverage_justification(self, strategy: Strategy) -> List[str]:
        """
        Validate that leveraged ETF usage includes proper justification.

        Requirements for 2x/3x ETFs:
        1. Convexity advantage explanation
        2. Decay cost quantification
        3. Realistic drawdown expectations
        4. Benchmark comparison

        Additional for 3x:
        5. Stress test (2022, 2020, or 2008 analog)
        6. Exit criteria

        This method orchestrates validation by delegating to specialized validators.
        """
        errors = []

        # Detect leveraged assets
        leveraged_2x, leveraged_3x, max_leverage = detect_leverage(strategy)

        # Check for non-approved leveraged tickers
        errors.extend(self._validate_non_approved_etfs(strategy, leveraged_2x, leveraged_3x))

        if not (leveraged_2x or leveraged_3x):
            return errors  # No leverage, validation passes

        leveraged_assets_str = ", ".join(leveraged_2x + leveraged_3x)
        thesis_lower = strategy.thesis_document.lower()
        rationale_lower = strategy.rebalancing_rationale.lower()
        combined_text = thesis_lower + " " + rationale_lower

        # Validate 4 core elements (all leveraged strategies)
        errors.extend(self._validate_convexity(strategy, max_leverage, combined_text, leveraged_assets_str))
        errors.extend(self._validate_decay(strategy, max_leverage, combined_text))
        errors.extend(self._validate_drawdown(strategy, max_leverage, combined_text))
        errors.extend(self._validate_benchmark(
            strategy, max_leverage, combined_text, leveraged_2x, leveraged_3x, leveraged_assets_str
        ))

        # Additional 2 elements for 3x only
        if max_leverage == 3:
            errors.extend(self._validate_stress_test(strategy, combined_text))
            errors.extend(self._validate_exit_criteria(strategy, combined_text))

        return errors

    def _validate_semantics(self, candidates: List[Strategy], market_context: dict) -> List[str]:
        """
        Validate semantic coherence of generated candidates.

        Checks:
        1. Thesis-logic_tree coherence (conditional keywords → logic_tree populated)
        2. Rebalancing alignment (edge type → frequency match)
        3. Weight derivation (no arbitrary round numbers without justification)
        4. Syntax validation (weights sum, logic_tree structure)
        5. Concentration limits (single asset, sector, min assets)
        6. Leverage justification (2x/3x ETF usage validation)

        Args:
            candidates: List of generated Strategy objects
            market_context: Market context pack for validation

        Returns:
            List of validation error messages (empty if all pass)
        """
        errors = []

        for idx, strategy in enumerate(candidates, 1):
            # Run syntax validation first (structural checks)
            syntax_errors = self._validate_syntax(strategy)
            errors.extend(syntax_errors)

            # Run concentration validation (Priority 4 suggestions)
            concentration_errors = self._validate_concentration(strategy)
            errors.extend(concentration_errors)

            # Run leverage justification validation
            leverage_errors = self._validate_leverage_justification(strategy)
            errors.extend(leverage_errors)

        # Continue with original semantic validation
        for idx, strategy in enumerate(candidates, 1):
            # Check 1: Conditional keywords in thesis require logic_tree
            import re

            # Context-aware patterns: require verb phrases or conditional context
            conditional_patterns = [
                r'\bif\s+\w+\s+(exceeds|crosses|triggers|above|below)',  # "if VIX exceeds", not just "if"
                r'\bwhen\s+.{5,50}\s+(exceeds|crosses|triggers|above|below|falls|rises)',  # "when X exceeds Y"
                r'\btrigger.{1,20}(rotation|rebalance|shift)',  # "trigger rotation" with context
                r'\bthreshold\s+of\s+\d+',  # "threshold of 25"
                r'\bbreach.{1,15}(level|threshold)',  # "breach threshold"
                r'\bcross\s+(above|below)',  # "cross above/below"
                r'\bexceed\s+\d+',  # "exceed 25"
                r'\bspike\s+(above|to|past)',  # "spike above"
                r'\brotate\s+(to|into|toward|from)',  # "rotate to defense" (verb phrase)
                r'\bdefensive\s+mode',  # Keep as is (already specific)
                r'\btactical\s+(shift|rotation|allocation)',  # "tactical shift" (with noun)
                r'\bswitch\s+(to|into|from)',  # "switch to bonds"
                r'\bshift\s+(to|into|toward)',  # "shift to defensive"
                r'\ballocate\s+based\s+on',  # Keep as is (already specific)
                r'vix\s*>', r'vix\s*<', r'vix\s+exceeds', r'vix\s+(above|below)'  # VIX patterns
            ]

            # Static context patterns that should NOT trigger (false positives)
            static_patterns = [
                r'sector\s+rotation\s+strategy',  # "sector rotation strategy" (descriptive, not conditional)
                r'when\s+performance',  # "when performance peaks" (past tense/general)
                r'rotational\s+(approach|strategy)',  # "rotational approach" (descriptive)
            ]

            thesis_lower = strategy.thesis_document.lower()

            # Check for static patterns first (exclude these)
            has_static_match = any(re.search(p, thesis_lower, re.IGNORECASE) for p in static_patterns)

            # Check for conditional patterns
            has_conditional_keywords = any(re.search(p, thesis_lower, re.IGNORECASE) for p in conditional_patterns)
            matched_keywords = [p for p in conditional_patterns if re.search(p, thesis_lower, re.IGNORECASE)]

            if has_conditional_keywords and not has_static_match and not strategy.logic_tree:
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

    def _validate_concentration(self, strategy: Strategy) -> List[str]:
        """
        Validate concentration risk limits with numeric thresholds.

        Priority 4 (SUGGESTION - Non-Blocking): Warnings only, not hard rejects.

        Checks:
        - Single asset concentration (max 40%, 50% OK with justification)
        - Sector concentration (max 75%, 100% OK for stock selection with 4+ stocks)
        - Minimum asset count (min 3, 2 OK for barbell/core-satellite)

        Args:
            strategy: Strategy to validate

        Returns:
            List of concentration warning messages (Priority 4)
        """
        errors = []

        # Check 1: Single asset concentration
        if strategy.weights:
            # Handle both dict and WeightsDict types
            weights_dict = dict(strategy.weights) if hasattr(strategy.weights, 'items') else strategy.weights
            max_weight = max(weights_dict.values())
            if max_weight > 0.40:
                max_asset = max(weights_dict, key=weights_dict.get)

                # Check if justification exists in rebalancing_rationale
                rationale_lower = strategy.rebalancing_rationale.lower()
                justification_keywords = [
                    "core-satellite", "barbell", "high-conviction", "concentrated",
                    "intentional", "deliberate", "justified"
                ]
                has_justification = any(kw in rationale_lower for kw in justification_keywords)

                if not has_justification:
                    errors.append(
                        f"Priority 4 (SUGGESTION): {strategy.name} - Single asset concentration high: "
                        f"{max_asset} = {max_weight:.0%} > 40% guideline. Consider adding justification "
                        f"in rebalancing_rationale (e.g., 'core-satellite', 'high-conviction bet', "
                        f"'barbell strategy') or diversifying further."
                    )

        # Check 2: Sector concentration (requires yfinance lookup)
        try:
            sector_weights = self._get_sector_weights(strategy.assets, strategy.weights)
            if sector_weights:
                max_sector_weight = max(sector_weights.values())

                if max_sector_weight > 0.75:
                    top_sector = max(sector_weights, key=sector_weights.get)

                    # Allow if 4+ stocks (stock selection strategy)
                    asset_count = len(strategy.assets)
                    if asset_count < 4:
                        errors.append(
                            f"Priority 4 (SUGGESTION): {strategy.name} - Sector concentration high: "
                            f"{top_sector} = {max_sector_weight:.0%} > 75% guideline with only "
                            f"{asset_count} assets. Consider diversifying across sectors or adding "
                            f"more stocks if this is a stock selection strategy (4+ stocks OK)."
                        )
        except Exception as e:
            # If sector lookup fails, log warning but don't fail validation
            print(f"[WARNING] Could not validate sector concentration for {strategy.name}: {e}")

        # Check 3: Minimum asset count
        if len(strategy.assets) < 3:
            # Check for barbell/core-satellite justification
            rationale_lower = strategy.rebalancing_rationale.lower()
            thesis_lower = strategy.thesis_document.lower()
            barbell_keywords = ["barbell", "core-satellite", "two-asset"]
            has_barbell_justification = any(
                kw in rationale_lower or kw in thesis_lower
                for kw in barbell_keywords
            )

            if not has_barbell_justification:
                errors.append(
                    f"Priority 4 (SUGGESTION): {strategy.name} - Low asset count ({len(strategy.assets)} < 3). "
                    f"High-conviction concentrated strategies should explicitly describe the structure "
                    f"(e.g., 'barbell', 'core-satellite') in thesis or rebalancing_rationale."
                )

        return errors

    def _get_sector_weights(self, assets: List[str], weights: Dict[str, float]) -> Dict[str, float]:
        """
        Map assets to sectors and aggregate weights.

        Args:
            assets: List of tickers
            weights: Asset weights dict (or WeightsDict)

        Returns:
            Dict mapping sector names to aggregated weights
        """
        import yfinance as yf

        # Handle both dict and WeightsDict types
        weights_dict = dict(weights) if hasattr(weights, 'items') else weights

        sector_weights = {}
        for asset in assets:
            try:
                ticker = yf.Ticker(asset)
                sector = ticker.info.get('sector', 'Unknown')
                weight = weights_dict.get(asset, 0.0)
                sector_weights[sector] = sector_weights.get(sector, 0.0) + weight
            except Exception:
                # If lookup fails, assign to Unknown
                weight = weights_dict.get(asset, 0.0)
                sector_weights['Unknown'] = sector_weights.get('Unknown', 0.0) + weight

        return sector_weights

    def _validate_syntax(self, strategy: Strategy) -> List[str]:
        """
        Validate syntactic correctness of strategy structure.

        Programmatic checks for mechanical issues that should never occur
        with properly structured Pydantic models but may slip through.

        Checks:
        - Weights sum to 1.0 (±0.01 tolerance)
        - Weight keys match assets
        - Logic tree structure (condition, if_true, if_false)
        - Assets in logic_tree exist in global assets list

        Args:
            strategy: Strategy to validate

        Returns:
            List of syntax error messages (blocking)
        """
        errors = []

        # Check 1: Weights sum to 1.0 (±0.01 tolerance)
        if strategy.weights:
            weight_sum = sum(strategy.weights.values())
            if not 0.99 <= weight_sum <= 1.01:
                errors.append(
                    f"Syntax Error: {strategy.name} - Weights sum to {weight_sum:.4f}, must equal 1.0. "
                    f"Current weights: {strategy.weights}"
                )

        # Check 2: Weights keys match assets
        if strategy.weights:
            weight_keys = set(strategy.weights.keys())
            assets_set = set(strategy.assets)
            if weight_keys != assets_set:
                missing = assets_set - weight_keys
                extra = weight_keys - assets_set
                errors.append(
                    f"Syntax Error: {strategy.name} - Weight keys don't match assets. "
                    f"Missing weights for: {missing}, Extra weight keys: {extra}"
                )

        # Check 3: Logic tree structure validation (if populated)
        if strategy.logic_tree:
            required_keys = {"condition", "if_true", "if_false"}
            tree_keys = set(strategy.logic_tree.keys())

            if not required_keys.issubset(tree_keys):
                missing = required_keys - tree_keys
                errors.append(
                    f"Syntax Error: {strategy.name} - logic_tree missing required keys: {missing}. "
                    f"Must have: condition, if_true, if_false. Current keys: {tree_keys}"
                )

            # Check condition has comparison operator
            condition = strategy.logic_tree.get("condition", "")
            if condition:
                comparison_ops = [">", "<", ">=", "<=", "==", "!=", " and ", " or "]
                if not any(op in str(condition) for op in comparison_ops):
                    errors.append(
                        f"Syntax Error: {strategy.name} - logic_tree condition '{condition}' lacks "
                        f"comparison operator. Must include >, <, >=, <=, ==, !=, and, or"
                    )

        # Check 4: All assets in logic_tree must be in global assets list
        if strategy.logic_tree:
            tree_assets = self._extract_assets_from_logic_tree(strategy.logic_tree)
            assets_set = set(strategy.assets)
            if not tree_assets.issubset(assets_set):
                unlisted = tree_assets - assets_set
                errors.append(
                    f"Syntax Error: {strategy.name} - logic_tree references assets not in global list: "
                    f"{unlisted}. Add to assets: {strategy.assets}"
                )

        return errors

    def _extract_assets_from_logic_tree(self, logic_tree: dict) -> set:
        """
        Recursively extract all assets mentioned in logic tree.

        Args:
            logic_tree: Logic tree dict (potentially nested)

        Returns:
            Set of all asset tickers mentioned in the tree
        """
        assets = set()

        if isinstance(logic_tree, dict):
            # Check if_true/if_false branches for asset lists
            for branch in ["if_true", "if_false"]:
                if branch in logic_tree:
                    branch_data = logic_tree[branch]
                    if isinstance(branch_data, dict):
                        # Extract assets from this branch
                        if "assets" in branch_data:
                            branch_assets = branch_data["assets"]
                            if isinstance(branch_assets, list):
                                assets.update(branch_assets)
                        # Recursive check for nested conditions
                        assets.update(self._extract_assets_from_logic_tree(branch_data))

        return assets

    def compute_quality_score(self, strategy: Strategy, validation_errors: List[str]) -> QualityScore:
        """
        Compute quality score from validation results.

        Args:
            strategy: Strategy to evaluate
            validation_errors: List of validation error messages for this strategy

        Returns:
            QualityScore with dimensional and overall scores
        """
        # Dimension 1: Quantification (check for Sharpe/alpha/drawdown in thesis)
        thesis_lower = strategy.thesis_document.lower()
        has_sharpe = "sharpe" in thesis_lower or "sharp ratio" in thesis_lower
        has_alpha = "alpha" in thesis_lower or "vs spy" in thesis_lower or "vs qqq" in thesis_lower
        has_drawdown = "drawdown" in thesis_lower or "dd" in thesis_lower or "max dd" in thesis_lower
        quantification = sum([has_sharpe, has_alpha, has_drawdown]) / 3.0

        # Dimension 2: Coherence (no Priority 1 errors = thesis-logic mismatch)
        coherence_errors = [e for e in validation_errors if "Priority 1" in e or "Implementation-Thesis" in e]
        coherence = 1.0 if not coherence_errors else 0.0

        # Dimension 3: Edge-Frequency (no Priority 2 errors = archetype-frequency mismatch)
        frequency_errors = [e for e in validation_errors if "Priority 2" in e or "Edge-Frequency" in e]
        edge_frequency = 1.0 if not frequency_errors else 0.0

        # Dimension 4: Diversification (inverse of max weight, 0-1 scale)
        if strategy.weights:
            # Handle both dict and WeightsDict types
            weights_dict = dict(strategy.weights) if hasattr(strategy.weights, 'items') else strategy.weights
            max_weight = max(weights_dict.values())
            # Convert max_weight to 0-1 scale: 100% concentration = 0, equal-weight = high score
            # Formula: 1 - max_weight (so 0.25 → 0.75, 0.50 → 0.50, 1.0 → 0.0)
            diversification = 1.0 - max_weight
        else:
            diversification = 0.5  # Neutral if no weights (dynamic strategy)

        # Dimension 5: Syntax (no syntax errors)
        syntax_errors = [e for e in validation_errors if "Syntax Error" in e]
        syntax = 1.0 if not syntax_errors else 0.0

        return QualityScore(
            quantification=quantification,
            coherence=coherence,
            edge_frequency=edge_frequency,
            diversification=diversification,
            syntax=syntax
        )

    def _create_fix_prompt(self, candidates: List[Strategy], validation_errors: List[str]) -> str:
        """
        Create targeted fix prompt from validation errors.

        Args:
            candidates: Original candidates with validation errors
            validation_errors: List of validation error messages

        Returns:
            Prompt string with specific fix instructions
        """
        fix_prompt = "# SURGICAL VALIDATION FIX - PRESERVE STRUCTURE\n\n"

        # NEW: Show concrete original values in code blocks
        fix_prompt += "## 📋 ORIGINAL VALUES (COPY EXACTLY - IMMUTABLE)\n\n"
        fix_prompt += "**The values below are from your original generation. You MUST copy them EXACTLY into your fixed response.**\n\n"

        for i, strategy in enumerate(candidates, 1):
            fix_prompt += f"### Candidate #{i}: {strategy.name}\n"
            fix_prompt += "```python\n"
            fix_prompt += f"assets = {strategy.assets}  # ❌ IMMUTABLE - Copy exactly\n"
            fix_prompt += f"weights = {dict(strategy.weights)}  # ❌ KEYS IMMUTABLE - Keys must match assets\n"
            fix_prompt += f"name = \"{strategy.name}\"  # ❌ IMMUTABLE - Copy exactly\n"
            fix_prompt += f"edge_type = EdgeType.{strategy.edge_type.name}  # ❌ IMMUTABLE - Copy exactly\n"
            fix_prompt += f"archetype = StrategyArchetype.{strategy.archetype.name}  # ❌ IMMUTABLE - Copy exactly\n"
            fix_prompt += f"rebalance_frequency = RebalanceFrequency.{strategy.rebalance_frequency.name}  # ⚠️ Can change ONLY if archetype-frequency mismatch\n"
            logic_tree_desc = "empty {{}}" if not strategy.logic_tree else "populated dict"
            fix_prompt += f"logic_tree = {logic_tree_desc}  # ❌ STRUCTURE IMMUTABLE - Empty stays empty, populated stays populated\n"
            fix_prompt += "```\n\n"

        fix_prompt += "**⚠️ CRITICAL INSTRUCTION:**\n"
        fix_prompt += "When fixing validation errors, COPY the immutable values above EXACTLY into your response.\n"
        fix_prompt += "Only modify these fields:\n"
        fix_prompt += "- ✅ **thesis_document**: Reword to fix coherence issues\n"
        fix_prompt += "- ✅ **rebalancing_rationale**: Add missing explanations\n"
        fix_prompt += "- ✅ **rebalance_frequency**: Change ONLY if archetype-frequency mismatch error\n\n"

        fix_prompt += "## ⚠️ CRITICAL: PRESERVE THESE FIELDS (DO NOT MODIFY)\n"
        fix_prompt += "**These fields MUST remain EXACTLY as shown in ORIGINAL VALUES above:**\n"
        fix_prompt += "- **assets**: MUST preserve EXACT list (same tickers, same order)\n"
        fix_prompt += "- **weights**: MUST preserve EXACT dict keys (same assets as keys)\n"
        fix_prompt += "- **name**: MUST preserve EXACT string\n"
        fix_prompt += "- **edge_type**: MUST preserve EXACT enum value\n"
        fix_prompt += "- **archetype**: MUST preserve EXACT enum value\n"
        fix_prompt += "- **logic_tree structure**: If originally empty {}, MUST stay empty. "
        fix_prompt += "If originally populated, preserve structure\n\n"
        fix_prompt += "**❌ EXAMPLE VIOLATIONS (DO NOT DO THIS):**\n"
        fix_prompt += "- ❌ Changing ['VYM', 'SCHD', 'NOBL'] to ['VYM', 'SCHD', 'JEPI']  # FORBIDDEN\n"
        fix_prompt += "- ❌ Changing name from 'Strategy A' to 'Improved Strategy A'  # FORBIDDEN\n"
        fix_prompt += "- ❌ Changing EdgeType.STRUCTURAL to EdgeType.BEHAVIORAL  # FORBIDDEN\n"
        fix_prompt += "- ❌ Populating empty logic_tree {{}}  # FORBIDDEN (unless validation explicitly requires it)\n\n"
        fix_prompt += "**✅ VALIDATION ENFORCEMENT:**\n"
        fix_prompt += "After this fix, programmatic checks will verify ALL immutable fields unchanged.\n"
        fix_prompt += "Any modification to structural fields will cause immediate failure with specific error message.\n\n"

        fix_prompt += f"## 🐛 VALIDATION ERRORS TO FIX ({len(validation_errors)}):\n\n"

        for idx, error in enumerate(validation_errors, 1):
            fix_prompt += f"{idx}. {error}\n"

        fix_prompt += "\n## ✅ FIX STRATEGY (MANDATORY):\n\n"
        fix_prompt += "For each error above:\n"
        fix_prompt += "1. **Read the error** - Understand what's wrong\n"
        fix_prompt += "2. **Identify the TEXT field** - Which field needs fixing (thesis/rationale/frequency)?\n"
        fix_prompt += "3. **Fix ONLY that field** - Modify thesis/rationale text or change frequency enum\n"
        fix_prompt += "4. **Copy structural fields** - Copy assets/weights/name/edge_type/archetype EXACTLY from ORIGINAL VALUES\n"
        fix_prompt += "5. **Return complete list** - Return all 5 candidates with errors fixed\n\n"
        fix_prompt += "**Examples:**\n"
        fix_prompt += "- Error: 'Thesis describes conditional logic but logic_tree empty'\n"
        fix_prompt += "  ✅ CORRECT FIX: Reword thesis to remove conditional keywords (keep logic_tree {{}})\n"
        fix_prompt += "  ❌ WRONG FIX: Populate logic_tree with conditions\n\n"
        fix_prompt += "- Error: 'Momentum archetype with quarterly rebalancing too slow'\n"
        fix_prompt += "  ✅ CORRECT FIX: Change rebalance_frequency to WEEKLY or MONTHLY\n"
        fix_prompt += "  ❌ WRONG FIX: Change assets or archetype\n\n"
        fix_prompt += "Return the CORRECTED List[Strategy] with all validation errors fixed and structural fields preserved.\n"

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
        fix_prompt = self._create_fix_prompt(candidates, validation_errors)

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

                # Check rebalance_frequency preserved (allow change only if archetype-frequency mismatch)
                if fixed.rebalance_frequency != original.rebalance_frequency:
                    # Check if validation explicitly mentioned frequency mismatch for this candidate
                    frequency_error_exists = any(
                        original.name in error and
                        ("archetype-frequency" in error.lower() or
                         "rebalance_frequency" in error.lower() or
                         "rebalancing" in error.lower())
                        for error in validation_errors
                    )
                    if not frequency_error_exists:
                        raise ValueError(
                            f"Retry modified rebalance_frequency for candidate {i+1} ({original.name}): "
                            f"{original.rebalance_frequency} → {fixed.rebalance_frequency}. "
                            f"Frequency must be preserved unless archetype-frequency mismatch error exists."
                        )

                # Check edge_type preserved
                if fixed.edge_type != original.edge_type:
                    raise ValueError(
                        f"Retry modified edge_type for candidate {i+1} ({original.name}): "
                        f"{original.edge_type} → {fixed.edge_type}. "
                        f"Edge type must be preserved exactly."
                    )

                # Check archetype preserved
                if fixed.archetype != original.archetype:
                    raise ValueError(
                        f"Retry modified archetype for candidate {i+1} ({original.name}): "
                        f"{original.archetype} → {fixed.archetype}. "
                        f"Archetype must be preserved exactly."
                    )

                # Check name preserved
                if fixed.name != original.name:
                    raise ValueError(
                        f"Retry modified name for candidate {i+1} ({original.name}): "
                        f"\"{original.name}\" → \"{fixed.name}\". "
                        f"Strategy name must be preserved exactly."
                    )

                # Check logic_tree structure preserved (empty stays empty, populated stays populated)
                original_has_logic = bool(original.logic_tree)
                fixed_has_logic = bool(fixed.logic_tree)
                if original_has_logic != fixed_has_logic:
                    raise ValueError(
                        f"Retry modified logic_tree structure for candidate {i+1} ({original.name}): "
                        f"{'populated' if original_has_logic else 'empty'} → {'populated' if fixed_has_logic else 'empty'}. "
                        f"Logic tree structure (empty vs populated) must be preserved."
                    )

            print("✓ Data integrity validated - all immutable fields preserved")
            return fixed_candidates
        except Exception as e:
            print(f"✗ Retry failed: {e}")
            print("  Returning original candidates (with validation warnings)")
            return candidates
