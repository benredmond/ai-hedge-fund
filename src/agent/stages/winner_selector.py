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
        Select best candidate using composite ranking.

        Ranking Formula:
            score = 0.4 × Sharpe + 0.3 × EdgeScore + 0.2 × RegimeFit + 0.1 × (1 - abs(Drawdown))

        Args:
            candidates: 5 strategies
            scorecards: 5 edge scorecards
            backtests: 5 backtest results
            market_context: Current market regime
            model: LLM for reasoning generation

        Returns:
            (winner, reasoning) tuple
        """
        # Compute composite scores
        composite_scores = []

        for i in range(5):
            # Normalize each component to 0-1 range
            sharpe_norm = (backtests[i].sharpe_ratio + 1) / 4  # -1 to 3 → 0 to 1
            edge_norm = scorecards[i].total_score / 5  # 1-5 → 0.2-1.0
            regime_norm = scorecards[i].regime_alignment / 5
            drawdown_norm = 1 - abs(backtests[i].max_drawdown)

            composite = (
                0.4 * sharpe_norm +
                0.3 * edge_norm +
                0.2 * regime_norm +
                0.1 * drawdown_norm
            )

            composite_scores.append((i, composite))

        # Rank candidates by composite score
        ranked = sorted(composite_scores, key=lambda x: x[1], reverse=True)
        winner_index = ranked[0][0]
        winner = candidates[winner_index]

        # Generate selection reasoning via AI
        agent_ctx = await create_agent(
            model=model,
            output_type=SelectionReasoning,
            system_prompt=load_prompt("winner_selection.md")
        )

        async with agent_ctx as agent:
            prompt = f"""Explain why we selected candidate {winner_index + 1} over the other 4 alternatives.

**Winner**: {winner.name}
- Sharpe: {backtests[winner_index].sharpe_ratio:.2f}
- Edge Score: {scorecards[winner_index].total_score:.1f}/5
- Composite Score: {ranked[0][1]:.3f}

**Other Candidates**:
"""
            for rank, (idx, score) in enumerate(ranked[1:], start=2):
                prompt += f"\n{rank}. {candidates[idx].name} (Composite: {score:.3f}, Sharpe: {backtests[idx].sharpe_ratio:.2f})"

            prompt += "\n\nProvide clear reasoning focusing on: risk-adjusted returns, regime fit, robustness, implementation."

            result = await agent.run(prompt)
            reasoning = result.output

        # Set reasoning fields
        reasoning.winner_index = winner_index
        reasoning.alternatives_compared = [
            c.name for i, c in enumerate(candidates) if i != winner_index
        ]

        return winner, reasoning
