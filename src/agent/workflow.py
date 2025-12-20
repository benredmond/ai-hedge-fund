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
    ComposerDeployer,
)
from src.agent.persistence import save_workflow_result


async def create_strategy_workflow(
    market_context: dict,
    model: str = DEFAULT_MODEL,
    cohort_id: str | None = None,
) -> WorkflowResult:
    """
    Execute complete strategy creation workflow.

    Workflow Stages:
    1. Generate 5 candidate strategies (AI with optional tool usage)
    2. Evaluate Edge Scorecard (AI scoring)
    3. Select winner (composite ranking + AI reasoning)
    4. Generate charter (AI with full context)
    5. Deploy to Composer (optional, graceful degradation if unavailable)

    Args:
        market_context: Market context pack (from src.market_context.assembler)
            Should include comprehensive regime analysis, sector data, and
            optional manual Composer pattern examples for pattern inspiration.
        model: LLM model identifier (default: from DEFAULT_MODEL env var or 'openai:gpt-4o')
        cohort_id: Optional cohort identifier for persistence (e.g., "2025-Q1").
            If provided, saves WorkflowResult to data/cohorts/{cohort_id}/strategies.json.

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
    deployer = ComposerDeployer()

    # Stage 1: Generate 5 candidates (single-phase with optional tool usage)
    print("Stage 1/5: Generating candidates...")
    candidates = await candidate_gen.generate(market_context, model)
    print(f"✓ Generated {len(candidates)} candidates")

    # Debug: Print candidate details
    print("\n" + "="*80)
    print("GENERATED CANDIDATES:")
    print("="*80)
    for i, candidate in enumerate(candidates, 1):
        print(f"\n{i}. {candidate.name}")
        print(f"   Assets: {', '.join(candidate.assets)}")
        # Handle weights as dict (model converts list to dict in validator)
        if isinstance(candidate.weights, dict):
            weight_strs = [f"{asset}: {weight:.2%}" for asset, weight in candidate.weights.items()]
            print(f"   Weights: {', '.join(weight_strs)}")
        else:
            print(f"   Weights: {candidate.weights}")
        print(f"   Rebalance: {candidate.rebalance_frequency.value}")
        print(f"   Logic Tree: {'Yes' if candidate.logic_tree else 'Static allocation'}")
    print("="*80 + "\n")

    # Stage 2: Evaluate Edge Scorecard (parallel scoring)
    print("Stage 2/5: Evaluating Edge Scorecard...")
    scoring_tasks = [
        edge_scorer.score(candidate, market_context, model)
        for candidate in candidates
    ]
    scorecards = await asyncio.gather(*scoring_tasks)

    # Filter candidates by Edge Scorecard threshold (≥3.0)
    # Log failures but allow partial success (winner_selector will handle filtering)
    passing_indices = []
    for i, scorecard in enumerate(scorecards):
        if scorecard.total_score >= 3.0:
            passing_indices.append(i)
        else:
            print(
                f"⚠️  Candidate {i + 1} failed Edge Scorecard: {scorecard.total_score:.1f}/5 "
                f"(thesis={scorecard.thesis_quality}, edge={scorecard.edge_economics}, "
                f"risk={scorecard.risk_framework}, regime={scorecard.regime_awareness}, "
                f"coherence={scorecard.strategic_coherence})"
            )

    print(f"✓ {len(passing_indices)}/5 candidates passed Edge Scorecard (avg: {sum(s.total_score for s in scorecards) / 5:.1f}/5)")

    # Stage 3: Select winner
    print("Stage 3/5: Selecting winner...")
    winner, reasoning = await selector.select(
        candidates, scorecards, market_context, model
    )
    print(f"✓ Selected: {winner.name}")

    # Stage 4: Generate charter
    print("Stage 4/5: Creating charter...")
    charter = await charter_gen.generate(
        winner,
        reasoning,
        candidates,
        scorecards,
        market_context,
        model,
    )
    print(f"✓ Charter created ({len(charter.failure_modes)} failure modes)")

    # Stage 5: Deploy to Composer (optional, graceful degradation)
    print("Stage 5/5: Deploying to Composer...")
    symphony_id, deployed_at = await deployer.deploy(winner, charter, market_context, model)
    if symphony_id:
        print(f"✓ Deployed symphony: {symphony_id}")
    else:
        print("⚠️  Deployment skipped (Composer unavailable)")

    # Build complete result
    result = WorkflowResult(
        strategy=winner,
        charter=charter,
        all_candidates=candidates,
        scorecards=scorecards,
        selection_reasoning=reasoning,
        symphony_id=symphony_id,
        deployed_at=deployed_at,
    )

    # Persist to cohort file if cohort_id provided
    if cohort_id:
        save_workflow_result(result, cohort_id)

    return result
