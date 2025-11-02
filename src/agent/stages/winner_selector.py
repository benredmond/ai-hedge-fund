"""Select best strategy from candidates using composite ranking."""

from typing import List, Tuple
from src.agent.strategy_creator import create_agent, load_prompt, DEFAULT_MODEL
from src.agent.models import (
    Strategy,
    EdgeScorecard,
    SelectionReasoning
)


class WinnerSelector:
    """
    Stage 3: Select winner from 5 candidates.

    Uses composite ranking based on Edge Scorecard dimensions.
    Generates AI reasoning for selection.
    """

    async def select(
        self,
        candidates: List[Strategy],
        scorecards: List[EdgeScorecard],
        market_context: dict,
        model: str = DEFAULT_MODEL
    ) -> Tuple[Strategy, SelectionReasoning]:
        """
        Select best candidate using composite ranking and AI reasoning.

        Composite Ranking Formula (for initial ordering):
            score = 0.50 × (Thesis + Edge + Risk)/3 + 0.30 × Regime + 0.20 × Coherence

        Note: AI may override composite ranking if strategic reasoning justifies it.

        Args:
            candidates: 5 strategies
            scorecards: 5 edge scorecards (with 5-dimension rubric)
            market_context: Current market conditions
            model: LLM for reasoning generation

        Returns:
            (winner, reasoning) tuple

        Example:
            >>> selector = WinnerSelector()
            >>> winner, reasoning = await selector.select(candidates, scorecards, context)
            >>> print(f"Selected: {winner.name} - {reasoning.why_selected[:100]}...")
        """
        # Extract regime tags for context
        regime_tags = market_context.get("regime_tags", [])

        # Filter to passing candidates only (scorecard.total_score ≥ 3.0)
        passing_pairs = [
            (i, c, s) for i, (c, s) in enumerate(zip(candidates, scorecards))
            if s.total_score >= 3.0
        ]

        if len(passing_pairs) < 3:
            # Detailed error with all scores for debugging
            all_scores = "\n".join([
                f"  Candidate {i+1}: {s.total_score:.1f}/5 "
                f"(thesis={s.thesis_quality}, edge={s.edge_economics}, "
                f"risk={s.risk_framework}, regime={s.regime_awareness}, coherence={s.strategic_coherence})"
                for i, s in enumerate(scorecards)
            ])
            raise ValueError(
                f"Only {len(passing_pairs)}/5 candidates passed Edge Scorecard validation (need ≥3).\n"
                f"Scores:\n{all_scores}\n"
                f"Likely cause: Prompt changes reduced strategy quality or LLM generated weak edges.\n"
                f"Review candidate_generation prompts and generated thesis_document content."
            )

        # Extract filtered candidates and scorecards for processing
        filtered_indices, filtered_candidates, filtered_scorecards = zip(*passing_pairs)
        filtered_candidates = list(filtered_candidates)
        filtered_scorecards = list(filtered_scorecards)

        print(f"Selecting winner from {len(filtered_candidates)} passing candidates (filtered {5 - len(filtered_candidates)} low-scoring)")

        # Compute composite scores for initial ranking
        composite_scores = []

        for i in range(len(filtered_scorecards)):
            # Strategic reasoning quality (average of thesis, edge, risk)
            # Note: EdgeScorecard uses 5-dimension rubric
            if hasattr(filtered_scorecards[i], 'thesis_quality'):
                # 5-dimension rubric
                reasoning_norm = (
                    filtered_scorecards[i].thesis_quality +
                    filtered_scorecards[i].edge_economics +
                    filtered_scorecards[i].risk_framework
                ) / 15.0  # Average of 3 dimensions, each 1-5
                regime_norm = filtered_scorecards[i].regime_awareness / 5.0
                coherence_norm = filtered_scorecards[i].strategic_coherence / 5.0
            else:
                # Old 6-dimension rubric (backwards compatibility)
                reasoning_norm = (
                    filtered_scorecards[i].specificity +
                    filtered_scorecards[i].structural_basis +
                    filtered_scorecards[i].failure_clarity
                ) / 15.0
                regime_norm = filtered_scorecards[i].regime_alignment / 5.0
                coherence_norm = filtered_scorecards[i].mental_model_coherence / 5.0

            # Weighted composite score (Edge Scorecard only)
            composite = (
                0.50 * reasoning_norm +
                0.30 * regime_norm +
                0.20 * coherence_norm
            )

            composite_scores.append((i, composite))

        # Rank candidates by composite score
        ranked = sorted(composite_scores, key=lambda x: x[1], reverse=True)

        # Build rich context for AI selection
        # Use 10 message history limit (single-pass reasoning, no tool usage)
        agent_ctx = await create_agent(
            model=model,
            output_type=SelectionReasoning,
            system_prompt=load_prompt("winner_selection.md"),
            history_limit=10
        )

        async with agent_ctx as agent:
            # Build comprehensive evaluation prompt
            num_candidates = len(filtered_candidates)
            prompt = f"""Select the best trading strategy from these {num_candidates} candidates for 90-day deployment.

**Note**: {5 - num_candidates} candidates failed Edge Scorecard validation and were filtered out.

## Market Context

**Regime Tags**: {", ".join(regime_tags)}
**Current Conditions**: {market_context.get("regime_snapshot", {}).get("trend_classification", "unknown")} trend, {market_context.get("regime_snapshot", {}).get("volatility_regime", "unknown")} volatility

## Candidate Evaluation Data

"""
            # Add detailed data for each passing candidate
            for idx in range(num_candidates):
                rank_position = next((rank + 1 for rank, (i, _) in enumerate(ranked) if i == idx), 0)
                composite = composite_scores[idx][1]
                original_idx = filtered_indices[idx]

                prompt += f"""
### Filtered Candidate #{idx + 1} (was Original #{original_idx + 1}): {filtered_candidates[idx].name} (Rank: #{rank_position}, Composite: {composite:.3f})

**Strategy Overview:**
- Assets: {", ".join(filtered_candidates[idx].assets[:5])}{"..." if len(filtered_candidates[idx].assets) > 5 else ""}
- Weights: {dict(list(filtered_candidates[idx].weights.items())[:3])}{"..." if len(filtered_candidates[idx].weights) > 3 else ""}
- Rebalancing: {filtered_candidates[idx].rebalance_frequency.value}

**Edge Scorecard:**
"""
                # Add scores (works with both old and new rubric)
                if hasattr(filtered_scorecards[idx], 'thesis_quality'):
                    # New 5-dimension rubric
                    prompt += f"""- Thesis Quality: {filtered_scorecards[idx].thesis_quality}/5
- Edge Economics: {filtered_scorecards[idx].edge_economics}/5
- Risk Framework: {filtered_scorecards[idx].risk_framework}/5
- Regime Awareness: {filtered_scorecards[idx].regime_awareness}/5
- Strategic Coherence: {filtered_scorecards[idx].strategic_coherence}/5
- **Total Score**: {filtered_scorecards[idx].total_score:.1f}/5

"""
                else:
                    # Old 6-dimension rubric
                    prompt += f"""- Specificity: {filtered_scorecards[idx].specificity}/5
- Structural Basis: {filtered_scorecards[idx].structural_basis}/5
- Regime Alignment: {filtered_scorecards[idx].regime_alignment}/5
- Differentiation: {filtered_scorecards[idx].differentiation}/5
- Failure Clarity: {filtered_scorecards[idx].failure_clarity}/5
- Mental Model Coherence: {filtered_scorecards[idx].mental_model_coherence}/5
- **Total Score**: {filtered_scorecards[idx].total_score:.1f}/5

"""

            prompt += f"""
## Your Task

Select the winner and provide comprehensive selection reasoning following the framework in your system prompt.

**Key Reminders:**
1. **Process quality**: Favor strategies with strong thesis/edge/risk reasoning and strategic coherence
2. **Tradeoffs matter**: Make explicit what you're optimizing for vs sacrificing
3. **Regime context**: Match strategy to current market conditions
4. **Risk awareness**: Enumerate failure scenarios and monitoring priorities

**Output Requirements:**
- winner_index: 0-{num_candidates - 1} (IMPORTANT: Index in FILTERED list above, NOT original candidate number)
  Example: To select "Filtered Candidate #2", use winner_index=1 (zero-indexed)
- why_selected: Detailed explanation (100-5000 chars) citing specific scores and metrics
- tradeoffs_accepted: Key tradeoffs in choosing this strategy (50-2000 chars)
- alternatives_rejected: List of {num_candidates - 1} rejected candidate names with brief reasons
- conviction_level: Confidence in selection (0.0-1.0) based on score delta and consistency

Return structured SelectionReasoning output.
"""

            result = await agent.run(prompt)
            reasoning = result.output

        # Debug logging: Print full LLM response
        print(f"\n[DEBUG:WinnerSelector] Full LLM response:")
        print(f"{reasoning}")

        # Validate and set index if not set by AI
        if reasoning.winner_index < 0 or reasoning.winner_index >= num_candidates:
            # Fallback to composite ranking if AI provided invalid index
            reasoning.winner_index = ranked[0][0]
            print(f"⚠️  Winner index out of range, using top-ranked candidate (index {reasoning.winner_index})")

        winner = filtered_candidates[reasoning.winner_index]

        # Set alternatives_rejected if not properly set
        if not reasoning.alternatives_rejected or len(reasoning.alternatives_rejected) < (num_candidates - 1):
            reasoning.alternatives_rejected = [
                c.name for i, c in enumerate(filtered_candidates) if i != reasoning.winner_index
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
