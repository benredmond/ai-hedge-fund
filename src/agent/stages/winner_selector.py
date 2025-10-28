"""Select best strategy from candidates using composite ranking."""

from typing import List, Tuple
from src.agent.strategy_creator import create_agent, load_prompt, DEFAULT_MODEL
from src.agent.models import (
    Strategy,
    BacktestResult,
    EdgeScorecard,
    SelectionReasoning
)


class WinnerSelector:
    """
    Stage 4: Select winner from 5 candidates.

    Uses composite ranking: Sharpe + Edge + Regime + Drawdown.
    Generates AI reasoning for selection.
    """

    async def select(
        self,
        candidates: List[Strategy],
        scorecards: List[EdgeScorecard],
        backtests: List[BacktestResult],
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> Tuple[Strategy, SelectionReasoning]:
        """
        Select best candidate using composite ranking and AI reasoning.

        Composite Ranking Formula (for initial ordering):
            score = 0.35 × Sharpe + 0.30 × (Thesis + Edge + Risk)/3 + 0.20 × Regime + 0.15 × Coherence

        Note: AI may override composite ranking if strategic reasoning justifies it
        (e.g., lower Sharpe but superior thesis quality)

        Args:
            candidates: 5 strategies
            scorecards: 5 edge scorecards (with new 5-dimension rubric)
            backtests: 5 backtest results
            market_context: Current market conditions
            model: LLM for reasoning generation

        Returns:
            (winner, reasoning) tuple

        Example:
            >>> selector = WinnerSelector()
            >>> winner, reasoning = await selector.select(candidates, scorecards, backtests, context)
            >>> print(f"Selected: {winner.name} - {reasoning.why_selected[:100]}...")
        """
        # Extract regime tags for context
        regime_tags = market_context.get("regime_tags", [])

        # Compute composite scores for initial ranking
        composite_scores = []

        for i in range(5):
            # Normalize each component to 0-1 range
            sharpe_norm = min(1.0, max(0.0, (backtests[i].sharpe_ratio + 1) / 4))  # -1 to 3 → 0 to 1

            # Strategic reasoning quality (average of thesis, edge, risk)
            # Note: Current EdgeScorecard has old dimension names; will work with both old and new
            if hasattr(scorecards[i], 'thesis_quality'):
                # New 5-dimension rubric
                reasoning_norm = (
                    scorecards[i].thesis_quality +
                    scorecards[i].edge_economics +
                    scorecards[i].risk_framework
                ) / 15.0  # Average of 3 dimensions, each 1-5
                regime_norm = scorecards[i].regime_awareness / 5.0
                coherence_norm = scorecards[i].strategic_coherence / 5.0
            else:
                # Old 6-dimension rubric (backwards compatibility)
                reasoning_norm = (
                    scorecards[i].specificity +
                    scorecards[i].structural_basis +
                    scorecards[i].failure_clarity
                ) / 15.0
                regime_norm = scorecards[i].regime_alignment / 5.0
                coherence_norm = scorecards[i].mental_model_coherence / 5.0

            drawdown_norm = min(1.0, 1 - abs(backtests[i].max_drawdown))

            # Weighted composite score
            composite = (
                0.35 * sharpe_norm +
                0.30 * reasoning_norm +
                0.20 * regime_norm +
                0.15 * coherence_norm
            )

            composite_scores.append((i, composite))

        # Rank candidates by composite score
        ranked = sorted(composite_scores, key=lambda x: x[1], reverse=True)

        # Build rich context for AI selection
        agent_ctx = await create_agent(
            model=model,
            output_type=SelectionReasoning,
            system_prompt=load_prompt("winner_selection.md")
        )

        async with agent_ctx as agent:
            # Build comprehensive evaluation prompt
            prompt = f"""Select the best trading strategy from these 5 candidates for 90-day deployment.

## Market Context

**Regime Tags**: {", ".join(regime_tags)}
**Current Conditions**: {market_context.get("regime_snapshot", {}).get("trend_classification", "unknown")} trend, {market_context.get("regime_snapshot", {}).get("volatility_regime", "unknown")} volatility

## Candidate Evaluation Data

"""
            # Add detailed data for each candidate
            for idx in range(5):
                rank_position = next((rank + 1 for rank, (i, _) in enumerate(ranked) if i == idx), 0)
                composite = composite_scores[idx][1]

                prompt += f"""
### Candidate {idx + 1}: {candidates[idx].name} (Rank: #{rank_position}, Composite: {composite:.3f})

**Strategy Overview:**
- Assets: {", ".join(candidates[idx].assets[:5])}{"..." if len(candidates[idx].assets) > 5 else ""}
- Weights: {dict(list(candidates[idx].weights.items())[:3])}{"..." if len(candidates[idx].weights) > 3 else ""}
- Rebalancing: {candidates[idx].rebalance_frequency.value}

**Backtest Results:**
- Sharpe Ratio: {backtests[idx].sharpe_ratio:.2f}
- Max Drawdown: {backtests[idx].max_drawdown:.1%}
- Total Return: {backtests[idx].total_return:.1%}
- Volatility: {backtests[idx].volatility_annualized:.1%}

**Edge Scorecard:**
"""
                # Add scores (works with both old and new rubric)
                if hasattr(scorecards[idx], 'thesis_quality'):
                    # New 5-dimension rubric
                    prompt += f"""- Thesis Quality: {scorecards[idx].thesis_quality}/5
- Edge Economics: {scorecards[idx].edge_economics}/5
- Risk Framework: {scorecards[idx].risk_framework}/5
- Regime Awareness: {scorecards[idx].regime_awareness}/5
- Strategic Coherence: {scorecards[idx].strategic_coherence}/5
- **Total Score**: {scorecards[idx].total_score:.1f}/5

"""
                else:
                    # Old 6-dimension rubric
                    prompt += f"""- Specificity: {scorecards[idx].specificity}/5
- Structural Basis: {scorecards[idx].structural_basis}/5
- Regime Alignment: {scorecards[idx].regime_alignment}/5
- Differentiation: {scorecards[idx].differentiation}/5
- Failure Clarity: {scorecards[idx].failure_clarity}/5
- Mental Model Coherence: {scorecards[idx].mental_model_coherence}/5
- **Total Score**: {scorecards[idx].total_score:.1f}/5

"""

            prompt += """
## Your Task

Select the winner and provide comprehensive selection reasoning following the framework in your system prompt.

**Key Reminders:**
1. **Process over past performance**: Favor strategies with strong thesis/edge/risk reasoning over pure backtest Sharpe
2. **Tradeoffs matter**: Make explicit what you're optimizing for vs sacrificing
3. **Regime context**: Match strategy to current market conditions
4. **Risk awareness**: Enumerate failure scenarios and monitoring priorities

**Output Requirements:**
- winner_index: 0-4 (index in candidates list)
- why_selected: Detailed explanation (100-5000 chars) citing specific scores and metrics
- tradeoffs_accepted: Key tradeoffs in choosing this strategy (50-2000 chars)
- alternatives_rejected: List of 4 rejected candidate names with brief reasons
- conviction_level: Confidence in selection (0.0-1.0) based on score delta and consistency

Return structured SelectionReasoning output.
"""

            result = await agent.run(prompt)
            reasoning = result.output

        # Validate and set index if not set by AI
        if reasoning.winner_index < 0 or reasoning.winner_index > 4:
            # Fallback to composite ranking if AI provided invalid index
            reasoning.winner_index = ranked[0][0]

        winner = candidates[reasoning.winner_index]

        # Set alternatives_rejected if not properly set
        if not reasoning.alternatives_rejected or len(reasoning.alternatives_rejected) < 4:
            reasoning.alternatives_rejected = [
                c.name for i, c in enumerate(candidates) if i != reasoning.winner_index
            ]

        # Set tradeoffs_accepted if empty (fallback)
        if not reasoning.tradeoffs_accepted or len(reasoning.tradeoffs_accepted) < 50:
            reasoning.tradeoffs_accepted = "Accepting the documented risks in favor of expected returns under current market regime."

        # Set conviction_level if not set (calculate from score delta)
        if reasoning.conviction_level is None or reasoning.conviction_level < 0 or reasoning.conviction_level > 1:
            winner_composite = composite_scores[reasoning.winner_index][1]
            runner_up_composite = ranked[1][1] if len(ranked) > 1 else 0.0
            score_delta = winner_composite - runner_up_composite
            reasoning.conviction_level = min(1.0, max(0.0, 0.5 + score_delta))

        return winner, reasoning
