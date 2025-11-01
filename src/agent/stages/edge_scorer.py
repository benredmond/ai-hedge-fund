"""Evaluate strategy using Edge Scorecard via AI agent."""

import json
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL
)
from src.agent.models import Strategy, EdgeScorecard


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

        # Create agent with dict output to handle rich scoring format
        # Use 10 message history limit (single evaluation, no tool usage)
        agent_ctx = await create_agent(
            model=model,
            output_type=dict,
            system_prompt=system_prompt,
            history_limit=10
        )

        # Build evaluation prompt
        async with agent_ctx as agent:
            # Serialize strategy for agent
            strategy_json = {
                "name": strategy.name,
                "assets": strategy.assets,
                "weights": strategy.weights,
                "rebalance_frequency": strategy.rebalance_frequency.value,
                "logic_tree": strategy.logic_tree if strategy.logic_tree else {}
            }

            # Extract relevant market context
            regime_tags = market_context.get("regime_tags", [])
            regime_snapshot = market_context.get("regime_snapshot", {})

            prompt = f"""Evaluate this trading strategy on the Edge Scorecard dimensions.

## Strategy to Evaluate

{json.dumps(strategy_json, indent=2)}

## Market Context

**Regime Tags**: {", ".join(regime_tags)}
**Current Trend**: {regime_snapshot.get("trend_classification", "unknown")}
**Volatility Regime**: {regime_snapshot.get("volatility_regime", "unknown")}
**Market Breadth**: {regime_snapshot.get("market_breadth_pct", 0):.1f}% sectors above 50d MA

## Your Task

Evaluate the strategy following the Edge Scorecard framework in your system prompt.

Return your evaluation as a JSON object with scores for all 5 dimensions.

**CRITICAL**: All dimensions must score ≥3 to pass threshold.
"""

            result = await agent.run(prompt)
            raw_output = result.output

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
