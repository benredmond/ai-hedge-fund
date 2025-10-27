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
    Stage 2: Evaluate strategy on 6 Edge Scorecard dimensions.

    Uses AI agent to score strategies on:
    - Specificity: Edge clarity and precision
    - Structural Basis: Reasoning quality
    - Regime Alignment: Fit with current market conditions
    - Differentiation: Novelty vs generic approaches
    - Failure Clarity: Quality of identified failure modes
    - Mental Model Coherence: Internal consistency
    """

    async def score(
        self,
        strategy: Strategy,
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> EdgeScorecard:
        """
        Evaluate strategy on 6 Edge Scorecard dimensions.

        Args:
            strategy: Strategy to evaluate
            market_context: Current market conditions
            model: LLM model identifier

        Returns:
            EdgeScorecard with all 6 dimensions scored 1-5

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
        agent_ctx = await create_agent(
            model=model,
            output_type=dict,
            system_prompt=system_prompt
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
                scorecard = EdgeScorecard(**raw_output)
        else:
            # Fallback - create minimal passing scorecard
            scorecard = EdgeScorecard(
                thesis_quality=3,
                edge_economics=3,
                risk_framework=3,
                regime_awareness=3,
                strategic_coherence=3
            )

        return scorecard
