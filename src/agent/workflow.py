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
    WorkflowResult,
)
from src.agent.stages import (
    CandidateGenerator,
    EdgeScorer,
    WinnerSelector,
    CharterGenerator,
)


async def create_strategy_workflow(
    market_context: dict, model: str = DEFAULT_MODEL
) -> WorkflowResult:
    """
    Execute complete strategy creation workflow.

    Workflow Stages:
    1. Generate 5 candidate strategies (AI with optional tool usage)
    2. Evaluate Edge Scorecard (AI scoring)
    3. Select winner (composite ranking + AI reasoning)
    4. Generate charter (AI with full context)

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
    print("Stage 1/4: Generating candidates...")
    candidates = await candidate_gen.generate(market_context, model)
    print(f"✓ Generated {len(candidates)} candidates")

    # Stage 2: Evaluate Edge Scorecard (parallel scoring)
    print("Stage 2/4: Evaluating Edge Scorecard...")
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

    # Stage 3: Select winner
    print("Stage 3/4: Selecting winner...")
    winner, reasoning = await selector.select(
        candidates, scorecards, market_context, model
    )
    print(f"✓ Selected: {winner.name}")

    # Stage 4: Generate charter
    print("Stage 4/4: Creating charter...")
    charter = await charter_gen.generate(
        winner,
        reasoning,
        candidates,
        scorecards,
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
        selection_reasoning=reasoning,
    )
