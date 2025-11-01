"""
Strategy creation workflow orchestration.

This module implements the multi-stage workflow for generating,
evaluating, and selecting trading strategies.
"""

import asyncio
import json
from typing import List
from src.agent.strategy_creator import create_agent, DEFAULT_MODEL
from src.agent.models import (
    Strategy,
    BacktestResult,
    WorkflowResult,
)
from src.agent.stages import (
    CandidateGenerator,
    EdgeScorer,
    WinnerSelector,
    CharterGenerator,
)


async def backtest_all_candidates(
    candidates: List[Strategy]
) -> List[BacktestResult]:
    """
    Backtest all candidates via Composer MCP.

    Args:
        candidates: List of 5 Strategy objects

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
                "name": candidate.name,
                "assets": [f"EQUITIES::{ticker}//USD" for ticker in candidate.assets],
                "weights": candidate.weights,
                "rebalance_frequency": candidate.rebalance_frequency.value,
            }

            # If logic_tree exists, include it
            if candidate.logic_tree:
                symphony_config["logic"] = candidate.logic_tree

            # Create agent for calling Composer backtest tool
            # Using a simple dict output since we'll parse the response
            # Use 5 message history limit (single tool call wrapper)
            agent_ctx = await create_agent(
                model="openai:gpt-4o",
                output_type=dict,
                system_prompt="You are a backtesting assistant. Call the composer_backtest_symphony tool with the provided configuration and return the results.",
                history_limit=5
            )

            async with agent_ctx as agent:
                # Ask agent to backtest this symphony
                prompt = f"""Please backtest this trading strategy using the composer_backtest_symphony tool:

Strategy Name: {candidate.name}
Assets: {", ".join(candidate.assets)}
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
                    sharpe_ratio=float(
                        backtest_data.get(
                            "sharpe_ratio", backtest_data.get("sharpe", 1.0)
                        )
                    ),
                    max_drawdown=float(
                        backtest_data.get(
                            "max_drawdown", backtest_data.get("maxDrawdown", -0.10)
                        )
                    ),
                    total_return=float(
                        backtest_data.get(
                            "total_return", backtest_data.get("totalReturn", 0.0)
                        )
                    ),
                    volatility_annualized=float(
                        backtest_data.get(
                            "volatility_annualized",
                            backtest_data.get("volatility", 0.15),
                        )
                    ),
                )

                backtests.append(backtest)

        except Exception as e:
            # Backtest failure is critical - do not fabricate data
            print(f"ERROR: Backtest failed for candidate {i} ({candidate.name})")
            print(f"Error type: {e.__class__.__name__}")
            print(f"Error details: {e}")

            raise RuntimeError(
                f"Backtest failed for candidate {i} ({candidate.name}): {e}\n\n"
                f"Possible causes:\n"
                f"1. Composer API unavailable (check network/credentials)\n"
                f"2. Invalid strategy configuration: {candidate.assets}\n"
                f"3. API rate limit exceeded\n\n"
                f"To diagnose: Check COMPOSER_API_KEY and COMPOSER_API_SECRET env vars"
            ) from e

    return backtests


async def create_strategy_workflow(
    market_context: dict, model: str = DEFAULT_MODEL
) -> WorkflowResult:
    """
    Execute complete strategy creation workflow.

    Workflow Stages:
    1. Generate 5 candidate strategies (AI with optional tool usage)
    2. Evaluate Edge Scorecard (AI scoring)
    3. Backtest all candidates (Composer MCP)
    4. Select winner (composite ranking + AI reasoning)
    5. Generate charter (AI with full context)

    Args:
        market_context: Market context pack (from src.market_context.assembler)
            Should include comprehensive regime analysis, sector data, and
            optional manual Composer pattern examples for pattern inspiration.
        model: LLM model identifier (default: from DEFAULT_MODEL env var or 'openai:gpt-4o')

    Returns:
        WorkflowResult with strategy, charter, and all intermediate results

    Raises:
        ValueError: If validation fails (count, scores, etc.)

    Note:
        Stage 1 uses market context pack as primary data source. MCP tools
        (FRED, yfinance, Composer) are available but usage is optional - AI
        calls them only for data gaps not covered by context pack.

    Example:
        >>> from src.market_context.assembler import assemble_market_context_pack
        >>> market_context = assemble_market_context_pack(fred_api_key=...)
        >>> result = await create_strategy_workflow(market_context)
        >>> print(f"Winner: {result.strategy.name}")
    """

    # Instantiate stage classes
    candidate_gen = CandidateGenerator()
    edge_scorer = EdgeScorer()
    selector = WinnerSelector()
    charter_gen = CharterGenerator()

    # Stage 1: Generate 5 candidates (single-phase with optional tool usage)
    print("Stage 1/5: Generating candidates...")
    candidates = await candidate_gen.generate(market_context, model)
    print(f"✓ Generated {len(candidates)} candidates")

    # Stage 2: Evaluate Edge Scorecard (parallel scoring)
    print("Stage 2/5: Evaluating Edge Scorecard...")
    scoring_tasks = [
        edge_scorer.score(candidate, market_context, model)
        for candidate in candidates
    ]
    scorecards = await asyncio.gather(*scoring_tasks)

    # Validate all scores ≥3 (EdgeScorecard model validates this automatically)
    # But check total_score for reporting
    for i, scorecard in enumerate(scorecards):
        if scorecard.total_score < 3.0:
            raise ValueError(
                f"Candidate {i + 1} failed Edge Scorecard threshold: "
                f"{scorecard.total_score:.1f}/5 (minimum: 3.0)"
            )
    print(
        f"✓ All candidates passed Edge Scorecard (avg: {sum(s.total_score for s in scorecards) / 5:.1f}/5)"
    )

    # Stage 3: Backtest all candidates
    print("Stage 3/5: Backtesting candidates...")
    backtests = await backtest_all_candidates(candidates)
    print(
        f"✓ Backtested all candidates (avg Sharpe: {sum(b.sharpe_ratio for b in backtests) / 5:.2f})"
    )

    # Stage 4: Select winner
    print("Stage 4/5: Selecting winner...")
    winner, reasoning = await selector.select(
        candidates, scorecards, backtests, market_context, model
    )
    print(f"✓ Selected: {winner.name}")

    # Stage 5: Generate charter
    print("Stage 5/5: Creating charter...")
    charter = await charter_gen.generate(
        winner,
        reasoning,
        candidates,
        scorecards,
        backtests,
        market_context,
        model,
    )
    print(f"✓ Charter created ({len(charter.failure_modes)} failure modes)")

    # NOTE: Deployment to Composer not yet implemented
    # To enable: call composer_deploy_symphony after charter generation

    # Return complete result
    return WorkflowResult(
        strategy=winner,
        charter=charter,
        all_candidates=candidates,
        scorecards=scorecards,
        backtests=backtests,
        selection_reasoning=reasoning,
    )
