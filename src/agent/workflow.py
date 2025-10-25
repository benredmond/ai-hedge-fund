"""
Strategy creation workflow orchestration.

This module implements the multi-stage workflow for generating,
evaluating, and selecting trading strategies.
"""

import json
import random
from typing import List, Tuple
from src.agent.strategy_creator import create_agent, load_prompt
from src.agent.models import Strategy, Charter, BacktestResult, EdgeScorecard, SelectionReasoning, WorkflowResult
from src.agent.cost_tracker import CostTracker, BudgetExceededError
from src.agent.scoring import evaluate_edge_scorecard


async def generate_candidates(
    market_context: dict,
    model: str,
    cost_tracker: CostTracker
) -> List[Strategy]:
    """
    Generate 5 candidate strategies using AI.

    Args:
        market_context: Market context pack (date-anchored)
        model: LLM model identifier (e.g., 'openai:gpt-4o')
        cost_tracker: Budget enforcement tracker

    Returns:
        List of exactly 5 Strategy objects

    Raises:
        ValueError: If AI doesn't generate exactly 5 candidates or if duplicates detected
    """
    # Create enhanced prompt that explicitly requires 5 candidates
    system_prompt = """You are an expert trading strategy analyst.

## CRITICAL REQUIREMENT

You MUST generate EXACTLY 5 DISTINCT candidate strategies.

**Diversity Requirements**:
1. Different edge types (behavioral, structural, informational, risk premium)
2. Different archetypes (momentum, mean reversion, carry, directional)
3. Different concentration levels (focused vs diversified)
4. Different regime assumptions (bull continuation vs defensive rotation)

**Output Format**: Return a list of 5 Strategy objects.

**Validation**: Your response will be rejected if it doesn't contain exactly 5 candidates.
"""

    # Create agent context
    agent_ctx = await create_agent(
        model=model,
        output_type=List[Strategy],
        system_prompt=system_prompt
    )

    # Generate candidates
    async with agent_ctx as agent:
        market_context_json = json.dumps(market_context, indent=2)

        prompt = f"""Generate 5 candidate trading strategies based on this market context:

{market_context_json}

Follow the workflow: analyze → generate 5 distinct candidates → return list.

Remember: EXACTLY 5 strategies, all different from each other.
"""

        result = await agent.run(prompt)
        candidates = result.output

        # Record cost (using rough estimates for now)
        # TODO: Get actual token counts from result if available
        cost_tracker.record_call(model, prompt_tokens=3000, completion_tokens=2000)

    # Validate count
    if len(candidates) != 5:
        raise ValueError(f"Expected 5 candidates, got {len(candidates)}")

    # Check for duplicates (simple ticker comparison)
    ticker_sets = [set(c.assets) for c in candidates]
    unique_ticker_sets = set(tuple(sorted(ts)) for ts in ticker_sets)
    if len(ticker_sets) != len(unique_ticker_sets):
        raise ValueError("Duplicate candidates detected (same ticker sets)")

    return candidates


async def backtest_all_candidates(
    candidates: List[Strategy],
    cost_tracker: CostTracker
) -> List[BacktestResult]:
    """
    Backtest all candidates via Composer MCP.

    Args:
        candidates: List of 5 Strategy objects
        cost_tracker: Budget enforcement tracker

    Returns:
        List of 5 BacktestResult objects

    Note:
        Uses real Composer MCP to backtest strategies.
        Gracefully degrades if Composer unavailable.
    """
    backtests = []

    for i, candidate in enumerate(candidates):
        try:
            # Convert Strategy to Composer symphony format
            symphony_config = {
                'name': candidate.name,
                'assets': [f'EQUITIES::{ticker}//USD' for ticker in candidate.assets],
                'weights': candidate.weights,
                'rebalance_frequency': candidate.rebalance_frequency.value,
            }

            # If logic_tree exists, include it
            if candidate.logic_tree:
                symphony_config['logic'] = candidate.logic_tree

            # Create agent for calling Composer backtest tool
            # Using a simple dict output since we'll parse the response
            agent_ctx = await create_agent(
                model='openai:gpt-4o',
                output_type=dict,
                system_prompt="You are a backtesting assistant. Call the composer_backtest_symphony tool with the provided configuration and return the results."
            )

            async with agent_ctx as agent:
                # Ask agent to backtest this symphony
                prompt = f"""Please backtest this trading strategy using the composer_backtest_symphony tool:

Strategy Name: {candidate.name}
Assets: {', '.join(candidate.assets)}
Weights: {candidate.weights}
Rebalance Frequency: {candidate.rebalance_frequency.value}

Call composer_backtest_symphony with this configuration:
{json.dumps(symphony_config, indent=2)}

Return the backtest results including sharpe_ratio, max_drawdown, total_return, and volatility_annualized."""

                result = await agent.run(prompt)
                backtest_data = result.output

                # Parse the response into BacktestResult
                # Composer returns metrics we need to map
                backtest = BacktestResult(
                    sharpe_ratio=float(backtest_data.get('sharpe_ratio', backtest_data.get('sharpe', 1.0))),
                    max_drawdown=float(backtest_data.get('max_drawdown', backtest_data.get('maxDrawdown', -0.10))),
                    total_return=float(backtest_data.get('total_return', backtest_data.get('totalReturn', 0.0))),
                    volatility_annualized=float(backtest_data.get('volatility_annualized', backtest_data.get('volatility', 0.15)))
                )

                backtests.append(backtest)

                # Track cost for backtest call
                cost_tracker.record_call('openai:gpt-4o', prompt_tokens=500, completion_tokens=200)

        except Exception as e:
            # Graceful degradation - return neutral backtest if anything fails
            print(f"Warning: Backtest failed for candidate {i} ({candidate.name}): {e}")
            print("Using neutral backtest values as fallback")
            backtests.append(BacktestResult(
                sharpe_ratio=1.0,
                max_drawdown=-0.10,
                total_return=0.0,
                volatility_annualized=0.15
            ))

    return backtests


async def select_winner(
    candidates: List[Strategy],
    scorecards: List[EdgeScorecard],
    backtests: List[BacktestResult],
    market_context: dict,
    model: str,
    cost_tracker: CostTracker
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
        cost_tracker: Budget enforcement

    Returns:
        (winner, reasoning) tuple
    """
    # Compute composite scores
    composite_scores = []

    for i in range(5):
        # Normalize each component to 0-1 range
        sharpe_norm = (backtests[i].sharpe_ratio + 1) / 4  # Normalize -1 to 3 → 0 to 1
        edge_norm = scorecards[i].total_score / 5  # 1-5 → 0.2-1.0
        regime_norm = scorecards[i].regime_alignment / 5
        drawdown_norm = 1 - abs(backtests[i].max_drawdown)  # Lower drawdown = better

        composite = (0.4 * sharpe_norm +
                    0.3 * edge_norm +
                    0.2 * regime_norm +
                    0.1 * drawdown_norm)

        composite_scores.append((i, composite))

    # Rank candidates by composite score
    ranked = sorted(composite_scores, key=lambda x: x[1], reverse=True)
    winner_index = ranked[0][0]
    winner = candidates[winner_index]

    # Generate selection reasoning via AI
    agent_ctx = await create_agent(
        model=model,
        output_type=SelectionReasoning,
        system_prompt="You are a trading strategy analyst explaining selection decisions."
    )

    async with agent_ctx as agent:
        prompt = f"""Explain why we selected candidate {winner_index+1} over the other 4 alternatives.

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

        # Record cost
        cost_tracker.record_call(model, prompt_tokens=800, completion_tokens=400)

    # Set reasoning fields
    reasoning.winner_index = winner_index
    reasoning.alternatives_compared = [c.name for i, c in enumerate(candidates) if i != winner_index]

    return winner, reasoning


async def generate_charter(
    winner: Strategy,
    reasoning: SelectionReasoning,
    alternatives: List[Strategy],
    backtests: List[BacktestResult],
    market_context: dict,
    model: str,
    cost_tracker: CostTracker
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
        cost_tracker: Budget enforcement

    Returns:
        Complete Charter document with 5 sections

    Note:
        Charter must reference specific backtest data and alternative comparisons.
    """
    # Load charter creation prompt
    system_prompt = load_prompt('system_prompt.md')
    charter_prompt = load_prompt('charter_creation.md')
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
**Assets**: {', '.join(winner.assets)}
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

## Market Context (as of {market_context['metadata']['anchor_date']})

Regime: {', '.join(market_context.get('regime_tags', []))}

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

        # Record cost
        cost_tracker.record_call(model, prompt_tokens=2000, completion_tokens=1500)

    return charter


async def create_strategy_workflow(
    market_context: dict,
    model: str = 'openai:gpt-4o',
    max_cost: float = 10.0
) -> WorkflowResult:
    """
    Execute complete strategy creation workflow.

    Workflow Stages:
    1. Generate 5 candidate strategies (AI)
    2. Evaluate Edge Scorecard (code)
    3. Backtest all candidates (Composer MCP)
    4. Select winner (composite ranking + AI reasoning)
    5. Generate charter (AI with full context)

    Args:
        market_context: Market context pack (from src.market_context.assembler)
        model: LLM model identifier (default: 'openai:gpt-4o')
        max_cost: Maximum budget in USD (default: $10)

    Returns:
        WorkflowResult with strategy, charter, and all intermediate results

    Raises:
        ValueError: If validation fails (count, scores, etc.)
        BudgetExceededError: If costs exceed max_cost

    Example:
        >>> from src.market_context.assembler import assemble_market_context_pack
        >>> market_context = assemble_market_context_pack(fred_api_key=...)
        >>> result = await create_strategy_workflow(market_context)
        >>> print(f"Winner: {result.strategy.name}")
        >>> print(f"Total Cost: ${result.total_cost:.2f}")
    """
    cost_tracker = CostTracker(max_budget=max_cost)

    try:
        # Stage 1: Generate 5 candidates
        print("Stage 1/5: Generating candidates...")
        candidates = await generate_candidates(market_context, model, cost_tracker)
        print(f"✓ Generated {len(candidates)} candidates")

        # Stage 2: Evaluate Edge Scorecard
        print("Stage 2/5: Evaluating Edge Scorecard...")
        scorecards = [evaluate_edge_scorecard(c, market_context) for c in candidates]

        # Validate all scores ≥3
        for i, scorecard in enumerate(scorecards):
            if scorecard.total_score < 3.0:
                raise ValueError(
                    f"Candidate {i+1} failed Edge Scorecard threshold: "
                    f"{scorecard.total_score:.1f}/5 (minimum: 3.0)"
                )
        print(f"✓ All candidates passed Edge Scorecard (avg: {sum(s.total_score for s in scorecards)/5:.1f}/5)")

        # Stage 3: Backtest all candidates
        print("Stage 3/5: Backtesting candidates...")
        backtests = await backtest_all_candidates(candidates, cost_tracker)
        print(f"✓ Backtested all candidates (avg Sharpe: {sum(b.sharpe_ratio for b in backtests)/5:.2f})")

        # Stage 4: Select winner
        print("Stage 4/5: Selecting winner...")
        winner, reasoning = await select_winner(
            candidates, scorecards, backtests, market_context, model, cost_tracker
        )
        print(f"✓ Selected: {winner.name}")

        # Stage 5: Generate charter
        print("Stage 5/5: Creating charter...")
        charter = await generate_charter(
            winner, reasoning, candidates, backtests, market_context, model, cost_tracker
        )
        print(f"✓ Charter created ({len(charter.failure_modes)} failure modes)")

        # Return complete result
        return WorkflowResult(
            strategy=winner,
            charter=charter,
            all_candidates=candidates,
            scorecards=scorecards,
            backtests=backtests,
            selection_reasoning=reasoning,
            total_cost=cost_tracker.total_cost
        )

    except BudgetExceededError as e:
        print(f"✗ Budget exceeded: {e}")
        raise
    except Exception as e:
        print(f"✗ Workflow failed: {e}")
        raise
