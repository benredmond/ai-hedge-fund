"""Generate 5 candidate strategies using AI via parallel prompts."""

from typing import List, Dict, Literal, TypedDict
import asyncio
import json
import os
import re
from dataclasses import dataclass
from pydantic_ai import ModelSettings
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    is_reasoning_model,
    get_model_settings,
)
from src.agent.models import Strategy, CandidateList, SingleStrategy, ConcentrationIntent


class PromptVariation(TypedDict):
    """Configuration for a single candidate generation prompt."""
    name: str
    emphasis: str
    persona: str
    constraint: str


# 5 distinct prompt variations to seed different reasoning paths
# Each variation produces one candidate; run in parallel for diversity
PROMPT_VARIATIONS: List[PromptVariation] = [
    {
        "name": "macro_regime",
        "emphasis": "macroeconomic regime shifts and rate cycle positioning",
        "persona": "You are a macro strategist who sees markets through the lens of Fed policy, yield curves, and economic cycles.",
        "constraint": "Your strategy must explicitly position for macro uncertainty or regime transitions."
    },
    {
        "name": "factor_quant",
        "emphasis": "systematic factor premiums (value, momentum, quality, size)",
        "persona": "You are a quantitative researcher who believes in harvesting persistent factor premiums.",
        "constraint": "Use systematic factor exposure as the primary driver, not discretionary picks."
    },
    {
        "name": "tail_risk",
        "emphasis": "downside protection and asymmetric payoffs",
        "persona": "You are a risk manager who prioritizes capital preservation over upside capture.",
        "constraint": "Maximum drawdown management must be the primary design consideration."
    },
    {
        "name": "sector_rotation",
        "emphasis": "sector leadership shifts and relative strength",
        "persona": "You are a sector analyst who exploits rotation patterns and leadership changes.",
        "constraint": "Sector allocation must be the primary active decision, not individual stocks."
    },
    {
        "name": "trend_follower",
        "emphasis": "price momentum across asset classes and timeframes",
        "persona": "You are a trend follower who believes price is the ultimate arbiter of value.",
        "constraint": "All position decisions must be derived from price action, not fundamentals."
    },
]
from src.agent.token_tracker import TokenTracker
from src.agent.config.leverage import (
    APPROVED_2X_ETFS,
    APPROVED_3X_ETFS,
    ALL_LEVERAGED_ETFS,
    detect_leverage,
    get_drawdown_bounds,
    get_decay_cost_range,
)
from src.agent.validators import BenchmarkValidator, CostValidator


# Pre-compiled regex patterns for validation (performance optimization)
_DECAY_NUMBER_PATTERN = re.compile(
    r'\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?%?\s*(?:annual|yearly|per year|decay)'
)
_DRAWDOWN_PATTERN = re.compile(r'(\d+)%?\s*(?:drawdown|dd|decline|loss)')
_EXIT_SPECIFIC_PATTERN = re.compile(r'(?:exit|rotate|stop).*(?:if|when|vix >|momentum <)')

# Threshold hygiene patterns - detect magic numbers vs relative thresholds
# Absolute price threshold: VIXY_price > 20 or 20 < VIXY_price
_ABSOLUTE_PRICE_THRESHOLD = re.compile(
    r'(\d+(?:\.\d+)?)\s*[><]=?\s*\w+_price|'  # 20 < VIXY_price
    r'\w+_price\s*[><]=?\s*(\d+(?:\.\d+)?)',   # VIXY_price > 20
    re.IGNORECASE
)

# Arbitrary return threshold: cumulative_return > 0.05 (non-zero)
_ARBITRARY_RETURN_THRESHOLD = re.compile(
    r'_cumulative_return_\d+d\s*[><]=?\s*(-?0?\.\d*[1-9]|-?[1-9]\d*(?:\.\d+)?)|'  # return > 0.05
    r'(-?0?\.\d*[1-9]|-?[1-9]\d*(?:\.\d+)?)\s*[><]=?\s*\w+_cumulative_return',    # 0.05 < return
    re.IGNORECASE
)

# Valid relative patterns (whitelist)
_VALID_RELATIVE_PATTERNS = [
    # Price vs own moving average: SPY_price > SPY_200d_MA
    re.compile(r'([A-Z]+)_price\s*[><]=?\s*\1_(?:EMA_)?\d+d_MA', re.IGNORECASE),
    # Cross-asset comparison: XLK_cumulative_return_30d > XLF_cumulative_return_30d
    re.compile(r'([A-Z]+)_\w+\s*[><]=?\s*([A-Z]+)_\w+', re.IGNORECASE),
    # Zero-bounded return: cumulative_return_30d > 0
    re.compile(r'_cumulative_return_\d+d\s*[><]=?\s*0(?:\.0*)?\s*(?:\)|$|and|or|\s)', re.IGNORECASE),
    # RSI with standard thresholds: RSI_14d > 70
    re.compile(r'_RSI_\d+d\s*[><]=?\s*(20|25|30|35|65|70|75|80)', re.IGNORECASE),
]


def extract_and_log_reasoning(result, stage_name: str) -> bool:
    """
    Extract and log full reasoning content from reasoning models (Kimi K2, DeepSeek R1, etc).

    Kimi K2 implementation:
    - Reasoning is in `reasoning_content` field on ChatCompletionMessage
    - Must use hasattr() + getattr() (OpenAI SDK doesn't expose it directly)
    - Field is at same level as `content` field

    Args:
        result: RunResult from agent.run()
        stage_name: Stage identifier for logging (e.g., "CandidateGenerator")

    Returns:
        True if reasoning content was found and logged, False otherwise
    """
    try:
        # Method 1: Access via pydantic-ai result._result (underlying model response)
        if hasattr(result, '_result') and hasattr(result._result, 'choices'):
            message = result._result.choices[0].message

            # Check for reasoning_content (Kimi K2, DeepSeek R1 format)
            if hasattr(message, 'reasoning_content'):
                reasoning = getattr(message, 'reasoning_content', None)
                if reasoning:
                    print(f"\n{'='*80}")
                    print(f"[DEBUG:{stage_name}] REASONING CONTENT")
                    print(f"[DEBUG:{stage_name}] Length: {len(reasoning)} chars")
                    print(f"{'='*80}")
                    print(reasoning)  # FULL content, NOT truncated
                    print(f"{'='*80}\n")
                    return True

        # Method 2: Check result.choices directly (for compatibility)
        if hasattr(result, 'choices') and result.choices:
            message = result.choices[0].message
            if hasattr(message, 'reasoning_content'):
                reasoning = getattr(message, 'reasoning_content', None)
                if reasoning:
                    print(f"\n{'='*80}")
                    print(f"[DEBUG:{stage_name}] REASONING CONTENT")
                    print(f"[DEBUG:{stage_name}] Length: {len(reasoning)} chars")
                    print(f"{'='*80}")
                    print(reasoning)  # FULL content
                    print(f"{'='*80}\n")
                    return True

        # No reasoning content found (not an error - just means model doesn't produce it)
        return False

    except Exception as e:
        print(f"[DEBUG:{stage_name}] Error extracting reasoning: {e}")
        return False


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

    def _detect_provider(self, model: str) -> Literal["kimi", "openai", "anthropic", "deepseek", "other"]:
        """
        Detect LLM provider from model string.

        Args:
            model: Model identifier (e.g., "openai:gpt-4o", "openai:kimi-k2-0905-preview")

        Returns:
            Provider identifier for provider-specific handling
        """
        model_lower = model.lower()

        # Kimi/Moonshot models
        if "kimi" in model_lower or "moonshot" in model_lower:
            return "kimi"

        # DeepSeek models
        if "deepseek" in model_lower:
            return "deepseek"

        # Anthropic models
        if "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"

        # OpenAI models (default for openai: prefix)
        if "gpt" in model_lower or model_lower.startswith("openai:"):
            return "openai"

        return "other"

    def _enhance_count_instruction(self, prompt: str, provider: str) -> str:
        """
        Add provider-specific count enforcement to generation prompt.

        All providers benefit from explicit count instructions to reliably
        generate the correct number of candidates.

        Args:
            prompt: Original generation prompt
            provider: Provider identifier from _detect_provider()

        Returns:
            Enhanced prompt with provider-specific count enforcement
        """
        # Universal count emphasis - positioned after the opening requirement
        # This applies to ALL providers since count failures are common
        count_emphasis = """
**🚨 CRITICAL: EXACTLY 5 STRATEGIES REQUIRED 🚨**

Your output MUST be a Python list with exactly 5 Strategy objects:

```
[
    Strategy(...),  # Strategy #1
    Strategy(...),  # Strategy #2
    Strategy(...),  # Strategy #3
    Strategy(...),  # Strategy #4
    Strategy(...),  # Strategy #5
]
```

Common failure mode: Generating only 1-3 strategies then stopping.
DO NOT STOP until you have generated all 5.

"""
        # Provider-specific additional guidance
        if provider == "kimi":
            count_emphasis += """
**Kimi K2 Specific:** You tend to generate fewer than 5.
Force yourself: After Strategy #3, keep going to #4 and #5.
Count before submitting: 1, 2, 3, 4, 5 = ✓

"""
        elif provider == "deepseek":
            count_emphasis += """
**DeepSeek Specific:** Ensure your reasoning produces exactly 5 diverse strategies.
Use different archetypes for each: Momentum, Mean Reversion, Carry, Volatility, Multi-factor.

"""

        # Insert after the opening OUTPUT REQUIREMENT section (after first ---)
        # Find the first --- separator and insert after it
        if "---" in prompt:
            parts = prompt.split("---", 1)
            if len(parts) == 2:
                return parts[0] + "---\n" + count_emphasis + parts[1]

        # Fallback: insert at beginning
        return count_emphasis + prompt

    async def generate(
        self,
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> List[Strategy]:
        """
        Generate 4-5 distinct candidate strategies via parallel prompts.

        Uses 5 parallel prompts with different emphases/personas to seed
        diverse reasoning paths. Minimum 4 candidates required.

        Args:
            market_context: Comprehensive market context pack with:
                - Macro indicators (FRED data)
                - Market regime (trend, volatility, breadth, leadership)
                - Sector performance and factor premiums
                - Manual Composer pattern examples (curated)
                - Recent market events
            model: LLM model identifier

        Returns:
            List of 4-5 Strategy objects

        Raises:
            ValueError: If <4 candidates or duplicates detected
        """
        # Load prompts for parallel single-candidate generation
        # System prompt for single-candidate generation (parallel mode)
        system_prompt = load_prompt("system/candidate_generation_system.md")
        # Single-candidate recipe prompt with {placeholders}
        recipe_prompt = load_prompt("candidate_generation.md")

        # Generate candidates via parallel prompts
        print("Generating candidate strategies (parallel mode)...")
        print(f"  Launching {len(PROMPT_VARIATIONS)} parallel generation tasks...")
        candidates = await self._generate_candidates_parallel(
            market_context, system_prompt, recipe_prompt, model
        )
        print(f"✓ Generated {len(candidates)} candidates")

        # Log candidate details
        for i, c in enumerate(candidates, 1):
            weights_str = ", ".join(f"{k}:{v:.0%}" for k, v in c.weights.items()) if c.weights else "dynamic"
            logic_status = "conditional" if c.logic_tree else "static"
            print(f"  [{i}] {c.name}")
            print(f"      Assets: {', '.join(c.assets)}")
            print(f"      Weights: {weights_str} | Rebalance: {c.rebalance_frequency} | {logic_status}")

        # Validate minimum count
        MIN_CANDIDATES = 5
        if len(candidates) < MIN_CANDIDATES:
            raise ValueError(
                f"Expected at least {MIN_CANDIDATES} candidates, got {len(candidates)}. "
                f"Too many generation failures."
            )

        # Check diversity (warn but don't fail)
        is_diverse, diversity_issues = self._check_diversity(candidates)
        if not is_diverse:
            print(f"\n[WARNING] Diversity check failed:")
            for issue in diversity_issues:
                print(f"  - {issue}")
            print("  Proceeding with candidates (diversity is recommended, not required)")

        # Check for duplicates (simple ticker comparison)
        ticker_sets = [set(c.assets) for c in candidates]
        unique_ticker_sets = set(tuple(sorted(ts)) for ts in ticker_sets)
        if len(ticker_sets) != len(unique_ticker_sets):
            raise ValueError("Duplicate candidates detected (same ticker sets)")

        return candidates

    async def _generate_candidates_parallel(
        self,
        market_context: dict,
        system_prompt: str,
        recipe_prompt: str,
        model: str,
    ) -> List[Strategy]:
        """
        Generate candidates via 5 parallel prompts with distinct emphases.

        Each variation (macro, factor, tail_risk, sector, trend) generates
        one candidate independently. Failed variations are retried up to 2x.
        Minimum 4 successful candidates required.

        Args:
            market_context: Comprehensive market context pack
            system_prompt: System-level prompt with schemas and constraints
            recipe_prompt: Single-candidate recipe template with {placeholders}
            model: LLM model identifier

        Returns:
            List of 4-5 Strategy objects
        """
        # Create generation tasks for all 5 variations
        tasks = [
            self._generate_single_candidate(
                market_context=market_context,
                system_prompt=system_prompt,
                recipe_prompt=recipe_prompt,
                variation=variation,
                model=model,
            )
            for variation in PROMPT_VARIATIONS
        ]

        # Execute all 5 in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful candidates and track failures
        candidates: List[Strategy] = []
        failures: List[tuple[PromptVariation, Exception]] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failures.append((PROMPT_VARIATIONS[i], result))
                print(f"  [{PROMPT_VARIATIONS[i]['name']}] ✗ Failed: {type(result).__name__}: {result}")
            else:
                candidates.append(result)

        print(f"\n  Initial results: {len(candidates)} succeeded, {len(failures)} failed")

        # Retry failed variations (up to 2x each)
        if failures:
            print(f"\n  Retrying {len(failures)} failed variation(s)...")
            for variation, original_error in failures:
                success = False
                for attempt in range(2):
                    try:
                        print(f"    [{variation['name']}] Retry attempt {attempt + 1}/2...")
                        candidate = await self._generate_single_candidate(
                            market_context=market_context,
                            system_prompt=system_prompt,
                            recipe_prompt=recipe_prompt,
                            variation=variation,
                            model=model,
                        )
                        candidates.append(candidate)
                        success = True
                        print(f"    [{variation['name']}] ✓ Retry succeeded")
                        break
                    except Exception as retry_error:
                        print(f"    [{variation['name']}] Retry {attempt + 1} failed: {retry_error}")

                if not success:
                    print(f"    [{variation['name']}] ✗ All retries exhausted")

        # Run semantic validation on each candidate
        print(f"\n  Validating {len(candidates)} candidates...")
        validated_candidates = []
        for candidate in candidates:
            errors = self._validate_semantics([candidate], market_context)
            if errors:
                # Filter for syntax errors only (retryable)
                syntax_errors = [e for e in errors if "Syntax Error" in e]
                if syntax_errors:
                    print(f"    [{candidate.name[:30]}...] ⚠️ Syntax errors (non-blocking): {len(syntax_errors)}")
                else:
                    print(f"    [{candidate.name[:30]}...] ⚠️ Quality warnings: {len(errors)}")
            else:
                print(f"    [{candidate.name[:30]}...] ✓ Validation passed")
            # Accept all candidates regardless of validation (quality warnings are informational)
            validated_candidates.append(candidate)

        return validated_candidates

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
        # Get model-specific settings (reasoning models require temperature=1.0, max_tokens=16384)
        # Fix for Pydantic AI bug #1429: parallel_tool_calls=False prevents LLM from calling
        # final_result multiple times. See: https://github.com/pydantic/pydantic-ai/issues/1429
        model_settings = get_model_settings(model, stage="candidate_generation")

        # Create agent with all tools available (but usage optional)
        agent_ctx = await create_agent(
            model=model,
            output_type=CandidateList,  # Wrapper enforces exactly 5 via JSON schema
            system_prompt=system_prompt,
            include_composer=False,  # Candidate generation uses FRED/yfinance only
            model_settings=model_settings
        )

        async with agent_ctx as agent:
            market_context_json = json.dumps(market_context, indent=2)

            generate_prompt = f"""**🎯 OUTPUT REQUIREMENT: EXACTLY 5 STRATEGIES**

You MUST return a List[Strategy] containing EXACTLY 5 Strategy objects.
Not 1. Not 3. Not 4. Exactly 5.

Before finalizing, count: Strategy #1 ✓, Strategy #2 ✓, Strategy #3 ✓, Strategy #4 ✓, Strategy #5 ✓

---

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

5. **Concentration Intent** (set when intentionally concentrated):
   - `DIVERSIFIED` (default): Standard diversification (≥3 assets, no asset >40%, no sector >75%)
   - `HIGH_CONVICTION`: Few assets (<3) with high confidence
     Example: {{AAPL: 0.50, MSFT: 0.50}} - Two stocks from deep research
   - `CORE_SATELLITE`: Large core position (>40%) + smaller satellites
     Example: {{SPY: 0.50, XLK: 0.20, XLF: 0.15, XLE: 0.15}} - SPY core + sector tilts
   - `BARBELL`: Extreme positions at both ends (risk-on + risk-off)
     Example: {{TQQQ: 0.50, TLT: 0.50}} - Aggressive growth + defensive bonds
   - `SECTOR_FOCUS`: Intentional single-sector concentration (>75% one sector)
     Example: {{JPM: 0.30, BAC: 0.25, WFC: 0.25, C: 0.20}} - All financials

   Set concentration_intent when your strategy *intentionally* violates diversification guidelines:
   - Single asset >40% → CORE_SATELLITE or BARBELL
   - <3 assets → HIGH_CONVICTION or BARBELL
   - >75% in one sector → SECTOR_FOCUS

**CRITICAL FIELD ORDERING:**
Generate thesis_document FIRST for each strategy (before name, assets, weights).
This enables chain-of-thought reasoning before committing to execution details.

**CRITICAL logic_tree STRUCTURE:**

**FOR STATIC STRATEGIES (no conditional logic):**
```python
logic_tree={{}}  # Empty dict - weights field defines fixed allocation
```

**FOR CONDITIONAL STRATEGIES (dynamic allocation based on conditions):**
You MUST use this EXACT nested structure with these EXACT keys:
```python
logic_tree={{
  "condition": "SPY_price > SPY_200d_MA",  # Relative trend condition (REQUIRED)
  "if_true": {{              # Dict with allocation when condition is TRUE (REQUIRED)
    "assets": ["TLT", "GLD"],
    "weights": {{"TLT": 0.5, "GLD": 0.5}}
  }},
  "if_false": {{             # Dict with allocation when condition is FALSE (REQUIRED)
    "assets": ["SPY", "QQQ"],
    "weights": {{"SPY": 0.6, "QQQ": 0.4}}
  }}
}}
```

**❌ WRONG - DO NOT GENERATE FLAT PARAMETER DICTS:**
```python
# THIS IS WRONG - flat dict with arbitrary parameters
logic_tree={{"momentum_threshold": 0.15, "vix_level": 22, "reversion_window": 20}}  # ❌ WRONG!
```

**✅ CORRECT - Nested conditional structure OR empty dict:**
```python
# Option A: Static strategy (most strategies)
logic_tree={{}}  # ✅ CORRECT for static allocation

# Option B: Conditional strategy
logic_tree={{"condition": "...", "if_true": {{...}}, "if_false": {{...}}}}  # ✅ CORRECT
```

The logic_tree field is for CONDITIONAL ALLOCATION LOGIC ONLY, not for storing strategy parameters.
If your strategy doesn't switch allocations based on conditions, use logic_tree={{}}.

**IMPORTANT:**
- Primary data source: Context pack above
- Tool usage: Optional, only for gaps in context pack
- Citation: Reference context pack data (e.g., "VIX 18.6 per context pack")
- Diversity: Essential - explore possibility space, don't optimize for single approach

**⚠️ FINAL COUNT VERIFICATION (MANDATORY):**

Before returning your output, verify:
- [ ] Strategy #1 exists with complete thesis_document
- [ ] Strategy #2 exists with complete thesis_document
- [ ] Strategy #3 exists with complete thesis_document
- [ ] Strategy #4 exists with complete thesis_document
- [ ] Strategy #5 exists with complete thesis_document
- [ ] Total count = 5 (not fewer, not more)

Return all 5 candidates together in a single List[Strategy] containing exactly 5 Strategy objects.
"""

            # Enhance prompt with provider-specific count enforcement
            provider = self._detect_provider(model)
            generate_prompt = self._enhance_count_instruction(generate_prompt, provider)

            # Track token usage before API call
            tracker.estimate_prompt(
                label="Candidate Generation",
                system_prompt=system_prompt,
                user_prompt=generate_prompt,
                tool_definitions_est=8000,  # Estimate for all MCP tools (optional usage)
                notes="Single-phase generation with optional tool usage"
            )

            # Debug logging: Print prompt being sent to LLM provider
            print(f"\n{'='*80}")
            print(f"[DEBUG:CandidateGenerator] Sending prompt to LLM provider")
            print(f"[DEBUG:CandidateGenerator] System prompt length: {len(system_prompt)} chars")
            print(f"[DEBUG:CandidateGenerator] User prompt length: {len(generate_prompt)} chars")
            print(f"{'='*80}")
            if os.getenv("DEBUG_PROMPTS", "0") == "1":
                print(f"\n[DEBUG:CandidateGenerator] ========== FULL SYSTEM PROMPT ==========")
                print(system_prompt)
                print(f"[DEBUG:CandidateGenerator] ========================================")
                print(f"\n[DEBUG:CandidateGenerator] ========== FULL USER PROMPT ==========")
                print(generate_prompt)
                print(f"[DEBUG:CandidateGenerator] ======================================")
                print(f"{'='*80}\n")

            result = await agent.run(generate_prompt)

            # Extract and log full reasoning content (Kimi K2, DeepSeek R1, etc.)
            extract_and_log_reasoning(result, "CandidateGenerator")

            # Debug logging: Print full LLM response
            print(f"\n[DEBUG:CandidateGenerator] Full LLM response:")
            print(f"{result.output}")

            # Post-generation validation (Fix #1: Post-validation retry)
            # Extract strategies from CandidateList wrapper
            candidates = result.output.strategies

            # Pre-semantic count validation: Fail fast on wrong count before expensive validation
            EXPECTED_CANDIDATE_COUNT = 5
            if len(candidates) != EXPECTED_CANDIDATE_COUNT:
                # Provider-specific guidance for count errors
                provider_guidance = ""
                if provider == "kimi":
                    provider_guidance = (
                        "\n\nKimi K2 Reminder: You need to return a Python list with exactly 5 Strategy objects. "
                        "Count your strategies: Strategy #1, Strategy #2, Strategy #3, Strategy #4, Strategy #5. "
                        "Verify the list length before submitting."
                    )
                elif provider == "deepseek":
                    provider_guidance = (
                        "\n\nDeepSeek Reminder: Ensure your final output is List[Strategy] containing exactly 5 items. "
                        "Use diverse archetypes across all 5 candidates."
                    )

                count_error = (
                    f"Syntax Error: Generated {len(candidates)} candidates, expected {EXPECTED_CANDIDATE_COUNT}. "
                    f"You MUST return exactly {EXPECTED_CANDIDATE_COUNT} Strategy objects in a single List[Strategy]. "
                    f"This is a hard requirement. Please generate {EXPECTED_CANDIDATE_COUNT - len(candidates)} more "
                    f"{'candidate' if EXPECTED_CANDIDATE_COUNT - len(candidates) == 1 else 'candidates'} to reach the required count."
                    f"{provider_guidance}"
                )
                # Trigger retry with count-specific error
                validation_errors = [count_error]
            else:
                # Only run expensive semantic validation if count is correct
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

                # Only retry on SYNTAX errors - non-syntax failures are subjective quality
                # issues that may not improve with retry (coherence, quantification, etc.)
                syntax_errors = [e for e in validation_errors if "Syntax Error" in e]

                if syntax_errors:
                    # Determine retry intensity based on quality (for logging)
                    if avg_quality < 0.4:
                        print("\n[RETRY INTENSITY] Low quality detected (<0.4) - providing detailed prescriptive guidance")
                    elif avg_quality < 0.6:
                        print("\n[RETRY INTENSITY] Moderate quality (0.4-0.6) - providing specific dimension feedback")
                    else:
                        print("\n[RETRY INTENSITY] Minor issues (>0.6) - providing targeted fixes only")

                    print(f"\n[RETRY] Found {len(syntax_errors)} syntax error(s) - attempting targeted fixes...")
                    fixed_candidates = await self._retry_failed_strategies(
                        candidates, syntax_errors, agent, market_context_json, tracker
                    )
                    return fixed_candidates
                else:
                    print("\n[NO RETRY] No syntax errors found - accepting candidates with quality warnings")

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

            # NEW: Run archetype-logic_tree coherence validation
            archetype_errors = self._validate_archetype_logic_tree(strategy, idx)
            errors.extend(archetype_errors)

            # NEW: Run thesis-logic_tree value coherence validation
            thesis_coherence_errors = self._validate_thesis_logic_tree_coherence(strategy, idx)
            errors.extend(thesis_coherence_errors)

            # NEW: Run weight derivation coherence validation
            weight_derivation_errors = self._validate_weight_derivation_coherence(strategy, idx)
            errors.extend(weight_derivation_errors)

            # NEW: Run VIXY usage validation (requires volatility justification)
            vixy_alignment_errors = self._validate_vixy_thesis_alignment(strategy, idx)
            errors.extend(vixy_alignment_errors)

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
                    f"Syntax Error: {strategy.name} - Thesis describes conditional logic "
                    f"(matched patterns: {matched_keywords[:3]}), but logic_tree is empty. "
                    f"PREFERRED FIX: Remove conditional language from thesis (keep static allocation). "
                    f"Alternative: Populate logic_tree with condition/if_true/if_false structure."
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

        # Professional validation features (controlled by feature flag)
        if os.getenv("ENABLE_PROFESSIONAL_VALIDATION", "true").lower() == "true":
            benchmark_validator = BenchmarkValidator()
            cost_validator = CostValidator()

            for strategy in candidates:
                # Benchmark comparison validation (Priority 3)
                benchmark_errors = benchmark_validator.validate(strategy)
                errors.extend(benchmark_errors)

                # Execution cost validation (Priority 3, high-frequency only)
                cost_errors = cost_validator.validate(strategy)
                errors.extend(cost_errors)

        return errors

    def _validate_archetype_logic_tree(self, strategy: Strategy, idx: int) -> List[str]:
        """
        Validate that archetypes requiring dynamic behavior have logic_tree.

        Momentum and volatility archetypes typically require conditional logic
        to implement properly. This catches cases where thesis describes rotation
        but implementation is static.

        Args:
            strategy: Strategy to validate
            idx: Candidate index (1-based) for error messages

        Returns:
            List of validation error messages
        """
        errors = []
        archetype_str = strategy.archetype.value.lower() if strategy.archetype else ""
        thesis_lower = strategy.thesis_document.lower()

        # Momentum archetype with rotation claims requires logic_tree
        if archetype_str == "momentum":
            rotation_patterns = [
                r'rotat\w*\s+to', r'rotat\w*\s+into', r'rotat\w*\s+toward',
                r'shift\s+allocation', r'reweight\s+based', r'dynamic\s+allocation'
            ]
            has_rotation_claim = any(re.search(p, thesis_lower) for p in rotation_patterns)
            if has_rotation_claim and not strategy.logic_tree:
                errors.append(
                    f"Priority 1 (Implementation-Thesis Mismatch): Candidate #{idx} ({strategy.name}): "
                    f"Momentum archetype with rotation claims in thesis but logic_tree is empty. "
                    f"Rotation requires conditional logic to implement. Either populate logic_tree "
                    f"with condition/if_true/if_false OR remove rotation language from thesis."
                )

        # Volatility archetype typically requires conditional logic
        if archetype_str == "volatility" and not strategy.logic_tree:
            errors.append(
                f"Priority 1 (Implementation-Thesis Mismatch): Candidate #{idx} ({strategy.name}): "
                f"Volatility archetype typically requires conditional logic_tree for regime response. "
                f"Add VIX-based or volatility-based conditions, or reconsider archetype choice."
            )

        return errors

    def _validate_thesis_logic_tree_coherence(self, strategy: Strategy, idx: int) -> List[str]:
        """
        Validate that thesis content MATCHES logic_tree implementation values.

        Checks numeric thresholds in thesis match logic_tree.condition within ±20% tolerance.
        This catches cases where thesis says "VIX > 25" but logic_tree has "VIX > 30".

        Args:
            strategy: Strategy to validate
            idx: Candidate index (1-based) for error messages

        Returns:
            List of validation error messages
        """
        errors = []
        thesis_lower = strategy.thesis_document.lower()

        # Only check if logic_tree is populated
        if not strategy.logic_tree:
            return errors

        # Extract VIX thresholds from thesis (e.g., "VIX > 25", "VIX exceeds 22", "vix above 20")
        vix_pattern = r'vix\s*(?:>|>=|exceeds?|above|crosses?|spikes?\s+(?:above|to|past))\s*(\d+(?:\.\d+)?)'
        thesis_vix_matches = re.findall(vix_pattern, thesis_lower)
        thesis_vix_thresholds = [float(v) for v in thesis_vix_matches]

        if thesis_vix_thresholds:
            # Extract VIX threshold from logic_tree condition
            condition = str(strategy.logic_tree.get("condition", "")).lower()
            logic_tree_vix_matches = re.findall(r'vix\s*[><=]+\s*(\d+(?:\.\d+)?)', condition)
            logic_tree_vix_thresholds = [float(v) for v in logic_tree_vix_matches]

            if logic_tree_vix_thresholds:
                # Check if ANY thesis threshold is within ±20% of ANY logic_tree threshold
                tolerance = 0.20
                thesis_val = thesis_vix_thresholds[0]  # Use first mentioned value
                logic_val = logic_tree_vix_thresholds[0]

                relative_diff = abs(thesis_val - logic_val) / thesis_val if thesis_val != 0 else 0

                if relative_diff > tolerance:
                    errors.append(
                        f"Priority 1 (Value Mismatch): Candidate #{idx} ({strategy.name}): "
                        f"Thesis mentions VIX threshold {thesis_val} but logic_tree condition "
                        f"uses {logic_val} (deviation: {relative_diff:.0%} > {tolerance:.0%} tolerance). "
                        f"Align thesis description with actual implementation values."
                    )

        return errors

    def _validate_weight_derivation_coherence(self, strategy: Strategy, idx: int) -> List[str]:
        """
        Validate that weight derivation claims match actual weights.

        Catches cases where thesis/rationale claims "momentum-weighted" allocation
        but weights are all round numbers that clearly weren't derived from momentum.

        Args:
            strategy: Strategy to validate
            idx: Candidate index (1-based) for error messages

        Returns:
            List of validation error messages
        """
        errors = []
        thesis_lower = strategy.thesis_document.lower()
        rationale_lower = strategy.rebalancing_rationale.lower()
        combined_text = thesis_lower + " " + rationale_lower

        # Check for momentum-weighted claims
        momentum_weight_patterns = [
            r'momentum[- ]?weighted', r'weighted\s+by\s+momentum',
            r'proportional\s+to\s+momentum', r'momentum[- ]?based\s+weight'
        ]
        has_momentum_weight_claim = any(re.search(p, combined_text) for p in momentum_weight_patterns)

        if has_momentum_weight_claim and strategy.weights:
            weights_list = list(strategy.weights.values())

            # Round numbers that suggest arbitrary assignment, not momentum derivation
            round_numbers = [0.20, 0.25, 0.30, 0.333, 0.334, 0.35, 0.40, 0.45, 0.50]

            all_round = all(
                any(abs(w - rn) < 0.01 for rn in round_numbers)
                for w in weights_list
            )

            if all_round and len(weights_list) >= 3:
                errors.append(
                    f"Priority 2 (Derivation Mismatch): Candidate #{idx} ({strategy.name}): "
                    f"Claims 'momentum-weighted' allocation but weights {weights_list} are all "
                    f"round numbers. Momentum weighting should produce non-round weights derived "
                    f"from actual momentum values (e.g., 0.54, 0.28, 0.18 from 4.09%, 2.1%, 1.5% momentum)."
                )

        return errors

    def _validate_concentration(self, strategy: Strategy) -> List[str]:
        """
        Validate concentration risk limits with numeric thresholds.

        Priority 4 (SUGGESTION - Non-Blocking): Warnings only, not hard rejects.

        Checks (skipped if concentration_intent is non-DIVERSIFIED):
        - Single asset concentration (max 40%)
        - Sector concentration (max 75%, 100% OK for stock selection with 4+ stocks)
        - Minimum asset count (min 3)

        Args:
            strategy: Strategy to validate

        Returns:
            List of concentration warning messages (Priority 4)
        """
        errors = []

        # Skip all concentration checks if intent signals intentional concentration
        if strategy.concentration_intent != ConcentrationIntent.DIVERSIFIED:
            return errors

        # Check 1: Single asset concentration
        if strategy.weights:
            weights_dict = dict(strategy.weights) if hasattr(strategy.weights, 'items') else strategy.weights
            max_weight = max(weights_dict.values())
            if max_weight > 0.40:
                max_asset = max(weights_dict, key=weights_dict.get)
                asset_count = len(strategy.assets)
                # Context-specific suggestion based on portfolio structure
                if asset_count <= 2:
                    suggestion = "BARBELL (two-position strategy) or HIGH_CONVICTION (focused bets)"
                elif asset_count == 3:
                    suggestion = "HIGH_CONVICTION (few high-confidence positions)"
                else:
                    suggestion = "CORE_SATELLITE (large core + smaller satellites)"
                errors.append(
                    f"Priority 4 (SUGGESTION): {strategy.name} - Single asset concentration high: "
                    f"{max_asset} = {max_weight:.0%} > 40% guideline. If intentional, set "
                    f"concentration_intent to {suggestion}."
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
                            f"{asset_count} assets. Set concentration_intent to SECTOR_FOCUS if intentional, "
                            f"or add more stocks (4+ stocks OK for stock selection strategies)."
                        )
        except Exception as e:
            print(f"[WARNING] Could not validate sector concentration for {strategy.name}: {e}")

        # Check 3: Minimum asset count
        if len(strategy.assets) < 3:
            asset_count = len(strategy.assets)
            # Context-specific suggestion based on asset count
            if asset_count == 2:
                suggestion = "BARBELL (two extreme positions) or HIGH_CONVICTION (two focused bets)"
            else:  # asset_count == 1
                suggestion = "HIGH_CONVICTION (single high-confidence position)"
            errors.append(
                f"Priority 4 (SUGGESTION): {strategy.name} - Low asset count ({asset_count} < 3). "
                f"If intentional, set concentration_intent to {suggestion}."
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

    def _extract_all_conditions(self, logic_tree: dict) -> List[str]:
        """
        Recursively extract all condition strings from nested logic_tree.

        Args:
            logic_tree: Logic tree dict (potentially nested)

        Returns:
            List of condition strings found at all levels
        """
        conditions = []
        if isinstance(logic_tree, dict):
            if "condition" in logic_tree and isinstance(logic_tree["condition"], str):
                conditions.append(logic_tree["condition"])
            for branch in ["if_true", "if_false"]:
                if branch in logic_tree and isinstance(logic_tree[branch], dict):
                    conditions.extend(self._extract_all_conditions(logic_tree[branch]))
        return conditions

    def _validate_threshold_hygiene(self, strategy: Strategy, idx: int) -> List[str]:
        """
        Validate that logic_tree conditions use relative thresholds, not magic numbers.

        Rejects absolute thresholds (VIXY_price > 20) in favor of relative patterns
        (VIXY_cumulative_return_5d > 0, SPY_price > SPY_200d_MA).

        Allowed patterns:
        - Price vs own MA: SPY_price > SPY_200d_MA
        - Cross-asset: XLK_return > XLF_return
        - Zero-bounded: cumulative_return_30d > 0
        - RSI standard: RSI_14d > 70 (bounded 0-100)

        Rejected patterns:
        - Absolute price: VIXY_price > 20
        - Arbitrary return: SPY_cumulative_return_30d > 0.05

        Args:
            strategy: Strategy to validate
            idx: Candidate index (1-based) for error messages

        Returns:
            List of Syntax Error messages (triggers retry)
        """
        errors = []

        if not strategy.logic_tree:
            return errors

        conditions = self._extract_all_conditions(strategy.logic_tree)

        for condition in conditions:
            # Split on 'and'/'or' to check each comparison independently
            comparisons = re.split(r'\s+(?:and|or)\s+', condition, flags=re.IGNORECASE)

            for comparison in comparisons:
                comparison = comparison.strip()
                if not comparison:
                    continue

                # Check if valid relative pattern (whitelist)
                is_valid = any(p.search(comparison) for p in _VALID_RELATIVE_PATTERNS)
                if is_valid:
                    continue

                # Check for violations (blacklist)
                if _ABSOLUTE_PRICE_THRESHOLD.search(comparison):
                    errors.append(
                        f"Syntax Error: {strategy.name} - condition '{comparison}' uses "
                        f"absolute price threshold (magic number). "
                        f"Use relative form: TICKER_price > TICKER_200d_MA or "
                        f"TICKER_cumulative_return_Nd > 0"
                    )
                elif _ARBITRARY_RETURN_THRESHOLD.search(comparison):
                    errors.append(
                        f"Syntax Error: {strategy.name} - condition '{comparison}' uses "
                        f"arbitrary return threshold (non-zero magic number). "
                        f"Use zero-bounded: > 0 or < 0"
                    )

        return errors

    def _validate_vixy_thesis_alignment(self, strategy: Strategy, idx: int) -> List[str]:
        """
        Validate that VIXY conditions are only used when volatility is central to the thesis.

        Requires volatility-related keywords in thesis_document or rebalancing_rationale
        when any logic_tree condition references VIXY.
        """
        errors = []

        if not strategy.logic_tree:
            return errors

        conditions = self._extract_all_conditions(strategy.logic_tree)
        vixy_count = sum(1 for condition in conditions if "vixy" in condition.lower())
        if vixy_count == 0:
            return errors

        combined_text = f"{strategy.thesis_document} {strategy.rebalancing_rationale}"
        keyword_patterns = [
            r"\bvix\b",
            r"\bvixy\b",
            r"\bvolatility\b",
            r"\bvol\s+regime\b",
            r"\bvol\s+spike\b",
        ]
        has_volatility_context = any(
            re.search(pattern, combined_text, re.IGNORECASE) for pattern in keyword_patterns
        )

        if not has_volatility_context:
            errors.append(
                f"Syntax Error: Candidate #{idx} ({strategy.name}): VIXY condition used "
                f"({vixy_count} occurrence{'s' if vixy_count != 1 else ''}) but thesis or "
                f"rebalancing rationale lacks volatility justification."
            )

        return errors

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
                    f"{unlisted}. PREFERRED FIX: Remove {unlisted} from logic_tree branches. "
                    f"Alternative: Add to assets (but assets are immutable during retry)."
                )

        # Check 5: Threshold hygiene - no magic numbers in conditions
        # Note: idx=0 since _validate_syntax is called per-strategy, not batch
        threshold_errors = self._validate_threshold_hygiene(strategy, 0)
        errors.extend(threshold_errors)

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

        # Add logic_tree schema guidance if any syntax errors mention logic_tree
        has_logic_tree_error = any("logic_tree" in error.lower() for error in validation_errors)
        if has_logic_tree_error:
            fix_prompt += "\n## 📐 LOGIC_TREE SCHEMA REFERENCE:\n\n"
            fix_prompt += "**Your logic_tree has structural issues. Here is the CORRECT schema:**\n\n"
            fix_prompt += "```python\n"
            fix_prompt += "# FOR STATIC STRATEGIES (no conditional logic):\n"
            fix_prompt += "logic_tree = {}  # Empty dict\n\n"
            fix_prompt += "# FOR CONDITIONAL STRATEGIES (if you need dynamic allocation):\n"
            fix_prompt += "logic_tree = {\n"
            fix_prompt += '  "condition": "SPY_price > SPY_200d_MA",  # Relative trend condition (REQUIRED)\n'
            fix_prompt += '  "if_true": {              # Allocation when TRUE (REQUIRED)\n'
            fix_prompt += '    "assets": ["TLT", "GLD"],\n'
            fix_prompt += '    "weights": {"TLT": 0.5, "GLD": 0.5}\n'
            fix_prompt += "  },\n"
            fix_prompt += '  "if_false": {             # Allocation when FALSE (REQUIRED)\n'
            fix_prompt += '    "assets": ["SPY", "QQQ"],\n'
            fix_prompt += '    "weights": {"SPY": 0.6, "QQQ": 0.4}\n'
            fix_prompt += "  }\n"
            fix_prompt += "}\n"
            fix_prompt += "```\n\n"
            fix_prompt += "**❌ WRONG (flat parameter dict):**\n"
            fix_prompt += "```python\n"
            fix_prompt += 'logic_tree = {"momentum_threshold": 0.15, "vix_level": 22}  # ❌ WRONG!\n'
            fix_prompt += "```\n\n"
            fix_prompt += "**If your strategy is STATIC (fixed allocation), use logic_tree = {}**\n"
            fix_prompt += "**Only use nested structure if you need CONDITIONAL allocation switching.**\n\n"

            # Add asset removal guidance if error mentions unlisted assets
            has_asset_error = any("not in global list" in error.lower() for error in validation_errors)
            if has_asset_error:
                fix_prompt += "## 🚨 ASSET MISMATCH FIX (CRITICAL):\n\n"
                fix_prompt += "**Your logic_tree references assets that aren't in your global assets list.**\n\n"
                fix_prompt += "**✅ CORRECT FIX: Remove unlisted assets from logic_tree branches:**\n"
                fix_prompt += "```python\n"
                fix_prompt += "# BEFORE (WRONG - SPY not in assets list):\n"
                fix_prompt += 'logic_tree = {\n'
                fix_prompt += '  "condition": "SPY_price > SPY_200d_MA",\n'
                fix_prompt += '  "if_true": {"assets": ["TLT", "GLD"], "weights": {"TLT": 0.5, "GLD": 0.5}},\n'
                fix_prompt += '  "if_false": {"assets": ["SPY", "QQQ"], "weights": {"SPY": 0.6, "QQQ": 0.4}}  # ❌ SPY not in assets!\n'
                fix_prompt += '}\n\n'
                fix_prompt += "# AFTER (CORRECT - use only assets from your global assets list):\n"
                fix_prompt += 'logic_tree = {\n'
                fix_prompt += '  "condition": "SPY_price > SPY_200d_MA",\n'
                fix_prompt += '  "if_true": {"assets": ["TLT", "GLD"], "weights": {"TLT": 0.5, "GLD": 0.5}},\n'
                fix_prompt += '  "if_false": {"assets": ["TLT", "GLD"], "weights": {"TLT": 0.4, "GLD": 0.6}}  # ✅ Uses same assets!\n'
                fix_prompt += '}\n'
                fix_prompt += "```\n\n"
                fix_prompt += "**❌ WRONG FIX: Adding assets to the global assets list (assets are IMMUTABLE)**\n"
                fix_prompt += "**You CANNOT add new assets during retry - only modify logic_tree to use existing assets.**\n\n"

        fix_prompt += "\n## ✅ FIX STRATEGY (MANDATORY):\n\n"
        fix_prompt += "For each error above:\n"
        fix_prompt += "1. **Read the error** - Understand what's wrong\n"
        fix_prompt += "2. **Identify the TEXT field** - Which field needs fixing (thesis/rationale/frequency)?\n"
        fix_prompt += "3. **Fix ONLY that field** - Modify thesis/rationale text or change frequency enum\n"
        fix_prompt += "4. **Copy structural fields** - Copy assets/weights/name/edge_type/archetype EXACTLY from ORIGINAL VALUES\n"
        fix_prompt += "5. **Return complete list** - Return all 5 candidates with errors fixed\n\n"
        fix_prompt += "**Examples:**\n"
        fix_prompt += "- Error: 'Syntax Error: Strategy - Thesis describes conditional logic...but logic_tree is empty'\n"
        fix_prompt += "  ✅ CORRECT FIX: Reword thesis to remove conditional keywords (keep logic_tree {{}})\n"
        fix_prompt += "  ❌ WRONG FIX: Populate logic_tree with conditions (structure is immutable)\n\n"
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

        # Serialize previous output for context (full output needed for LLM to preserve immutable fields)
        previous_output_json = json.dumps(
            [c.model_dump() for c in candidates],
            indent=2,
            default=str  # Handle enums
        )

        retry_prompt = f"""You generated strategies, but post-validation found issues. Here is your previous output for reference.

**YOUR PREVIOUS OUTPUT (for context - preserve immutable fields):**
```json
{previous_output_json}
```

**ORIGINAL MARKET CONTEXT:**
{market_context_json}

**FIXES REQUIRED:**
{fix_prompt}

**YOUR TASK:**
Fix ONLY the validation errors listed above. Return complete List[Strategy] with exactly 5 candidates.
- PRESERVE all immutable fields (assets, weights keys, name, edge_type, archetype) from your previous output
- FIX only the fields mentioned in validation errors (thesis_document, rebalancing_rationale, logic_tree structure, rebalance_frequency if archetype mismatch)

Output List[Strategy] with all errors corrected."""

        print(f"\n[RETRY] Sending fix prompt ({len(retry_prompt)} chars)...")
        tracker.estimate_prompt(
            label="Retry Fix",
            system_prompt="(same as generation)",
            user_prompt=retry_prompt,
            notes="Single retry with targeted error fixes"
        )

        # Debug logging: Print retry prompt being sent to LLM provider
        print(f"\n{'='*80}")
        print(f"[DEBUG:CandidateGenerator:RETRY] Sending retry prompt to LLM provider")
        print(f"[DEBUG:CandidateGenerator:RETRY] System prompt: (same as initial generation)")
        print(f"[DEBUG:CandidateGenerator:RETRY] User prompt length: {len(retry_prompt)} chars")
        print(f"{'='*80}")
        if os.getenv("DEBUG_PROMPTS", "0") == "1":
            print(f"\n[DEBUG:CandidateGenerator:RETRY] ========== FULL RETRY PROMPT ==========")
            print(retry_prompt)
            print(f"[DEBUG:CandidateGenerator:RETRY] =======================================")
            print(f"{'='*80}\n")

        try:
            result = await agent.run(retry_prompt)
            # Extract strategies from CandidateList wrapper
            fixed_candidates = result.output.strategies
            print(f"✓ Retry succeeded - received {len(fixed_candidates)} candidates")

            # Extract and log full reasoning content from retry (Kimi K2, DeepSeek R1, etc.)
            extract_and_log_reasoning(result, "CandidateGenerator:RETRY")

            # Debug logging: Print retry output
            print(f"\n[DEBUG:CandidateGenerator] Retry output:")
            print(f"{result.output}")

            # CRITICAL: Validate count against EXPECTED (5), not original length.
            # Retry may be fixing a wrong count (e.g., 1→5), which is valid.
            # We only reject if retry fails to produce exactly 5 candidates.
            EXPECTED_CANDIDATE_COUNT = 5
            if len(fixed_candidates) != EXPECTED_CANDIDATE_COUNT:
                raise ValueError(
                    f"Retry produced {len(fixed_candidates)} candidates (expected {EXPECTED_CANDIDATE_COUNT}). "
                    f"Original generation had {len(candidates)} candidates. "
                    f"Retry must always produce exactly {EXPECTED_CANDIDATE_COUNT} candidates."
                )

            # CRITICAL: Validate immutability for all candidates when counts match.
            # When retry CORRECTS count (e.g., 1→5), we can only validate the candidates
            # that exist in the original list. New candidates from retry cannot be
            # validated against originals (no 1-to-1 correspondence).
            validation_count = min(len(candidates), len(fixed_candidates))
            if len(candidates) != len(fixed_candidates):
                print(f"[WARNING] Retry changed count ({len(candidates)} → {len(fixed_candidates)}). "
                      f"Validating only first {validation_count} candidate(s) for immutability. "
                      f"New candidates from retry cannot be validated against originals.")

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
                # EXCEPTION: Allow logic_tree changes when retry is fixing count error (1→5)
                # because new candidates may have different structures than the single original
                original_has_logic = bool(original.logic_tree)
                fixed_has_logic = bool(fixed.logic_tree)

                # Detect if count error exists in validation_errors
                count_error_exists = any(
                    "count" in error.lower() or
                    "5 candidates" in error.lower() or
                    "strategy objects" in error.lower()
                    for error in validation_errors
                )

                # Debug logging for count error detection
                if i == 0 and count_error_exists:
                    print(f"[DEBUG] Count error detected in validation - allowing logic_tree structure changes")

                if original_has_logic != fixed_has_logic and not count_error_exists:
                    raise ValueError(
                        f"Retry modified logic_tree structure for candidate {i+1} ({original.name}): "
                        f"{'populated' if original_has_logic else 'empty'} → {'populated' if fixed_has_logic else 'empty'}. "
                        f"Logic tree structure (empty vs populated) must be preserved."
                    )

            print("✓ Data integrity validated - all immutable fields preserved")
            return fixed_candidates
        except Exception as e:
            print(f"✗ Retry failed: {e}")
            print(f"  Exception type: {type(e).__name__}")
            if "assets" in str(e).lower():
                print("  💡 Hint: LLM likely added assets to fix logic_tree references.")
                print("     The error message instructs removing from logic_tree instead.")
                print("     If this persists, check if the fix prompt guidance is being followed.")
            print("  Returning original candidates (with validation warnings)")
            return candidates

    async def _generate_single_candidate(
        self,
        market_context: dict,
        system_prompt: str,
        recipe_prompt: str,
        variation: PromptVariation,
        model: str,
    ) -> Strategy:
        """
        Generate a single candidate with a specific emphasis/persona.

        Args:
            market_context: Comprehensive market context pack
            system_prompt: System-level prompt with schemas and constraints
            recipe_prompt: Single-candidate recipe template (with {placeholders})
            variation: Prompt variation dict with name, emphasis, persona, constraint
            model: LLM model identifier

        Returns:
            Single Strategy object

        Raises:
            Exception: If generation fails (caller handles retry)
        """
        # Get model-specific settings
        model_settings = get_model_settings(model, stage="candidate_generation")

        # Fill in prompt template with variation values
        # Use replace() instead of format() to avoid conflicts with literal {} in code examples
        filled_recipe = (
            recipe_prompt
            .replace("{persona}", variation["persona"])
            .replace("{emphasis}", variation["emphasis"])
            .replace("{constraint}", variation["constraint"])
        )

        market_context_json = json.dumps(market_context, indent=2)

        generate_prompt = f"""**MARKET CONTEXT PACK:**

{market_context_json}

This context pack includes:
- Macro regime: Interest rates, inflation, employment, yield curve
- Market regime: Trend (bull/bear), volatility (VIX), breadth (% sectors >50d MA)
- Sector leadership: Top 3 leaders and bottom 3 laggards vs SPY (30d)
- Factor premiums: Value vs growth, momentum, quality, size (30d)
- Benchmark performance: SPY/QQQ/AGG/60-40/risk parity (30d returns, Sharpe, vol)
- Recent events: Curated market-moving events (30d lookback)

**RECIPE GUIDANCE:**

{filled_recipe}

**YOUR TASK:**

Generate exactly 1 Strategy object with:

1. **thesis_document (GENERATE FIRST - MOST IMPORTANT):**
   - Write 200-2000 character investment thesis explaining:
     - Market opportunity: What regime/trend are you exploiting?
     - Edge explanation: Why does this inefficiency exist? Why persistent?
     - Regime fit: Why NOW? Cite context pack data (VIX, breadth, sector leadership)
     - Risk factors: Specific failure modes with triggers and impact
   - Plain text paragraphs (NO markdown headers)
   - Specific to THIS strategy (not generic boilerplate)

2. **rebalancing_rationale:** 150-1000 chars explaining:
   - How rebalancing implements the edge
   - Why this frequency (daily/weekly/monthly) matches edge timescale
   - What rebalancing does to winners/losers and why

3. **edge_type:** behavioral | structural | informational | risk_premium

4. **archetype:** momentum | mean_reversion | carry | directional | volatility | multi_strategy

5. **concentration_intent:** diversified | high_conviction | core_satellite | barbell | sector_focus

6. **name, assets, weights, rebalance_frequency, logic_tree** (execution fields)

Remember: You are a {variation["emphasis"]} specialist. Your strategy should reflect this unique perspective.

**Return a single Strategy object.**"""

        # Create agent with SingleStrategy output type
        agent_ctx = await create_agent(
            model=model,
            output_type=SingleStrategy,
            system_prompt=system_prompt,
            include_composer=False,
            model_settings=model_settings
        )

        async with agent_ctx as agent:
            print(f"  [{variation['name']}] Generating candidate...")
            result = await agent.run(generate_prompt)

            # Extract and log reasoning if available
            extract_and_log_reasoning(result, f"CandidateGenerator:{variation['name']}")

            strategy = result.output.strategy

            # Debug: Print full strategy output (matches EdgeScorer pattern)
            print(f"\n[DEBUG:CandidateGenerator:{variation['name']}] Full LLM response:")
            print(f"{strategy.model_dump()}")

            print(f"  [{variation['name']}] ✓ Generated: {strategy.name[:50]}...")
            return strategy

    def _check_diversity(self, candidates: List[Strategy]) -> tuple[bool, List[str]]:
        """
        Verify candidates meet minimum diversity requirements.

        Checks:
        - At least 3 different edge types
        - At least 3 different archetypes

        Args:
            candidates: List of generated strategies

        Returns:
            Tuple of (passes_check, list_of_issues)
        """
        edge_types = {c.edge_type for c in candidates}
        archetypes = {c.archetype for c in candidates}
        frequencies = {c.rebalance_frequency for c in candidates}

        issues = []

        if len(edge_types) < 3:
            issues.append(
                f"Only {len(edge_types)} edge types ({', '.join(str(e.value) for e in edge_types)}). "
                f"Recommend ≥3 for diversity."
            )

        if len(archetypes) < 3:
            issues.append(
                f"Only {len(archetypes)} archetypes ({', '.join(str(a.value) for a in archetypes)}). "
                f"Recommend ≥3 for diversity."
            )

        return len(issues) == 0, issues
