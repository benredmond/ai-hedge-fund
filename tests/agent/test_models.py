"""
Tests for Pydantic models (Strategy and Charter).
Following TDD: Write tests first, then implement models.
"""

import pytest
from pydantic import ValidationError


class TestStrategyModel:
    """Test Strategy model validation"""

    def test_valid_strategy_accepted(self):
        """Valid strategy with all required fields passes validation"""
        from src.agent.models import Strategy

        strategy = Strategy(
            name="60/40 Portfolio",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            rebalance_frequency="monthly",
            logic_tree={},
            rebalancing_rationale="Monthly equal-weight rebalancing implements mean-reversion by mechanically buying relative losers and selling relative winners, exploiting temporary sector rotation overshoots that typically reverse within 30-60 days."
        )

        assert strategy.name == "60/40 Portfolio"
        assert len(strategy.assets) == 2
        assert sum(strategy.weights.values()) == pytest.approx(1.0)

    def test_empty_assets_rejected(self):
        """Strategy with empty assets list fails validation"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="at least 1 item"):
            Strategy(
                name="Empty Strategy",
                assets=[],
                weights={},
                rebalance_frequency="monthly",
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_weights_must_sum_to_one(self):
        """Strategy weights must sum to 1.0 within tolerance"""
        from src.agent.models import Strategy

        # Too low
        with pytest.raises(ValidationError, match="sum to"):
            Strategy(
                name="Incomplete",
                assets=["SPY"],
                weights={"SPY": 0.5},
                rebalance_frequency="monthly",
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

        # Too high
        with pytest.raises(ValidationError, match="sum to"):
            Strategy(
                name="Overweight",
                assets=["SPY"],
                weights={"SPY": 1.5},
                rebalance_frequency="monthly",
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_weights_tolerance_accepted(self):
        """Weights within 0.99-1.01 are accepted with normalization"""
        from src.agent.models import Strategy

        # Slightly under 1.0 (acceptable)
        strategy = Strategy(
            name="Slightly Under",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.595, "AGG": 0.40},  # Sums to 0.995
            rebalance_frequency="monthly",
            logic_tree={},
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
        )
        assert sum(strategy.weights.values()) == pytest.approx(1.0, abs=0.01)

    def test_weights_missing_asset(self):
        """Weights must include all assets"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="cover all assets"):
            Strategy(
                name="Missing Weight",
                assets=["SPY", "QQQ", "AGG"],
                weights={"SPY": 0.6, "QQQ": 0.4},  # AGG missing
                rebalance_frequency="monthly",
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_weights_extra_asset(self):
        """Weights cannot include assets not in assets list"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="cover all assets"):
            Strategy(
                name="Extra Weight",
                assets=["SPY"],
                weights={"SPY": 0.7, "QQQ": 0.3},  # QQQ not in assets
                rebalance_frequency="monthly",
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_rebalance_frequency_enum(self):
        """Rebalance frequency must be valid enum value"""
        from src.agent.models import Strategy

        # Valid values
        for freq in ["daily", "weekly", "monthly", "quarterly", "none"]:
            strategy = Strategy(
                name="Test",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency=freq,
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )
            assert strategy.rebalance_frequency == freq

        # Invalid value
        with pytest.raises(ValidationError):
            Strategy(
                name="Test",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency="every_tuesday",
                logic_tree={},
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_dynamic_strategy_with_empty_weights(self):
        """Dynamic strategies (with logic_tree) can have empty weights"""
        from src.agent.models import Strategy

        strategy = Strategy(
            name="VIX Rotation",
            assets=["SPY", "TLT", "GLD"],
            weights={},  # Empty - allocation defined in logic_tree
            logic_tree={
                "condition": "VIX > 20",
                "if_true": {"assets": ["TLT", "GLD"], "weights": {"TLT": 0.6, "GLD": 0.4}},
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}}
            },
            rebalance_frequency="daily",
            rebalancing_rationale="Daily rebalancing implements VIX rotation edge by checking volatility threshold and shifting allocation when VIX crosses 20 (defensive) or drops below 15 (growth)."
        )

        assert strategy.weights == {}
        assert strategy.logic_tree != {}
        assert len(strategy.assets) == 3

    def test_dynamic_strategy_with_partial_weights(self):
        """Dynamic strategies can have partial weights that sum to 1.0"""
        from src.agent.models import Strategy

        strategy = Strategy(
            name="Momentum Rotation",
            assets=["XLK", "XLF", "XLY", "XLE"],
            weights={"XLK": 0.4, "XLF": 0.6},  # Partial weights as default, logic_tree overrides
            logic_tree={
                "condition": "momentum_90d > 0",
                "if_true": {"assets": ["XLK", "XLF"], "weights": {"XLK": 0.6, "XLF": 0.4}},
                "if_false": {"assets": ["XLY", "XLE"], "weights": {"XLY": 0.5, "XLE": 0.5}}
            },
            rebalance_frequency="monthly",
            rebalancing_rationale="Monthly rebalancing selects top 2 sectors by 90-day momentum, implementing sector rotation edge by systematically increasing allocation to recent winners and decreasing laggards, which exploits the 6-12 week institutional rebalancing lag."
        )

        assert sum(strategy.weights.values()) == pytest.approx(1.0)
        assert strategy.logic_tree != {}

    def test_static_strategy_requires_all_weights(self):
        """Static strategies (empty logic_tree) must have weights for all assets"""
        from src.agent.models import Strategy

        # Missing weights for some assets
        with pytest.raises(ValidationError, match="cover all assets"):
            Strategy(
                name="Static Portfolio",
                assets=["SPY", "TLT", "GLD"],
                weights={"SPY": 0.6, "TLT": 0.4},  # GLD missing
                logic_tree={},  # Static strategy
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_static_strategy_cannot_have_empty_weights(self):
        """Static strategies (empty logic_tree) cannot have empty weights"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="cannot be empty for static strategies"):
            Strategy(
                name="Static Portfolio",
                assets=["SPY", "TLT"],
                weights={},  # Empty weights not allowed for static
                logic_tree={},  # Static strategy
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_dynamic_strategy_weights_must_be_subset_of_assets(self):
        """Dynamic strategy weights (if provided) cannot include assets not in assets list"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="not in assets list"):
            Strategy(
                name="VIX Rotation",
                assets=["SPY", "TLT"],
                weights={"SPY": 0.6, "GLD": 0.4},  # GLD not in assets list
                logic_tree={
                    "condition": "VIX > 20",
                    "if_true": {"assets": ["TLT"], "weights": {"TLT": 1.0}},
                    "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}}
                },
                rebalance_frequency="daily",
                rebalancing_rationale="Daily VIX rotation implements volatility regime changes by checking threshold every market day and shifting allocation when VIX crosses 20, exploiting the 2-4 day institutional rebalancing lag that exists due to committee approval requirements."
            )

    def test_dynamic_strategy_partial_weights_must_sum_to_one(self):
        """Dynamic strategy partial weights (if provided) must sum to 1.0"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="sum to"):
            Strategy(
                name="Momentum Rotation",
                assets=["XLK", "XLF", "XLY"],
                weights={"XLK": 0.3, "XLF": 0.3},  # Sums to 0.6, not 1.0
                logic_tree={
                    "condition": "VIX > 20",
                    "if_true": {"assets": ["XLK"], "weights": {"XLK": 1.0}},
                    "if_false": {"assets": ["XLF", "XLY"], "weights": {"XLF": 0.5, "XLY": 0.5}}
                },
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly momentum rotation selects top 2 sectors by 90-day momentum, implementing sector rotation edge by systematically increasing allocation to recent winners and decreasing laggards, exploiting institutional rebalancing lag."
            )


class TestLogicTreeValidation:
    """Test logic_tree structure validation"""

    def test_empty_logic_tree_accepted(self):
        """Empty logic_tree is valid for static strategies"""
        from src.agent.models import Strategy

        strategy = Strategy(
            name="Static Portfolio",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            logic_tree={},
            rebalance_frequency="monthly",
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
        )
        assert strategy.logic_tree == {}

    def test_valid_conditional_logic_tree_accepted(self):
        """Valid conditional logic_tree with {condition, if_true, if_false} is accepted"""
        from src.agent.models import Strategy

        strategy = Strategy(
            name="VIX Rotation",
            assets=["SPY", "TLT", "GLD"],
            weights={},
            logic_tree={
                "condition": "VIX > 22",
                "if_true": {"assets": ["TLT", "GLD"], "weights": {"TLT": 0.6, "GLD": 0.4}},
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}}
            },
            rebalance_frequency="daily",
            rebalancing_rationale="Daily VIX rotation implements volatility regime changes by checking threshold every market day and shifting allocation when VIX exceeds 22, exploiting institutional rebalancing lag."
        )
        assert "condition" in strategy.logic_tree
        assert "if_true" in strategy.logic_tree
        assert "if_false" in strategy.logic_tree

    def test_flat_parameter_dict_rejected(self):
        """Flat parameter dict without {condition, if_true, if_false} is rejected"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="must have keys"):
            Strategy(
                name="Bad Strategy",
                assets=["SPY", "TLT"],
                weights={"SPY": 0.6, "TLT": 0.4},
                logic_tree={"market_condition": "fed_pivot", "yield_curve": "normalizing"},
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_logic_tree_missing_condition_rejected(self):
        """logic_tree with if_true/if_false but missing condition is rejected"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="Missing.*condition"):
            Strategy(
                name="Bad Strategy",
                assets=["SPY", "TLT"],
                weights={},
                logic_tree={
                    "if_true": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
                    "if_false": {"assets": ["TLT"], "weights": {"TLT": 1.0}}
                },
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_logic_tree_branch_missing_assets_rejected(self):
        """logic_tree branch without assets key is rejected"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="must have 'assets' and 'weights'"):
            Strategy(
                name="Bad Strategy",
                assets=["SPY", "TLT"],
                weights={},
                logic_tree={
                    "condition": "VIX > 20",
                    "if_true": {"weights": {"SPY": 1.0}},  # Missing assets
                    "if_false": {"assets": ["TLT"], "weights": {"TLT": 1.0}}
                },
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_logic_tree_branch_not_dict_rejected(self):
        """logic_tree branch that is not a dict is rejected"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="must be a dict"):
            Strategy(
                name="Bad Strategy",
                assets=["SPY", "TLT"],
                weights={},
                logic_tree={
                    "condition": "VIX > 20",
                    "if_true": "SPY",  # Not a dict
                    "if_false": {"assets": ["TLT"], "weights": {"TLT": 1.0}}
                },
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_logic_tree_branch_with_empty_assets_rejected(self):
        """logic_tree branch with empty assets list is rejected"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="must be a non-empty list"):
            Strategy(
                name="Bad Strategy",
                assets=["SPY", "TLT"],
                weights={},
                logic_tree={
                    "condition": "VIX > 20",
                    "if_true": {"assets": [], "weights": {"SPY": 1.0}},  # Empty assets
                    "if_false": {"assets": ["TLT"], "weights": {"TLT": 1.0}}
                },
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )

    def test_logic_tree_branch_with_empty_weights_rejected(self):
        """logic_tree branch with empty weights dict is rejected"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="must be a non-empty dict"):
            Strategy(
                name="Bad Strategy",
                assets=["SPY", "TLT"],
                weights={},
                logic_tree={
                    "condition": "VIX > 20",
                    "if_true": {"assets": ["SPY"], "weights": {}},  # Empty weights
                    "if_false": {"assets": ["TLT"], "weights": {"TLT": 1.0}}
                },
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights."
            )


class TestCharterModel:
    """Test Charter model validation"""

    def test_valid_charter_accepted(self):
        """Valid charter with all required fields passes validation"""
        from src.agent.models import Charter

        charter = Charter(
            market_thesis="Bull market driven by AI adoption",
            strategy_selection="Selected 60/40 for risk-adjusted returns",
            expected_behavior="Outperform in rising markets, lag in bear markets",
            failure_modes=["Bond yields spike above 6%", "AI bubble bursts", "Recession fears spike"],
            outlook_90d="Expect 5-10% returns over next 90 days"
        )

        assert "AI adoption" in charter.market_thesis
        assert len(charter.failure_modes) >= 3

    def test_empty_failure_modes_rejected(self):
        """Charter must have at least 3 failure modes"""
        from src.agent.models import Charter

        with pytest.raises(ValidationError, match="at least 3"):
            Charter(
                market_thesis="Test thesis",
                strategy_selection="Test selection",
                expected_behavior="Test behavior",
                failure_modes=[],  # Empty list not allowed
                outlook_90d="Test outlook"
            )

    def test_required_fields_present(self):
        """Charter requires all fields to be non-empty strings"""
        from src.agent.models import Charter

        # Missing market_thesis
        with pytest.raises(ValidationError):
            Charter(
                market_thesis="",  # Empty string
                strategy_selection="Selection",
                expected_behavior="Behavior",
                failure_modes=["Failure mode 1", "Failure mode 2", "Failure mode 3"],
                outlook_90d="Outlook"
            )

    def test_failure_modes_minimum_length(self):
        """Each failure mode must be meaningful (min 10 chars)"""
        from src.agent.models import Charter

        # Too short failure mode (with 3 modes, one too short)
        with pytest.raises(ValidationError, match="at least 10 characters"):
            Charter(
                market_thesis="This is a valid thesis with enough characters",
                strategy_selection="This is a valid selection rationale",
                expected_behavior="This is valid expected behavior description",
                failure_modes=["Valid first mode", "Valid second mode", "Bad"],  # Third too short
                outlook_90d="This is a valid 90-day outlook"
            )

        # All failure modes long enough
        charter = Charter(
            market_thesis="This is a valid thesis with enough characters",
            strategy_selection="This is a valid selection rationale",
            expected_behavior="This is valid expected behavior description",
            failure_modes=["Market crash occurs", "VIX spikes above 30", "Fed pivots hawkish"],
            outlook_90d="This is a valid 90-day outlook"
        )
        assert len(charter.failure_modes) == 3


class TestEdgeScorecardModel:
    """Test EdgeScorecard model validation"""

    def test_valid_scorecard_accepted(self):
        """Valid scorecard with all dimensions 3-5 passes validation"""
        from src.agent.models import EdgeScorecard

        scorecard = EdgeScorecard(
            thesis_quality=4,
            edge_economics=3,
            risk_framework=3,
            regime_awareness=5,
            strategic_coherence=4
        )

        assert scorecard.thesis_quality == 4
        assert scorecard.total_score == pytest.approx(3.8, abs=0.01)

    def test_dimension_minimum_is_one(self):
        """Dimensions can be 1-5 (filtering happens in winner_selector, not validation)"""
        from src.agent.models import EdgeScorecard

        # Score of 1 is valid (low quality, but structurally valid)
        scorecard = EdgeScorecard(
            thesis_quality=1,
            edge_economics=1,
            risk_framework=1,
            regime_awareness=1,
            strategic_coherence=1
        )
        assert scorecard.total_score == 1.0

        # Score of 0 should fail
        with pytest.raises(ValidationError):
            EdgeScorecard(
                thesis_quality=0,  # Below minimum
                edge_economics=3,
                risk_framework=4,
                regime_awareness=3,
                strategic_coherence=3
            )

    def test_dimension_above_max_rejected(self):
        """Dimensions cannot exceed 5"""
        from src.agent.models import EdgeScorecard

        with pytest.raises(ValidationError):
            EdgeScorecard(
                thesis_quality=6,  # Above maximum
                edge_economics=4,
                risk_framework=4,
                regime_awareness=3,
                strategic_coherence=3
            )

    def test_total_score_calculation(self):
        """total_score property calculates average correctly"""
        from src.agent.models import EdgeScorecard

        scorecard = EdgeScorecard(
            thesis_quality=3,
            edge_economics=3,
            risk_framework=3,
            regime_awareness=3,
            strategic_coherence=3
        )
        assert scorecard.total_score == 3.0

        scorecard2 = EdgeScorecard(
            thesis_quality=5,
            edge_economics=5,
            risk_framework=5,
            regime_awareness=5,
            strategic_coherence=5
        )
        assert scorecard2.total_score == 5.0


class TestSelectionReasoningModel:
    """Test SelectionReasoning model validation"""

    def test_valid_reasoning_accepted(self):
        """Valid selection reasoning passes validation"""
        from src.agent.models import SelectionReasoning

        reasoning = SelectionReasoning(
            winner_index=2,
            why_selected="This strategy was selected because it has the highest Sharpe ratio (2.1) combined with excellent regime alignment and low drawdown risk.",
            tradeoffs_accepted="Accepting higher short-term volatility for superior risk-adjusted returns over the full evaluation period",
            alternatives_rejected=["Strategy A", "Strategy B", "Strategy C", "Strategy D"],
            conviction_level=0.85
        )

        assert reasoning.winner_index == 2
        assert len(reasoning.alternatives_rejected) == 4

    def test_winner_index_out_of_range_rejected(self):
        """Winner index must be 0-4"""
        from src.agent.models import SelectionReasoning

        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=5,  # Out of range
                why_selected="This strategy was selected for its superior risk-adjusted returns and alignment with current market regime.",
                tradeoffs_accepted="Minimal tradeoffs given strong alignment across all dimensions",
                alternatives_rejected=["A", "B", "C", "D"],
                conviction_level=0.9
            )

    def test_why_selected_too_short_rejected(self):
        """why_selected must be at least 100 chars"""
        from src.agent.models import SelectionReasoning

        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=0,
                why_selected="Good strategy.",  # Too short
                tradeoffs_accepted="Accepting standard market beta exposure for simplicity",
                alternatives_rejected=["A", "B", "C", "D"],
                conviction_level=0.7
            )

    def test_alternatives_count_bounds(self):
        """Must have 1-4 alternatives (varies based on how many passed quality gate)"""
        from src.agent.models import SelectionReasoning

        # 1 alternative is valid (4 candidates, 1 passed besides winner)
        reasoning_1 = SelectionReasoning(
            winner_index=0,
            why_selected="This strategy was selected because it has the highest Sharpe ratio combined with excellent regime alignment.",
            tradeoffs_accepted="Standard tradeoffs between return and risk apply here",
            alternatives_rejected=["A"],
            conviction_level=0.8
        )
        assert len(reasoning_1.alternatives_rejected) == 1

        # 4 alternatives is valid (all 4 other candidates passed quality gate)
        reasoning_4 = SelectionReasoning(
            winner_index=0,
            why_selected="This strategy was selected because it has the highest Sharpe ratio combined with excellent regime alignment.",
            tradeoffs_accepted="Standard tradeoffs between return and risk apply here",
            alternatives_rejected=["A", "B", "C", "D"],
            conviction_level=0.8
        )
        assert len(reasoning_4.alternatives_rejected) == 4

        # 0 alternatives should fail (must have at least 1)
        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=0,
                why_selected="This strategy was selected because it has the highest Sharpe ratio combined with excellent regime alignment.",
                tradeoffs_accepted="Standard tradeoffs between return and risk apply here",
                alternatives_rejected=[],  # Empty not allowed
                conviction_level=0.8
            )

        # 5 alternatives should fail (max is 4)
        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=0,
                why_selected="This strategy was selected because it has the highest Sharpe ratio combined with excellent regime alignment.",
                tradeoffs_accepted="Standard tradeoffs between return and risk apply here",
                alternatives_rejected=["A", "B", "C", "D", "E"],  # 5 is too many
                conviction_level=0.8
            )


class TestWorkflowResultModel:
    """Test WorkflowResult model validation"""

    def test_valid_workflow_result_accepted(self):
        """Valid workflow result with all fields passes validation"""
        from src.agent.models import WorkflowResult, Strategy, Charter, EdgeScorecard, SelectionReasoning

        # Create 5 candidates
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=["SPY", "AGG"],
                weights={"SPY": 0.6, "AGG": 0.4},
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )
            for i in range(5)
        ]

        # Create scorecards
        scorecards = [
            EdgeScorecard(
                thesis_quality=3,
                edge_economics=4,
                risk_framework=3,
                regime_awareness=3,
                strategic_coherence=4
            )
            for _ in range(5)
        ]

        # Create charter
        charter = Charter(
            market_thesis="Strong bull market with AI adoption driving growth",
            strategy_selection="Selected for best risk-adjusted returns",
            expected_behavior="Outperform in rising markets, moderate downside protection",
            failure_modes=["VIX spikes above 30", "Fed pivots hawkish", "Recession fears spike"],
            outlook_90d="Expect continued uptrend with potential 5-10% gains"
        )

        # Create reasoning
        reasoning = SelectionReasoning(
            winner_index=0,
            why_selected="This strategy achieved the best composite score combining Edge Scorecard dimensions across thesis quality, edge economics, risk framework, regime awareness, and strategic coherence metrics for optimal regime fit.",
            tradeoffs_accepted="Accepting moderate sector concentration for stronger momentum exposure",
            alternatives_rejected=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"],
            conviction_level=0.82
        )

        # Create workflow result
        result = WorkflowResult(
            strategy=candidates[0],
            charter=charter,
            all_candidates=candidates,
            scorecards=scorecards,
            selection_reasoning=reasoning
        )

        assert len(result.all_candidates) == 5

    def test_exactly_five_candidates_enforced(self):
        """Must have exactly 5 candidates"""
        from src.agent.models import WorkflowResult, Strategy, Charter, EdgeScorecard, SelectionReasoning

        # Create 3 candidates (wrong count)
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency="monthly",
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )
            for i in range(3)
        ]

        charter = Charter(
            market_thesis="Test thesis",
            strategy_selection="Test selection",
            expected_behavior="Test behavior",
            failure_modes=["Test failure mode 1", "Test failure mode 2", "Test failure mode 3"],
            outlook_90d="Test outlook"
        )

        reasoning = SelectionReasoning(
            winner_index=0,
            why_selected="This is test reasoning with enough characters to pass validation requirements for the minimum length of 100 characters.",
            tradeoffs_accepted="Minimal tradeoffs for this test case scenario validation",
            alternatives_rejected=["A", "B", "C", "D"],
            conviction_level=0.75
        )

        with pytest.raises(ValidationError, match="at least 5 items"):
            WorkflowResult(
                strategy=candidates[0],
                charter=charter,
                all_candidates=candidates,  # Only 3
                scorecards=[],
                selection_reasoning=reasoning
            )


class TestCandidateListModel:
    """Test CandidateList wrapper model that enforces exactly 5 strategies."""

    def _make_strategy(self, name: str) -> "Strategy":
        """Helper to create a valid Strategy for testing."""
        from src.agent.models import Strategy
        return Strategy(
            name=name,
            assets=["SPY", "QQQ"],
            weights={"SPY": 0.6, "QQQ": 0.4},
            rebalance_frequency="monthly",
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes.",
            thesis_document=""
        )

    def test_exactly_five_strategies_accepted(self):
        """CandidateList with exactly 5 strategies passes validation"""
        from src.agent.models import CandidateList

        strategies = [self._make_strategy(f"Strategy {i}") for i in range(5)]
        candidate_list = CandidateList(strategies=strategies)

        assert len(candidate_list.strategies) == 5

    def test_fewer_than_five_rejected(self):
        """CandidateList with fewer than 5 strategies fails validation"""
        from src.agent.models import CandidateList

        # 1 strategy
        with pytest.raises(ValidationError, match="at least 5"):
            CandidateList(strategies=[self._make_strategy("Only One")])

        # 3 strategies
        with pytest.raises(ValidationError, match="at least 5"):
            CandidateList(strategies=[self._make_strategy(f"Strategy {i}") for i in range(3)])

        # 4 strategies
        with pytest.raises(ValidationError, match="at least 5"):
            CandidateList(strategies=[self._make_strategy(f"Strategy {i}") for i in range(4)])

    def test_more_than_five_rejected(self):
        """CandidateList with more than 5 strategies fails validation"""
        from src.agent.models import CandidateList

        # 6 strategies
        with pytest.raises(ValidationError, match="at most 5"):
            CandidateList(strategies=[self._make_strategy(f"Strategy {i}") for i in range(6)])

        # 10 strategies
        with pytest.raises(ValidationError, match="at most 5"):
            CandidateList(strategies=[self._make_strategy(f"Strategy {i}") for i in range(10)])

    def test_empty_list_rejected(self):
        """CandidateList with empty strategies list fails validation"""
        from src.agent.models import CandidateList

        with pytest.raises(ValidationError, match="at least 5"):
            CandidateList(strategies=[])

    def test_strategies_are_accessible(self):
        """CandidateList.strategies returns the list of Strategy objects"""
        from src.agent.models import CandidateList

        strategies = [self._make_strategy(f"Strategy {i}") for i in range(5)]
        candidate_list = CandidateList(strategies=strategies)

        # Verify each strategy is accessible and has correct name
        for i, strategy in enumerate(candidate_list.strategies):
            assert strategy.name == f"Strategy {i}"
            assert len(strategy.assets) == 2

