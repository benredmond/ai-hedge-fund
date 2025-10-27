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

        # Create agent
        agent_ctx = await create_agent(
            model=model,
            output_type=EdgeScorecard,
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

Score the strategy on all 6 dimensions (1-5 scale):

1. **Specificity**: How clear and precise is the edge?
2. **Structural Basis**: Quality of reasoning (behavioral/structural/informational/risk premium)
3. **Regime Alignment**: Fit with current market conditions
4. **Differentiation**: Novelty vs generic approaches
5. **Failure Clarity**: Quality of identified failure modes
6. **Mental Model Coherence**: Internal consistency

**CRITICAL**: All dimensions must score ≥3 to pass threshold.

Provide your scores as structured output (EdgeScorecard format).
"""

            result = await agent.run(prompt)
            scorecard = result.output

        return scorecard
