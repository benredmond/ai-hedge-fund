"""Generate charter document for selected strategy."""

import asyncio
from typing import List
import json
import os
import openai
from pydantic import ValidationError
from pydantic_ai import ModelSettings
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL,
    is_reasoning_model,
    get_model_settings,
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
        # Load prompts (compressed versions for token efficiency)
        system_prompt = load_prompt("system/charter_creation_system_compressed.md")
        recipe_prompt = load_prompt("charter_creation_compressed.md")

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
        length_warning_given = False

        for attempt in range(1, max_attempts + 1):
            try:
                # Get model-specific settings (reasoning models require temperature=1.0, max_tokens=16384)
                model_settings = get_model_settings(model, stage="charter_generation")

                agent_ctx = await create_agent(
                    model=model,
                    output_type=Charter,
                    system_prompt=system_prompt,
                    history_limit=20,
                    model_settings=model_settings
                )

                async with agent_ctx as agent:
                    # Add length reminder on retries
                    current_prompt = prompt
                    if attempt > 1 and length_warning_given:
                        current_prompt = f"""IMPORTANT: Previous attempt exceeded field length limits.
Remember the CRITICAL LENGTH CONSTRAINTS:
- market_thesis: MAX 5000 characters (target 300-800 words)
- strategy_selection: MAX 5000 characters (target 300-800 words)
- expected_behavior: MAX 5000 characters (target 300-800 words)
- outlook_90d: MAX 2000 characters (target 100-200 words)

{prompt}"""

                    # Debug logging: Print prompt being sent to LLM provider
                    print(f"\n{'='*80}")
                    print(f"[DEBUG:CharterGenerator] Sending prompt to LLM provider (attempt {attempt}/{max_attempts})")
                    print(f"[DEBUG:CharterGenerator] System prompt length: {len(system_prompt)} chars")
                    print(f"[DEBUG:CharterGenerator] User prompt length: {len(current_prompt)} chars")
                    print(f"{'='*80}")
                    if os.getenv("DEBUG_PROMPTS", "0") == "1":
                        print(f"\n[DEBUG:CharterGenerator] ========== FULL SYSTEM PROMPT ==========")
                        print(system_prompt)
                        print(f"[DEBUG:CharterGenerator] ========================================")
                        print(f"\n[DEBUG:CharterGenerator] ========== FULL USER PROMPT ==========")
                        print(current_prompt)
                        print(f"[DEBUG:CharterGenerator] ======================================")
                        print(f"{'='*80}\n")

                    result = await agent.run(current_prompt)

                    # Extract and log full reasoning content (Kimi K2, DeepSeek R1, etc.)
                    from src.agent.stages.candidate_generator import extract_and_log_reasoning
                    extract_and_log_reasoning(result, f"CharterGenerator:Attempt{attempt}")

                    charter = result.output

                    # Validate failure_modes are actual descriptions, not dict keys
                    # (pydantic may coerce dict to list via list(dict.keys()))
                    charter_field_names = {'outlook_90d', 'market_thesis', 'strategy_selection', 'expected_behavior', 'failure_modes'}
                    for i, mode in enumerate(charter.failure_modes):
                        is_json_key_fragment = (
                            len(mode) < 20 and (
                                '": ' in mode or
                                mode.strip('"').lower() in charter_field_names
                            )
                        )
                        if is_json_key_fragment:
                            raise ValueError(
                                f"failure_modes[{i}] appears to be a JSON key, not a description: '{mode}'\n"
                                f"LLM likely returned failure_modes as dict instead of List[str]."
                            )

                    # Semantic validation (check for issues even if Pydantic passed)
                    validation_warnings = self._validate_charter_semantics(charter)
                    if validation_warnings:
                        if attempt < max_attempts:
                            print(f"⚠️  Charter has semantic issues (attempt {attempt}/{max_attempts}):")
                            for warning in validation_warnings:
                                print(f"   - {warning}")
                            if any("approaching limit" in w or "exceeds" in w for w in validation_warnings):
                                length_warning_given = True
                            continue
                        else:
                            print(f"⚠️  Charter has warnings but proceeding (final attempt):")
                            for warning in validation_warnings:
                                print(f"   - {warning}")

                    # Debug: Log charter field lengths
                    print(
                        f"[DEBUG] Charter field lengths: "
                        f"thesis={len(charter.market_thesis)}, "
                        f"selection={len(charter.strategy_selection)}, "
                        f"behavior={len(charter.expected_behavior)}, "
                        f"outlook={len(charter.outlook_90d)}, "
                        f"failure_modes={len(charter.failure_modes)}"
                    )

                    # Check for truncation
                    is_truncated, truncation_reasons = self._is_truncated(charter)
                    if is_truncated:
                        if attempt < max_attempts:
                            print(f"⚠️  Charter appears truncated (attempt {attempt}/{max_attempts}):")
                            for reason in truncation_reasons:
                                print(f"   - {reason}")
                            print("   Retrying...")
                            continue
                        else:
                            reasons_str = "; ".join(truncation_reasons)
                            raise ValueError(
                                f"Charter generation incomplete after {max_attempts} attempts. "
                                f"Failed checks: {reasons_str}"
                            )

                    return charter
            except ValidationError as err:
                # Pydantic validation failed (likely max_length exceeded)
                if attempt < max_attempts:
                    print(
                        f"⚠️  Charter validation failed (attempt {attempt}/{max_attempts}). "
                        f"Error: {str(err)[:200]}... "
                        f"Retrying with length constraints reminder..."
                    )
                    length_warning_given = True
                    last_error = err
                    continue
                raise
            except ValueError as err:
                # Structure validation failed (e.g., failure_modes malformed)
                if attempt < max_attempts:
                    print(
                        f"⚠️  Charter structure invalid (attempt {attempt}/{max_attempts}). "
                        f"Error: {str(err)[:200]}... "
                        f"Retrying..."
                    )
                    last_error = err
                    continue
                raise
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

    def _validate_charter_semantics(self, charter: Charter) -> List[str]:
        """
        Validate charter for semantic issues beyond Pydantic schema.

        Checks:
        - Field lengths approaching or exceeding limits
        - Imbalanced sections (one field much longer than others)
        - Incomplete content patterns

        Returns:
            List of warning messages (empty if all checks pass)
        """
        warnings = []

        # Character limits from Charter model (relaxed limits)
        LIMITS = {
            'market_thesis': 8000,
            'strategy_selection': 8000,
            'expected_behavior': 8000,
            'outlook_90d': 4000
        }

        # Only warn if actually exceeding limits (not approaching)
        for field_name, limit in LIMITS.items():
            field_value = getattr(charter, field_name)
            field_len = len(field_value)

            if field_len > limit:
                warnings.append(
                    f"{field_name} EXCEEDS limit: {field_len}/{limit} chars. "
                    f"This will fail Pydantic validation!"
                )

        # Check for imbalanced sections (one field at max while others are short)
        major_fields = ['market_thesis', 'strategy_selection', 'expected_behavior']
        field_lengths = [len(getattr(charter, f)) for f in major_fields]
        max_len = max(field_lengths)
        min_len = min(field_lengths)

        if max_len > 4000 and min_len < max_len * 0.3:
            warnings.append(
                f"Imbalanced sections: longest={max_len} chars, shortest={min_len} chars. "
                f"Consider redistributing content more evenly."
            )

        # Check for incomplete bullet patterns (mid-field truncation)
        for field_name in ['market_thesis', 'strategy_selection',
                          'expected_behavior', 'outlook_90d']:
            field_value = getattr(charter, field_name)
            if field_value.rstrip().endswith((':\n- ', ':\n-', ':\n')):
                warnings.append(
                    f"{field_name} ends with incomplete bullet list. "
                    f"Likely truncated mid-generation."
                )

        return warnings

    def _is_truncated(self, charter: Charter) -> tuple[bool, list[str]]:
        """
        Detect if charter was truncated during generation.

        Uses minimal heuristic checks - only catch obvious truncation:
        - Minimum field lengths (very short = clearly incomplete)
        - Minimum failure modes count (≥3 expected)

        Returns:
            Tuple of (is_truncated, list of failure reasons)
        """
        reasons = []

        # Check minimum field lengths (very lenient - just catch empty/near-empty)
        if len(charter.market_thesis) < 50:
            reasons.append(f"market_thesis: {len(charter.market_thesis)} chars (min 50)")
        if len(charter.strategy_selection) < 50:
            reasons.append(f"strategy_selection: {len(charter.strategy_selection)} chars (min 50)")
        if len(charter.expected_behavior) < 50:
            reasons.append(f"expected_behavior: {len(charter.expected_behavior)} chars (min 50)")
        if len(charter.outlook_90d) < 30:
            reasons.append(f"outlook_90d: {len(charter.outlook_90d)} chars (min 30)")

        # Check minimum failure modes (expect at least 3)
        if len(charter.failure_modes) < 3:
            reasons.append(f"failure_modes: {len(charter.failure_modes)} items (min 3)")

        return (len(reasons) > 0, reasons)
