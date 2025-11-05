"""Generate charter document for selected strategy."""

import asyncio
from typing import List
import json
import openai
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL
)
from src.agent.models import (
    Strategy,
    Charter,
    SelectionReasoning,
    EdgeScorecard
)
from pydantic_ai.exceptions import ModelHTTPError


class CharterGenerator:
    """
    Stage 4: Generate charter document.

    Creates comprehensive charter with market thesis, selection reasoning,
    expected behavior, failure modes, and 90-day outlook.

    Uses all selection context from prior stages:
    - Winner strategy and Edge Scorecard evaluation
    - Selection reasoning (why this vs alternatives)
    - Edge scorecard scores for all 5 candidates (institutional evaluation)
    - Market context for tool-based regime analysis
    """

    async def generate(
        self,
        winner: Strategy,
        reasoning: SelectionReasoning,
        candidates: List[Strategy],
        scorecards: List[EdgeScorecard],
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
            market_context: Current market regime (date-anchored)
            model: LLM model identifier

        Returns:
            Complete Charter document with 5 sections
        """
        # Load prompts
        system_prompt = load_prompt("system/charter_creation_system.md")
        recipe_prompt = load_prompt("charter_creation.md")

        # Build selection context
        winner_idx = reasoning.winner_index
        winner_scorecard = scorecards[winner_idx]

        # Format selection context for agent
        # Serialize all context
        selection_context = {
            "winner": {
                "name": winner.name,
                "assets": winner.assets,
                "weights": winner.weights,
                "rebalance_frequency": winner.rebalance_frequency.value,
                "edge_type": getattr(winner.edge_type, "value", winner.edge_type),
                "archetype": getattr(winner.archetype, "value", winner.archetype),
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
            "all_candidates": [],
            "market_context_summary": {
                "anchor_date": market_context["metadata"]["anchor_date"],
                "regime_tags": market_context.get("regime_tags", []),
                "regime_snapshot": market_context.get("regime_snapshot", {})
            }
        }

        for i, (candidate, scorecard) in enumerate(zip(candidates, scorecards)):
            selection_context["all_candidates"].append({
                "index": i,
                "name": candidate.name,
                "assets": candidate.assets,
                "edge_type": getattr(candidate.edge_type, "value", candidate.edge_type),
                "archetype": getattr(candidate.archetype, "value", candidate.archetype),
                "is_winner": i == winner_idx,
                "edge_score": scorecard.total_score
            })

        selection_context_json = json.dumps(selection_context, indent=2)

        prompt = f"""Create a comprehensive charter document for the selected strategy.

## SELECTION CONTEXT FROM PRIOR STAGES

You have access to the complete selection context from Stages 1-3:

{selection_context_json}

## INSTRUCTIONS FROM RECIPE

{recipe_prompt}

## YOUR TASK

Follow the workflow in the recipe:

**Pre-Work**: Parse the SelectionReasoning and Edge Scorecard results above.

**Phase 1: Market Data Gathering**
- Use FRED tools (fred_get_series) for macro regime classification
- Use yfinance tools (stock_get_historical_stock_prices) for market regime analysis
- Ground Market Thesis section in tool data (not just the context summary above)

**Phase 2: Charter Writing**
- Section 1 (Market Thesis): Tool-cited, connect regime to strategy's edge
- Section 2 (Strategy Selection): Integrate SelectionReasoning verbatim, cite Edge Scorecard scores, compare Edge evaluations vs alternatives
- Section 3 (Expected Behavior): Best/base/worst case scenarios + regime transitions
- Section 4 (Failure Modes): 3-8 specific, measurable conditions (use templates from recipe)
- Section 5 (90-Day Outlook): Milestones (Day 30/60/90) + red flags from failure modes

**Critical Requirements**:
1. Strategy Selection MUST reference why_selected, alternatives_rejected, tradeoffs_accepted
2. MUST cite Edge Scorecard scores (total + 2-3 dimensions) and compare across all 5 candidates
3. MUST use FRED and yfinance tools for current data (don't rely only on context summary)
4. Failure modes MUST be specific with: Condition + Impact + Early Warning
5. Run Pre-Submission Checklist before returning Charter

Begin by using MCP tools to gather current market data, then write the 5-section charter.
"""

        # Use 20 message history limit (complex synthesis with tools)
        charter = await self._run_with_retries(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt
        )

        # Debug logging: Print full LLM response
        print(f"\n[DEBUG:CharterGenerator] Full LLM response:")
        print(f"{charter}")

        return charter

    async def _run_with_retries(
        self,
        prompt: str,
        model: str,
        system_prompt: str,
        max_attempts: int = 3,
        base_delay: float = 5.0
    ) -> Charter:
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                agent_ctx = await create_agent(
                    model=model,
                    output_type=Charter,
                    system_prompt=system_prompt,
                    history_limit=20
                )

                async with agent_ctx as agent:
                    result = await agent.run(prompt)
                    return result.output
            except ModelHTTPError as err:
                if getattr(err, "status_code", None) == 429 and attempt < max_attempts:
                    wait_time = base_delay * (2 ** (attempt - 1))
                    print(
                        f"⚠️  Charter generation hit model rate limit (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                    last_error = err
                    continue
                raise
            except openai.RateLimitError as err:
                if attempt < max_attempts:
                    wait_time = base_delay * (2 ** (attempt - 1))
                    print(
                        f"⚠️  Charter generation hit OpenAI rate limit (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                    last_error = err
                    continue
                raise

        if last_error is not None:
            raise last_error

        raise RuntimeError("Charter generation failed without raising an error")
