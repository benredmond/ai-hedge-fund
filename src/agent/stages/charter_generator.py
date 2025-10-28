"""Generate charter document for selected strategy."""

from typing import List
import json
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL
)
from src.agent.models import (
    Strategy,
    Charter,
    BacktestResult,
    SelectionReasoning,
    EdgeScorecard
)


class CharterGenerator:
    """
    Stage 5: Generate charter document.

    Creates comprehensive charter with market thesis, selection reasoning,
    expected behavior, failure modes, and 90-day outlook.

    Uses all selection context from prior stages:
    - Winner strategy and backtest results
    - Selection reasoning (why this vs alternatives)
    - Edge scorecard scores (institutional evaluation)
    - All 5 candidates and their backtests for comparison
    - Market context for tool-based regime analysis
    """

    async def generate(
        self,
        winner: Strategy,
        reasoning: SelectionReasoning,
        candidates: List[Strategy],
        scorecards: List[EdgeScorecard],
        backtests: List[BacktestResult],
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> Charter:
        """
        Generate charter document with full context.

        Args:
            winner: Selected strategy
            reasoning: SelectionReasoning (why this vs alternatives)
            candidates: All 5 candidates (including winner)
            scorecards: Edge Scorecard evaluations for all candidates
            backtests: Backtest results for all candidates
            market_context: Current market regime (date-anchored)
            model: LLM model identifier

        Returns:
            Complete Charter document with 5 sections
        """
        # Load prompts
        system_prompt = load_prompt("system/charter_creation_system.md")
        recipe_prompt = load_prompt("charter_creation.md")

        # Create agent
        agent_ctx = await create_agent(
            model=model,
            output_type=Charter,
            system_prompt=system_prompt
        )

        # Build selection context
        winner_idx = reasoning.winner_index
        winner_scorecard = scorecards[winner_idx]
        winner_backtest = backtests[winner_idx]

        # Format selection context for agent
        async with agent_ctx as agent:
            # Serialize all context
            selection_context = {
                "winner": {
                    "name": winner.name,
                    "assets": winner.assets,
                    "weights": winner.weights,
                    "rebalance_frequency": winner.rebalance_frequency.value,
                    "logic_tree": winner.logic_tree
                },
                "reasoning": {
                    "winner_index": winner_idx,
                    "why_selected": reasoning.why_selected,
                    "tradeoffs_accepted": reasoning.tradeoffs_accepted,
                    "alternatives_rejected": reasoning.alternatives_rejected,
                    "conviction_level": reasoning.conviction_level
                },
                "edge_scorecard": {
                    "thesis_quality": winner_scorecard.thesis_quality,
                    "edge_economics": winner_scorecard.edge_economics,
                    "risk_framework": winner_scorecard.risk_framework,
                    "regime_awareness": winner_scorecard.regime_awareness,
                    "strategic_coherence": winner_scorecard.strategic_coherence,
                    "total_score": winner_scorecard.total_score
                },
                "backtest_winner": {
                    "sharpe_ratio": winner_backtest.sharpe_ratio,
                    "max_drawdown": winner_backtest.max_drawdown,
                    "total_return": winner_backtest.total_return,
                    "volatility_annualized": winner_backtest.volatility_annualized
                },
                "all_candidates": [],
                "market_context_summary": {
                    "anchor_date": market_context["metadata"]["anchor_date"],
                    "regime_tags": market_context.get("regime_tags", []),
                    "regime_snapshot": market_context.get("regime_snapshot", {})
                }
            }

            # Add all candidates with their metrics
            for i, (candidate, scorecard, backtest) in enumerate(zip(candidates, scorecards, backtests)):
                selection_context["all_candidates"].append({
                    "index": i,
                    "name": candidate.name,
                    "assets": candidate.assets,
                    "is_winner": i == winner_idx,
                    "edge_score": scorecard.total_score,
                    "sharpe_ratio": backtest.sharpe_ratio,
                    "max_drawdown": backtest.max_drawdown
                })

            selection_context_json = json.dumps(selection_context, indent=2)

            prompt = f"""Create a comprehensive charter document for the selected strategy.

## SELECTION CONTEXT FROM PRIOR STAGES

You have access to the complete selection context from Stages 1-4:

{selection_context_json}

## INSTRUCTIONS FROM RECIPE

{recipe_prompt}

## YOUR TASK

Follow the workflow in the recipe:

**Pre-Work**: Parse the SelectionReasoning, Edge Scorecard, and Backtest results above.

**Phase 1: Market Data Gathering**
- Use FRED tools (fred_get_series) for macro regime classification
- Use yfinance tools (stock_get_historical_stock_prices) for market regime analysis
- Ground Market Thesis section in tool data (not just the context summary above)

**Phase 2: Charter Writing**
- Section 1 (Market Thesis): Tool-cited, connect regime to strategy's edge
- Section 2 (Strategy Selection): Integrate SelectionReasoning verbatim, cite Edge Scorecard scores, compare backtests vs alternatives
- Section 3 (Expected Behavior): Best/base/worst case scenarios + regime transitions
- Section 4 (Failure Modes): 3-8 specific, measurable conditions (use templates from recipe)
- Section 5 (90-Day Outlook): Milestones (Day 30/60/90) + red flags from failure modes

**Critical Requirements**:
1. Strategy Selection MUST reference why_selected, alternatives_rejected, tradeoffs_accepted
2. MUST cite Edge Scorecard scores (total + 2-3 dimensions)
3. MUST use FRED and yfinance tools for current data (don't rely only on context summary)
4. Failure modes MUST be specific with: Condition + Impact + Early Warning
5. Run Pre-Submission Checklist before returning Charter

Begin by using MCP tools to gather current market data, then write the 5-section charter.
"""

            result = await agent.run(prompt)
            charter = result.output

        return charter
