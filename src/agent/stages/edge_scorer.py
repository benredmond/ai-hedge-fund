"""Evaluate strategy using Edge Scorecard via AI agent."""

import json
import os
from pydantic_ai import ModelSettings
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    is_reasoning_model,
    get_model_settings,
)
from src.agent.models import Strategy, EdgeScorecard, EdgeScorecardDetailed
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
        # Load scoring prompt (compressed version)
        system_prompt = load_prompt("edge_scoring_compressed.md")

        # Get model-specific settings (reasoning models require temperature=1.0, max_tokens=16384)
        model_settings = get_model_settings(model, stage="edge_scoring")

        # Create agent with typed output to avoid dict schemas for Gemini
        # Use 10 message history limit (single evaluation, no tool usage)
        agent_ctx = await create_agent(
            model=model,
            output_type=EdgeScorecardDetailed,
            system_prompt=system_prompt,
            include_composer=False,  # Edge scoring doesn't deploy - no Composer tools needed
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

            # Pass full context pack - let LLM interpret the nested structure
            # This includes: regime_snapshot, macro_indicators, benchmark_performance, recent_events

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

## Market Context (Full Context Pack)

{json.dumps(market_context, indent=2, default=str)}
{leverage_context}

## Your Task

Score this strategy on the 5 Edge Scorecard dimensions. Do NOT analyze assets - ONLY score.

Return JSON with these exact keys: thesis_quality, edge_economics, risk_framework, regime_awareness, strategic_coherence

Each dimension: {{"score": 1-5, "reasoning": "...", "key_strengths": [...], "key_weaknesses": [...]}}

**CRITICAL**: All dimensions must score ≥3 to pass.
"""

            # Debug logging: Print prompt being sent to LLM provider
            print(f"\n{'='*80}")
            print(f"[DEBUG:EdgeScorer] Sending prompt to LLM provider")
            print(f"[DEBUG:EdgeScorer] System prompt length: {len(system_prompt)} chars")
            print(f"[DEBUG:EdgeScorer] User prompt length: {len(prompt)} chars")
            print(f"{'='*80}")
            if os.getenv("DEBUG_PROMPTS", "0") == "1":
                print(f"\n[DEBUG:EdgeScorer] ========== FULL SYSTEM PROMPT ==========")
                print(system_prompt)
                print(f"[DEBUG:EdgeScorer] ========================================")
                print(f"\n[DEBUG:EdgeScorer] ========== FULL USER PROMPT ==========")
                print(prompt)
                print(f"[DEBUG:EdgeScorer] ======================================")
                print(f"{'='*80}\n")

            result = await agent.run(prompt)

            # Extract and log full reasoning content (Kimi K2, DeepSeek R1, etc.)
            from src.agent.stages.candidate_generator import extract_and_log_reasoning
            extract_and_log_reasoning(result, "EdgeScorer")

            raw_output = result.output

        # Debug logging: Print full LLM response for debugging format issues
        print(f"\n[DEBUG:EdgeScorer] Full LLM response:")
        print(f"{raw_output}")

        if not isinstance(raw_output, EdgeScorecardDetailed):
            raise ValueError(
                f"Edge scoring failed - LLM returned invalid output type: {type(raw_output)}"
            )

        scorecard = EdgeScorecard(
            thesis_quality=raw_output.thesis_quality.score,
            edge_economics=raw_output.edge_economics.score,
            risk_framework=raw_output.risk_framework.score,
            regime_awareness=raw_output.regime_awareness.score,
            strategic_coherence=raw_output.strategic_coherence.score,
        )

        return scorecard
