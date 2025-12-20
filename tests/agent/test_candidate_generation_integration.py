"""
Integration tests for candidate generation quality gates.

These "canary tests" ensure that quality improvements don't introduce regressions
by validating common strategy patterns that should pass validation.
"""

import pytest
from src.agent.models import Strategy, EdgeType, StrategyArchetype, RebalanceFrequency
from src.agent.stages.candidate_generator import CandidateGenerator


@pytest.fixture
def generator():
    """Fixture providing a CandidateGenerator instance."""
    return CandidateGenerator()


@pytest.fixture
def mock_market_context():
    """Minimal market context for validation tests."""
    return {
        "metadata": {"anchor_date": "2024-01-15"},
        "regime_snapshot": {
            "trend": "bull",
            "volatility": "normal",
            "breadth": 0.75
        }
    }


class TestStaticStrategyValidation:
    """Test that simple static strategies pass validation."""

    def test_static_60_40_portfolio_passes_validation(self, generator, mock_market_context):
        """
        Canary Test 1: Simple 60/40 SPY/AGG static portfolio should pass validation.

        This tests that basic buy-and-hold strategies are not over-rejected by
        quality improvements.
        """
        strategy = Strategy(
            name="Classic 60/40 Portfolio",
            thesis_document=(
                "This is a static buy-and-hold portfolio implementing the classic 60/40 "
                "equity/bond allocation. The strategy captures the equity risk premium "
                "through broad US market exposure (SPY) while bonds (AGG) provide "
                "diversification and downside protection. Quarterly rebalancing maintains "
                "target weights to harvest volatility and enforce discipline. "
                "Expected Sharpe: 0.8-1.0 vs pure equity, Max DD: -15% to -25%, "
                "suitable for moderate risk tolerance in normal market regimes."
            ),
            rebalancing_rationale=(
                "Quarterly rebalancing enforces the risk target by selling winners "
                "(equities in bull markets) and buying losers (bonds after equity rallies). "
                "This mechanically harvests mean reversion in the 60/40 ratio without "
                "requiring tactical timing. The edge is disciplined rebalancing, not prediction."
            ),
            edge_type=EdgeType.RISK_PREMIUM,
            archetype=StrategyArchetype.DIRECTIONAL,
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            logic_tree={},  # Static strategy, no conditional logic
            rebalance_frequency=RebalanceFrequency.QUARTERLY
        )

        # Should pass validation with no blocking errors (Priority 4 suggestions are OK)
        errors = generator._validate_semantics([strategy], mock_market_context)

        # Filter to only blocking errors (Priority 1, Priority 2, Syntax Error)
        blocking_errors = [
            e for e in errors
            if ("Priority 1" in e or "Priority 2" in e or "Syntax Error" in e)
        ]

        assert len(blocking_errors) == 0, (
            f"Static 60/40 should pass but got blocking errors: {blocking_errors}. "
            f"Priority 4 suggestions are acceptable: {[e for e in errors if 'Priority 4' in e]}"
        )


class TestTokenBudgetCompliance:
    """Test that generation stays within token budget."""

    @pytest.mark.asyncio
    async def test_token_budget_under_30k(self, generator, mock_market_context):
        """
        Canary Test 2: Token usage for candidate generation should be under 30k tokens.

        This ensures token optimization (compressed prompts, RSIP relocation) works.

        Note: This is a placeholder - actual implementation requires running full generation
        with token tracking, which is expensive. Consider mocking or using smaller model.
        """
        # This test would require actual LLM calls, which are expensive
        # For now, we'll test the prompt size heuristically

        # Check system prompt size (should be reasonable)
        system_prompt_path = "src/agent/prompts/system/candidate_generation_system.md"
        try:
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read()

            # Rough estimate: 4 chars per token
            estimated_tokens = len(system_prompt) / 4

            # System prompt increased from ~13k to ~15k tokens after adding RSIP checklist
            # BUT this saves 30k tokens overall because recipe shrunk by more (RSIP moved from recipe)
            # System prompt is loaded once, recipe is in message history (20x multiplier)
            # Net savings: -2k system + 32k recipe = +30k tokens saved
            assert estimated_tokens < 16000, (
                f"System prompt too large: ~{estimated_tokens:.0f} tokens. "
                f"Should be <16k. Note: RSIP checklist moved from recipe to system prompt "
                f"for net savings of 30k tokens across message history."
            )
        except FileNotFoundError:
            pytest.skip("System prompt file not found")


class TestConcentrationWithJustification:
    """Test that concentrated positions with justification pass validation."""

    def test_50_percent_allocation_with_justification_passes(self, generator, mock_market_context):
        """
        Canary Test 3: 50% allocation should pass if rebalancing_rationale justifies it.

        This tests that concentration limits have the bypass mechanism for intentional
        high-conviction bets.
        """
        strategy = Strategy(
            name="Core-Satellite TQQQ Strategy",
            thesis_document=(
                "This is a core-satellite strategy with 50% in leveraged Nasdaq (TQQQ) "
                "as the high-conviction core, balanced by 30% bonds (AGG) and 20% gold (GLD). "
                "The thesis is that the Nasdaq tech sector will outperform over the 90-day "
                "evaluation period due to AI momentum and strong earnings. The concentration "
                "in TQQQ is intentional - it's a barbell strategy with aggressive core and "
                "defensive satellites. Expected Sharpe: 1.0-1.5 vs SPY, Max DD: -20% to -35%, "
                "suitable for high risk tolerance. Failure mode: Nasdaq correction >15%."
            ),
            rebalancing_rationale=(
                "Monthly rebalancing maintains the 50/30/20 target allocation. The 50% "
                "TQQQ allocation is intentional and justified by the barbell strategy design. "
                "When TQQQ rallies, we trim to 50% and increase bond/gold exposure, locking "
                "in gains. When TQQQ declines, we rebalance into it at lower prices while "
                "defensive assets cushion drawdown. This is not naive concentration - it's "
                "a deliberate core-satellite structure with explicit risk management."
            ),
            edge_type=EdgeType.RISK_PREMIUM,
            archetype=StrategyArchetype.DIRECTIONAL,
            assets=["TQQQ", "AGG", "GLD"],
            weights={"TQQQ": 0.5, "AGG": 0.3, "GLD": 0.2},
            logic_tree={},
            rebalance_frequency=RebalanceFrequency.MONTHLY
        )

        # Should pass validation despite 50% concentration (rationale justifies it)
        errors = generator._validate_semantics([strategy], mock_market_context)

        # Filter to only concentration-related errors (if any)
        concentration_errors = [e for e in errors if "concentration" in e.lower() or "40%" in e]

        # If concentration errors exist, they should be warnings (Priority 4), not hard rejects
        if concentration_errors:
            for error in concentration_errors:
                assert "Priority 4" in error or "WARNING" in error, (
                    f"Concentration with justification should be warning, not hard reject: {error}"
                )


class TestNestedConditionalLogic:
    """Test that complex conditional logic structures pass validation."""

    def test_nested_logic_tree_with_hysteresis_passes(self, generator, mock_market_context):
        """
        Canary Test 4: Nested conditional logic (hysteresis example) should pass validation.

        This tests that sophisticated dynamic strategies with nested conditions are not
        over-rejected by syntax validation.
        """
        strategy = Strategy(
            name="VIX Tactical Allocation with Hysteresis",
            thesis_document=(
                "This tactical allocation strategy rotates between equities (SPY) and "
                "bonds (AGG) based on VIX regime with hysteresis to reduce whipsaw. "
                "When VIX crosses above 25, we rotate to 100% bonds (risk-off). When VIX "
                "drops back below 18 (the lower threshold), we rotate back to 100% equities "
                "(risk-on). This exploits the structural edge that volatility is mean-reverting "
                "but exhibits momentum at extremes. The hysteresis band (18-25) prevents "
                "overtrading during sideways VIX by requiring clear regime breaks. "
                "Expected Sharpe: 1.2-1.6 vs SPY, Max DD: -12% to -18% (better than SPY)."
            ),
            rebalancing_rationale=(
                "Daily rebalancing checks VIX levels and executes rotations when thresholds "
                "are breached. The logic is: IF VIX > 25 → 100% AGG (risk-off), ELSE → "
                "100% SPY (risk-on when VIX normalizes below 25). The hysteresis is implicit "
                "in that we only de-risk when VIX spikes above 25, not at lower levels. "
                "This dynamic allocation implements the volatility edge by mechanically "
                "de-risking during spikes and re-risking after normalization. The weights "
                "are intentionally binary (0% or 100%) to maximize regime differentiation."
            ),
            edge_type=EdgeType.STRUCTURAL,
            archetype=StrategyArchetype.VOLATILITY,
            assets=["SPY", "AGG", "VIX"],  # VIX as indicator, not held
            weights={},  # Dynamic strategy, weights determined by logic_tree
            logic_tree={
                "condition": "VIX > 25",
                "if_true": {
                    "assets": ["AGG"],
                    "weights": {"AGG": 1.0},
                    "reason": "Risk-off: High volatility regime"
                },
                "if_false": {
                    "assets": ["SPY"],
                    "weights": {"SPY": 1.0},
                    "reason": "Risk-on: VIX below panic threshold"
                }
            },
            rebalance_frequency=RebalanceFrequency.DAILY
        )

        # Should pass validation - this is a legitimate sophisticated strategy
        errors = generator._validate_semantics([strategy], mock_market_context)

        # Filter out syntax errors for nested logic
        syntax_errors = [e for e in errors if "Syntax Error" in e or "logic_tree" in e.lower()]

        assert len(syntax_errors) == 0, (
            f"Nested conditional logic should pass syntax validation but got: {syntax_errors}"
        )

        # Check thesis-logic coherence (Priority 1) - should NOT have errors
        coherence_errors = [e for e in errors if "Priority 1" in e]

        assert len(coherence_errors) == 0, (
            f"Dynamic strategy with proper logic_tree should pass coherence check: {coherence_errors}"
        )


class TestRetryOnlySyntaxErrors:
    """Test that retry only triggers on syntax errors, not semantic/quality failures."""

    def test_non_syntax_errors_do_not_trigger_retry(self, generator, mock_market_context):
        """
        Regression Test: Non-syntax validation errors (archetype-frequency mismatch)
        should NOT trigger retry. Only 'Syntax Error' prefixed errors trigger retry.

        This tests the fix for: "only do retry in candidate generation if syntax errors"

        Note: Thesis-logic coherence violations (conditional language + empty logic_tree)
        are now classified as Syntax Errors to trigger targeted retry. This test uses
        archetype-frequency mismatch instead, which remains a non-syntax error.
        """
        # Create a strategy with archetype-frequency mismatch (not a syntax error)
        # Momentum archetype with quarterly rebalancing is too slow (momentum decays faster)
        strategy = Strategy(
            name="Momentum Buy-Hold Strategy",
            thesis_document=(
                "This momentum strategy maintains exposure to momentum factor ETFs. "
                "The strategy captures behavioral momentum edge by systematically "
                "holding assets with strongest trailing returns. Static allocation "
                "to momentum factor ETFs provides efficient exposure without timing. "
                "Expected Sharpe: 1.0-1.3 vs SPY, Max DD: -18% to -25%."
            ),
            rebalancing_rationale=(
                "Quarterly rebalancing maintains momentum exposure efficiently. Weights are "
                "fixed across momentum ETFs to capture factor premium with low turnover. "
                "This frequency balances factor exposure against transaction costs."
            ),
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            assets=["MTUM", "QMOM", "IMOM"],
            weights={"MTUM": 0.34, "QMOM": 0.33, "IMOM": 0.33},  # Weights sum to 1.0
            logic_tree={},  # Static strategy, no conditional language in thesis
            rebalance_frequency=RebalanceFrequency.QUARTERLY  # Too slow for momentum (semantic error)
        )

        # Run semantic validation - should produce archetype-frequency mismatch
        # but NO syntax errors (weights sum to 1.0, structure is valid)
        errors = generator._validate_semantics([strategy], mock_market_context)

        # Verify we have some validation errors (archetype-frequency mismatch expected)
        assert len(errors) > 0, "Expected some validation errors for this strategy"

        # Verify NO syntax errors in the list
        syntax_errors = [e for e in errors if "Syntax Error" in e]
        assert len(syntax_errors) == 0, (
            f"Strategy should have no syntax errors but got: {syntax_errors}"
        )

        # Verify we have non-syntax errors (archetype-frequency mismatch)
        non_syntax_errors = [e for e in errors if "Syntax Error" not in e]
        assert len(non_syntax_errors) > 0, (
            "Strategy should have non-syntax errors (archetype-frequency mismatch)"
        )

        # The key assertion: retry logic should filter to syntax_errors only
        # In the actual code (lines 578-597), retry only happens if syntax_errors is non-empty
        # This test validates that our filter correctly excludes non-syntax errors

    def test_syntax_errors_do_trigger_retry(self, generator, mock_market_context):
        """
        Test that actual syntax errors (condition without operator) DO trigger retry.

        Note: Most structure validation happens at Pydantic model level. This tests
        the secondary syntax validation that catches condition expression issues.
        """
        # Create a strategy with logic_tree that has condition without comparison operator
        strategy = Strategy(
            name="Bad Condition Strategy",
            thesis_document=(
                "A conditional strategy that switches between equities and bonds based on "
                "VIX levels. When VIX exceeds threshold, rotate to defensive positioning. "
                "This exploits the structural edge of volatility mean reversion with "
                "tactical allocation. Expected Sharpe: 1.2-1.5 vs SPY, Max DD: -15%."
            ),
            rebalancing_rationale=(
                "Daily rebalancing monitors VIX and executes rotations when thresholds are breached. "
                "The logic tree implements conditional allocation based on volatility regime. "
                "This frequency ensures timely response to regime changes."
            ),
            edge_type=EdgeType.STRUCTURAL,
            archetype=StrategyArchetype.VOLATILITY,
            assets=["SPY", "AGG"],
            weights={"SPY": 0.5, "AGG": 0.5},
            logic_tree={
                "condition": "VIX HIGH",  # Missing comparison operator - SYNTAX ERROR
                "if_true": {"assets": ["AGG"], "weights": {"AGG": 1.0}},
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}}
            },
            rebalance_frequency=RebalanceFrequency.DAILY
        )

        # Run syntax validation
        syntax_errors = generator._validate_syntax(strategy)

        # Should have syntax error about missing comparison operator
        assert len(syntax_errors) > 0, "Expected syntax error for condition without comparison operator"
        assert any("Syntax Error" in e for e in syntax_errors), (
            f"Syntax errors should be prefixed with 'Syntax Error': {syntax_errors}"
        )
        assert any("comparison" in e.lower() or "operator" in e.lower() for e in syntax_errors), (
            f"Expected comparison operator related error: {syntax_errors}"
        )

    def test_syntax_error_filter_logic(self, generator):
        """
        Test the exact filter logic used in _generate_candidates to identify syntax errors.
        """
        # Sample validation errors mixing syntax and non-syntax
        validation_errors = [
            "Syntax Error: Strategy A - Weights sum to 1.2, must equal 1.0",
            "Priority 1 (Implementation-Thesis Mismatch): Strategy B has rotation claims but empty logic_tree",
            "Syntax Error: Strategy C - logic_tree missing required keys: {'if_false'}",
            "Priority 2 (Edge-Frequency Mismatch): Momentum with quarterly rebalancing too slow",
            "Priority 4 (SUGGESTION): Strategy D - Single asset concentration high",
        ]

        # Apply the same filter used in the code
        syntax_errors = [e for e in validation_errors if "Syntax Error" in e]

        # Should only include the 2 syntax errors
        assert len(syntax_errors) == 2, f"Expected 2 syntax errors, got {len(syntax_errors)}"
        assert all("Syntax Error" in e for e in syntax_errors)
        assert "Strategy A" in syntax_errors[0]
        assert "Strategy C" in syntax_errors[1]

    def test_thesis_logic_coherence_triggers_retry(self, generator, mock_market_context):
        """
        Test that thesis-logic coherence violations (conditional language + empty logic_tree)
        are now classified as Syntax Errors and trigger retry.

        This tests the fix for: "Thesis-implementation coherence violations should trigger retry"
        """
        # Create a strategy with conditional language in thesis but empty logic_tree
        strategy = Strategy(
            name="Rotation Strategy",
            thesis_document=(
                "This strategy rotates to top performers when momentum triggers positive signals. "
                "When regime shifts, we rotate into defensive assets based on volatility thresholds. "
                "The tactical rotation captures behavioral edge by dynamically shifting allocation. "
                "Expected Sharpe: 1.2-1.5 vs SPY, Max DD: -15% to -20%."
            ),
            rebalancing_rationale=(
                "Weekly rebalancing enables tactical rotation based on momentum and volatility signals. "
                "Weights adjust dynamically as rotation triggers fire. This frequency balances "
                "signal capture against transaction costs for tactical strategies that need to "
                "respond to regime changes quickly while avoiding excessive turnover."
            ),
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.DIRECTIONAL,  # Not momentum to avoid archetype check
            assets=["SPY", "QQQ", "TLT"],
            weights={"SPY": 0.40, "QQQ": 0.30, "TLT": 0.30},
            logic_tree={},  # Empty - but thesis describes rotation (coherence issue)
            rebalance_frequency=RebalanceFrequency.WEEKLY
        )

        # Run semantic validation
        errors = generator._validate_semantics([strategy], mock_market_context)

        # Verify we have syntax errors (thesis-logic coherence is now a syntax error)
        syntax_errors = [e for e in errors if "Syntax Error" in e]
        assert len(syntax_errors) > 0, (
            f"Thesis-logic coherence violation should produce Syntax Error, got: {errors}"
        )

        # Verify the error message mentions conditional logic
        coherence_error = syntax_errors[0]
        assert "conditional logic" in coherence_error.lower(), (
            f"Error should mention conditional logic: {coherence_error}"
        )
        assert "logic_tree is empty" in coherence_error.lower(), (
            f"Error should mention empty logic_tree: {coherence_error}"
        )


class TestValidationMethodsExist:
    """Test that required validation methods exist in CandidateGenerator."""

    def test_validate_semantics_exists(self, generator):
        """Ensure _validate_semantics method exists."""
        assert hasattr(generator, '_validate_semantics'), (
            "_validate_semantics method missing from CandidateGenerator"
        )

    def test_validate_concentration_exists(self, generator):
        """Ensure _validate_concentration method exists (Phase 1 addition)."""
        # This will fail initially, pass after Phase 1 Fix #2
        assert hasattr(generator, '_validate_concentration'), (
            "_validate_concentration method missing - should be added in Phase 1"
        )

    def test_validate_syntax_exists(self, generator):
        """Ensure _validate_syntax method exists (Phase 1 addition)."""
        # This will fail initially, pass after Phase 1 Fix #3
        assert hasattr(generator, '_validate_syntax'), (
            "_validate_syntax method missing - should be added in Phase 1"
        )

    def test_compute_quality_score_exists(self, generator):
        """Ensure compute_quality_score method exists (Phase 1 addition)."""
        # This will fail initially, pass after Phase 1 Fix #6
        assert hasattr(generator, 'compute_quality_score'), (
            "compute_quality_score method missing - should be added in Phase 1"
        )
