"""Generate charter document for selected strategy."""

from typing import List
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL
)
from src.agent.models import (
    Strategy,
    Charter,
    BacktestResult,
    SelectionReasoning
)


class CharterGenerator:
    """
    Stage 5: Generate charter document.

    Creates comprehensive charter with market thesis, selection reasoning,
    expected behavior, failure modes, and 90-day outlook.
    """

    async def generate(
        self,
        winner: Strategy,
        reasoning: SelectionReasoning,
        alternatives: List[Strategy],
        backtests: List[BacktestResult],
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> Charter:
        """
        Generate charter document with full context.

        Args:
            winner: Selected strategy
            reasoning: Why it was selected
            alternatives: All 5 candidates (including winner)
            backtests: Backtest results for all candidates
            market_context: Current market regime
            model: LLM model identifier

        Returns:
            Complete Charter document with 5 sections
        """
        # Load charter creation prompt
        system_prompt = load_prompt("system_prompt.md")
        charter_prompt = load_prompt("charter_creation.md")
        combined_prompt = f"{system_prompt}\n\n{charter_prompt}"

        # Create agent
        agent_ctx = await create_agent(
            model=model,
            output_type=Charter,
            system_prompt=combined_prompt
        )

        # Build context-rich prompt
        async with agent_ctx as agent:
            prompt = f"""Create charter document for the selected strategy.

## Selected Strategy

**Name**: {winner.name}
**Assets**: {", ".join(winner.assets)}
**Weights**: {winner.weights}
**Rebalance Frequency**: {winner.rebalance_frequency.value}

## Backtest Results

- Sharpe Ratio: {backtests[reasoning.winner_index].sharpe_ratio:.2f}
- Max Drawdown: {backtests[reasoning.winner_index].max_drawdown:.1%}
- Total Return: {backtests[reasoning.winner_index].total_return:.1%}
- Volatility: {backtests[reasoning.winner_index].volatility_annualized:.1%}

## Selection Reasoning

{reasoning.why_selected}

## Alternative Candidates Considered

"""
            for i, alt in enumerate(alternatives):
                if i != reasoning.winner_index:
                    prompt += f"\n**{alt.name}**"
                    prompt += f"\n- Sharpe: {backtests[i].sharpe_ratio:.2f}"
                    prompt += f"\n- Why Rejected: [Compare to winner]\n"

            prompt += f"""

## Market Context (as of {market_context["metadata"]["anchor_date"]})

Regime: {", ".join(market_context.get("regime_tags", []))}

Now create a complete charter with all 5 required sections:
1. Market Thesis
2. Strategy Selection
3. Expected Behavior
4. Failure Modes
5. 90-Day Outlook

Ensure you reference the specific backtest data and alternative comparisons above.
"""

            result = await agent.run(prompt)
            charter = result.output

        return charter
