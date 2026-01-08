"""
Strategy creation workflow orchestration.

This module implements the multi-stage workflow for generating,
evaluating, and selecting trading strategies.

Supports checkpoint/resume for fault tolerance:
- After each stage completes, state is checkpointed to disk
- On resume, workflow skips completed stages and continues from checkpoint
- Checkpoint is cleared on successful completion
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import List
from src.agent.strategy_creator import create_agent, DEFAULT_MODEL
from src.agent.models import (
    Strategy,
    WorkflowResult,
    WorkflowStage,
    WorkflowCheckpoint,
)
from src.agent.stages import (
    CandidateGenerator,
    QuotaExhaustedError,
    EdgeScorer,
    WinnerSelector,
    CharterGenerator,
    ComposerDeployer,
)
from src.agent.persistence import (
    save_workflow_result,
    save_checkpoint,
    clear_checkpoint,
)
from src.agent.mcp_config import set_summarization_model


def _parse_model_list(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _canonical_model(model: str) -> str:
    if model.startswith("gemini:"):
        return f"google-gla:{model.split(':', 1)[1]}"
    return model


def _dedupe_models(models: List[str]) -> List[str]:
    seen: set[str] = set()
    deduped: List[str] = []
    for model in models:
        key = _canonical_model(model)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(model)
    return deduped


def _auto_fallback_models() -> List[str]:
    models: List[str] = []
    if os.getenv("GOOGLE_API_KEY"):
        models.append("google-gla:gemini-3-pro-preview")
    if os.getenv("DEEPSEEK_API_KEY"):
        models.append("openai:deepseek-chat")
    if os.getenv("KIMI_API_KEY"):
        models.append("openai:kimi-k2-thinking")
    if os.getenv("ANTHROPIC_API_KEY"):
        models.append("anthropic:claude-3-5-sonnet-20241022")
    return models


def _resolve_fallback_models(user_fallbacks: List[str] | None) -> List[str]:
    if user_fallbacks is not None:
        return _dedupe_models([m.strip() for m in user_fallbacks if m.strip()])

    env_fallbacks = _parse_model_list(os.getenv("MODEL_FALLBACKS"))
    if env_fallbacks:
        return _dedupe_models(env_fallbacks)

    return _dedupe_models(_auto_fallback_models())


def _create_checkpoint(
    stage: WorkflowStage,
    model: str,
    cohort_id: str,
    market_context: dict,
    candidates: List[Strategy] | None = None,
    scorecards: list | None = None,
    winner: Strategy | None = None,
    selection_reasoning=None,
    charter=None,
    symphony_id: str | None = None,
    deployed_at: str | None = None,
    strategy_summary: str | None = None,
    existing_checkpoint: WorkflowCheckpoint | None = None,
) -> WorkflowCheckpoint:
    """Create a checkpoint with current workflow state."""
    now = datetime.now(timezone.utc).isoformat()

    return WorkflowCheckpoint(
        last_completed_stage=stage,
        created_at=existing_checkpoint.created_at if existing_checkpoint else now,
        updated_at=now,
        model=model,
        cohort_id=cohort_id,
        market_context=market_context,
        candidates=candidates,
        scorecards=scorecards,
        winner=winner,
        selection_reasoning=selection_reasoning,
        charter=charter,
        symphony_id=symphony_id,
        deployed_at=deployed_at,
        strategy_summary=strategy_summary,
    )


async def create_strategy_workflow(
    market_context: dict,
    model: str = DEFAULT_MODEL,
    cohort_id: str | None = None,
    resume_checkpoint: WorkflowCheckpoint | None = None,
    fallback_models: List[str] | None = None,
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
            If provided, saves WorkflowResult to data/cohorts/{cohort_id}/strategies.json
            and enables checkpoint/resume functionality.
        resume_checkpoint: Optional checkpoint to resume from. If provided, skips
            completed stages and uses cached results from checkpoint.
        fallback_models: Optional list of fallback models to try if the primary model
            fails due to hard quota exhaustion. If None, uses MODEL_FALLBACKS env var
            (comma-separated), otherwise auto-detects available non-OpenAI providers.

    Returns:
        WorkflowResult with strategy, charter, and all intermediate results

    Raises:
        ValueError: If validation fails (count, scores, etc.)

    Note:
        Stage 1 uses market context pack as primary data source. MCP tools
        (FRED, yfinance, Composer) are available but usage is optional - AI
        calls them only for data gaps not covered by context pack.

        Checkpoint/Resume: When cohort_id is provided, workflow saves checkpoints
        after each stage. If workflow fails, pass the checkpoint to resume_checkpoint
        to continue from last completed stage.

    Example:
        >>> from src.market_context.assembler import assemble_market_context_pack
        >>> market_context = assemble_market_context_pack(fred_api_key=...)
        >>> result = await create_strategy_workflow(market_context)
        >>> print(f"Winner: {result.strategy.name}")

        # Resume from checkpoint:
        >>> from src.agent.persistence import load_checkpoint
        >>> checkpoint = load_checkpoint("2025-Q1")
        >>> result = await create_strategy_workflow(
        ...     market_context=checkpoint.market_context,
        ...     model=checkpoint.model,
        ...     cohort_id="2025-Q1",
        ...     resume_checkpoint=checkpoint
        ... )
    """

    # Set summarization model to match workflow model (may change if fallback is used)
    set_summarization_model(model)

    # Determine resume stage (None = fresh start)
    resume_stage = resume_checkpoint.get_resume_stage() if resume_checkpoint else None
    if resume_stage:
        print(f"🔄 Resuming workflow from stage: {resume_stage.value}")

        # Check if workflow is already complete
        if resume_stage == WorkflowStage.COMPLETE:
            print("✓ Workflow already complete. Nothing to resume.")
            # Use model_construct to bypass validation for cached checkpoint data
            return WorkflowResult.model_construct(
                strategy=resume_checkpoint.winner,
                charter=resume_checkpoint.charter,
                all_candidates=resume_checkpoint.candidates,
                scorecards=resume_checkpoint.scorecards,
                selection_reasoning=resume_checkpoint.selection_reasoning,
                symphony_id=resume_checkpoint.symphony_id,
                deployed_at=resume_checkpoint.deployed_at,
                strategy_summary=resume_checkpoint.strategy_summary,
            )

    resolved_fallbacks = _resolve_fallback_models(fallback_models)
    if resume_checkpoint and resolved_fallbacks:
        print("⚠️  Fallback models ignored when resuming to preserve model consistency.")
        resolved_fallbacks = []

    # Instantiate stage classes
    candidate_gen = CandidateGenerator()
    edge_scorer = EdgeScorer()
    selector = WinnerSelector()
    charter_gen = CharterGenerator()
    deployer = ComposerDeployer()

    # Initialize results from checkpoint or fresh
    candidates = resume_checkpoint.candidates if resume_checkpoint else None
    scorecards = resume_checkpoint.scorecards if resume_checkpoint else None
    winner = resume_checkpoint.winner if resume_checkpoint else None
    reasoning = resume_checkpoint.selection_reasoning if resume_checkpoint else None
    charter = resume_checkpoint.charter if resume_checkpoint else None
    symphony_id = resume_checkpoint.symphony_id if resume_checkpoint else None
    deployed_at = resume_checkpoint.deployed_at if resume_checkpoint else None
    strategy_summary = resume_checkpoint.strategy_summary if resume_checkpoint else None

    # Helper to check if we should skip a stage
    def should_run_stage(stage: WorkflowStage) -> bool:
        if not resume_stage:
            return True  # Fresh start, run all stages
        stage_order = [
            WorkflowStage.CANDIDATES,
            WorkflowStage.SCORING,
            WorkflowStage.SELECTION,
            WorkflowStage.CHARTER,
            WorkflowStage.DEPLOYMENT,
        ]
        return stage_order.index(stage) >= stage_order.index(resume_stage)

    # Stage 1: Generate 5 candidates (single-phase with optional tool usage)
    if should_run_stage(WorkflowStage.CANDIDATES):
        print("Stage 1/5: Generating candidates...")
        candidate_models = _dedupe_models([model] + resolved_fallbacks)
        candidates = None
        last_quota_error: Exception | None = None

        for idx, candidate_model in enumerate(candidate_models):
            set_summarization_model(candidate_model)
            try:
                candidates = await candidate_gen.generate(market_context, candidate_model)
                if candidate_model != model:
                    print(f"⚠️  Using fallback model for remainder of workflow: {candidate_model}")
                    model = candidate_model
                break
            except QuotaExhaustedError as err:
                last_quota_error = err
                print(f"⚠️  {err}")
                if idx < len(candidate_models) - 1:
                    print(f"⚠️  Trying fallback model: {candidate_models[idx + 1]}")
                continue

        if candidates is None:
            if last_quota_error is not None:
                hint = ""
                if not resolved_fallbacks:
                    hint = " Configure MODEL_FALLBACKS or pass --fallback-models to use a different provider."
                raise RuntimeError(
                    f"Candidate generation failed due to quota exhaustion for {model}.{hint}"
                ) from last_quota_error
            raise RuntimeError("Candidate generation failed for all models.")
        print(f"✓ Generated {len(candidates)} candidates")

        # Save checkpoint after Stage 1
        if cohort_id:
            checkpoint = _create_checkpoint(
                stage=WorkflowStage.CANDIDATES,
                model=model,
                cohort_id=cohort_id,
                market_context=market_context,
                candidates=candidates,
                existing_checkpoint=resume_checkpoint,
            )
            save_checkpoint(checkpoint, cohort_id)
    else:
        print("Stage 1/5: Generating candidates... (skipped - using checkpoint)")
        print(f"✓ Loaded {len(candidates)} candidates from checkpoint")

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
    if should_run_stage(WorkflowStage.SCORING):
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

        # Save checkpoint after Stage 2
        if cohort_id:
            checkpoint = _create_checkpoint(
                stage=WorkflowStage.SCORING,
                model=model,
                cohort_id=cohort_id,
                market_context=market_context,
                candidates=candidates,
                scorecards=list(scorecards),
                existing_checkpoint=resume_checkpoint,
            )
            save_checkpoint(checkpoint, cohort_id)
    else:
        print("Stage 2/5: Evaluating Edge Scorecard... (skipped - using checkpoint)")
        print(f"✓ Loaded {len(scorecards)} scorecards from checkpoint")

    # Stage 3: Select winner
    if should_run_stage(WorkflowStage.SELECTION):
        print("Stage 3/5: Selecting winner...")
        winner, reasoning = await selector.select(
            candidates, scorecards, market_context, model
        )
        print(f"✓ Selected: {winner.name}")

        # Save checkpoint after Stage 3
        if cohort_id:
            checkpoint = _create_checkpoint(
                stage=WorkflowStage.SELECTION,
                model=model,
                cohort_id=cohort_id,
                market_context=market_context,
                candidates=candidates,
                scorecards=list(scorecards),
                winner=winner,
                selection_reasoning=reasoning,
                existing_checkpoint=resume_checkpoint,
            )
            save_checkpoint(checkpoint, cohort_id)
    else:
        print("Stage 3/5: Selecting winner... (skipped - using checkpoint)")
        print(f"✓ Loaded winner: {winner.name}")

    # Stage 4: Generate charter
    if should_run_stage(WorkflowStage.CHARTER):
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

        # Save checkpoint after Stage 4
        if cohort_id:
            checkpoint = _create_checkpoint(
                stage=WorkflowStage.CHARTER,
                model=model,
                cohort_id=cohort_id,
                market_context=market_context,
                candidates=candidates,
                scorecards=list(scorecards),
                winner=winner,
                selection_reasoning=reasoning,
                charter=charter,
                existing_checkpoint=resume_checkpoint,
            )
            save_checkpoint(checkpoint, cohort_id)
    else:
        print("Stage 4/5: Creating charter... (skipped - using checkpoint)")
        print(f"✓ Loaded charter ({len(charter.failure_modes)} failure modes)")

    # Stage 5: Deploy to Composer (optional, graceful degradation)
    if should_run_stage(WorkflowStage.DEPLOYMENT):
        print("Stage 5/5: Deploying to Composer...")
        symphony_id, deployed_at, strategy_summary = await deployer.deploy(winner, charter, market_context, model)
        if symphony_id:
            print(f"✓ Deployed symphony: {symphony_id}")
            if strategy_summary:
                print(f"✓ Captured strategy summary")
        else:
            print("⚠️  Deployment skipped (Composer unavailable)")

        # Save checkpoint after Stage 5 only on success (failed deployment = retry from CHARTER)
        if cohort_id and symphony_id:
            checkpoint = _create_checkpoint(
                stage=WorkflowStage.DEPLOYMENT,
                model=model,
                cohort_id=cohort_id,
                market_context=market_context,
                candidates=candidates,
                scorecards=list(scorecards),
                winner=winner,
                selection_reasoning=reasoning,
                charter=charter,
                symphony_id=symphony_id,
                deployed_at=deployed_at,
                strategy_summary=strategy_summary,
                existing_checkpoint=resume_checkpoint,
            )
            save_checkpoint(checkpoint, cohort_id)
    else:
        print("Stage 5/5: Deploying to Composer... (skipped - using checkpoint)")
        if symphony_id:
            print(f"✓ Loaded symphony: {symphony_id}")
        else:
            print("⚠️  Deployment was skipped in original run")

    # Build complete result
    result = WorkflowResult(
        strategy=winner,
        charter=charter,
        all_candidates=candidates,
        scorecards=scorecards,
        selection_reasoning=reasoning,
        symphony_id=symphony_id,
        deployed_at=deployed_at,
        strategy_summary=strategy_summary,
    )

    # Persist to cohort file if cohort_id provided
    if cohort_id:
        save_workflow_result(result, cohort_id, model=model)
        # Only clear checkpoint on full success (deployment completed)
        if symphony_id:
            clear_checkpoint(cohort_id)
        else:
            print("💾 Checkpoint preserved (deployment incomplete)")

    return result
