"""Evaluate strategy using Edge Scorecard via AI agent."""

import json
from pydantic_ai import ModelSettings
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    is_reasoning_model,
    get_model_settings,
)
from src.agent.models import Strategy, EdgeScorecard
from src.agent.config.leverage import detect_leverage


class EdgeScorer:
    """
    Stage 2: Evaluate strategy on 5 Edge Scorecard dimensions.

    Uses AI agent to score strategies on:
    - Thesis Quality: Clear, falsifiable investment thesis with causal reasoning
    - Edge Economics: Why edge exists and why it hasn't been arbitraged away
    - Risk Framework: Understanding of risk profile and failure modes
    - Regime Awareness: Fit with current market conditions and adaptation logic
    - Strategic Coherence: Unified thesis with feasible execution
    """

    async def score(
        self,
        strategy: Strategy,
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> EdgeScorecard:
        """
        Evaluate strategy on 5 Edge Scorecard dimensions.

        Args:
            strategy: Strategy to evaluate
            market_context: Current market conditions
            model: LLM model identifier

        Returns:
            EdgeScorecard with all 5 dimensions scored 1-5

        Raises:
            ValueError: If any dimension scores below 3 (via EdgeScorecard validation)

        Example:
            >>> scorer = EdgeScorer()
            >>> strategy = Strategy(name="Tech Momentum", ...)
            >>> context = {"regime_tags": ["strong_bull", "growth_favored"]}
            >>> scorecard = await scorer.score(strategy, context)
            >>> print(f"Total score: {scorecard.total_score:.1f}/5")
        """
        # Load scoring prompt
        system_prompt = load_prompt("edge_scoring.md")

        # Get model-specific settings (reasoning models require temperature=1.0, max_tokens=16384)
        model_settings = get_model_settings(model, stage="edge_scoring")

        # Create agent with dict output to handle rich scoring format
        # Use 10 message history limit (single evaluation, no tool usage)
        agent_ctx = await create_agent(
            model=model,
            output_type=dict,
            system_prompt=system_prompt,
            history_limit=10,
            model_settings=model_settings
        )

        # Build evaluation prompt
        async with agent_ctx as agent:
            # Serialize strategy for agent
            strategy_json = {
                "name": strategy.name,
                "assets": strategy.assets,
                "weights": strategy.weights,
                "rebalance_frequency": strategy.rebalance_frequency.value,
                "edge_type": getattr(strategy.edge_type, "value", strategy.edge_type),
                "archetype": getattr(strategy.archetype, "value", strategy.archetype),
                "logic_tree": strategy.logic_tree if strategy.logic_tree else {},
                "thesis_document": getattr(strategy, 'thesis_document', '')  # Defensive access for backward compat
            }

            # Extract relevant market context
            regime_tags = market_context.get("regime_tags", [])
            regime_snapshot = market_context.get("regime_snapshot", {})

            # Detect leveraged assets using centralized utility
            leveraged_2x, leveraged_3x, max_leverage = detect_leverage(strategy)
            uses_leverage = bool(leveraged_2x or leveraged_3x)

            # Build leverage context section if leverage detected
            leverage_context = ""
            if uses_leverage:
                leveraged_assets_list = leveraged_2x + leveraged_3x
                leverage_labels = [
                    f"{asset} ({('3x' if asset in leveraged_3x else '2x')})"
                    for asset in leveraged_assets_list
                ]

                leverage_context = f"""

## ⚠️ LEVERAGE PROFILE DETECTED

**Uses Leverage**: Yes
**Leveraged Assets**: {", ".join(leverage_labels)}
**Maximum Leverage**: {max_leverage}x

**CRITICAL EVALUATION INSTRUCTIONS FOR LEVERAGED STRATEGIES:**

This strategy uses {max_leverage}x leveraged ETFs. You MUST apply the "Special Evaluation: Leveraged Strategies" rubric from your system prompt.

**Required Elements for Scoring:**

{'**For 3x Leverage - ALL 6 ELEMENTS REQUIRED for score ≥4:**' if max_leverage == 3 else '**For 2x Leverage - 4 CORE ELEMENTS REQUIRED for score ≥4:**'}
1. ✅ Convexity Advantage: Why leverage enhances edge vs unleveraged version
2. ✅ Decay Cost Quantification: Specific estimate ({('2-5% annually' if max_leverage == 3 else '0.5-1% annually')})
3. ✅ Realistic Drawdown: {('40-65% range' if max_leverage == 3 else '18-40% range')} (historical worst-case)
4. ✅ Benchmark Comparison: Why not just SPY/QQQ/etc?
{'5. ✅ Stress Test: 2022/2020/2008 analog with drawdown data' if max_leverage == 3 else ''}
{'6. ✅ Exit Criteria: Specific triggers (VIX threshold, momentum reversal, etc.)' if max_leverage == 3 else ''}

**Scoring Caps (Red Flags):**
- Fantasy drawdown ({('<40%' if max_leverage == 3 else '<18%')}) → Thesis Quality capped at 1/5
- No decay discussion → Edge Economics capped at 2/5
- Missing convexity explanation → Thesis Quality capped at 2/5
{'- Missing stress test → Risk Framework capped at 2/5' if max_leverage == 3 else ''}
{'- Missing exit criteria → Risk Framework capped at 2/5' if max_leverage == 3 else ''}

**REMEMBER:** Do NOT penalize leverage per se. Score on PROCESS QUALITY.
- Well-justified {max_leverage}x strategy CAN score 5/5 if all elements present
- Poorly-justified conservative strategy deserves 2/5

Check thesis_document and rebalancing_rationale for these required elements before scoring.
"""

            prompt = f"""Evaluate this trading strategy on the Edge Scorecard dimensions.

## Strategy to Evaluate

{json.dumps(strategy_json, indent=2)}

## Market Context

**Regime Tags**: {", ".join(regime_tags)}
**Current Trend**: {regime_snapshot.get("trend_classification", "unknown")}
**Volatility Regime**: {regime_snapshot.get("volatility_regime", "unknown")}
**Market Breadth**: {regime_snapshot.get("market_breadth_pct", 0):.1f}% sectors above 50d MA
{leverage_context}

## Your Task

Evaluate the strategy following the Edge Scorecard framework in your system prompt.

Return your evaluation as a JSON object with scores for all 5 dimensions.

**CRITICAL**: All dimensions must score ≥3 to pass threshold.
"""

            # Debug logging: Print prompt being sent to LLM provider
            print(f"\n[DEBUG:EdgeScorer] Sending prompt to LLM provider")
            print(f"[DEBUG:EdgeScorer] System prompt: {system_prompt[:500]}... [Total: {len(system_prompt)} chars]")
            print(f"[DEBUG:EdgeScorer] User prompt (preview): {prompt[:1000]}... [Total: {len(prompt)} chars]")
            print(f"[DEBUG:EdgeScorer] ========== FULL USER PROMPT ==========")
            print(prompt)
            print(f"[DEBUG:EdgeScorer] =====================================")

            result = await agent.run(prompt)
            raw_output = result.output

        # Debug logging: Print full LLM response for debugging format issues
        print(f"\n[DEBUG:EdgeScorer] Full LLM response:")
        print(f"{raw_output}")

        # Unwrap nested response if model wraps in single-key dict (e.g., Kimi K2 uses "evaluation")
        # This handles provider differences while preserving GPT-4o flat format compatibility
        if isinstance(raw_output, dict) and len(raw_output) == 1:
            wrapper_key = list(raw_output.keys())[0]
            # Check if it's a known wrapper pattern (not a legitimate single-field response)
            known_wrappers = ["evaluation", "result", "data", "output", "response"]
            if wrapper_key in known_wrappers:
                print(f"[DEBUG:EdgeScorer] Unwrapping '{wrapper_key}' wrapper from LLM response")
                raw_output = raw_output[wrapper_key]
                print(f"[DEBUG:EdgeScorer] After unwrap - keys: {list(raw_output.keys()) if isinstance(raw_output, dict) else 'not-dict'}")

        # Parse the rich output format from the new prompt
        # The prompt returns: {dimension: {score: X, reasoning: ..., evidence_cited: ..., ...}}
        # We need to extract just the scores to create EdgeScorecard

        # Handle both old simple format and new rich format
        if isinstance(raw_output, dict):
            # Check if it's the new rich format (has nested dicts with 'score' key)
            if any(isinstance(v, dict) and 'score' in v for v in raw_output.values()):
                # New rich format - extract scores
                scorecard = EdgeScorecard(
                    thesis_quality=raw_output.get('thesis_quality', {}).get('score', 3),
                    edge_economics=raw_output.get('edge_economics', {}).get('score', 3),
                    risk_framework=raw_output.get('risk_framework', {}).get('score', 3),
                    regime_awareness=raw_output.get('regime_awareness', {}).get('score', 3),
                    strategic_coherence=raw_output.get('strategic_coherence', {}).get('score', 3)
                )
            else:
                # Old simple format - direct scores
                try:
                    scorecard = EdgeScorecard(**raw_output)
                except Exception as e:
                    raise ValueError(
                        f"Edge scoring returned invalid format: {e}\n"
                        f"Expected dict with 'score' keys or flat score dict\n"
                        f"Got: {raw_output}"
                    ) from e
        else:
            raise ValueError(
                f"Edge scoring failed - LLM returned non-dict output: {type(raw_output)}\n"
                f"Output: {raw_output}"
            )

        return scorecard
